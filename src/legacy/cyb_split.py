#!/usr/bin/env python3
"""Cibernética GERAL × ORGANIZACIONAL na estrutura da rede (sem rede; stdlib).

Pergunta: o eixo "cibernética" é um bloco só, ou a estrutura de cocitação separa a
cibernética fundacional/geral (Wiener, Ashby, Shannon, teoria geral dos sistemas,
autopoiese) da cibernética organizacional/de gestão (MSV/Beer, Espejo, syntegrity,
soft systems aplicado)? E qual das duas faz fronteira com regulação e política
industrial? Roda sobre as redes já coletadas (data/network_4axis.json por padrão):
detecção de subcomunidades (CNM) dentro da cibernética + rótulo geral/organizacional
por vocabulário + cocitação de cada subtipo com os outros eixos.

Uso:  python src/cyb_split.py [--net data/network_4axis.json]
"""
import argparse
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sfi_methods as sfi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ORG = ("viable system", "vsm", "stafford beer", "beer ", "espejo", "management cybernet",
       "organizational cybernet", "organizational systems", "team syntegrity", "syntegrity",
       "brain of the firm", "heart of enterprise", "diagnosing the system", "designing freedom",
       "platform for change", "cybersyn", "managing complexity", "soft systems", "systems thinking",
       "systems practice", "systems methodolog", "systems approach", "critical systems",
       "problem structuring", "operational research", "total systems", "fifth discipline",
       "creating the corporate future", "organizational learning")
GERAL = ("ashby", "wiener", "requisite variety", "second-order", "second order", "von foerster",
         "introduction to cybernetics", "theory of communication", "shannon", "general system",
         "von bertalanffy", "autopoiesis", "maturana", "varela", "self-organ", "homeostat",
         "self-organizing", "law of requisite", "principles of systems", "general systems theory")


def subtype(label):
    t = (label or "").lower()
    org = any(k in t for k in ORG)
    ger = any(k in t for k in GERAL)
    if org and not ger:
        return "org"
    if ger and not org:
        return "geral"
    if org and ger:
        return "org"        # menção a ambos → trata como organizacional/aplicada
    return "?"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--net", default=os.path.join(ROOT, "data", "network_4axis.json"))
    args = ap.parse_args()
    if not os.path.exists(args.net):
        args.net = os.path.join(ROOT, "data", "network.json")
    net = json.load(open(args.net, encoding="utf-8"))
    nodes = {n["id"]: n for n in net["nodes"]}
    links = net["links"]
    axis = {n: nodes[n].get("axis") or "" for n in nodes}
    lab = {n: nodes[n].get("label", n) for n in nodes}
    cyb = [n for n in nodes if axis[n] == "Cyb"]
    print(f"rede: {args.net.split('/')[-1]} — {len(nodes)} obras; cibernética: {len(cyb)}")

    # (1) subcomunidades EMERGENTES dentro da cibernética (CNM no subgrafo induzido)
    cybset = set(cyb)
    sub_links = [l for l in links if l["source"] in cybset and l["target"] in cybset]
    comm, Q, k = sfi.cnm_communities(cyb, sub_links)
    print(f"\n(1) subcomunidades dentro da cibernética (CNM): {k}, Q={Q}")
    deg = defaultdict(float)
    for l in sub_links:
        deg[l["source"]] += l["peso"]; deg[l["target"]] += l["peso"]
    bycomm = defaultdict(list)
    for n in cyb:
        bycomm[comm[n]].append(n)
    for c, mem in sorted(bycomm.items(), key=lambda kv: -len(kv[1]))[:6]:
        top = sorted(mem, key=lambda n: -deg[n])[:5]
        st = Counter(subtype(lab[n]) for n in mem)
        print(f"   c{c} (n={len(mem)}; {dict(st)}): " + " · ".join(lab[n][:24] for n in top))

    # (2) rótulo geral/organizacional por vocabulário
    st = {n: subtype(lab[n]) for n in cyb}
    print(f"\n(2) rótulo por vocabulário: {dict(Counter(st.values()))}")

    # (3) qual subtipo faz fronteira com os outros eixos?
    cross = {"org": Counter(), "geral": Counter()}
    for l in links:
        a, b = l["source"], l["target"]
        for x, y in ((a, b), (b, a)):
            if axis[x] == "Cyb" and axis[y] in ("Reg", "PolInd", "Cplx") and st.get(x) in ("org", "geral"):
                cross[st[x]][axis[y]] += l["peso"]
    print("\n(3) cocitação (peso) de cada subtipo de cibernética com os outros eixos:")
    for sub in ("org", "geral"):
        tot = sum(cross[sub].values())
        print(f"   {sub:6} → {dict(cross[sub])}  (total {tot})")

    # (4) participação (Guimerà-Amaral) média por subtipo, na rede inteira
    P, _ = sfi.participation_z(list(nodes), links, {n: axis[n] for n in nodes})
    for sub in ("org", "geral", "?"):
        ms = [n for n in cyb if st[n] == sub]
        if ms:
            print(f"   participação média {sub:6}: {sum(P[n] for n in ms)/len(ms):.3f} (n={len(ms)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
