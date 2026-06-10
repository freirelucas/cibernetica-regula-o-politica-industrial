#!/usr/bin/env python3
"""Verifica, de forma REPRODUTÍVEL, o achado central (§00): a partição por EIXO da
rede de cocitação tem modularidade muito acima do acaso (silos reais) e quase nenhuma
obra é conector significativo — e quão ROBUSTO é esse achado à reamostragem da rede.

Reusa `sfi_methods.configuration_null` — o MESMO modelo nulo do relatório (configuração,
preserva o grau). A modularidade é computada SÓ sobre os nós CLASSIFICADOS (eixo
conhecido); os nós sem eixo (`None`) — referências que o vocabulário não alcança (H1) —
são reportados à parte, NÃO tratados como comunidade (isso distorceria Q para baixo).

Robustez: *bootstrap* por reamostragem de nós (mantém cada nó com prob. `frac`),
recomputando Q a cada sorteio → média, desvio e IC de 95%. Se o IC fica bem acima de 0,
os silos não são artefato de quais obras entraram na rede.

Escreve `data/modularity_check.json`. Uso: `python src/modularity_check.py`
"""
import json
import os
import random
import statistics
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import sfi_methods  # noqa: E402

EIXOS = {"Cyb", "Reg", "PolInd", "Cplx"}


def _axis(n):
    return n.get("axis") or n.get("eixo")


def _Q(nodes, links):
    """Modularidade observada da partição por eixo (mesma fórmula do modelo nulo)."""
    comm = {n["id"]: _axis(n) for n in nodes}
    keep = set(comm)
    el = [(l["source"], l["target"]) for l in links
          if l["source"] in keep and l["target"] in keep and l["source"] != l["target"]]
    m = len(el) or 1
    ew, ends = defaultdict(int), defaultdict(int)
    for a, b in el:
        ca, cb = comm[a], comm[b]
        ends[ca] += 1
        ends[cb] += 1
        if ca == cb:
            ew[ca] += 1
    comms = set(comm.values())
    return sum(ew[c] / m for c in comms) - sum((ends[c] / (2 * m)) ** 2 for c in comms)


def _bootstrap(nodes, links, frac=0.8, B=300, seed=1):
    rnd = random.Random(seed)
    qs = []
    for _ in range(B):
        sub = [n for n in nodes if rnd.random() < frac]
        if len(sub) >= 10:
            qs.append(_Q(sub, links))
    qs.sort()
    lo, hi = qs[int(0.025 * len(qs))], qs[int(0.975 * len(qs))]
    return {"B": len(qs), "frac_mantida": frac, "Q_medio": round(statistics.mean(qs), 3),
            "Q_sd": round(statistics.pstdev(qs), 3), "Q_ic95": [round(lo, 3), round(hi, 3)]}


def _seed_sensitivity(nodes, links, k=5, drop=0.2, seed=7):
    """Robustez à SELEÇÃO de sementes (item 2 do backlog de rigor): a cada rodada
    remove uma fração `drop` das obras-semente e recompõe Q. Se Q se mantém, os
    silos não dependem de sementes específicas. CAVEAT: é um proxy de REDE — remove
    as sementes do grafo final; não re-roda a bola de neve (que exigiria recrawl)."""
    rnd = random.Random(seed)
    seeds = [n for n in nodes if n.get("seed")]
    others = [n for n in nodes if not n.get("seed")]
    n_drop = int(round(drop * len(seeds)))
    runs = []
    for _ in range(k):
        ns = seeds[:]
        rnd.shuffle(ns)
        runs.append(round(_Q(ns[n_drop:] + others, links), 3))
    return {"k": k, "drop": drop, "n_sementes": len(seeds), "n_dropadas": n_drop,
            "metodo": "drop de nós-semente da rede final (proxy; não re-snowball)",
            "Q_runs": runs, "Q_medio": round(statistics.mean(runs), 3),
            "Q_min": min(runs), "Q_max": max(runs)}


def _modularidade(nodes, links):
    keep = {n["id"] for n in nodes}
    el = [l for l in links if l["source"] in keep and l["target"] in keep]
    nid = [n["id"] for n in nodes]
    comm = {n["id"]: _axis(n) for n in nodes}
    q, Pz = sfi_methods.configuration_null(nid, el, comm, n_iter=100, seed=1)
    n_conn = sum(1 for n in nid
                 if sfi_methods.ga_role(Pz[n]["P_obs"], Pz[n]["z"]) in ("conector", "hub conector")
                 and Pz[n]["z"] > 0)
    return {"n_nos": len(nid), "n_arestas": len(el), **q, "n_conectores_significativos": n_conn}


def main():
    net = json.load(open(os.path.join(ROOT, "data", "network_4axis.json"), encoding="utf-8"))
    all_nodes = net["nodes"]
    links = net.get("links") or net.get("edges") or []

    classificados = [n for n in all_nodes if _axis(n) in EIXOS]
    nucleo = [n for n in classificados if _axis(n) in ("Cyb", "Reg", "PolInd")]
    n_none = sum(1 for n in all_nodes if _axis(n) not in EIXOS)

    out = {
        "_doc": "verificação reprodutível do achado central (§00): modularidade da partição "
                "por eixo vs. modelo nulo de configuração; + bootstrap de robustez. Só nós classificados.",
        "rede": "network_4axis.json",
        "n_nos_total": len(all_nodes),
        "n_nos_sem_eixo": n_none,
        "pct_sem_eixo": round(100 * n_none / max(len(all_nodes), 1), 1),
        "nota_H1": "nós sem eixo são referências cocitadas que o vocabulário não classifica "
                   "(título sem abstract etc.); ficam de fora da partição, não viram comunidade.",
        "tres_eixos": _modularidade(nucleo, links),
        "quatro_eixos_com_Cplx": _modularidade(classificados, links),
        "robustez_bootstrap_3eixos": _bootstrap(nucleo, links, frac=0.8, B=300, seed=1),
        "sensibilidade_sementes_3eixos": _seed_sensitivity(nucleo, links, k=5, drop=0.2),
    }
    json.dump(out, open(os.path.join(ROOT, "data", "modularity_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    t, b = out["tres_eixos"], out["robustez_bootstrap_3eixos"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n→ silos: Q={t['Q_obs']} (acaso {t['Q_rand']}, z={t['Q_z']}), "
          f"{t['n_conectores_significativos']} conectores · {out['pct_sem_eixo']}% sem eixo (H1)")
    print(f"→ robustez (drop-20%, B={b['B']}): Q={b['Q_medio']} ± {b['Q_sd']}, "
          f"IC95 [{b['Q_ic95'][0]}, {b['Q_ic95'][1]}]")
    ss = out["sensibilidade_sementes_3eixos"]
    print(f"→ sensibilidade às sementes (drop-20% ×{ss['k']}, {ss['n_dropadas']}/{ss['n_sementes']} fora): "
          f"Q∈[{ss['Q_min']}, {ss['Q_max']}], média {ss['Q_medio']}")


if __name__ == "__main__":
    main()
