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
    "design": {"null_iter": 200, "seed": 42, "fdr_alpha": 0.05},   # nulo CASADO por eixos + BH-FDR
    "latente": {"holdout_year": 2015, "tau_baixo_pct": 20, "min_positivos": 5,
                "bootstrap": 500, "max_eval": 4000},
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
    """DESIGN é o PROPOSITOR (sempre acha integração) — medido por raridade do cruzamento
    de eixos × centralidade cross-silo dos membros. Significância contra NULO CASADO pelo
    multiset de eixos dos MEMBROS (remove a inflação de "eu selecionei cross-silo"), p
    EMPÍRICO, e correção de multiplicidade Benjamini-Hochberg (FDR) sobre as 3000 candidatas.
    Marca c["design_sig"] = sobreviveu ao FDR. NÃO é teste independente do latente — é a
    hipótese; quem falsifica é o eixo temporal (out-of-sample) e o semântico."""
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
            g += rarity * (0.5 + cent)
        n_eixos = len({e[m] for m in members if e[m] in EIXOS})
        return g * (1 + 0.5 * (n_eixos - 1))

    pools = collections.defaultdict(list)
    for n, a in axis_of.items():
        pools[a].append(n)
    rng = random.Random(cfg["design"]["seed"])
    N = cfg["design"]["null_iter"]
    null_cache = {}

    def null_for(key):                       # key = multiset de eixos dos membros (ex.: ('Cyb','PolInd','Reg'))
        if key not in null_cache:
            rs = []
            for _ in range(N):
                tri = [rng.choice(pools[a]) for a in key if pools.get(a)]
                if len(tri) == len(key):
                    rs.append(raw(tri))
            null_cache[key] = rs
        return null_cache[key]

    pvals = []
    for c in cands:
        key = tuple(sorted(axis_of.get(m, "") for m in c["membros"]))
        rs = null_for(key)
        r = raw(c["membros"])
        mean = sum(rs) / len(rs) if rs else 0.0
        sd = (sum((x - mean) ** 2 for x in rs) / max(len(rs) - 1, 1)) ** 0.5 or 1e-9
        p = (sum(1 for x in rs if x >= r) + 1) / (len(rs) + 1) if rs else 1.0   # p empírico
        c["design_raw"] = round(r, 4)
        c["design_z"] = round((r - mean) / sd, 3)
        c["design_p"] = round(p, 5)
        pvals.append(p)
    # Benjamini-Hochberg FDR sobre todas as candidatas (controla multiplicidade)
    alpha = cfg["design"]["fdr_alpha"]
    m = max(len(pvals), 1)
    order = sorted(range(len(pvals)), key=lambda i: pvals[i])
    kmax = 0
    for rank, i in enumerate(order, 1):
        if pvals[i] <= rank / m * alpha:
            kmax = rank
    sig = set(order[:kmax])
    for j, c in enumerate(cands):
        c["design_sig"] = bool(j in sig)
    return {"nulo": "casado por multiset de eixos dos membros", "n_iter": N,
            "seed": cfg["design"]["seed"], "fdr_alpha": alpha, "n_design_sig": len(sig)}


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


