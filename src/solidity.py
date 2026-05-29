#!/usr/bin/env python3
"""Camada de pontes de ordem superior — solidez tripla (handoff da modelagem).

Prediz HIPERARESTAS AUSENTES que costurariam os silos (Cyb/Reg/PolInd[/Cplx]) e
reporta só as SÓLIDAS — as que passam nos TRÊS testes independentes (fontes de
sinal não-correlacionadas, para não confirmar a hipótese de forma circular):

  DESIGN  (estrutural) — adicionar a tríade integra os silos? (vs modelo nulo)
  LATENTE (temporal)   — a estrutura tende a fechá-la? fechamento simplicial +
                          HOLDOUT temporal (treina ≤T, testa >T) anti-circularidade
  SEMÂNTICO (freio)    — há argumento comum? FAIXA INTERMEDIÁRIA de similaridade
                          (trivial demais e quimera são ambas rejeitadas)

Decisões (handoff + repo): silos = `axis_of` (vocabulário controlado, não Leiden
novo — convenção do repo vence); v1 = tríades OBRA-só (H_obra, maior confiança, onde
o fechamento vive); saída = derivado próprio `data/solidity_bridges.json` (NÃO mexe
na fonte curada scisci_results.json). Resultado NEGATIVO é válido: se nada passa nos
três, grava lista vazia + status, sem erro. Confiança modal (obra>autor>conceito)
preservada na coluna `confianca_modal`.

Reusa: data_io, src/oa.py+budget (recrawl/enriquecimento sob teto), o H_obra já
persistido em data/cocitation_hyperedges.json. Roda: python src/solidity.py
"""
import collections
import itertools
import json
import math
import os
import random
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_io  # noqa: E402
import oa  # noqa: E402  (cache-respecting; OA_OFFLINE/teto valem aqui também)

ROOT = data_io.ROOT
API = "https://api.openalex.org"
EIXOS = ("Cyb", "Reg", "PolInd")          # os três silos canônicos (Cplx é 4º eixo)

# ── config versionada (calibração explícita; calibrável vs nulo/percentis) ───────
DEFAULT_CONFIG = {
    "_doc": "limiares e parâmetros da solidez tripla — versionado e reprodutível",
    "poda": {"min_cited_by": 5, "max_candidatos": 3000, "min_par_peso": 1},
    "design": {"null_iter": 200, "seed": 42, "tau_z": 2.0},
    "latente": {"holdout_year": 2015, "tau_baixo_pct": 20},   # latente abaixo do P20 = "repelida"
    "semantico": {"faixa_low_pct": 40, "faixa_high_pct": 75, "metodo": "auto"},
}


def load_config():
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    disk = data_io.load_data("solidity_config.json", required=False)
    if isinstance(disk, dict):
        for k, v in disk.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


# ── M-1 · incidência + H_obra + pares (co-ocorrência) ────────────────────────────
def load_hobra():
    """Lê o H_obra canônico já persistido (PR-1). Devolve (hyperedges[set], citers,
    axis_of, pair_weight{frozenset:count}, faces{frozenset(tríades já fechadas)})."""
    H = data_io.load_data("cocitation_hyperedges.json", required=True)
    edges = [set(e) for e in H["hyperedges"]]
    citers = H.get("edge_to_citer", [None] * len(edges))
    axis_of = H.get("axis_of", {})
    pair_w = collections.Counter()
    closed_pairs_in_edge = collections.defaultdict(set)   # par -> idx de arestas
    for i, e in enumerate(edges):
        for a, b in itertools.combinations(sorted(e), 2):
            pair_w[frozenset((a, b))] += 1
            closed_pairs_in_edge[frozenset((a, b))].add(i)
    central = H.get("cross_axis_degree", {}) or H.get("degree", {})   # centralidade cross-silo
    return edges, citers, axis_of, pair_w, closed_pairs_in_edge, central


