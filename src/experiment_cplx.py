#!/usr/bin/env python3
"""Experimento: a economia da complexidade (Santa Fe, EECS-IV) é um 4º eixo — ou a ponte?
(uso único; requer rede)

Adiciona obras canônicas da economia da complexidade como sementes de um 4º eixo (Cplx)
ao funil e refaz a bola de neve. Depois testa, com os métodos de Clauset/Guimerà:
(1) a economia da complexidade forma uma COMUNIDADE própria? (composição das comunidades
CNM); (2) ela CONECTA os três eixos (coeficiente de participação dos nós Cplx) ou apenas
forma mais um silo? Escreve data/network_cplx.json e imprime o veredito. NÃO altera o
site de três eixos — é uma sondagem.

Uso:  python src/experiment_cplx.py
"""
import json
import os
import time
import urllib.error
import urllib.request
from collections import Counter, defaultdict
from itertools import combinations

import minirun as mr
import sfi_methods as sfi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERPAGE, TOPN, THRESH = 150, 160, 3


def get(url):
    """Fetch robusto com backoff exponencial honrando o 429 do OpenAlex."""
    for i in range(7):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=mr.UA), timeout=45) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            time.sleep(min(60, 5 * (2 ** i)) if e.code == 429 else 3)
        except Exception:
            time.sleep(3)
    return {}

CPLX_SEEDS = {
    "W2137358449": ("Nelson & Winter · Evolutionary Theory", "Cplx"),
    "W2009202666": ("Arthur · Increasing Returns", "Cplx"),
    "W2141042444": ("Arthur · Economy as Evolving Complex System II", "Cplx"),
    "W2050032417": ("Farmer & Foley · Agent-based modelling", "Cplx"),
}
CPLX_VOCAB = ("complexity econom", "increasing returns", "path dependen", "agent-based",
              "evolutionary econom", "complex adaptive", "out-of-equilibrium", "self-organ",
              "santa fe", "complexity and the economy", "economic complexity", "nonequilibrium",
              "emergent", "adaptive system", "evolutionary theory of economic")

SEEDS = {**mr.SEEDS, **CPLX_SEEDS}
VOCAB = {**mr.VOCAB, "Cplx": CPLX_VOCAB}


def axis_of(text):
    t = (text or "").lower()
    hit = [a for a, ks in VOCAB.items() if any(k in t for k in ks)]
    return hit[0] if hit else ""


