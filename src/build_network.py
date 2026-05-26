#!/usr/bin/env python3
"""Constrói a rede do núcleo intelectual (uso único; requer rede).

Nós = obras-semente + referências em rajada + ponto pivotal (as que têm ID
OpenAlex). Arestas = citações reais entre elas (A -> B se A cita B), obtidas de
``referenced_works``. Cor por eixo (semente: eixo conhecido; demais: heurística
de vocabulário no título). Escreve data/network.json (lido offline por build_site).

Uso:  python src/build_network.py
"""
import json
import os
import sys
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from report_from_json import _axis_of  # noqa: E402

JSON = os.path.join(ROOT, "data", "scisci_results.json")
OUT = os.path.join(ROOT, "data", "network.json")
API = "https://api.openalex.org/works"
UA = {"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"}

VOCAB = {
    "Cyb": ("cybernet", "viable system", "vsm", "beer", "ashby", "espejo", "requisite variety",
            "autopoiesis", "systems thinking", "soft systems", "complexity", "organizational systems",
            "operational research", "intelligent organizations"),
    "Reg": ("tools of government", "policy instrument", "policy mix", "nodality", "governance",
            "regulation", "regulatory", "hood", "margetts", "howlett", "public policy", "policy design"),
    "PolInd": ("industrial policy", "entrepreneurial state", "mission", "rodrik", "mazzucato",
               "smart special", "developmental state", "state capacity", "innovation policy"),
}


def classify(title):
    t = (title or "").lower()
    for ax, kws in VOCAB.items():
        if any(k in t for k in kws):
            return ax
    return ""


def fetch(ids):
    out = {}
    for i in range(0, len(ids), 50):
        chunk = "|".join(ids[i:i + 50])
        url = (f"{API}?filter=openalex:{chunk}&per-page=50"
               "&select=id,title,publication_year,cited_by_count,referenced_works")
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            data = json.load(r)
        for w in data.get("results", []):
            wid = (w.get("id") or "").split("/")[-1]
            refs = [x.split("/")[-1] for x in (w.get("referenced_works") or [])]
            out[wid] = {"title": w.get("title") or "", "year": w.get("publication_year"),
                        "cited_by": w.get("cited_by_count") or 0, "refs": refs}
        time.sleep(0.2)
    return out


def short(title, n=42):
    t = title or ""
    return t if len(t) <= n else t[:n - 1].rstrip() + "…"


def main():
    R = json.load(open(JSON, encoding="utf-8"))
    seed_axis = {s["id"]: _axis_of(s.get("ref", "")) for s in R["seeds"]}
    ids = list(seed_axis) + [b["ref_id"] for b in R["top_bursts"]] + [p["ref_id"] for p in R.get("top_pivotal", [])]
    ids = sorted(set(ids))
    meta = fetch(ids)
    print(f"nós buscados: {len(meta)} de {len(ids)}")

    nodes = []
    for wid in ids:
        m = meta.get(wid)
        if not m:
            continue
        ax = seed_axis.get(wid) or classify(m["title"])
        nodes.append({"id": wid, "label": short(m["title"]), "axis": ax,
                      "cited_by": m["cited_by"], "year": m["year"], "seed": wid in seed_axis})
    nodeset = {n["id"] for n in nodes}
    links = []
    for wid in nodeset:
        for ref in meta[wid]["refs"]:
            if ref in nodeset and ref != wid:
                links.append({"source": wid, "target": ref, "tipo": "cita"})  # wid cita ref
    # acoplamento bibliográfico: pares com >= 3 referências em comum (sem citação direta)
    citados = {(l["source"], l["target"]) for l in links}
    node_refs = {wid: set(meta[wid]["refs"]) for wid in nodeset}
    nl = sorted(nodeset)
    for i in range(len(nl)):
        for j in range(i + 1, len(nl)):
            a, b = nl[i], nl[j]
            if (a, b) in citados or (b, a) in citados:
                continue
            shared = len(node_refs[a] & node_refs[b])
            if shared >= 3:
                links.append({"source": a, "target": b, "tipo": "acopla", "peso": shared})
    json.dump({"nodes": nodes, "links": links}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    deg = {}
    for l in links:
        deg[l["source"]] = deg.get(l["source"], 0) + 1
        deg[l["target"]] = deg.get(l["target"], 0) + 1
    iso = sum(1 for n in nodes if n["id"] not in deg)
    print(f"nós: {len(nodes)} | arestas (citação): {len(links)} | isolados: {iso}")
    from collections import Counter
    print("por eixo:", dict(Counter(n["axis"] or "—" for n in nodes)))


if __name__ == "__main__":
    main()
