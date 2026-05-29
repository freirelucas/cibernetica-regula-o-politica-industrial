"""Normaliza o volume editado "The Economy as an Evolving Complex System II"
(W2141042444) nos seus capítulos individuais, usando o OpenAlex como referência.

Os capítulos da edição CRC 2018 têm DOI determinístico
`10.1201/9780429496639-N`, onde N é a posição no sumário (1 = Introdução …
21 = Anderson). Assim a resolução é UMA requisição em lote por DOI — sem busca
por título ambígua e amigável ao limite de taxa.

IMPORTANTE: exige IP "fresco" no OpenAlex (o container de sessão fica limitado
após muitas requisições). Roda limpo no Colab (Célula 13 / ambiente novo).

Uso:  python src/split_eecs2.py            # grava data/eecs2_chapters.json
      python src/split_eecs2.py --merge    # funde em data/cplx_works.json
"""
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARENT = "W2141042444"
DOI_BASE = "10.1201/9780429496639"
OUT = os.path.join(ROOT, "data", "eecs2_chapters.json")
CPLX = os.path.join(ROOT, "data", "cplx_works.json")

# Sumário do volume, em ordem (posição N -> DOI -N). Autores conferem o casamento.
TOC = [
    ("Introduction", ["Arthur", "Durlauf", "Lane"]),
    ("Asset Pricing Under Endogenous Expectations in an Artificial Stock Market",
     ["Arthur", "Holland", "LeBaron", "Palmer", "Tayler"]),
    ("Natural Rationality", ["Darley", "Kauffman"]),
    ("Statistical Mechanics Approaches to Socioeconomic Behavior", ["Durlauf"]),
    ("Is What Is Good for Each Best for All? Learning From Others in the Information Contagion Model",
     ["Lane"]),
    ("Evolution of Trading Structures", ["Ioannides"]),
    ("Foresight, Complexity, and Strategy", ["Lane", "Maxfield"]),
    ("The Emergence of Simple Ecologies of Skill", ["Padgett"]),
    ("Some Fundamental Puzzles in Economic History/Development", ["North"]),
    ("How the Economy Organizes Itself in Space: A Survey of the New Economic Geography",
     ["Krugman"]),
    ("Time and Money", ["Shubik"]),
    ("Promises Promises", ["Geanakoplos"]),
    ("Macroeconomics and Complexity: Inflation Theory", ["Leijonhufvud"]),
    ("Evolutionary Dynamics in Game-Theoretic Models", ["Lindgren"]),
    ("Identification of Anonymous Endogenous Interactions", ["Manski"]),
    ("Asset Price Behavior in Complex Environments", ["Brock"]),
    ("Population Games", ["Blume"]),
    ("Computational Political Economy", ["Kollman", "Miller", "Page"]),
    ("The Economy as an Interactive System", ["Kirman"]),
    ("How Economists Can Get A Life", ["Tesfatsion"]),
    ("Some Thoughts About Distribution in Economics", ["Anderson"]),
]

RIS_TYPE = {"article": "JOUR", "book": "BOOK", "book-chapter": "CHAP", "preprint": "JOUR"}


def reconstruct_abstract(inv):
    if not inv:
        return ""
    n = sum(len(v) for v in inv.values())
    slots = [None] * n
    for w, pos in inv.items():
        for p in pos:
            if 0 <= p < n:
                slots[p] = w
    return " ".join(w for w in slots if w)


def to_entry(w):
    auth = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
    auth = [a for a in auth if a][:6]
    return {
        "oa_id": (w.get("id") or "").split("/")[-1],
        "title": w.get("title") or "",
        "authors": auth,
        "year": w.get("publication_year"),
        "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
        "type": RIS_TYPE.get((w.get("type") or "").lower(), "CHAP"),
        "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
        "subtrad": "Santa Fe — economia como sistema complexo (EECS-II)",
    }


def resolve():
    dois = [f"{DOI_BASE}-{n}" for n in range(1, len(TOC) + 1)]
    flt = "doi:" + "|".join("https://doi.org/" + d for d in dois)
    sel = "id,title,authorships,publication_year,type,doi,abstract_inverted_index"
    url = (f"https://api.openalex.org/works?filter={urllib.parse.quote(flt, safe=':|/.')}"
           f"&per-page=30&select={sel}")
    res = oa.get(url).get("results", [])
    by_doi = {(w.get("doi") or "").replace("https://doi.org/", "").lower(): w for w in res}
    out = []
    for n, (title, _authors) in enumerate(TOC, start=1):
        w = by_doi.get(f"{DOI_BASE}-{n}".lower())
        if w:
            out.append(to_entry(w))
            print(f"  -{n:<2} {out[-1]['oa_id']} {w.get('publication_year')} {(w.get('title') or title)[:50]}")
        else:
            print(f"  -{n:<2} (não resolveu — IP limitado? rodar em IP novo)")
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\nresolvidos {len(out)}/{len(TOC)} -> {OUT}")
    return out


def merge_into_cplx(chapters):
    """Substitui a entrada do volume (W2141042444) pelos capítulos em cplx_works.json."""
    works = json.load(open(CPLX, encoding="utf-8"))
    works = [w for w in works if w.get("oa_id") != PARENT]
    have = {w.get("oa_id") for w in works}
    for ch in chapters:
        if ch["oa_id"] and ch["oa_id"] not in have:
            works.append(ch)
            have.add(ch["oa_id"])
    json.dump(works, open(CPLX, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"cplx_works.json: volume substituído por {len(chapters)} capítulos ({len(works)} obras no total)")


if __name__ == "__main__":
    chs = resolve()
    if "--merge" in sys.argv and chs:
        merge_into_cplx(chs)
