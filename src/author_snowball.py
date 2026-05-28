"""Snowball por AUTOR — estratégia de expansão mais ousada (cache do OpenAlex).

Além do snowball por citação (frente/trás) e do filtro lexical de título, recupera
a OBRA dos autores-semente filtrada pelo vocabulário dos eixos. Pega trabalhos
relevantes que os outros caminhos perdem — p.ex. os demais livros de Beer
(Designing Freedom, Platform for Change…), de Hood, Espejo, etc.

Usa oa.get (com cache em disco): a primeira passada consulta o OpenAlex; as
seguintes leem do cache — resumível se o IP limitar no meio.

Saída: data/author_works.json (consumido por build_rayyan como "obra de
autor-semente"). Uso:  python src/author_snowball.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "author_works.json")
API = "https://api.openalex.org"

# 13 obras-semente (IDs verificados) — fonte dos autores
SEEDS = ["W2048086870", "W1566478880", "W2154683088", "W2325487953", "W4244612406",
         "W1601629960", "W2126563689", "W4386803846", "W3124879925", "W1553746973",
         "W4230710385", "W3130930004", "W2063282131"]

# Vocabulário dos eixos (compacto, fiel ao funil) — filtra a obra do autor por relevância
VOCAB = {
    "Cibernética": ("cybernetic", "viable system", "vsm", "stafford beer", "ashby",
                    "requisite variety", "second-order", "self-organ", "autopoiesis",
                    "management cybernetic", "organizational cybernetic", "brain of the firm",
                    "heart of enterprise", "designing freedom", "platform for change",
                    "general system", "systems thinking", "syntegr", "good regulator"),
    "Instrumentos de governo": ("nodality", "tools of government", "policy instrument",
                                "policy tool", "policy mix", "policy design", "regulation",
                                "regulatory", "smart regulation", "responsive regulation",
                                "instrument choice", "governance", "digital government", "nodal"),
    "Política industrial": ("industrial policy", "developmental state", "state capacity",
                            "entrepreneurial state", "mission-oriented", "innovation policy",
                            "smart specialis", "smart specializ", "economic cybernetics",
                            "market socialism", "central planning", "optimal planning",
                            "self-discovery", "structural transformation"),
}
RIS = {"article": "JOUR", "book": "BOOK", "book-chapter": "CHAP", "preprint": "JOUR"}
PER_AUTHOR = 15   # teto de obras novas por autor (mais citadas)


def axes_of(title):
    t = (title or "").lower()
    return [ax for ax, kws in VOCAB.items() if any(k in t for k in kws)]


def reconstruct_abstract(inv):
    if not inv:
        return ""
    n = sum(len(v) for v in inv.values())
    s = [None] * n
    for w, ps in inv.items():
        for p in ps:
            if 0 <= p < n:
                s[p] = w
    return " ".join(w for w in s if w)


def main():
    # 1) autores das sementes (id + nome) a partir das próprias obras-semente
    authors = {}
    for sid in SEEDS:
        w = oa.get(f"{API}/works/{sid}?select=id,authorships")
        for a in (w.get("authorships") or []):
            au = a.get("author") or {}
            aid = (au.get("id") or "").split("/")[-1]
            if aid:
                authors.setdefault(aid, au.get("display_name") or aid)
    print(f"autores-semente: {len(authors)}")

    # 2) obra de cada autor, filtrada por eixo, deduplicada contra as sementes
    seen = set(SEEDS)
    out = []
    sel = "id,title,publication_year,type,doi,authorships,abstract_inverted_index,cited_by_count"
    for aid, name in authors.items():
        url = (f"{API}/works?filter=author.id:{aid},type:article|book|book-chapter"
               f"&sort=cited_by_count:desc&per-page=50&select={sel}")
        data = oa.get(url)
        kept = 0
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            if not wid or wid in seen:
                continue
            ax = axes_of(w.get("title"))
            if not ax:
                continue
            seen.add(wid)
            auth = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
            out.append({
                "oa_id": wid, "title": w.get("title") or "",
                "authors": [a for a in auth if a][:6],
                "year": w.get("publication_year"),
                "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                "type": RIS.get((w.get("type") or "").lower(), "GEN"),
                "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
                "axes": ax, "seed_author": name,
            })
            kept += 1
            if kept >= PER_AUTHOR:
                break
        print(f"  {name[:28]:28} +{kept}")
    # dedup por título (variantes de edição do OpenAlex sob ids distintos)
    seen_t, dedup = set(), []
    for w in out:
        key = re.sub(r"[^a-z0-9]", "", (w["title"] or "").lower())
        if key and key in seen_t:
            continue
        seen_t.add(key)
        dedup.append(w)
    out = dedup
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(out)} obras novas de autores-semente -> {OUT}")
    import collections
    print("por eixo:", dict(collections.Counter(a for w in out for a in w["axes"])))


if __name__ == "__main__":
    main()
