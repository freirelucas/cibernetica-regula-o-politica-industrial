#!/usr/bin/env python3
"""Cruzamento de citação: o material brasileiro cita as obras-semente globais?
(uso único; requer rede)

Lê os DOIs de docs/material-brasil/dataset_politica_industrial_brasil.csv, resolve
cada trabalho no OpenAlex e verifica, na lista de referências de cada um, quais
obras-semente do mapeamento global são citadas — separando por eixo (cibernética,
regulação, política industrial). Fundamenta o achado da seção "Análise independente".

Uso:  python src/crosscheck_brasil.py
"""
import csv
import json
import os
import re
import time
import urllib.request
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASET = os.path.join(ROOT, "docs", "material-brasil", "dataset_politica_industrial_brasil.csv")
UA = {"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"}

SEEDS = {
    "W2048086870": "Beer · Brain of the Firm (cibernética)",
    "W1566478880": "Beer · Heart of Enterprise (cibernética)",
    "W2154683088": "Beer · Diagnosing the System (cibernética)",
    "W2325487953": "Ashby · Introduction to Cybernetics (cibernética)",
    "W4244612406": "Espejo & Reyes (cibernética)",
    "W1601629960": "Hood · Tools of Government (regulação)",
    "W2126563689": "Hood & Margetts (regulação)",
    "W4386803846": "Margetts · Nodality (regulação)",
    "W3124879925": "Rodrik · Industrial Policy 21C (política industrial)",
    "W1553746973": "Mazzucato · Entrepreneurial State (política industrial)",
}


def dois_do_dataset():
    out = set()
    for r in csv.DictReader(open(DATASET, encoding="utf-8")):
        d = (r.get("DOI") or "").strip()
        d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I).lower()
        if d.startswith("10."):
            out.add(d)
    return sorted(out)


def main():
    dois = dois_do_dataset()
    resolved, with_refs, hits = 0, 0, Counter()
    cite_seed = 0
    for i in range(0, len(dois), 25):
        chunk = "|".join(dois[i:i + 25])
        url = (f"https://api.openalex.org/works?filter=doi:{chunk}&per-page=25"
               "&select=id,referenced_works")
        try:
            data = json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40))
        except Exception as e:
            print("erro no lote:", e); continue
        for w in data.get("results", []):
            resolved += 1
            refs = {x.split("/")[-1] for x in (w.get("referenced_works") or [])}
            if refs:
                with_refs += 1
            inter = refs & set(SEEDS)
            if inter:
                cite_seed += 1
            for sid in inter:
                hits[SEEDS[sid]] += 1
        time.sleep(0.2)

    print(f"DOIs no dataset: {len(dois)} | resolvidos no OpenAlex: {resolved} | com referências: {with_refs}")
    print(f"trabalhos que citam ao menos uma obra-semente: {cite_seed}")
    print("obras-semente citadas:")
    for k, v in hits.most_common():
        print(f"  {v:>2} × {k}")
    eixos = {"cibernética": 0, "regulação": 0, "política industrial": 0}
    for k, v in hits.items():
        for e in eixos:
            if e in k:
                eixos[e] += v
    print("por eixo:", eixos)


if __name__ == "__main__":
    main()
