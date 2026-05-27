"""Resolve os capítulos de "The Economy as an Evolving Complex System II"
(W2141042444) como obras individuais no OpenAlex — normaliza a referência do
volume editado em entradas por capítulo. Uso único, exige rede (OpenAlex).

Para cada capítulo (título + sobrenomes da sumário do volume), busca no
OpenAlex, pontua os candidatos por semelhança de título + presença de autor, e
imprime um relatório para revisão. Com --emit, grava os casados em
data/eecs2_chapters.json no esquema de data/cplx_works.json.
"""
import difflib
import json
import re
import sys
import time
import urllib.parse

sys.path.insert(0, "src")
import oa  # noqa: E402

PARENT = "W2141042444"

# (título do capítulo, [sobrenomes dos autores]) — do sumário do volume
CHAPTERS = [
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

ACCEPT_SIM = 0.78  # semelhança de título para aceitar


def norm(s):
    return re.sub(r"[^a-z0-9 ]", " ", (s or "").lower()).split()


def sim(a, b):
    return difflib.SequenceMatcher(None, " ".join(norm(a)), " ".join(norm(b))).ratio()


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


def surnames_in(authorships, wanted):
    names = " ".join((a.get("author") or {}).get("display_name", "") for a in authorships).lower()
    return [w for w in wanted if w.lower() in names]


def search(title, authors):
    q = urllib.parse.quote(title)
    data = oa.get(f"https://api.openalex.org/works?filter=title.search:{q}&per-page=10")
    cands = data.get("results", []) or []
    if not cands:  # fallback busca geral
        data = oa.get(f"https://api.openalex.org/works?search={q}&per-page=10")
        cands = data.get("results", []) or []
    scored = []
    for w in cands:
        s = sim(title, w.get("title") or "")
        hit = surnames_in(w.get("authorships") or [], authors)
        scored.append((s + 0.15 * bool(hit), s, hit, w))
    scored.sort(key=lambda x: -x[0])
    return scored


RIS_TYPE = {"article": "JOUR", "book": "BOOK", "book-chapter": "CHAP",
            "preprint": "JOUR", "dissertation": "THES", "report": "RPRT"}


def to_entry(w):
    auth = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])]
    auth = [a for a in auth if a][:6]
    doi = (w.get("doi") or "").replace("https://doi.org/", "")
    return {
        "oa_id": (w.get("id") or "").split("/")[-1],
        "title": w.get("title") or "",
        "authors": auth,
        "year": w.get("publication_year"),
        "doi": doi,
        "type": RIS_TYPE.get((w.get("type") or "").lower(), "CHAP"),
        "abstract": reconstruct_abstract(w.get("abstract_inverted_index")),
    }


def pick(scored):
    """Entre os candidatos fortes (semelhança + autor), prefere o mais antigo
    (capítulo original, não a reimpressão de 2018) e, em empate, o que tem DOI."""
    strong = [(s, w) for (sc, s, hit, w) in scored if s >= ACCEPT_SIM and hit]
    if not strong:
        return None
    strong.sort(key=lambda sw: (sw[1].get("publication_year") or 9999,
                                0 if sw[1].get("doi") else 1))
    return strong[0][1]


CKPT = "data/eecs2_ckpt.json"        # {título: entrada|null} — retoma entre execuções
OUT = "data/eecs2_chapters.json"     # capítulos casados (consumido na fusão)


def main(retry_misses=False):
    ck = {}
    if __import__("os").path.exists(CKPT):
        ck = json.load(open(CKPT, encoding="utf-8"))
    for title, authors in CHAPTERS:
        if title in ck and not (retry_misses and ck[title] is None):
            continue
        scored = search(title, authors)
        print("=" * 70, flush=True)
        print(f"CAP: {title[:64]}", flush=True)
        for (sc, s, hit, w) in scored[:3]:
            mark = "✓" if (s >= ACCEPT_SIM and hit) else " "
            doi = (w.get("doi") or "").replace("https://doi.org/", "")
            print(f"  {mark} [{s:.2f} aut={','.join(hit) or '-'}] {(w.get('id') or '').split('/')[-1]} "
                  f"{w.get('publication_year')} doi={doi or '-'} {(w.get('title') or '')[:48]}", flush=True)
        w = pick(scored)
        ck[title] = to_entry(w) if w else None
        json.dump(ck, open(CKPT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print("     ->", "casado" if w else "SEM CASAMENTO", flush=True)
        time.sleep(1.5)
    done = [t for t, v in ck.items() if v]
    miss = [t for t in (c[0] for c in CHAPTERS) if not ck.get(t)]
    accepted = [ck[t] for t in (c[0] for c in CHAPTERS) if ck.get(t)]
    json.dump(accepted, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("=" * 70)
    print(f"CASADOS: {len(done)}/{len(CHAPTERS)} | FALHAS: {len(miss)}")
    for m in miss:
        print("  falta:", m[:64])
    print(f"gravado {OUT} ({len(accepted)} capítulos)")


if __name__ == "__main__":
    main(retry_misses="--retry-misses" in sys.argv)
