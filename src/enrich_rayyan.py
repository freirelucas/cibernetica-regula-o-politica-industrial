#!/usr/bin/env python3
"""Enriquece a síntese do Rayyan com metadados do OpenAlex + Crossref (uso único; requer rede).

Resolve CADA obra da síntese no OpenAlex (por id quando há, por DOI, ou por busca de
título com casamento por contenção de tokens) e guarda o registro canônico — id, DOI,
resumo, título completo, ano, autores e tipo. Para as que ficam sem resumo mas têm DOI,
tenta o Crossref. O cache (data/openalex_enrich.json) é lido pelo build_rayyan para:
(a) deduplicar pelo id canônico do OpenAlex — fundindo variantes do mesmo trabalho
(títulos truncados, com/sem subtítulo, "The X"/"X"); (b) completar autoria e tipo;
(c) preencher resumos — essenciais para o ranqueamento e o PICO do Rayyan.

Uso:  python src/enrich_rayyan.py
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import build_rayyan  # noqa: E402

OUT = os.path.join(ROOT, "data", "openalex_enrich.json")
API = "https://api.openalex.org/works"
CROSSREF = "https://api.crossref.org/works/"
UA = {"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"}
OA_TYPE = {"article": "JOUR", "journal-article": "JOUR", "book": "BOOK", "monograph": "BOOK",
           "book-chapter": "CHAP", "dissertation": "THES", "report": "RPRT", "preprint": "JOUR"}
SELECT = "id,title,publication_year,doi,type,authorships,abstract_inverted_index"


def get(url):
    for _ in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(2)
    return {}


def abstract_of(inv):
    if not inv:
        return ""
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    pos.sort()
    return re.sub(r"\s+", " ", " ".join(w for _, w in pos)).strip()


def _doi(w):
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (w.get("doi") or ""), flags=re.I).lower()


def _rec(w):
    auth = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
    return {"oa_id": (w.get("id") or "").split("/")[-1], "doi": _doi(w),
            "abstract": abstract_of(w.get("abstract_inverted_index")),
            "title": w.get("title") or "", "year": w.get("publication_year"),
            "authors": [a for a in auth if a][:25],
            "type": OA_TYPE.get((w.get("type") or "").lower(), "")}


STOP = {"the", "of", "and", "in", "a", "an", "for", "to", "from", "on", "with", "as", "by",
        "der", "die", "und", "el", "la", "los", "las", "de", "do", "da", "uma", "um", "no", "na"}


def _tokens(s):
    return {w for w in build_rayyan._norm(s).split() if len(w) > 2 and w not in STOP}


def by_id(wid):
    w = get(f"{API}/{wid}?select={SELECT}")
    return _rec(w) if w.get("id") else None


def by_doi(doi):
    d = get(f"{API}?filter=doi:{urllib.parse.quote(doi)}&per-page=1&select={SELECT}")
    res = d.get("results") or []
    return _rec(res[0]) if res else None


def by_title(title, year):
    qclean = " ".join(re.sub(r"[^A-Za-z0-9 ]", " ", title or "").split()[:12])
    if not qclean:
        return None
    data = get(f"{API}?filter=title.search:{urllib.parse.quote(qclean)}&per-page=8&select={SELECT}")
    qt = _tokens(title)
    if not qt:
        return None
    nt = build_rayyan._norm(title)
    best, best_score = None, 0.0
    for w in data.get("results", []):
        cand = build_rayyan._norm(w.get("title") or "")
        ct = _tokens(w.get("title") or "")
        if not ct:
            continue
        contain = len(qt & ct) / min(len(qt), len(ct))
        exact = cand == nt or cand.startswith(nt) or nt.startswith(cand)
        yok = (not year) or (not w.get("publication_year")) or abs(int(w["publication_year"]) - int(year)) <= 1
        score = 1.0 if exact else contain
        if yok and score >= 0.8 and score > best_score:
            best, best_score = w, score
    return _rec(best) if best else None


def crossref_abstract(doi):
    m = get(CROSSREF + urllib.parse.quote(doi)).get("message") or {}
    ab = m.get("abstract") or ""
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", ab)).strip()


def main():
    works = build_rayyan.consolidate()
    print(f"obras na síntese (antes do dedup por id): {len(works)}")
    enrich, res, ab, cr = {}, 0, 0, 0
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", ""))
        rec = by_id(m.group(1)) if m else (by_doi(e["doi"]) if e.get("doi") else by_title(e["title"], e.get("year")))
        time.sleep(0.18)
        if not rec:
            continue
        res += 1
        # Crossref como complemento de resumo quando o OpenAlex não tem
        if not rec["abstract"] and (rec["doi"] or e.get("doi")):
            rec["abstract"] = crossref_abstract(rec["doi"] or e["doi"])
            if rec["abstract"]:
                cr += 1
            time.sleep(0.18)
        if rec["abstract"]:
            ab += 1
        enrich[build_rayyan._norm(e["title"])] = rec
    json.dump(enrich, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    ids = {r["oa_id"] for r in enrich.values() if r["oa_id"]}
    print(f"resolvidas: {res}/{len(works)} | com resumo: {ab} (Crossref: {cr}) | ids OpenAlex distintos: {len(ids)}")
    print(f"cache: {OUT} ({len(enrich)} entradas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
