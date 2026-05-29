#!/usr/bin/env python3
"""PR-5 — orquestrador do funil derivado: DAG + sentinelas + guarda-corpos.

Reconstrói os derivados em data/ e o site em docs/ a partir dos INSUMOS versionados
(data/scisci_results.json + data/oa_cache/), em ordem topológica. Cada fase declara
o que LÊ e ESCREVE; pula fases cujas saídas já existem (sentinela natural) salvo
--force; grava data/.done_<fase> e um relatório de execução (estilo
00_registro_execucao.csv).

Guarda-corpos:
  - Sanidade (espelha a Célula 3 do Colab): aborta cedo se scisci_results.json
    faltar, for JSON inválido ou tiver corpus vazio.
  - Budget (fases de REDE, modo online): consulta budget.budget_status() e
    pré-estima volume com 1 group_by (custo de 1 filtro); se não couber no teto
    (OA_DAILY_CAP_USD) pula a fase de rede com aviso (degrada, não trava).
  - Degradação graciosa: sem API-key, avisa e segue no pool grátis; --offline força
    cache-only (OA_OFFLINE=1, zero fetch) — é como a CI regenera sem gastar budget.

A regra de pulo é "saída já existe" (não re-roda crawl cujo derivado está
versionado); por isso, num checkout limpo, só regenera o que falta (ex.:
data/author_network.json, gitignored no PR-3) e reconstrói o site. --force re-roda
tudo (recomendado online, p/ consistência total).

Uso:
  python src/run_all.py [--offline] [--force] [--dry-run] [--only f1,f2] [--list]
"""
import argparse
import csv
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import budget      # noqa: E402  (PR-4 — teto/contabilidade de custo)
import data_io     # noqa: E402  (PR-2 — leitura tolerante)

REPORT = os.path.join(ROOT, "data", "run_all_report.csv")


def _p(name):
    """Caminho de uma saída declarada: data/<name> ou, se começar com 'docs/', sob ROOT."""
    if name.startswith("docs/"):
        return os.path.join(ROOT, name)
    return data_io.data_path(name)


def _sentinel(name):
    return os.path.join(ROOT, "data", f".done_{name}")


# ─────────────────────────────────────────────────────────────────────────────
# DAG — ordem topológica do insumo (scisci_results + cache) ao site.
# Cada fase: script (em src/), reads/writes (derivados), network (toca a rede?).
# As 4 últimas são puro-cache/cálculo (não fazem fetch). build_site sempre roda.
# ─────────────────────────────────────────────────────────────────────────────
PHASES = [
    {"name": "enrich",        "script": "enrich_rayyan.py",          "reads": ["scisci_results.json"],
     "writes": ["openalex_enrich.json"], "network": True},
    {"name": "cplx",          "script": "cplx_works.py",             "reads": [],
     "writes": ["cplx_works.json"], "network": True},
    {"name": "author_works",  "script": "author_snowball.py",        "reads": ["scisci_results.json"],
     "writes": ["author_works.json"], "network": True},
    {"name": "cross_brasil",  "script": "cross_brasil.py",           "reads": ["scisci_results.json"],
     "writes": ["cross_brasil.json"], "network": True},
    {"name": "brazil",        "script": "brazil_snowball.py",        "reads": [],
     "writes": ["brazil_expanded.json"], "network": True},
    {"name": "depth2",        "script": "depth2_snowball.py",        "reads": ["scisci_results.json"],
     "writes": ["depth2_corpus.json"], "network": True},
    {"name": "network",       "script": "build_network.py",          "reads": ["scisci_results.json"],
     "writes": ["network.json"], "network": True},
    {"name": "network_4axis", "script": "experiment_cplx.py",        "reads": [],
     "writes": ["network_4axis.json"], "network": True},
    {"name": "hypergraph",    "script": "cocitation_hypergraph.py",  "reads": ["network_4axis.json"],
     "writes": ["cocitation_hyperedges.json"], "network": True},
    {"name": "author_network", "script": "author_network.py",        "reads": [],
     "writes": ["author_network.json", "author_snowball_expansion.json", "adjacent_tradition_probes.json"],
     "network": True},
    {"name": "temporal",      "script": "temporal_cocitation.py",    "reads": ["scisci_results.json"],
     "writes": ["temporal_cocitation.json"], "network": False},
    {"name": "ho_bc",         "script": "higher_order_betweenness.py", "reads": ["cocitation_hyperedges.json"],
     "writes": ["higher_order_bc.json"], "network": False},
    {"name": "bridge_priority", "script": "bridge_priority.py",      "reads": ["cocitation_hyperedges.json", "network_4axis.json"],
     "writes": ["bridge_priority.json"], "network": False},
    {"name": "brokerage",     "script": "brokerage_roles.py",        "reads": ["author_network.json"],
     "writes": ["brokerage_roles.json"], "network": False},
    {"name": "solidity",      "script": "solidity.py",               "reads": ["cocitation_hyperedges.json"],
     "writes": ["solidity_bridges.json"], "network": True},   # recrawl/enrich/embeddings só no recompute;
     #                                                            saída versionada -> --offline PULA (CI sem modelo)
    {"name": "site",          "script": "build_site.py",             "reads": ["scisci_results.json"],
     "writes": ["docs/index.html"], "network": False, "always": True},
]


