#!/usr/bin/env python3
"""Conexões de ordem superior na rede de cocitação — caça às pontes epistêmicas.

As ligações DIRETAS entre eixos são raras (poucas cocitações cruzam cibernética ×
regulação × política industrial). A hipótese aqui é que a riqueza está nas conexões
INDIRETAS — de 2ª, 3ª ordem: obras que não cocitam diretamente entre eixos, mas que
ligam as tradições por cadeias curtas. Este script, sobre data/network_exploded.json
(ou network.json), mede:

  • centralidade de intermediação (Brandes, 2001) — os intermediários globais;
  • a ORDEM (comprimento do caminho mais curto) em que cada par de eixos se conecta,
    com um caminho-exemplo e seus intermediários (as pontes epistêmicas candidatas);
  • o alcance por nº de saltos: quais eixos cada obra atinge em 1, 2, 3 saltos, e quais
    obras alcançam os TRÊS eixos em poucos saltos (corretoras tri-axiais).

Uso:  python src/bridges_higher_order.py [--net data/network_exploded.json]
"""
import argparse
import json
import os
import sys
from collections import defaultdict, deque

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfi_methods as sfi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AXN = {"Cyb": "cibernética", "Reg": "instrumentos de governo", "PolInd": "política industrial"}


def load(path):
    net = json.load(open(path, encoding="utf-8"))
    nodes = {n["id"]: n for n in net["nodes"]}
    adj = defaultdict(set)
    for l in net["links"]:
        adj[l["source"]].add(l["target"]); adj[l["target"]].add(l["source"])
    return nodes, adj


def betweenness(adj, V):
    """Brandes (2001), não-ponderado."""
    CB = dict.fromkeys(V, 0.0)
    for s in V:
        S, P = [], defaultdict(list)
        sigma = dict.fromkeys(V, 0); sigma[s] = 1
        d = dict.fromkeys(V, -1); d[s] = 0
        Q = deque([s])
        while Q:
            v = Q.popleft(); S.append(v)
            for w in adj[v]:
                if d[w] < 0:
                    d[w] = d[v] + 1; Q.append(w)
                if d[w] == d[v] + 1:
                    sigma[w] += sigma[v]; P[w].append(v)
        delta = dict.fromkeys(V, 0.0)
        while S:
            w = S.pop()
            for v in P[w]:
                delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
            if w != s:
                CB[w] += delta[w]
    return {v: c / 2 for v, c in CB.items()}


def shortest_path(adj, sources, targets):
    """BFS multi-fonte: menor caminho de qualquer source a qualquer target. Devolve o caminho."""
    prev = {s: None for s in sources}
    Q = deque(sources)
    tset = set(targets)
    while Q:
        v = Q.popleft()
        if v in tset and v not in sources:
            path = [v]
            while prev[path[-1]] is not None:
                path.append(prev[path[-1]])
            return path[::-1]
        for w in adj[v]:
            if w not in prev:
                prev[w] = v; Q.append(w)
    return None


def khop_axes(adj, axis, start, k):
    seen, frontier, reach = {start}, {start}, set()
    for _ in range(k):
        nxt = set()
        for v in frontier:
            for w in adj[v]:
                if w not in seen:
                    seen.add(w); nxt.add(w)
                    if axis.get(w):
                        reach.add(axis[w])
        frontier = nxt
    return reach


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default=os.path.join(ROOT, "data", "network_exploded.json"))
    args = ap.parse_args()
    if not os.path.exists(args.net):
        args.net = os.path.join(ROOT, "data", "network.json")
    nodes, adj = load(args.net)
    V = list(nodes)
    axis = {n: nodes[n].get("axis") or "" for n in V}
    lab = {n: nodes[n].get("label", n) for n in V}
    print(f"rede: {args.net.split('/')[-1]} — {len(V)} nós, {sum(len(a) for a in adj.values())//2} arestas")

    net = json.load(open(args.net, encoding="utf-8"))
    links = net["links"]
    CB = betweenness(adj, V)

    # CONECTORES ENTRE COMUNIDADES — coeficiente de participação (Guimerà & Amaral, 2005),
    # sobre as comunidades DETECTADAS (CNM), ponderado e normalizado pelo grau. É a medida
    # correta de "conector entre comunidades" — separa o conector do simples hub citado.
    comm, Qd, k = sfi.cnm_communities(V, links)
    P, z = sfi.participation_z(V, links, comm)
    deg = defaultdict(float)
    for l in links:
        deg[l["source"]] += l.get("peso", 1); deg[l["target"]] += l.get("peso", 1)
    print(f"\n== conectores entre comunidades (participação; CNM: {k} comunidades, Q={Qd}) ==")
    print("   os de MAIOR participação P — ligações espalhadas por comunidades:")
    for n in sorted(V, key=lambda n: -P[n])[:15]:
        print(f"   P={P[n]:.2f} z={z[n]:+.1f} {sfi.ga_role(P[n], z[n]):14} | {AXN.get(axis[n], '—'):22} | {lab[n][:38]}")

    print("\n== contraste: os TOP intermediação são conectores ou só hubs citados? ==")
    for n, c in sorted(CB.items(), key=lambda kv: -kv[1])[:10]:
        print(f"   bt={c:8.0f} P={P[n]:.2f} {sfi.ga_role(P[n], z[n]):14} | {lab[n][:40]}")

    print("\n== ordem de conexão entre eixos (caminho mais curto de cocitação) ==")
    groups = {a: [n for n in V if axis[n] == a] for a in ("Cyb", "Reg", "PolInd")}
    for a, b in (("Cyb", "Reg"), ("Cyb", "PolInd"), ("Reg", "PolInd")):
        path = shortest_path(adj, set(groups[a]), set(groups[b])) if groups[a] and groups[b] else None
        if not path:
            print(f"   {AXN[a]} × {AXN[b]}: desconexos"); continue
        order = len(path) - 1
        inter = " → ".join(f"{lab[p][:24]} [{AXN.get(axis[p], '—')[:3]}]" for p in path)
        print(f"   {AXN[a]} × {AXN[b]}: ordem {order}")
        print(f"      {inter}")
        if order >= 2:
            mids = [p for p in path[1:-1]]
            print(f"      pontes epistêmicas (intermediárias): " +
                  ", ".join(f"{lab[m][:34]}" for m in mids))

    print("\n== corretoras tri-axiais (alcançam os 3 eixos em poucos saltos) ==")
    rows = []
    for n in V:
        for k in (1, 2, 3):
            r = khop_axes(adj, axis, n, k)
            if len(r) == 3:
                rows.append((k, CB[n], n))
                break
    rows.sort(key=lambda x: (x[0], -x[1]))
    for k, c, n in rows[:15]:
        print(f"   {k} salto(s) | interm. {c:7.1f} | {AXN.get(axis[n], '—'):24} | {lab[n][:40]}")
    print(f"\n   total de obras que alcançam os 3 eixos em ≤3 saltos: {len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
