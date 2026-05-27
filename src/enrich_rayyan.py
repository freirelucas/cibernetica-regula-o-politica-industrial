#!/usr/bin/env python3
"""Enriquece a síntese do Rayyan com resumos e DOIs do OpenAlex (uso único; requer rede).

A documentação do Rayyan é explícita: os recursos de IA (ranqueamento por relevância,
extração PICO) dependem dos resumos. O corpus brasileiro já traz resumo; as obras do
núcleo global, não. Este script resolve cada obra global sem resumo no OpenAlex —
por identificador quando há (sementes, rajadas), por busca de título caso contrário
(casamento conservador: título igual/prefixo + ano compatível) — reconstrói o resumo
a partir do índice invertido e grava um cache em data/openalex_enrich.json, lido pelo
build_rayyan para preencher os campos ausentes.

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
UA = {"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"}


def get(url):
    for _ in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception:
            time.sleep(2)
    return {}


def abstract_of(inv):
    """Reconstrói o resumo a partir do abstract_inverted_index do OpenAlex."""
    if not inv:
        return ""
    pos = [(i, w) for w, idxs in inv.items() for i in idxs]
    pos.sort()
    return re.sub(r"\s+", " ", " ".join(w for _, w in pos)).strip()


def _doi(w):
    return re.sub(r"^https?://(dx\.)?doi\.org/", "", (w.get("doi") or ""), flags=re.I).lower()


def by_id(wid):
    w = get(f"{API}/{wid}?select=id,title,publication_year,doi,abstract_inverted_index")
    if not w.get("id"):
        return None
    return {"oa_id": wid, "doi": _doi(w), "abstract": abstract_of(w.get("abstract_inverted_index")),
            "title": w.get("title") or "", "year": w.get("publication_year")}


STOP = {"the", "of", "and", "in", "a", "an", "for", "to", "from", "on", "with", "as", "by",
        "der", "die", "und", "el", "la", "los", "las", "de", "do", "da", "uma", "um", "no", "na"}


def _tokens(s):
    return {w for w in build_rayyan._norm(s).split() if len(w) > 2 and w not in STOP}


def by_title(title, year):
    # busca limpa (sem pontuação, ~12 palavras) e casamento por contenção de tokens,
    # robusto a títulos truncados (o truncado é subconjunto do título completo).
    qclean = " ".join(re.sub(r"[^A-Za-z0-9 ]", " ", title or "").split()[:12])
    if not qclean:
        return None
    data = get(f"{API}?filter=title.search:{urllib.parse.quote(qclean)}&per-page=8"
               "&select=id,title,publication_year,doi,abstract_inverted_index")
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
        inter = len(qt & ct)
        contain = inter / min(len(qt), len(ct))          # 1.0 quando um é subconjunto do outro
        exact = cand == nt or cand.startswith(nt) or nt.startswith(cand)
        yok = (not year) or (not w.get("publication_year")) or abs(int(w["publication_year"]) - int(year)) <= 1
        score = 1.0 if exact else contain
        if yok and score >= 0.8 and score > best_score:
            best, best_score = w, score
    if not best:
        return None
    return {"oa_id": (best.get("id") or "").split("/")[-1], "doi": _doi(best),
            "abstract": abstract_of(best.get("abstract_inverted_index")),
            "title": best.get("title") or "", "year": best.get("publication_year")}


def main():
    works = build_rayyan.consolidate()
    pend = [e for e in works if not e["abstract"]]
    print(f"obras na síntese: {len(works)} | sem resumo (a enriquecer): {len(pend)}")
    enrich, got_ab, got_doi, matched = {}, 0, 0, 0
    for e in pend:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", ""))
        data = by_id(m.group(1)) if m else by_title(e["title"], e.get("year"))
        time.sleep(0.2)
        if not data:
            continue
        matched += 1
        rec = {}
        if data["abstract"]:
            rec["abstract"] = data["abstract"]; got_ab += 1
        if data["doi"]:
            rec["doi"] = data["doi"]; got_doi += 1
        if data["oa_id"]:
            rec["oa_id"] = data["oa_id"]
        if rec:
            enrich[build_rayyan._norm(e["title"])] = rec
    json.dump(enrich, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"resolvidas: {matched}/{len(pend)} | com resumo: {got_ab} | com DOI: {got_doi}")
    print(f"cache: {OUT} ({len(enrich)} entradas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