def sanity_check():
    """Espelha a Célula 3 do Colab: a fonte curada existe, é JSON válido e tem corpus."""
    R = data_io.load_data("scisci_results.json", required=True)   # erro claro se faltar
    corpus = R.get("corpus_size")
    if not corpus or not isinstance(corpus, int) or corpus <= 0:
        raise SystemExit(f"[run_all] sanidade FALHOU: corpus_size inválido/vazio ({corpus!r}) "
                         f"em data/scisci_results.json — funil interrompido.")
    print(f"[run_all] sanidade ok: corpus_size={corpus}, seeds={R.get('n_seeds')}")
    return R


def _groupby_estimate(seed="W2048086870"):
    """§5.2 — 1 group_by (custo de 1 filtro) p/ pré-estimar volume de citantes antes
    de uma fase de rede. Devolve (n_estimado, custo_usd) ou (None, None) se offline."""
    import oa
    url = f"https://api.openalex.org/works?filter=cites:{seed}&group_by=publication_year"
    data = oa.get(url) or {}
    groups = data.get("group_by") or []
    n = sum(g.get("count", 0) for g in groups)
    cost = (data.get("meta") or {}).get("cost_usd")
    return (n or None), cost


def _is_stale(phase, force):
    if force or phase.get("always"):
        return True
    return any(not os.path.exists(_p(w)) for w in phase["writes"])


def run_phase(phase, offline, force):
    """Roda uma fase como subprocesso isolado. Devolve (status, segundos)."""
    name = phase["name"]
    env = dict(os.environ)
    if offline:
        env["OA_OFFLINE"] = "1"           # PR-3/PR-5 — cache-only, zero fetch

    # guarda-corpo de budget nas fases de REDE (só online)
    if phase["network"] and not offline:
        st = budget.budget_status()
        if st["over_cap"]:
            print(f"[run_all] ⚠ '{name}': teto de budget atingido "
                  f"(US${st['used_usd']:.4f}/{st['cap_usd']:.2f}) — PULA fase de rede.")
            return "skip-budget", 0.0
        if name == "hypergraph":          # pré-estimativa exemplar via group_by
            try:
                n_est, c = _groupby_estimate()
                if n_est:
                    print(f"[run_all]   pré-estimativa (group_by): ~{n_est} citantes; "
                          f"custo marginal do filtro US${c}")
            except Exception:
                pass

    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, os.path.join(HERE, phase["script"])],
                           cwd=ROOT, env=env, capture_output=True, text=True, timeout=1800)
    except subprocess.TimeoutExpired:
        return "timeout", time.time() - t0
    dt = time.time() - t0
    if r.returncode != 0:
        sys.stderr.write(f"[run_all] ✗ '{name}' falhou (exit {r.returncode}):\n"
                         f"{(r.stdout or '')[-600:]}\n{(r.stderr or '')[-600:]}\n")
        return "fail", dt
    # confere que as saídas declaradas apareceram
    missing = [w for w in phase["writes"] if not os.path.exists(_p(w))]
    if missing:
        sys.stderr.write(f"[run_all] ✗ '{name}' rodou mas não gerou: {missing}\n")
        return "no-output", dt
    open(_sentinel(name), "w").write(str(int(time.time())))   # sentinela = marca de execução
    return "ran", dt