def temporal_validation(edges, citers, axis_of, cfg):
    """O eixo INDEPENDENTE de verdade (out-of-sample no tempo) — o que quebra a
    circularidade. Gera tríades abertas SÓ do treino (arestas com citante ≤T: ≥2 pares
    co-ocorrem, FACE ausente no treino) e pergunta se a face FECHA no teste (>T). Mede
    AUC-PR do escore latente-de-treino predizendo o fechamento futuro, contra a
    PREVALÊNCIA (acaso) com IC bootstrap. "Validado" se o IC95 inferior da AP > prevalência.

    Não vaza o futuro: candidatas e features vêm só de ≤T; rótulo vem só de >T. Se há
    poucos fechamentos (silos!), devolve validated=False com n_positivos — resultado
    negativo válido (nenhum método pode reivindicar predição sem positivos)."""
    years = data_io.load_data("citer_years.json", required=False) or {}
    T = cfg["latente"]["holdout_year"]
    tr = [edges[i] for i, c in enumerate(citers) if years.get(c, 9999) <= T]
    te = [edges[i] for i, c in enumerate(citers) if years.get(c, 0) > T]
    if len(tr) < 30 or len(te) < 30:
        return {"validated": False, "motivo": f"anos insuficientes (treino={len(tr)}, teste={len(te)}) — rode o recrawl online",
                "n_train": len(tr), "n_test": len(te), "T": T}
    pw_tr = collections.Counter()
    adj_tr = collections.defaultdict(set)
    for e in tr:
        for a, b in itertools.combinations(sorted(e), 2):
            pw_tr[frozenset((a, b))] += 1
            adj_tr[a].add(b); adj_tr[b].add(a)
    tr_faces = [set(e) for e in tr]
    te_faces = [set(e) for e in te]
    maxw = max(pw_tr.values()) if pw_tr else 1

    def in_any(tri, faces):
        s = set(tri)
        return any(s <= f for f in faces)

    seen, feats, labels = set(), [], []
    for pair in list(pw_tr):
        a, b = tuple(pair)
        for c in (adj_tr[a] | adj_tr[b]):
            if c in (a, b):
                continue
            tri = frozenset((a, b, c))
            if tri in seen:
                continue
            eix = {axis_of.get(x) for x in tri if axis_of.get(x) in EIXOS}
            if len(eix) < 2 or in_any(tri, tr_faces):   # cross-silo E aberta no treino
                continue
            seen.add(tri)
            ws = [pw_tr.get(frozenset((x, y)), 0) / maxw for x, y in itertools.combinations(sorted(tri), 2)]
            ws = [w for w in ws if w > 0]
            feats.append(len(ws) / sum(1 / w for w in ws) if len(ws) == 3 else (sum(ws) / 3) * 0.5)
            labels.append(1 if in_any(tri, te_faces) else 0)   # FECHOU no futuro?
            if len(seen) >= cfg["latente"]["max_eval"]:
                break
        if len(seen) >= cfg["latente"]["max_eval"]:
            break
    n, n_pos = len(labels), sum(labels)
    base = {"validated": False, "T": T, "n_train": len(tr), "n_test": len(te),
            "n_eval": n, "n_positivos": n_pos}
    if n_pos < cfg["latente"]["min_positivos"] or n_pos in (0, n):
        base["motivo"] = f"fechamentos insuficientes no teste (positivos={n_pos}/{n}) — sem poder estatístico"
        return base
    try:
        import numpy as np
        from sklearn.metrics import average_precision_score
        y, s = np.array(labels), np.array(feats)
        prev = float(y.mean())
        ap = float(average_precision_score(y, s))
        rng = np.random.default_rng(cfg["design"]["seed"])
        aps = []
        for _ in range(cfg["latente"]["bootstrap"]):
            bi = rng.integers(0, n, n)
            if y[bi].sum() > 0:
                aps.append(average_precision_score(y[bi], s[bi]))
        lo = float(np.percentile(aps, 2.5)) if aps else None
        hi = float(np.percentile(aps, 97.5)) if aps else None
        base.update({"validated": bool(lo is not None and lo > prev),
                     "prevalencia": round(prev, 4), "average_precision": round(ap, 4),
                     "ap_ci95": [round(lo, 4) if lo else None, round(hi, 4) if hi else None],
                     "lift_sobre_acaso": round(ap / prev, 3) if prev > 0 else None,
                     "criterio": "validado se IC95 inferior da AP > prevalência"})
    except Exception as e:
        base["motivo"] = f"falha na métrica: {str(e)[:120]}"
    return base


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
def classify(cands, cfg, temporal_validated):
    """DESIGN propõe (significativo no FDR); SEMÂNTICO e TEMPORAL falsificam. A tríade
    só é "sólida (3 de 3)" se o eixo temporal tiver poder (temporal_validated) E a
    candidata passar nos três. Sem validação temporal, NÃO se certifica a tripla —
    reporta-se "2 de 3" (design+semântico) à espera de validação. Devolve (n_solidas, n_2de3)."""
    lat_vals = sorted(c["latente"] for c in cands)

    def pct(vals, p):
        if not vals:
            return 0.0
        k = min(len(vals) - 1, max(0, int(round(p / 100 * (len(vals) - 1)))))
        return vals[k]
    lat_hi = pct(lat_vals, 60)
    lat_lo = pct(lat_vals, cfg["latente"]["tau_baixo_pct"])
    n_solidas, n_2de3 = 0, 0
    for c in cands:
        design_pass = bool(c.get("design_sig"))      # significativo após FDR (propositor)
        sem_pass = bool(c["sem_na_faixa"])
        two = design_pass and sem_pass
        n_2de3 += two
        c["design_pass"] = design_pass
        c["sem_pass"] = sem_pass
        if temporal_validated:
            latent_pass = c["latente"] >= lat_lo      # não-repelida (eixo temporal tem poder)
            c["latente_pass"] = latent_pass
            c["solida"] = bool(design_pass and latent_pass and sem_pass)
        else:
            c["latente_pass"] = None                  # eixo temporal sem poder -> não certifica
            c["solida"] = False
        n_solidas += c["solida"]
        hi_lat = c["latente"] >= lat_hi
        if not sem_pass or (not design_pass and not hi_lat):
            c["quadrante"] = "ruido_quimera"
        elif hi_lat and design_pass:
            c["quadrante"] = "costura_ouro"
        elif design_pass and not hi_lat:
            c["quadrante"] = "agenda_pesquisa"
        else:
            c["quadrante"] = "fechamento_trivial"
        c["confianca_modal"] = "obra"      # v1 = obra-só (maior confiança)
    return n_solidas, n_2de3