def incidence_table(edges, citers, axis_of):
    """Tecido conjuntivo §2.2 (obra-só nesta v1): work -> obras cocitadas, eixos, ano(None)."""
    inc = {}
    for w, ax in axis_of.items():
        inc[w] = {"eixo": ax, "cocitada_em": [], "eixos_vizinhos": set()}
    for i, e in enumerate(edges):
        for w in e:
            if w in inc:
                inc[w]["cocitada_em"].append(i)
                for o in e:
                    a = axis_of.get(o)
                    if a and o != w:
                        inc[w]["eixos_vizinhos"].add(a)
    for w in inc:
        inc[w]["eixos_vizinhos"] = sorted(inc[w]["eixos_vizinhos"])
    return inc


# ── M-2 · candidatas: tríades cross-silo "quase fechando" (Benson-style) ──────────
def gen_candidates(edges, axis_of, pair_w, cfg):
    """Tríades {a,b,c} cross-silo (≥2 eixos) cujos pares JÁ co-ocorrem (≥1) mas a
    FACE tríade NUNCA co-ocorreu numa só hiperaresta (face ausente). Espaço único,
    gerado UMA vez, antes de qualquer pontuação. Podado e capado (determinístico)."""
    minp = cfg["poda"]["min_par_peso"]
    # grafo de co-ocorrência (pares com peso ≥ minp)
    adj = collections.defaultdict(set)
    for pair, w in pair_w.items():
        if w >= minp:
            a, b = tuple(pair)
            adj[a].add(b); adj[b].add(a)
    edge_node_sets = edges  # list[set]
    def face_present(tri):
        s = set(tri)
        return any(s <= e for e in edge_node_sets)
    cands = {}
    # cada par (a,b) co-ocorrente estende a c vizinho de a ou b (wedge/triângulo)
    for pair in pair_w:
        a, b = tuple(pair)
        for c in (adj[a] | adj[b]):
            if c in (a, b):
                continue
            tri = frozenset((a, b, c))
            if tri in cands:
                continue
            eixos = {axis_of.get(x) for x in tri if axis_of.get(x) in EIXOS}
            if len(eixos) < 2:                    # tem de tocar ≥2 silos canônicos
                continue
            if face_present(tri):                 # face já existe -> não é "ausente"
                continue
            pw = [pair_w.get(frozenset(p), 0) for p in itertools.combinations(sorted(tri), 2)]
            n_pares = sum(1 for x in pw if x > 0)
            cands[tri] = {"membros": sorted(tri), "eixos": sorted(eixos),
                          "pares_peso": sorted(pw, reverse=True), "n_pares": n_pares}
    # ordena determinístico (mais suporte diádico primeiro) e capa
    ordered = sorted(cands.values(),
                     key=lambda c: (-sum(c["pares_peso"]), -c["n_pares"], c["membros"]))
    return ordered[: cfg["poda"]["max_candidatos"]]


# ── M-3 · DESIGN: ganho de integração vs modelo nulo ─────────────────────────────
def _cross_pair_counts(edges, axis_of):
    """Quantas co-ocorrências existem HOJE entre cada par de eixos (separação atual)."""
    cc = collections.Counter()
    for e in edges:
        for a, b in itertools.combinations(sorted(e), 2):
            ea, eb = axis_of.get(a), axis_of.get(b)
            if ea in EIXOS and eb in EIXOS and ea != eb:
                cc[frozenset((ea, eb))] += 1
    return cc