def main(argv=None):
    ap = argparse.ArgumentParser(description="Orquestrador do funil derivado (DAG + guardas).")
    ap.add_argument("--offline", action="store_true", help="cache-only (OA_OFFLINE=1), zero fetch")
    ap.add_argument("--force", action="store_true", help="re-roda todas as fases (ignora 'saída existe')")
    ap.add_argument("--dry-run", action="store_true", help="só mostra o plano (não executa)")
    ap.add_argument("--only", default="", help="roda só estas fases (csv de nomes)")
    ap.add_argument("--list", action="store_true", help="lista o DAG e sai")
    args = ap.parse_args(argv)

    if args.list:
        for ph in PHASES:
            net = "rede " if ph["network"] else "local"
            print(f"  {ph['name']:16} [{net}] {ph['script']:26} -> {', '.join(ph['writes'])}")
        return 0

    only = {s.strip() for s in args.only.split(",") if s.strip()}
    print(f"== run_all {'(OFFLINE)' if args.offline else '(online)'}"
          f"{' --force' if args.force else ''} ==")
    sanity_check()

    if not args.offline and not os.environ.get("OPENALEX_API_KEY") and not os.path.exists(
            os.path.expanduser("~/.openalex_key")):
        print("[run_all] ⚠ sem API-key — seguindo no pool grátis (10 req/s). "
              "Use --offline p/ garantir zero rede.")

    rows, status_counts = [], {}
    for ph in PHASES:
        if only and ph["name"] not in only:
            continue
        if not _is_stale(ph, args.force):
            print(f"[run_all] ⏭  {ph['name']}: saídas já existem — pula.")
            rows.append((ph["name"], "skip-fresh", 0.0, ";".join(ph["writes"])))
            status_counts["skip-fresh"] = status_counts.get("skip-fresh", 0) + 1
            continue
        if args.dry_run:
            print(f"[run_all] •  {ph['name']}: RODARIA ({ph['script']})")
            rows.append((ph["name"], "would-run", 0.0, ";".join(ph["writes"])))
            continue
        print(f"[run_all] ▶  {ph['name']} ({ph['script']})...")
        status, dt = run_phase(ph, args.offline, args.force)
        print(f"[run_all]    {status} em {dt:.1f}s")
        rows.append((ph["name"], status, round(dt, 1), ";".join(ph["writes"])))
        status_counts[status] = status_counts.get(status, 0) + 1
        if status in ("fail", "no-output", "timeout"):
            # dependências quebram cedo: aborta e relata (contrato do handout)
            _write_report(rows)
            raise SystemExit(f"[run_all] ABORTADO em '{ph['name']}' ({status}). "
                            f"Relatório: {REPORT}")

    _write_report(rows)
    print(f"\n[run_all] resumo: " + " · ".join(f"{k}={v}" for k, v in sorted(status_counts.items())))
    print(f"[run_all] relatório: {REPORT}")
    return 0


def _write_report(rows):
    try:
        with open(REPORT, "w", encoding="utf-8", newline="") as f:
            w = csv.writer(f, lineterminator="\n")
            w.writerow(["fase", "status", "segundos", "saidas"])
            w.writerows(rows)
    except Exception:
        pass


if __name__ == "__main__":
    raise SystemExit(main())
