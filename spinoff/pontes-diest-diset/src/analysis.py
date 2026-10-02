"""Etapa 4 — pontes epistêmicas DIEST × DISET sobre hipergrafos (só stdlib).

Dois hipergrafos sobre os mesmos autores:
  H_co  (coautoria)  — hiperaresta = obra; nós = todos que a assinam.
  H_sem (semântico)  — hiperaresta = termo (vocabulário controlado VCIpea + palavras-chave
                       + classificação + áreas de estudo do portal); nós = autores que o usam.

Produz:
  A. Perfil de produção de cada diretoria + termos CARACTERÍSTICOS (log-odds com prior
     de Dirichlet informativo, Monroe-Colaresi-Quinn 2008; prior = todo o Ipea).
  B. Ligação estrutural: hiperarestas mistas (DIEST+DISET) vs modelo nulo de permutação
     de rótulos; quanto da ponte vem de obras grandes (≥4 assinaturas) e se sobrevive
     no grafo-linha s (s=1,2,3); corretores (brokers) de ordem superior.
  C. Zonas de convergência: termos usados pelos dois lados, com equilíbrio, agrupados
     por sobreposição de usuários.
  D. Colaboradores potenciais: pares DIEST×DISET ativos que ainda não coassinaram,
     por similaridade de perfil (TF-IDF) + fechamento triádico (coautores comuns).
  E. Hiperarestas potenciais: equipes sugeridas por zona (2+2 + corretor).

Saída: data/results.json (lido por src/report.py)
Uso:   python src/analysis.py [--start 2010] [--perm 1000]
"""
import argparse
import collections
import itertools
import math
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, load_json, norm, save_json  # noqa: E402
import membership  # noqa: E402

D, S = FOCUS
STOP_TERMS = {"brasil", "brazil", "ipea", "", "-", "outros"}


# ───────────────────────────── termos ─────────────────────────────
def split_terms(values):
    for v in values:
        for t in re.split(r"[;|]", v):
            t = t.strip(" .;,:-").strip()
            if 2 < len(t) < 90:
                yield t


def item_terms(it, with_classes=True):
    """Termos da obra. `with_classes=False` tira as classes amplas (ipea.classification),
    que servem ao contraste de perfis mas aglutinam tudo nas zonas de convergência."""
    out = collections.Counter()
    fields = it.get("vcipea", []) + it.get("keywords", []) + (it.get("classification", []) if with_classes else [])
    for t in split_terms(fields):
        k = norm(t)
        if k not in STOP_TERMS:
            out[k] += 1
    return out


def log_odds(counts_a, counts_b, prior, alpha0=None):
    """Monroe et al. (2008): log-odds com prior de Dirichlet informativo → z-scores."""
    na, nb, n0 = sum(counts_a.values()), sum(counts_b.values()), sum(prior.values())
    alpha0 = alpha0 or max(100.0, 0.01 * n0)
    z = {}
    for w in set(counts_a) | set(counts_b):
        aw = alpha0 * prior.get(w, 0.5) / n0
        ya, yb = counts_a.get(w, 0), counts_b.get(w, 0)
        la = math.log((ya + aw) / (na + alpha0 - ya - aw))
        lb = math.log((yb + aw) / (nb + alpha0 - yb - aw))
        var = 1.0 / (ya + aw) + 1.0 / (yb + aw)
        z[w] = (la - lb) / math.sqrt(var)
    return z


# ───────────────────────────── hipergrafo ─────────────────────────────
def s_line_components(edges, s):
    """Componentes do grafo-linha s (hiperarestas ligadas se partilham ≥ s nós)."""
    parent = list(range(len(edges)))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    by_node = collections.defaultdict(list)
    for i, e in enumerate(edges):
        for v in e:
            by_node[v].append(i)
    for i, e in enumerate(edges):
        shared = collections.Counter()
        for v in e:
            for j in by_node[v]:
                if j > i:
                    shared[j] += 1
        for j, c in shared.items():
            if c >= s:
                parent[find(i)] = find(j)
    return [find(i) for i in range(len(edges))]


