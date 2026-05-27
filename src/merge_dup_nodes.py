"""Higiene x10: funde nós duplicados nas redes de cocitação. O OpenAlex registra
a mesma obra sob vários ids (edições, reimpressões, caixa, "Organizations"/
"Organisations", ponto final) — no grafo isso vira vários nós para um só
trabalho, fragmentando citações e distorcendo a centralidade.

Agrupa por título real (semelhança ≥ 0,92), elege o canônico (semente > mais
citado > mais antigo), remapeia arestas (soma pesos, sem laços nem paralelas) e
funde os nós. Dry-run por padrão; --apply grava.

Títulos reais vêm de /tmp/found.json (verificação por lote contra OpenAlex).
"""
import difflib
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
NETWORKS = ["network.json", "network_4axis.json", "network_exploded.json", "network_cplx.json"]
TITLES = json.load(open("/tmp/found.json"))   # {wid: {title, year, type, cb}}
SIM = 0.92


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split())


def title_of(wid):
    return (TITLES.get(wid) or {}).get("title") or ""


def cb_of(wid):
    return (TITLES.get(wid) or {}).get("cb") or 0


def clusters(ids):
    """União por semelhança de título (≥ SIM), comparação par-a-par completa
    (pega variantes com/sem artigo inicial, caixa, ponto, 'Organizations'/
    'Organisations'). n≤250 por rede, então O(n²) é barato."""
    parent = {i: i for i in ids}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    nt = [(i, norm(title_of(i))) for i in ids]
    for a in range(len(nt)):
        ia, ta = nt[a]
        if len(ta) < 6:                       # títulos curtos demais: não casa por ruído
            continue
        for b in range(a + 1, len(nt)):
            ib, tb = nt[b]
            if len(tb) < 6:
                continue
            if abs(len(ta) - len(tb)) > 0.4 * max(len(ta), len(tb)):
                continue
            if difflib.SequenceMatcher(None, ta, tb).ratio() >= SIM:
                parent[find(ia)] = find(ib)
    cl = {}
    for i in ids:
        cl.setdefault(find(i), []).append(i)
    return [v for v in cl.values() if len(v) > 1]


def canonical(members, nodes):
    """semente > mais citado (OpenAlex) > mais antigo."""
    def key(wid):
        nd = nodes.get(wid, {})
        seed = 1 if nd.get("seed") else 0
        yr = nd.get("year") or 9999
        return (seed, cb_of(wid), -int(yr))
    return max(members, key=key)


def merge_network(path, apply):
    net = json.load(open(path, encoding="utf-8"))
    nodes = {n["id"]: n for n in net["nodes"]}
    cls = clusters(list(nodes))
    remap = {}
    plan = []
    for members in cls:
        can = canonical(members, nodes)
        for m in members:
            if m != can:
                remap[m] = can
        plan.append((can, [m for m in members if m != can]))
    if not apply:
        return None, plan
    # funde nós: canônico herda seed=any, cited_by=max, mantém label/year/axis dele
    for dup, can in remap.items():
        c, d = nodes[can], nodes[dup]
        c["seed"] = bool(c.get("seed") or d.get("seed"))
        c["cited_by"] = max(int(c.get("cited_by") or 0), int(d.get("cited_by") or 0))
        if not c.get("axis") and d.get("axis"):
            c["axis"] = d["axis"]
    net["nodes"] = [n for n in net["nodes"] if n["id"] not in remap]
    # remapeia arestas, soma pesos, descarta laços e paralelas
    agg = {}
    for l in net["links"]:
        s = remap.get(l["source"], l["source"])
        t = remap.get(l["target"], l["target"])
        if s == t:
            continue
        k = tuple(sorted((s, t)))
        agg[k] = agg.get(k, 0) + (l.get("peso", 1) or 1)
    net["links"] = [{"source": a, "target": b, "tipo": "cocita", "peso": w} for (a, b), w in agg.items()]
    json.dump(net, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return (len(nodes), len(net["nodes"]), len(net["links"])), plan


def main(apply):
    for fn in NETWORKS:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        res, plan = merge_network(p, apply)
        print("=" * 70)
        print(f"{fn}: {sum(len(d) for _, d in plan)} nós duplicados em {len(plan)} grupos")
        for can, dups in plan:
            print(f"  canônico {can} ({title_of(can)[:42]})  <- {', '.join(dups)}")
        if res:
            print(f"  -> nós {res[0]}->{res[1]} (-{res[0]-res[1]}), arestas agora {res[2]}")
    print("\n", "APLICADO" if apply else "DRY-RUN (use --apply para gravar)")


if __name__ == "__main__":
    main(apply="--apply" in sys.argv)