def design_scores(cands, edges, axis_of, central, cfg):
    """Ganho de integração CANDIDATA-ESPECÍFICO: a tríade integra mais quando (a) cruza
    eixos pouco conectados hoje (raridade) e (b) seus membros são centrais ao tráfego
    cross-silo (cross_axis_degree). z vs nulo de tríades aleatórias cross-silo
    (determinístico, seed). NÃO depende só da composição de eixos — varia por membro."""
    cc = _cross_pair_counts(edges, axis_of)
    maxc = max(cc.values()) if cc else 1
    maxd = max(central.values()) if central else 1

    def raw(members):
        e = {m: axis_of.get(m) for m in members}
        cross = [(a, b) for a, b in itertools.combinations(members, 2)
                 if e[a] in EIXOS and e[b] in EIXOS and e[a] != e[b]]
        if not cross:
            return 0.0
        g = 0.0
        for a, b in cross:
            rarity = 1.0 - cc.get(frozenset((e[a], e[b])), 0) / maxc
            cent = (central.get(a, 0) + central.get(b, 0)) / (2 * maxd)
            g += rarity * (0.5 + cent)            # membros centrais integram mais
        n_eixos = len({e[m] for m in members if e[m] in EIXOS})
        return g * (1 + 0.5 * (n_eixos - 1))      # tocar 3 eixos > tocar 2
    # modelo nulo: tríades aleatórias cross-silo
    rng = random.Random(cfg["design"]["seed"])
    pool = [n for n, a in axis_of.items() if a in EIXOS]
    null_raws = []
    for _ in range(cfg["design"]["null_iter"]):
        if len(pool) >= 3:
            null_raws.append(raw(rng.sample(pool, 3)))
    mean = sum(null_raws) / max(len(null_raws), 1)
    var = sum((x - mean) ** 2 for x in null_raws) / max(len(null_raws) - 1, 1)
    sd = var ** 0.5 or 1e-9
    for c in cands:
        r = raw(c["membros"])
        c["design_raw"] = round(r, 4)
        c["design_z"] = round((r - mean) / sd, 3)
    return {"null_mean": round(mean, 4), "null_sd": round(sd, 4),
            "n_iter": cfg["design"]["null_iter"], "seed": cfg["design"]["seed"]}


# ── M-4 · LATENTE: fechamento simplicial + holdout temporal ──────────────────────
def latent_scores(cands, pair_w):
    """Escore latente = média harmônica dos 3 pesos diádicos (subfaces já coexistentes).
    Alto = as 3 subfaces densas + face ausente = costura prestes a acontecer."""
    maxw = max(pair_w.values()) if pair_w else 1
    for c in cands:
        m = c["membros"]
        ws = [pair_w.get(frozenset((m[i], m[j])), 0) / maxw
              for i, j in itertools.combinations(range(len(m)), 2)]
        ws = [w for w in ws if w > 0]
        # harmônica penaliza par fraco (precisa das 3 subfaces, não só 1)
        c["latente"] = round(len(ws) / sum(1 / w for w in ws), 4) if len(ws) == 3 else \
                       round((sum(ws) / 3) * 0.5, 4)   # <3 subfaces -> meia-força
    return cands