def cosine(a, b):
    if not a or not b:
        return 0.0
    if len(a) > len(b):
        a, b = b, a
    num = sum(v * b.get(k, 0.0) for k, v in a.items())
    return num / (math.sqrt(sum(v * v for v in a.values())) * math.sqrt(sum(v * v for v in b.values())))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=2010)
    ap.add_argument("--perm", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    rng = random.Random(args.seed)

    authors = load_json("authors.json")
    items = [i for i in load_json("items_tagged.json") if i["year"] and i["year"] >= args.start]
    dir_of = {a: v["diretoria"] for a, v in authors.items() if v["diretoria"]}
    members = {d: {a for a, x in dir_of.items() if x == d} for d in FOCUS}
    # ativo = no diretório do portal, OU com cargo explícito, OU com produção recente e ≥3 obras
    # rotuladas na diretoria (o diretório do portal é incompleto: há servidores e bolsistas fora dele)
    active = {d: {a for a in members[d] if authors[a]["active"]
                  and (authors[a]["staff"] or authors[a]["n_tagged"] >= 3)} for d in FOCUS}
    display = {}  # forma de exibição de cada termo normalizado

    # ── A. perfil de produção ──
    prior, prof = collections.Counter(), {d: collections.Counter() for d in FOCUS}
    by_year = {d: collections.Counter() for d in FOCUS}
    by_type = {d: collections.Counter() for d in FOCUS}
    corpus_of = {d: [] for d in FOCUS}
    for it in items:
        tc = item_terms(it)
        for t in split_terms(it.get("vcipea", []) + it.get("keywords", []) + it.get("classification", [])):
            display.setdefault(norm(t), t)
        prior.update(tc)
        sides = {d for d in FOCUS if d in it["dirs"] or any(dir_of.get(a) == d for a in it["authors"])}
        for d in sides:
            corpus_of[d].append(it)
            by_year[d][it["year"]] += 1
            by_type[d][it["type"] or "?"] += 1
            if len(sides) == 1:  # contraste limpo: obra exclusiva de um lado
                prof[d].update(tc)
    z = log_odds(prof[D], prof[S], prior)
    ranked = sorted(z.items(), key=lambda kv: kv[1])
    characteristic = {
        D: [{"term": display.get(w, w), "z": round(v, 2), "n": prof[D][w]} for w, v in reversed(ranked[-30:])],
        S: [{"term": display.get(w, w), "z": round(v, 2), "n": prof[S][w]} for w, v in ranked[:30]],
    }
    for d in (S,):
        for x in characteristic[d]:
            x["z"] = -x["z"]
    shared_terms = sorted(
        (w for w in z if abs(z[w]) < 1.5 and prof[D][w] >= 5 and prof[S][w] >= 5),
        key=lambda w: -(prof[D][w] * prof[S][w]))[:30]

    # ── B. hipergrafo de coautoria ──
    edges = [(it, set(it["authors"])) for it in items if it["authors"]]
    sizes = collections.Counter(min(len(e), 10) for _, e in edges)
    focus_edges = [(it, e) for it, e in edges if any(dir_of.get(a) in FOCUS for a in e)]

    def is_mixed(e, lab):
        ds = {lab.get(a) for a in e}
        return D in ds and S in ds
    mixed = [(it, e) for it, e in focus_edges if is_mixed(e, dir_of)]
    obs = len(mixed)
    pool = [a for a in dir_of if dir_of[a] in FOCUS]
    labels = [dir_of[a] for a in pool]
    null = []
    for _ in range(args.perm):
        rng.shuffle(labels)
        lab = dict(zip(pool, labels))
        null.append(sum(1 for _, e in focus_edges if is_mixed(e, lab)))
    mu = sum(null) / len(null)
    sd = math.sqrt(sum((x - mu) ** 2 for x in null) / max(1, len(null) - 1)) or 1.0
    p_low = sum(1 for x in null if x <= obs) / len(null)

    # pares cruzados e de onde vêm
    pair_min = {}
    pair_w = collections.Counter()
    for it, e in focus_edges:
        ds_ = [a for a in e if dir_of.get(a) == D]
        ss_ = [a for a in e if dir_of.get(a) == S]
        for a, b in itertools.product(ds_, ss_):
            pair_min[(a, b)] = min(pair_min.get((a, b), 99), len(e))
            pair_w[(a, b)] += 1.0 / (len(e) - 1)
    big_only = sum(1 for v in pair_min.values() if v >= 4)
    s_line = {}
    fe = [e for _, e in focus_edges]
    dominant = []
    for _, e in focus_edges:
        cd = sum(1 for a in e if dir_of.get(a) == D)
        cs = sum(1 for a in e if dir_of.get(a) == S)
        dominant.append(D if cd > cs else S if cs > cd else None)
    for s in (1, 2, 3):
        comp = s_line_components(fe, s)
        sides = collections.defaultdict(set)
        for c, dom in zip(comp, dominant):
            if dom:
                sides[c].add(dom)
        bridged = [c for c, v in sides.items() if len(v) == 2]
        sz = collections.Counter(comp)
        s_line[s] = {"components": len(sz), "bridging_components": len(bridged),
                     "largest_bridging_size": max((sz[c] for c in bridged), default=0)}

    # corretores: quem coassina com os dois lados
    nbr = collections.defaultdict(lambda: {D: set(), S: set(), "eD": 0, "eS": 0})
    for it, e in focus_edges:
        hasD = any(dir_of.get(a) == D for a in e)
        hasS = any(dir_of.get(a) == S for a in e)
        for a in e:
            for b in e:
                if b != a and dir_of.get(b) in FOCUS:
                    nbr[a][dir_of[b]].add(b)
            nbr[a]["eD"] += hasD
            nbr[a]["eS"] += hasS
    brokers = []
    for a, x in nbr.items():
        nd, ns = len(x[D]), len(x[S])
        if nd and ns:
            brokers.append({"id": a, "name": authors[a]["name"], "diretoria": dir_of.get(a),
                            "staff": authors[a]["staff"], "active": authors[a]["active"],
                            "n_coaut_DIEST": nd, "n_coaut_DISET": ns,
                            "score": round(math.sqrt(nd * ns), 2),
                            "balance": round(2 * min(nd, ns) / (nd + ns), 2)})
    brokers.sort(key=lambda b: -b["score"])
    trajectory = []
    for a, v in authors.items():
        w = v["dir_weights"]
        tot = sum(w.values()) or 1
        if v["staff"] and w.get(D, 0) / tot >= 0.2 and w.get(S, 0) / tot >= 0.2:
            trajectory.append({"id": a, "name": v["name"], "diretoria": v["diretoria"],
                               "share_DIEST": round(w.get(D, 0) / tot, 2),
                               "share_DISET": round(w.get(S, 0) / tot, 2), "active": v["active"]})
    trajectory.sort(key=lambda t: -min(t["share_DIEST"], t["share_DISET"]))

    # ── C. hipergrafo semântico e zonas de convergência ──
    act = active[D] | active[S]
    aprof = {a: collections.Counter() for a in act}
    for it in items:
        tc = item_terms(it, with_classes=False)
        for a in it["authors"]:
            if a in aprof:
                aprof[a].update(tc)
    for a in act:
        for ar in authors[a]["areas"]:
            k = norm(ar)
            display.setdefault(k, ar)
            aprof[a][k] += 2
    users = collections.defaultdict(set)
    for a, c in aprof.items():
        for t in c:
            users[t].add(a)
    n_act = len(act) or 1
    idf = {t: math.log(n_act / len(u)) + 1 for t, u in users.items()}
    vec = {a: {t: (1 + math.log(c)) * idf[t] for t, c in aprof[a].items()} for a in act}

    conv = []
    for t, u in users.items():
        if len(u) > 0.25 * n_act:  # termo genérico demais para definir zona
            continue
        nd = sum(1 for a in u if a in active[D])
        ns = sum(1 for a in u if a in active[S])
        if nd >= 2 and ns >= 2:
            bal = 2 * min(nd, ns) / (nd + ns)
            conv.append((t, nd, ns, bal * math.log(1 + nd + ns)))
    conv.sort(key=lambda x: -x[3])
    conv = conv[:60]
    # agrupa termos por Jaccard dos usuários (union-find, limiar 0,3)
    parent = {t: t for t, *_ in conv}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for (t1, *_), (t2, *_) in itertools.combinations(conv, 2):
        u1, u2 = users[t1], users[t2]
        if len(u1 & u2) / len(u1 | u2) >= 0.3:
            parent[find(t1)] = find(t2)
    groups = collections.defaultdict(list)
    for t, nd, ns, sc in conv:
        groups[find(t)].append((t, nd, ns, sc))
    zones = []
    for g in sorted(groups.values(), key=lambda g: -sum(x[3] for x in g)):
        terms = [x[0] for x in sorted(g, key=lambda x: -x[3])]
        weight = collections.Counter()
        for t in terms:
            for a in users[t]:
                weight[a] += vec[a].get(t, 0.0)
        topD = [a for a, _ in weight.most_common() if a in active[D]][:4]
        topS = [a for a, _ in weight.most_common() if a in active[S]][:4]
        zitems = [it for it, e in mixed if set(item_terms(it, with_classes=False)) & set(terms)]
        # corretor: quem já coassinou com pelo menos um de cada lado da zona
        best, best_key = None, (0, 0)
        for b in brokers:
            nb = nbr[b["id"]]
            hd, hs = len(nb[D] & set(topD)), len(nb[S] & set(topS))
            if hd and hs and (hd + hs, b["score"]) > best_key:
                best, best_key = b["id"], (hd + hs, b["score"])
        team = topD[:2] + topS[:2] + ([best] if best and best not in topD[:2] + topS[:2] else [])
        zones.append({
            "label": " · ".join(display.get(t, t) for t in terms[:3]),
            "terms": [display.get(t, t) for t in terms],
            "score": round(sum(x[3] for x in g), 2),
            "DIEST": [authors[a]["name"] for a in topD], "DISET": [authors[a]["name"] for a in topS],
            "mixed_items_existing": len(zitems),
            "examples": [{"title": it["title"], "year": it["year"], "uri": it["uri"]} for it in zitems[:3]],
            "potential_hyperedge": [authors[a]["name"] for a in team],
            "broker": authors[best]["name"] if best else None,
        })

    # ── D. colaboradores potenciais ──
    coauth = set()
    common = collections.defaultdict(set)
    for _, e in edges:
        for a, b in itertools.permutations(e, 2):
            coauth.add((a, b))
    neigh = collections.defaultdict(set)
    for a, b in coauth:
        neigh[a].add(b)
    pairs = []
    for a in active[D]:
        for b in active[S]:
            c = cosine(vec[a], vec[b])
            if c <= 0:
                continue
            already = (a, b) in coauth
            cm = neigh[a] & neigh[b]
            score = c * (1 + 0.25 * min(len(cm), 4))
            shared = sorted(set(vec[a]) & set(vec[b]), key=lambda t: -(vec[a][t] * vec[b][t]))[:5]
            pairs.append({"DIEST": authors[a]["name"], "DISET": authors[b]["name"],
                          "cosine": round(c, 3), "score": round(score, 3), "already": already,
                          "common_coauthors": [authors[x]["name"] for x in list(cm)[:4]],
                          "n_common": len(cm), "shared_terms": [display.get(t, t) for t in shared]})
    pairs.sort(key=lambda p: -p["score"])
    potential = [p for p in pairs if not p["already"]][:40]
    existing = [p for p in pairs if p["already"]][:20]

    def roster_view(d):
        rows = []
        for a in sorted(members[d], key=lambda a: -authors[a]["n_items"]):
            v = authors[a]
            rows.append({"name": v["name"], "active": a in active[d], "staff": v["staff"],
                         "source": "diretório" if v["roster"] else ("cargo" if v["staff"] else "produção"),
                         "confidence": v["confidence"], "validation": v.get("validation"),
                         "share": v["share"], "n_items": v["n_items"],
                         "n_tagged": v["n_tagged"], "last_year": v["last_year"],
                         "top_terms": [display.get(t, t) for t, _ in sorted(
                             vec.get(a, {}).items(), key=lambda kv: -kv[1])[:6]],
                         "areas": v["areas"][:6], "profile_url": v["profile_url"]})
        return rows

    results = {
        "params": {"start": args.start, "perm": args.perm, "seed": args.seed},
        "counts": {
            "items_window": len(items), "authors_total": len(authors),
            "members": {d: len(members[d]) for d in FOCUS},
            "active_staff": {d: len(active[d]) for d in FOCUS},
            "items_by_side": {d: len(corpus_of[d]) for d in FOCUS},
            "hyperedge_sizes": {str(k): v for k, v in sorted(sizes.items())},
            "share_size_ge3": round(sum(v for k, v in sizes.items() if k >= 3) / max(1, sum(sizes.values())), 3),
        },
        "validation": membership.audit(authors, save=False),
        "people": {d: roster_view(d) for d in FOCUS},
        "unassigned_with_signal": sorted(
            ({"name": v["name"], "dir_weights": v["dir_weights"], "n_items": v["n_items"]}
             for v in authors.values()
             if v["roster"] and not v["diretoria"] and (v["dir_weights"].get(D) or v["dir_weights"].get(S))),
            key=lambda x: -(x["dir_weights"].get(D, 0) + x["dir_weights"].get(S, 0))),
        "production": {d: {"by_year": dict(sorted(by_year[d].items())),
                           "by_type": dict(by_type[d].most_common(10))} for d in FOCUS},
        "characteristic": characteristic,
        "shared_high_volume_terms": [{"term": display.get(w, w), "n_DIEST": prof[D][w], "n_DISET": prof[S][w]}
                                     for w in shared_terms],
        "structural": {
            "focus_hyperedges": len(focus_edges), "mixed_hyperedges": obs,
            "null_mean": round(mu, 1), "null_sd": round(sd, 1), "z": round((obs - mu) / sd, 2),
            "p_le_obs": round(p_low, 4),
            "cross_pairs": len(pair_min), "cross_pairs_only_via_size_ge4": big_only,
            "s_line": s_line,
            "mixed_by_year": dict(sorted(collections.Counter(it["year"] for it, _ in mixed).items())),
            "mixed_examples": [{"title": it["title"], "year": it["year"], "uri": it["uri"],
                                "authors": [authors[a]["name"] for a in it["authors"]][:8]}
                               for it, _ in sorted(mixed, key=lambda x: -x[0]["year"])[:25]],
            "strongest_cross_pairs": [{"DIEST": authors[a]["name"], "DISET": authors[b]["name"],
                                       "newman_w": round(w, 2)} for (a, b), w in pair_w.most_common(15)],
        },
        "brokers": brokers[:30],
        "trajectory_bridges": trajectory[:20],
        "convergence_terms": [{"term": display.get(t, t), "n_DIEST": nd, "n_DISET": ns, "score": round(sc, 2)}
                              for t, nd, ns, sc in conv[:40]],
        "zones": zones[:12],
        "potential_collaborators": potential,
        "existing_collaborations": existing,
    }
    save_json("results.json", results)
    st = results["structural"]
    print(f"janela ≥{args.start}: {len(items)} obras · membros {results['counts']['members']} · "
          f"ativos {results['counts']['active_staff']}", file=sys.stderr)
    print(f"mistas DIEST+DISET: {obs} (nulo {mu:.1f}±{sd:.1f}, z={st['z']}) · zonas: {len(zones)} · "
          f"pares potenciais: {len(potential)}", file=sys.stderr)


if __name__ == "__main__":
    main()
