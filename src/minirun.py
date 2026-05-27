#!/usr/bin/env python3
"""Mini-funil de cocitação (Python puro + OpenAlex; uso único, requer rede).

Versão enxuta e local do funil pesado do Colab: faz snowball progressivo das
obras-semente, computa a rede de COCITAÇÃO real entre as referências mais
cocitadas, atribui eixo por vocabulário e detecta pontes (nós cocitados entre
eixos distintos). Escreve data/network.json (esquema do site) com a rede real.

NÃO substitui o funil completo (Leiden/Kleinberg/betweenness): é um corte
verificável aqui para alimentar a visualização e testar a convergência.

Uso:  python src/minirun.py
"""
import json
import math
import os
import time
from collections import Counter, defaultdict
from itertools import combinations

from oa import UA, get  # noqa: F401  (pool polido + chave Premium via ambiente)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SEEDS = {  # id -> (rótulo curto, eixo)
    "W2048086870": ("Beer · Brain of the Firm", "Cyb"),
    "W1566478880": ("Beer · Heart of Enterprise", "Cyb"),
    "W2154683088": ("Beer · Diagnosing the System", "Cyb"),
    "W2325487953": ("Ashby · Intro to Cybernetics", "Cyb"),
    "W4244612406": ("Espejo & Reyes · Org. Systems", "Cyb"),
    "W1601629960": ("Hood · Tools of Government", "Reg"),
    "W2126563689": ("Hood & Margetts · Digital Age", "Reg"),
    "W4386803846": ("Margetts · Nodality", "Reg"),
    "W3124879925": ("Rodrik · Industrial Policy 21C", "PolInd"),
    "W1553746973": ("Mazzucato · Entrepreneurial State", "PolInd"),
    "W4230710385": ("Lange · Economic Cybernetics", "Cyb"),
    "W3130930004": ("Lange · Economic Theory of Socialism", "PolInd"),
    "W2063282131": ("Lange · Wholes and Parts", "Cyb"),
}
VOCAB = {  # vocabulário conservador (de preferência multipalavra) por eixo
    "Cyb": ("cybernet", "viable system", "vsm", "stafford beer", "ashby", "requisite variety",
            "autopoiesis", "systems thinking", "soft systems", "homeostas", "second-order", "wiener",
            "feedback", "systems approach", "systems practice", "systems methodolog", "system of systems",
            "systems engineering", "general system theory", "critical systems", "critical heuristics",
            "team syntegrity", "fifth discipline", "system dynamics", "multimethodolog", "self-organ",
            "brain of the firm", "heart of enterprise", "diagnosing the system", "corporate future",
            "von bertalanffy", "organizational learning", "theory of communication", "total systems",
            "problem structuring", "principles of systems"),
    "Reg": ("tools of government", "policy instrument", "policy mix", "nodality", "regulat",
            "governance", "policy design", "policy capacity", "public polic", "policy cycle",
            "policy process", "instruments of government", "policy tool"),
    "PolInd": ("industrial policy", "developmental state", "state capacity", "entrepreneurial state",
               "mission-oriented", "industrial strategy", "central plan", "socialism", "economic cybernetic",
               "innovation policy", "reindustrial", "competitive advantage", "economic development",
               "economic change", "self-discovery", "innovation system"),
}


def axis_of(title):
    t = (title or "").lower()
    hit = [a for a, ks in VOCAB.items() if any(k in t for k in ks)]
    return hit[0] if hit else ""


