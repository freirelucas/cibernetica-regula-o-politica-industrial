#!/usr/bin/env python3
"""Metadados das obras do 4º eixo (economia da complexidade) p/ a síntese Rayyan.
(uso único; requer rede)

Pega as obras classificadas como Cplx em data/network_4axis.json (+ as 4 sementes),
busca título/autoria/ano/DOI/tipo/resumo no OpenAlex e grava data/cplx_works.json,
lido pelo build_rayyan para incluí-las no seletor e na exportação da triagem.

Uso:  python src/cplx_works.py
"""
import json
import os
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from oa import get  # noqa: E402

NET = os.path.join(ROOT, "data", "network_4axis.json")
OUT = os.path.join(ROOT, "data", "cplx_works.json")
SEEDS_FORCE = ["W2137358449", "W2009202666", "W2141042444", "W2050032417"]
OA_TYPE = {"article": "JOUR", "journal-article": "JOUR", "book": "BOOK", "monograph": "BOOK",
           "book-chapter": "CHAP", "dissertation": "THES", "report": "RPRT", "preprint": "JOUR"}
SELECT = "id,title,publication_year,doi,type,authorships,abstract_inverted_index"


def abstract_of(inv):
    if not inv:
        return ""
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    pos.sort()
    return re.sub(r"\s+", " ", " ".join(w for _, w in pos)).strip()


def main():
    net = json.load(open(NET, encoding="utf-8"))
    ids = sorted({n["id"] for n in net["nodes"] if n.get("axis") == "Cplx"} | set(SEEDS_FORCE))
    print(f"obras do 4º eixo a enriquecer: {len(ids)}")
    recs = []
    for i in range(0, len(ids), 25):
        d = get(f"https://api.openalex.org/works?filter=openalex:{'|'.join(ids[i:i+25])}"
                f"&per-page=25&select={SELECT}")
        for w in d.get("results", []):
            auth = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
            recs.append({"oa_id": (w.get("id") or "").split("/")[-1],
                         "title": w.get("title") or "",
                         "authors": [a for a in auth if a][:25],
                         "year": w.get("publication_year"),
                         "doi": re.sub(r"^https?://(dx\.)?doi\.org/", "", (w.get("doi") or ""), flags=re.I).lower(),
                         "type": OA_TYPE.get((w.get("type") or "").lower(), "GEN"),
                         "abstract": abstract_of(w.get("abstract_inverted_index"))})
        time.sleep(0.3)
    json.dump(recs, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"gravadas {len(recs)} obras (com resumo: {sum(1 for r in recs if r['abstract'])}) em {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
