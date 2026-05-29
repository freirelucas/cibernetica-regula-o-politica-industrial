#!/usr/bin/env python3
"""Caminhos potenciais entre as comunidades epistêmicas (sem rede; stdlib).

As pontes diretas entre cibernética, instrumentos de governo, política industrial e
economia da complexidade são raras (modelo nulo: nenhuma acima do acaso). A questão
construtiva é: por ONDE passam as rotas mais curtas entre essas comunidades, e quais
obras são os DEGRAUS dessas rotas? Para cada par de comunidades (eixos), este script
encontra a distância de cocitação mais curta, um caminho-exemplo e o conjunto de obras
INTERMEDIÁRIAS que se situam em algum caminho mínimo — ranqueando as que ligam o maior
número de pares (os degraus para construir a convergência).

Uso:  python src/paths_between.py [--net data/network_4axis.json]
"""
import argparse
import json
import os
from collections import defaultdict, deque
from itertools import combinations

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AXES = ["Cyb", "Reg", "PolInd", "Cplx"]
AXN = {"Cyb": "cibernética", "Reg": "instrumentos de governo",
       "PolInd": "política industrial", "Cplx": "economia da complexidade"}


def load(path):
    net = json.load(open(path, encoding="utf-8"))
    nodes = {n["id"]: n for n in net["nodes"]}
    adj = defaultdict(set)
    for l in net["links"]:
        adj[l["source"]].add(l["target"]); adj[l["target"]].add(l["source"])
    return nodes, adj


def bfs_dist(adj, sources):
    d = {s: 0 for s in sources}
    Q = deque(sources)
    while Q:
        v = Q.popleft()
        for w in adj[v]:
            if w not in d:
                d[w] = d[v] + 1; Q.append(w)
    return d


def example_path(adj, A, B):
    prev = {s: None for s in A}
    Q = deque(A); tgt = set(B)
    while Q:
        v = Q.popleft()
        if v in tgt and v not in A:
            p = [v]
            while prev[p[-1]] is not None:
                p.append(prev[p[-1]])
            return p[::-1]
        for w in adj[v]:
            if w not in prev:
                prev[w] = v; Q.append(w)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default=os.path.join(ROOT, "data", "network_4axis.json"))
    args = ap.parse_args()
    if not os.path.exists(args.net):
        args.net = os.path.join(ROOT, "data", "network.json")
    nodes, adj = load(args.net)
    axis = {n: nodes[n].get("axis") or "" for n in nodes}
    lab = {n: nodes[n].get("label", n) for n in nodes}
    grp = {a: [n for n in nodes if axis[n] == a] for a in AXES}
    present = [a for a in AXES if grp[a]]
    print(f"rede: {args.net.split('/')[-1]} — {len(nodes)} obras; comunidades presentes: "
          + ", ".join(AXN[a] + f" ({len(grp[a])})" for a in present))

    # arestas que cruzam comunidades, por par (as rotas DIRETAS já existentes)
    wt = {}
    for l in json.load(open(args.net, encoding="utf-8"))["links"]:
        wt[(l["source"], l["target"])] = l.get("peso", 1)
        wt[(l["target"], l["source"])] = l.get("peso", 1)
    print("\n== rotas diretas entre comunidades (cocitações que cruzam eixos) ==")
    for a, b in combinations(present, 2):
        xs = [(wt[(u, v)], u, v) for u in grp[a] for v in adj[u] if axis[v] == b]
        xs.sort(reverse=True)
        D = 1 if xs else (min((bfs_dist(adj, grp[a]).get(n, 9) for n in grp[b]), default=9))
        print(f"  {AXN[a]} × {AXN[b]}: {len(xs)} ligações diretas" + (f" (ordem {D}, sem direta)" if not xs else ""))
        for w, u, v in xs[:3]:
            print(f"     {w:>2}× {lab[u][:30]} ~ {lab[v][:30]}")

    # obras na INTERSEÇÃO: cuja vizinhança de cocitação toca várias comunidades
    print("\n== obras na encruzilhada (vizinhança toca ≥3 comunidades) — candidatas a ponte ==")
    rows = []
    for n in nodes:
        comms = {axis[w] for w in adj[n] if axis[w] in AXES}
        comms.discard("")
        cross_w = sum(wt[(n, w)] for w in adj[n] if axis[w] in AXES and axis[w] != axis[n])
        if len(comms) >= 3:
            rows.append((len(comms), cross_w, n, sorted(comms)))
    rows.sort(reverse=True)
    for k, cw, n, comms in rows[:18]:
        cs = "+".join(c[:3] for c in comms)
        print(f"  {k} comunidades (força {cw:>3}) | {AXN.get(axis[n], '—'):22} | {lab[n][:36]}  [{cs}]")
    print(f"\n  total de obras tocando ≥3 comunidades: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