def build(out_dados=None):
    """Pipeline completo → data/solidity_bridges.json + CSVs em docs/dados/."""
    out_dados = out_dados or os.path.join(ROOT, "docs", "dados")
    cfg = load_config()
    edges, citers, axis_of, pair_w, _, central = load_hobra()
    cands = gen_candidates(edges, axis_of, pair_w, cfg)
    null = design_scores(cands, edges, axis_of, central, cfg)   # propositor + nulo casado + FDR
    latent_scores(cands, pair_w)                                # feature (validade vem do holdout)
    fetch_citer_years(citers)                                   # recrawl barato (no-op se offline/cacheado)
    tv = temporal_validation(edges, citers, axis_of, cfg)       # eixo independente out-of-sample
    members = sorted({m for c in cands for m in c["membros"]})
    topics, absts = enrich_members(members)
    sem_meta = semantic_scores(cands, topics, absts, axis_of, cfg)
    n_solidas, n_2de3 = classify(cands, cfg, tv.get("validated", False))
    cands.sort(key=lambda c: (-int(c["solida"]), -int(c.get("design_sig", False)),
                              -(c.get("design_z") or 0), -c["latente"]))

    solidas = [c for c in cands if c["solida"]]
    if tv.get("validated"):
        status = "sem ponte sólida" if n_solidas == 0 else f"{n_solidas} pontes sólidas (3 de 3)"
    else:
        status = (f"0 sólidas — eixo temporal sem poder (ver validacao_temporal); "
                  f"{n_2de3} candidatas em 2 de 3 (design+semântico), à espera de validação temporal")
    out = {
        "_generated": "camada de pontes de ordem superior — solidez tripla",
        "metodo": "v2 — DESIGN propõe (nulo casado por eixos + BH-FDR); falsificadores "
                  "INDEPENDENTES: holdout temporal out-of-sample (AUC-PR vs prevalência) e semântico",
        "config": cfg, "modelo_nulo": null, "validacao_temporal": tv, "semantico": sem_meta,
        "n_candidatas": len(cands), "n_solidas": n_solidas, "n_2de3": n_2de3,
        "tripla_certificavel": bool(tv.get("validated")),
        "status": status,
        "por_quadrante": dict(collections.Counter(c["quadrante"] for c in cands)),
        "solidas": solidas[:200],
        "candidatas": cands[:500],
    }
    data_io.save_data("solidity_bridges.json", out)
    data_io.save_data("solidity_config.json", cfg)   # materializa a config versionada
    os.makedirs(out_dados, exist_ok=True)
    _write_csvs(cands, out_dados)
    print(f"solidity: {len(cands)} candidatas | {n_solidas} sólidas (3de3) | {n_2de3} em 2de3 | "
          f"temporal_validado={tv.get('validated')} (AP={tv.get('average_precision')}, "
          f"prev={tv.get('prevalencia')}, pos={tv.get('n_positivos')}) | semântico={sem_meta['metodo']}")
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