def fetch_citer_years(citers):
    """Recrawl BARATO (decisão do Lucas): anos dos citantes via filtro openalex:
    em lote (select=id,publication_year). Cacheado -> holdout roda offline depois.
    Sob OA_OFFLINE/teto: usa só o que já está em data/citer_years.json + cache."""
    years = data_io.load_data("citer_years.json", required=False) or {}
    pend = sorted({c for c in citers if c and c not in years})
    for i in range(0, len(pend), 50):
        chunk = pend[i:i + 50]
        flt = "openalex:" + "|".join(chunk)
        url = (f"{API}/works?filter={urllib.parse.quote(flt, safe=':|')}"
               f"&per-page=50&select=id,publication_year")
        for w in (oa.get(url).get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            if w.get("publication_year"):
                years[wid] = int(w["publication_year"])
    if pend:
        data_io.save_data("citer_years.json", years)
    return years


def temporal_holdout(edges, citers, pair_w, cands, cfg):
    """Anti-circularidade: treina o fechamento em arestas com citante ≤T, testa se as
    tríades de alto escore-treino de fato ganharam suporte em arestas >T. Reporta a
    diferença de fechamento entre o topo e o resto (sinal preditivo, não circular)."""
    years = data_io.load_data("citer_years.json", required=False) or {}
    T = cfg["latente"]["holdout_year"]
    train_idx = [i for i, c in enumerate(citers) if years.get(c, 9999) <= T]
    test_idx = [i for i, c in enumerate(citers) if years.get(c, 0) > T]
    if len(train_idx) < 30 or len(test_idx) < 30:
        return {"ok": False, "motivo": "anos de citantes insuficientes (rode o recrawl online)",
                "n_train": len(train_idx), "n_test": len(test_idx)}
    pw_train = collections.Counter()
    for i in train_idx:
        for a, b in itertools.combinations(sorted(edges[i]), 2):
            pw_train[frozenset((a, b))] += 1
    test_pairs = set()
    for i in test_idx:
        for a, b in itertools.combinations(sorted(edges[i]), 2):
            test_pairs.add(frozenset((a, b)))
    # escore-treino por candidata e "fechou no teste" = algum par novo surgiu em >T
    def closed_after(c):
        m = c["membros"]
        return any(frozenset((m[i], m[j])) in test_pairs
                   for i, j in itertools.combinations(range(len(m)), 2))
    scored = []
    for c in cands:
        m = c["membros"]
        ws = [pw_train.get(frozenset((m[i], m[j])), 0)
              for i, j in itertools.combinations(range(len(m)), 2)]
        scored.append((sum(ws), closed_after(c)))
    scored.sort(key=lambda x: -x[0])
    top = scored[: max(1, len(scored) // 5)]
    rest = scored[len(top):]
    rate_top = sum(1 for _, cl in top if cl) / max(len(top), 1)
    rate_rest = sum(1 for _, cl in rest if cl) / max(len(rest), 1)
    return {"ok": True, "T": T, "n_train": len(train_idx), "n_test": len(test_idx),
            "fechamento_top20pct": round(rate_top, 3), "fechamento_resto": round(rate_rest, 3),
            "lift": round(rate_top - rate_rest, 3)}


# ── M-5 · SEMÂNTICO: tópicos (Jaccard) + embeddings (faixa intermediária) ─────────
def enrich_members(member_ids):
    """Puxa topics+abstract SÓ dos membros das candidatas (nunca o corpus inteiro)."""
    topics, absts = {}, {}
    cached = data_io.load_data("solidity_member_enrich.json", required=False) or {}
    topics = {k: v["topics"] for k, v in cached.items() if v.get("topics")}
    absts = {k: v["abstract"] for k, v in cached.items() if v.get("abstract")}
    pend = sorted({m for m in member_ids if m not in cached})
    new = dict(cached)
    for i in range(0, len(pend), 50):
        chunk = pend[i:i + 50]
        flt = "openalex:" + "|".join(chunk)
        url = (f"{API}/works?filter={urllib.parse.quote(flt, safe=':|')}"
               f"&per-page=50&select=id,title,display_name,topics,abstract_inverted_index")
        for w in (oa.get(url).get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            tps = [t.get("id") for t in (w.get("topics") or []) if t.get("id")]
            ab = _reverse_abstract(w.get("abstract_inverted_index"))
            ttl = w.get("title") or w.get("display_name") or ""
            new[wid] = {"topics": tps, "abstract": (ttl + ". " + ab).strip()}
            if tps:
                topics[wid] = tps
            if new[wid]["abstract"]:
                absts[wid] = new[wid]["abstract"]
    if pend:
        data_io.save_data("solidity_member_enrich.json", new)
    return topics, absts


def _reverse_abstract(inv):
    if not inv or not isinstance(inv, dict):
        return ""
    pos = {}
    for word, idxs in inv.items():
        for p in (idxs or []):
            if isinstance(p, int):
                pos[p] = word
    return " ".join(pos.get(i, "") for i in range(max(pos) + 1)) if pos else ""


def _embed(texts, method):
    """Embeddings fortes (decisão do Lucas) com fallback offline. Devolve (vetores, metodo)."""
    if method in ("auto", "embeddings"):
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            mdl = SentenceTransformer("all-MiniLM-L6-v2")
            v = mdl.encode(texts, normalize_embeddings=True, show_progress_bar=False)
            return np.asarray(v), "sentence-transformers/all-MiniLM-L6-v2"
        except Exception as e:
            sys.stderr.write(f"[solidity] embeddings fortes indisponíveis ({str(e)[:80]}); "
                             f"caindo p/ TF-IDF\n")
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np
    X = TfidfVectorizer(max_features=4096, stop_words="english").fit_transform(texts)
    X = X.toarray()
    norms = (X ** 2).sum(1) ** 0.5
    norms[norms == 0] = 1
    return X / norms[:, None], "tfidf"


def semantic_scores(cands, topics, absts, axis_of, cfg):
    """Jaccard de tópicos (sempre) + cosseno de embeddings (forte). Calibra a FAIXA
    por percentis da distribuição cross-silo e marca quem está DENTRO (gate)."""
    members = sorted({m for c in cands for m in c["membros"]})
    have_abs = [m for m in members if absts.get(m)]
    cos = {}
    method = "tfidf"
    if len(have_abs) >= 2:
        vecs, method = _embed([absts[m] for m in have_abs], cfg["semantico"]["metodo"])
        idx = {m: i for i, m in enumerate(have_abs)}
        import numpy as np
        for c in cands:
            ms = [m for m in c["membros"] if m in idx]
            if len(ms) >= 2:
                sims = [float(np.dot(vecs[idx[a]], vecs[idx[b]]))
                        for a, b in itertools.combinations(ms, 2)]
                cos[frozenset(c["membros"])] = sum(sims) / len(sims)

    def jac(a, b):
        ta, tb = set(topics.get(a, [])), set(topics.get(b, []))
        return len(ta & tb) / len(ta | tb) if (ta | tb) else 0.0
    for c in cands:
        m = c["membros"]
        js = [jac(a, b) for a, b in itertools.combinations(m, 2)]
        c["sem_jaccard"] = round(sum(js) / len(js), 4) if js else 0.0
        cv = cos.get(frozenset(m))
        c["sem_cos"] = round(cv, 4) if cv is not None else None
        c["semantico"] = c["sem_cos"] if cv is not None else c["sem_jaccard"]
    # faixa intermediária por percentis das similaridades observadas (cross-silo)
    vals = sorted(c["semantico"] for c in cands if c["semantico"] is not None)
    def pct(p):
        if not vals:
            return 0.0
        k = min(len(vals) - 1, max(0, int(round(p / 100 * (len(vals) - 1)))))
        return vals[k]
    lo, hi = pct(cfg["semantico"]["faixa_low_pct"]), pct(cfg["semantico"]["faixa_high_pct"])
    for c in cands:
        s = c["semantico"]
        c["sem_na_faixa"] = bool(s is not None and lo <= s <= hi)
    return {"metodo": method, "faixa_low": round(lo, 4), "faixa_high": round(hi, 4),
            "n_com_abstract": len(have_abs)}


# ── M-6 · quadrante + solidez + confiança modal + entregável ─────────────────────
def classify(cands, cfg):
    lat_vals = sorted(c["latente"] for c in cands)
    def pct(vals, p):
        if not vals:
            return 0.0
        k = min(len(vals) - 1, max(0, int(round(p / 100 * (len(vals) - 1)))))
        return vals[k]
    lat_hi = pct(lat_vals, 60)
    lat_lo = pct(lat_vals, cfg["latente"]["tau_baixo_pct"])     # abaixo disso = "repelida"
    tau_z = cfg["design"]["tau_z"]
    n_solidas = 0
    for c in cands:
        design_pass = c.get("design_z", 0) >= tau_z
        latent_pass = c["latente"] >= lat_lo                    # não-repelida (não exige alta)
        sem_pass = c["sem_na_faixa"]
        c["solida"] = bool(design_pass and latent_pass and sem_pass)
        n_solidas += c["solida"]
        hi_lat = c["latente"] >= lat_hi
        hi_des = design_pass
        if not sem_pass or (not hi_des and not hi_lat):
            c["quadrante"] = "ruido_quimera"
        elif hi_lat and hi_des:
            c["quadrante"] = "costura_ouro"
        elif hi_des and not hi_lat:
            c["quadrante"] = "agenda_pesquisa"
        else:
            c["quadrante"] = "fechamento_trivial"
        c["confianca_modal"] = "obra"      # v1 = obra-só (maior confiança)
    return n_solidas


def build(out_dados=None):
    """Pipeline completo → data/solidity_bridges.json + CSVs em docs/dados/."""
    out_dados = out_dados or os.path.join(ROOT, "docs", "dados")
    cfg = load_config()
    edges, citers, axis_of, pair_w, _, central = load_hobra()
    cands = gen_candidates(edges, axis_of, pair_w, cfg)
    null = design_scores(cands, edges, axis_of, central, cfg)
    latent_scores(cands, pair_w)
    fetch_citer_years(citers)                       # recrawl barato (no-op se offline/cacheado)
    holdout = temporal_holdout(edges, citers, pair_w, cands, cfg)
    members = sorted({m for c in cands for m in c["membros"]})
    topics, absts = enrich_members(members)
    sem_meta = semantic_scores(cands, topics, absts, axis_of, cfg)
    n_solidas = classify(cands, cfg)
    cands.sort(key=lambda c: (-int(c["solida"]), -(c.get("design_z") or 0), -c["latente"]))

    solidas = [c for c in cands if c["solida"]]
    out = {
        "_generated": "camada de pontes de ordem superior — solidez tripla (v1, obra-só)",
        "config": cfg, "modelo_nulo": null, "holdout_temporal": holdout, "semantico": sem_meta,
        "n_candidatas": len(cands), "n_solidas": n_solidas,
        "status": "sem ponte sólida" if n_solidas == 0 else f"{n_solidas} pontes sólidas",
        "por_quadrante": dict(collections.Counter(c["quadrante"] for c in cands)),
        "solidas": solidas[:200],
        "candidatas": cands[:500],
    }
    data_io.save_data("solidity_bridges.json", out)
    data_io.save_data("solidity_config.json", cfg)   # materializa a config versionada
    os.makedirs(out_dados, exist_ok=True)
    _write_csvs(cands, out_dados)
    print(f"solidity: {len(cands)} candidatas | {n_solidas} sólidas | "
          f"quadrantes {out['por_quadrante']} | semântico={sem_meta['metodo']} | "
          f"holdout={'ok' if holdout.get('ok') else 'pendente'}")
    return out


def _csv(path, header, rows):
    import csv
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(header)
        w.writerows(rows)


def _write_csvs(cands, out):
    _csv(os.path.join(out, "12_pontes_candidatas.csv"),
         ["membros", "eixos", "escore_latente", "escore_design_z", "similaridade_semantica",
          "na_faixa", "quadrante", "solida", "confianca_modal"],
         [["|".join(c["membros"]), "|".join(c["eixos"]), c["latente"], c.get("design_z"),
           c["semantico"], int(c["sem_na_faixa"]), c["quadrante"], int(c["solida"]),
           c["confianca_modal"]] for c in cands])
    _csv(os.path.join(out, "13_diagrama_solidez.csv"),
         ["membros", "x_latente", "y_design_z", "semantico", "na_faixa", "quadrante"],
         [["|".join(c["membros"]), c["latente"], c.get("design_z"), c["semantico"],
           int(c["sem_na_faixa"]), c["quadrante"]] for c in cands])


if __name__ == "__main__":
    build()