def main():
    # 1) Snowball progressivo: trabalhos que citam cada semente (até 50 por semente)
    corpus_refs = []  # lista de listas de referências (uma por trabalho do corpus)
    for sid in SEEDS:
        r = get(f"https://api.openalex.org/works?filter=cites:{sid}&sort=cited_by_count:desc"
                f"&per-page=50&select=id,referenced_works")
        for w in r.get("results", []):
            refs = [x.split("/")[-1] for x in (w.get("referenced_works") or [])]
            if refs:
                corpus_refs.append(refs[:60])
        time.sleep(0.2)
    print(f"corpus (citantes com refs): {len(corpus_refs)} trabalhos")

    # 2) Cocitação: pares de referências citadas juntas
    cocit = Counter()
    freq = Counter()
    for refs in corpus_refs:
        for a in refs:
            freq[a] += 1
        for a, b in combinations(sorted(set(refs)), 2):
            cocit[(a, b)] += 1
    # nós: referências mais cocitadas (por força total) + as sementes
    strength = Counter()
    for (a, b), w in cocit.items():
        strength[a] += w; strength[b] += w
    TOPN = 70
    top = {n for n, _ in strength.most_common(TOPN)} | set(SEEDS)
    edges = [(a, b, w) for (a, b), w in cocit.items() if a in top and b in top and w >= 3]
    nodeset = set(SEEDS) | {n for e in edges for n in e[:2]}
    print(f"nós candidatos: {len(nodeset)} | arestas (cocit>=3): {len(edges)}")

    # 3) metadados dos nós (título/ano/citações) para rótulo e eixo
    ids = list(nodeset)
    meta = {}
    for i in range(0, len(ids), 50):
        r = get(f"https://api.openalex.org/works?filter=openalex:{'|'.join(ids[i:i+50])}"
                f"&per-page=50&select=id,title,publication_year,cited_by_count,topics")
        for w in r.get("results", []):
            wid = w["id"].split("/")[-1]
            cnames = " ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:6])
            meta[wid] = (w.get("title") or "", w.get("publication_year"), w.get("cited_by_count") or 0, cnames)
        time.sleep(0.2)
    # fallback individual para ids que o lote descartou (obras mescladas/redirecionadas)
    for wid in [i for i in ids if i not in meta]:
        w = get(f"https://api.openalex.org/works/{wid}?select=id,title,publication_year,cited_by_count,topics")
        if w.get("id"):
            cnames = " ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:6])
            meta[wid] = (w.get("title") or "", w.get("publication_year"), w.get("cited_by_count") or 0, cnames)
        time.sleep(0.2)

    nodes = []
    for n in nodeset:
        title, year, cit, cnames = meta.get(n, ("", None, 0, ""))
        if n in SEEDS:
            label, ax = SEEDS[n][0], SEEDS[n][1]
        else:
            label, ax = (title[:42] or n), axis_of(title + " " + cnames)
        nodes.append({"id": n, "label": label, "axis": ax, "cited_by": int(cit),
                      "year": (int(year) if year else None), "seed": n in SEEDS})
    links = [{"source": a, "target": b, "tipo": "cocita", "peso": int(w)} for a, b, w in edges]

    # 4) pontes: nós cujos vizinhos por cocitação abrangem >= 2 eixos
    ax_by = {n["id"]: n["axis"] for n in nodes}
    neigh = defaultdict(set)
    for l in links:
        neigh[l["source"]].add(ax_by.get(l["target"], ""))
        neigh[l["target"]].add(ax_by.get(l["source"], ""))
    bridges = [n["id"] for n in nodes if len({a for a in neigh[n["id"]] if a}) >= 2]

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump({"nodes": nodes, "links": links},
              open(os.path.join(ROOT, "data", "network.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"REDE: {len(nodes)} nós, {len(links)} arestas de cocitação")
    print("eixos:", dict(Counter(n["axis"] or "—" for n in nodes)))

    # 4b) métricas estruturais (Science of Science): modularidade da partição por
    #     eixo (os eixos são comunidades reais?), fração de cocitação entre eixos e
    #     cocitação normalizada (força de associação), que corrige o viés de citação.
    deg = defaultdict(float); m = 0.0
    for l in links:
        deg[l["source"]] += l["peso"]; deg[l["target"]] += l["peso"]; m += l["peso"]
    within = sum(l["peso"] for l in links if ax_by[l["source"]] == ax_by[l["target"]])
    sumk = defaultdict(float)
    for n in nodes:
        sumk[n["axis"] or ""] += deg[n["id"]]
    Q = within / m - sum((s / (2 * m)) ** 2 for s in sumk.values()) if m else 0
    cl = [l for l in links if ax_by[l["source"]] and ax_by[l["target"]]]
    cross = sum(1 for l in cl if ax_by[l["source"]] != ax_by[l["target"]])
    print(f"modularidade Q (partição por eixo): {Q:.3f}")
    if cl:
        print(f"cocitação entre classificados: {len(cl)} | cruzam eixos: {cross} ({100 * cross / len(cl):.0f}%)")
    lab = {n["id"]: n["label"] for n in nodes}
    assoc = sorted(((l["peso"] / math.sqrt(deg[l["source"]] * deg[l["target"]]), l) for l in links
                    if deg[l["source"]] * deg[l["target"]] > 0), key=lambda x: -x[0])
    print("maiores forças de associação (cocitação normalizada):")
    for s, l in assoc[:6]:
        print(f"   {s:.3f} | {lab[l['source']][:24]} ~ {lab[l['target']][:24]}")
    lange = [n for n in nodes if "Lange" in n["label"]]
    print("Lange na rede:", [(n["label"], n["axis"], n["id"] in bridges) for n in lange])
    print(f"nós-ponte (vizinhança cruza eixos): {len(bridges)}")
    for nid in bridges[:12]:
        nm = next(n["label"] for n in nodes if n["id"] == nid)
        print("   ponte ·", ax_by[nid] or "—", "·", nm[:48])


if __name__ == "__main__":
    main()