def main():
    # crawl enxuto: só as 4 sementes de complexidade (menos requisições = menos 429).
    # Os trabalhos que CITAM a economia da complexidade revelam, em suas referências,
    # se ela cocita os outros eixos (ponte) ou só a própria linhagem (silo).
    corpus_refs = []
    cites_core = Counter()                      # citantes Cplx que também citam as sementes dos 3 eixos
    for sid in CPLX_SEEDS:
        r = get(f"https://api.openalex.org/works?filter=cites:{sid}&sort=cited_by_count:desc"
                f"&per-page={PERPAGE}&select=id,referenced_works")
        n0 = len(corpus_refs)
        for w in r.get("results", []):
            refs = [x.split("/")[-1] for x in (w.get("referenced_works") or [])]
            if refs:
                corpus_refs.append(refs[:80])
                for s in set(refs) & set(mr.SEEDS):     # cita alguma semente dos 3 eixos?
                    cites_core[mr.SEEDS[s][1]] += 1
        print(f"  semente {sid}: +{len(corpus_refs)-n0} citantes com refs (total {len(corpus_refs)})", flush=True)
        time.sleep(0.6)
    print(f"corpus (com refs): {len(corpus_refs)} trabalhos citantes", flush=True)
    print(f"citantes de complexidade que também citam as sementes dos 3 eixos: {dict(cites_core)}", flush=True)

    cocit, freq = Counter(), Counter()
    for refs in corpus_refs:
        for a in refs:
            freq[a] += 1
        for a, b in combinations(sorted(set(refs)), 2):
            cocit[(a, b)] += 1
    strength = Counter()
    for (a, b), w in cocit.items():
        strength[a] += w; strength[b] += w
    top = {n for n, _ in strength.most_common(TOPN)} | set(SEEDS)
    edges = [(a, b, w) for (a, b), w in cocit.items() if a in top and b in top and w >= THRESH]
    nodeset = set(SEEDS) | {n for e in edges for n in e[:2]}

    ids = list(nodeset)
    print(f"nós candidatos: {len(ids)} | arestas: {len(edges)} — buscando metadados…", flush=True)
    meta = {}
    for i in range(0, len(ids), 25):
        r = get(f"https://api.openalex.org/works?filter=openalex:{'|'.join(ids[i:i+25])}"
                   f"&per-page=25&select=id,title,publication_year,cited_by_count,topics")
        for w in r.get("results", []):
            wid = w["id"].split("/")[-1]
            cnames = " ".join(t.get("display_name", "") for t in (w.get("topics") or [])[:6])
            meta[wid] = (w.get("title") or "", w.get("publication_year"), w.get("cited_by_count") or 0, cnames)
        time.sleep(0.3)
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
            label, ax = (title[:60] or n), axis_of(title + " " + cnames)
        nodes.append({"id": n, "label": label, "axis": ax, "cited_by": int(cit),
                      "year": (int(year) if year else None), "seed": n in SEEDS})
    links = [{"source": a, "target": b, "tipo": "cocita", "peso": int(w)} for a, b, w in edges]
    json.dump({"nodes": nodes, "links": links},
              open(os.path.join(ROOT, "data", "network_cplx.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    print(f"\nREDE (4 eixos): {len(nodes)} nós, {len(links)} arestas")
    print("eixos:", dict(Counter(n["axis"] or "—" for n in nodes)))

    # ANÁLISE: comunidade própria ou ponte?
    ids = [n["id"] for n in nodes]
    comm, Q, k = sfi.cnm_communities(ids, links)
    P, z = sfi.participation_z(ids, links, comm)
    axof = {n["id"]: n["axis"] for n in nodes}
    lab = {n["id"]: n["label"] for n in nodes}
    print(f"\nCNM: {k} comunidades, Q={Q}")
    bycomm = defaultdict(Counter)
    for n in nodes:
        bycomm[comm[n["id"]]][n["axis"] or "—"] += 1
    for cid, comp in sorted(bycomm.items(), key=lambda kv: -sum(kv[1].values()))[:8]:
        print(f"   c{cid} (n={sum(comp.values())}): {dict(comp)}")

    print("\n(1) os SEEDS de complexidade caem juntos (comunidade própria) ou dispersos?")
    for sid in CPLX_SEEDS:
        if sid in comm:
            print(f"   c{comm[sid]} | P={P[sid]:.2f} {sfi.ga_role(P[sid], z[sid]):14} | {lab[sid][:40]}")

    print("\n(2) os nós Cplx CONECTAM (participação alta) ou são provinciais?")
    cnodes = [n["id"] for n in nodes if n["axis"] == "Cplx"]
    if cnodes:
        avgP = sum(P[n] for n in cnodes) / len(cnodes)
        print(f"   {len(cnodes)} nós Cplx | participação média P={avgP:.2f} "
              f"(conectores: {sum(1 for n in cnodes if P[n] > 0.5)}, provinciais: {sum(1 for n in cnodes if P[n] < 0.2)})")
        for n in sorted(cnodes, key=lambda n: -P[n])[:8]:
            print(f"   P={P[n]:.2f} {sfi.ga_role(P[n], z[n]):14} | {lab[n][:44]}")

    # arestas de Cplx para cada outro eixo (conecta os três?)
    reach = Counter()
    for l in links:
        a, b = axof[l["source"]], axof[l["target"]]
        if a == "Cplx" and b in ("Cyb", "Reg", "PolInd"):
            reach[b] += 1
        if b == "Cplx" and a in ("Cyb", "Reg", "PolInd"):
            reach[a] += 1
    print(f"\n(3) cocitações Cplx × cada eixo: {dict(reach)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
