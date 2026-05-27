#!/usr/bin/env python3
"""Cruzamento Brasil × núcleo global (super snowball cruzado; uso único, requer rede).

Pega as obras do corpus brasileiro de Claucia Faganello (DOIs do dataset), busca
no OpenAlex a lista de referências de cada uma e cruza com o núcleo global da rede
de cocitação (data/network.json). Identifica:
  • as obras do núcleo global efetivamente CITADAS pelo material brasileiro;
  • as obras brasileiras que CITAM o núcleo global.
Juntas, elas são a PONTE real (por citação) entre os dois mundos — o "cruzamento"
que o segundo cenário de exportação isola para triagem. Salva data/cross_brasil.json,
lido pelo build_rayyan para rotular as obras-ponte e emitir o recorte rayyan_cruzamento.*

Uso:  python src/cross_brasil.py
"""
import csv
import json
import os
import re
import sys
import time
import urllib.parse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
from oa import get  # noqa: E402  (pool polido + chave Premium via ambiente; backoff 429)

DATASET = os.path.join(ROOT, "docs", "material-brasil", "dataset_politica_industrial_brasil.csv")
NETWORK = os.path.join(ROOT, "data", "network.json")
OUT = os.path.join(ROOT, "data", "cross_brasil.json")


def main():
    core = {n["id"]: n.get("label", n["id"]) for n in json.load(open(NETWORK, encoding="utf-8"))["nodes"]}
    rows = list(csv.DictReader(open(DATASET, encoding="utf-8")))
    by_doi = {}
    for r in rows:
        d = re.sub(r"^https?://(dx\.)?doi\.org/", "", (r.get("DOI") or "").strip(), flags=re.I).lower()
        if d.startswith("10."):
            by_doi[d] = r.get("Paper Title", "")
    dois = sorted(by_doi)

    global_cited, brasil_bridge, resolved = set(), [], 0
    for i in range(0, len(dois), 25):
        chunk = "|".join(dois[i:i + 25])
        data = get(f"https://api.openalex.org/works?filter=doi:{urllib.parse.quote(chunk)}"
                   "&per-page=25&select=id,doi,title,referenced_works")
        for w in data.get("results", []):
            resolved += 1
            refs = {x.split("/")[-1] for x in (w.get("referenced_works") or [])}
            hit = refs & set(core)
            if hit:
                global_cited |= hit
                d = re.sub(r"^https?://(dx\.)?doi\.org/", "", (w.get("doi") or ""), flags=re.I).lower()
                brasil_bridge.append({"oa_id": (w.get("id") or "").split("/")[-1], "doi": d,
                                      "title": w.get("title") or by_doi.get(d, ""),
                                      "cita": sorted(hit)})
        time.sleep(0.2)

    out = {"generated": time.strftime("%Y-%m-%d"),
           "global": sorted(global_cited),
           "global_labels": {g: core[g] for g in sorted(global_cited)},
           "brasil": brasil_bridge}
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"Brasil resolvidos: {resolved}/{len(dois)} | que citam o núcleo: {len(brasil_bridge)}")
    print(f"obras do núcleo citadas (cruzamento): {len(global_cited)}")
    for g in sorted(global_cited):
        print(f"   {g} · {core[g][:50]}")
    print(f"cache: {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
