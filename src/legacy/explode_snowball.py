#!/usr/bin/env python3
"""Snowball "explodido": versão muito mais ampla do funil local (uso único; requer rede).

Onde o minirun.py pega 50 citantes por semente, este pega até 200 (o teto do
OpenAlex) e amplia o núcleo (top-N de referências cocitadas), produzindo uma rede
de cocitação de centenas de nós. Depois APRENDE com o resultado, aplicando os
métodos do círculo do Santa Fe Institute (sfi_methods): ajuste de lei de potência
da distribuição de citações (Clauset, Shalizi & Newman, 2009) e detecção de
comunidades por modularidade gulosa (Clauset, Newman & Moore, 2004) — e compara a
estrutura ampliada com os eixos atribuídos por vocabulário.

Escreve data/network_exploded.json e imprime os aprendizados.

Uso:  python src/explode_snowball.py
"""
import json
import os
import time
from collections import Counter, defaultdict
from itertools import combinations

import minirun as mr        # reusa SEEDS, VOCAB, axis_of, get, UA
import sfi_methods as sfi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERPAGE = 200
TOPN = 250
THRESH = 3


def main():
    corpus_refs, corpus_cited = [], []
    for sid in mr.SEEDS:
        r = mr.get(f"https://api.openalex.org/works?filter=cites:{sid}&sort=cited_by_count:desc"
                   f"&per-page={PERPAGE}&select=id,referenced_works,cited_by_count")
        for w in r.get("results", []):
            corpus_cited.append(w.get("cited_by_count") or 0)
            refs = [x.split("/")[-1] for x in (w.get("referenced_works") or [])]
            if refs:
                corpus_refs.append(refs[:80])
        time.sleep(0.2)
    print(f"corpus explodido: {len(corpus_refs)} trabalhos citantes (com refs)")

    cocit, freq = Counter(), Counter()
    for refs in corpus_refs:
        for a in refs:
            freq[a] += 1
        for a, b in combinations(sorted(set(refs)), 2):
            cocit[(a, b)] += 1
    strength = Counter()
    for (a, b), w in cocit.items():
        strength[a] += w; strength[b] += w
    top = {n for n, _ in strength.most_common(TOPN)} | set(mr.SEEDS)
    edges = [(a, b, w) for (a, b), w in cocit.items() if a in top and b in top and w >= THRESH]
    nodeset = set(mr.SEEDS) | {n for e in edges for n in e[:2]}
    print(f"nós candidatos: {len(nodeset)} | arestas (cocit>={THRESH}): {len(edges)}")

    ids = list(nodeset)
    meta = {}
    for i in range(0, len(ids), 25):           # lotes menores são mais robustos no run grande
        r = mr.get(f"https://api.openalex.org/works?filter=openalex:{'|'.join(ids[i:i+25])}"
                   f"&per-page=25&select=id,title,publication_year,cited_by_count,topics")
        for w in r.get("results", []):
            wid = w["id"].split("/")[-1]
            cnames = " ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:6])
            meta[wid] = (w.get("title") or "", w.get("publication_year"), w.get("cited_by_count") or 0, cnames)
        time.sleep(0.2)
    for wid in [i for i in ids if i not in meta]:   # fallback individual p/ ids descartados
        w = mr.get(f"https://api.openalex.org/works/{wid}?select=id,title,publication_year,cited_by_count,topics")
        if w.get("id"):
            cnames = " ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:6])
            meta[wid] = (w.get("title") or "", w.get("publication_year"), w.get("cited_by_count") or 0, cnames)
        time.sleep(0.15)

    nodes = []
    for n in nodeset:
        title, year, cit, cnames = meta.get(n, ("", None, 0, ""))
        if n in mr.SEEDS:
            label, ax = mr.SEEDS[n][0], mr.SEEDS[n][1]
        else:
            label, ax = (title[:60] or n), mr.axis_of(title + " " + cnames)
        nodes.append({"id": n, "label": label, "axis": ax, "cited_by": int(cit),
                      "year": (int(year) if year else None), "seed": n in mr.SEEDS})
    links = [{"source": a, "target": b, "tipo": "cocita", "peso": int(w)} for a, b, w in edges]

    os.makedirs(os.path.join(ROOT, "data"), exist_ok=True)
    json.dump({"nodes": nodes, "links": links},
              open(os.path.join(ROOT, "data", "network_exploded.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"\nREDE EXPLODIDA: {len(nodes)} nós, {len(links)} arestas")
    print("eixos:", dict(Counter(n["axis"] or "—" for n in nodes)))

    # APRENDIZADOS (métodos Santa Fe / Clauset)
    print("\n== aprendizados (métodos do círculo Santa Fe) ==")
    pl_nodes = sfi.powerlaw_fit([n["cited_by"] for n in nodes])
    pl_corpus = sfi.powerlaw_fit(corpus_cited)
    print(f"lei de potência — citações dos nós : {pl_nodes}")
    print(f"lei de potência — corpus citante   : {pl_corpus}")
    comm, Q, k = sfi.cnm_communities([n["id"] for n in nodes], links)
    print(f"CNM (modularidade gulosa): {k} comunidades, Q = {Q}")
    # modularidade da partição por eixo, para comparar
    ax = {n["id"]: (n["axis"] or "") for n in nodes}
    deg = Counter(); m = 0.0
    for l in links:
        deg[l["source"]] += l["peso"]; deg[l["target"]] += l["peso"]; m += l["peso"]
    within = sum(l["peso"] for l in links if ax[l["source"]] == ax[l["target"]])
    sk = Counter()
    for n in nodes:
        sk[ax[n["id"]]] += deg[n["id"]]
    Qax = within / m - sum((s / (2 * m)) ** 2 for s in sk.values()) if m else 0
    print(f"modularidade da partição por eixo: Q = {round(Qax, 3)}")
    # composição das maiores comunidades CNM por eixo
    bycomm = defaultdict(Counter)
    for n in nodes:
        bycomm[comm[n["id"]]][n["axis"] or "—"] += 1
    big = sorted(bycomm.items(), key=lambda kv: -sum(kv[1].values()))[:6]
    print("composição das maiores comunidades (eixo):")
    for cid, comp in big:
        print(f"   c{cid}: {dict(comp)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
