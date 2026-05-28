"""A.4 — Brazil full snowball.

Sementes: 73 obras da Faganello em docs/material-brasil/.
Para cada uma:
  1. Resolver OA id via DOI ou search por título.
  2. Fetch /works/{id} para metadados completos.
  3. Fetch citers /works?filter=cites:{id}&per-page=200 (1 nível).
Plus: 1 query global filtrando country_code=BR + topics policy/regulation.

Output: data/brazil_expanded.json com network Brasil×global.
"""
import csv
import json
import os
import re
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
FAGANELLO_CSV = os.path.join(ROOT, "docs", "material-brasil",
                              "dataset_politica_industrial_brasil.csv")
CROSS_BRASIL = os.path.join(ROOT, "data", "cross_brasil.json")
OUTPUT = os.path.join(ROOT, "data", "brazil_expanded.json")
BUDGET_FILE = os.path.join(ROOT, "data", "_budget_used.txt")


def read_budget():
    if not os.path.exists(BUDGET_FILE):
        return 0
    try:
        return int(open(BUDGET_FILE).read().strip())
    except Exception:
        return 0


def bump_budget(n=1):
    cur = read_budget()
    open(BUDGET_FILE, "w").write(str(cur + n))
    return cur + n


def cache_hit(url):
    return os.path.exists(oa._cache_file(url))


def tracked_get(url):
    if cache_hit(url):
        return oa.get(url)
    data = oa.get(url) or {}
    if data:
        bump_budget(1)
    return data


def load_faganello():
    rows = []
    with open(FAGANELLO_CSV, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append({
                "title": (r.get("Paper Title") or "").strip(),
                "doi": (r.get("DOI") or "").strip(),
                "year": (r.get("Publication Year") or "").strip(),
                "authors": (r.get("Author Names") or "").strip(),
            })
    return rows


def resolve_oa_id(item):
    """Resolve OA id via DOI ou search title. Devolve W-id ou None."""
    doi = item.get("doi", "").strip()
    if doi:
        if not doi.startswith("http"):
            doi = f"https://doi.org/{doi}"
        url = f"{API}/works/doi:{urllib.parse.quote(doi, safe='')}"
        data = tracked_get(url)
        wid = (data.get("id") or "").split("/")[-1] if data else ""
        if wid.startswith("W"):
            return wid
    # fallback: search by title (top result)
    title = item.get("title", "").strip()[:200]
    if not title:
        return None
    url = (f"{API}/works?search={urllib.parse.quote(title)}"
           f"&per-page=3&select=id,title,doi,publication_year,authorships,cited_by_count")
    data = tracked_get(url)
    results = (data.get("results") or [])
    if not results:
        return None
    # take top result (already ranked by relevance)
    wid = (results[0].get("id") or "").split("/")[-1]
    return wid if wid.startswith("W") else None


def fetch_brazil_citers(oa_id):
    """Fetch citantes BR de um work via /works?filter=cites:."""
    url = (f"{API}/works?filter=cites:{oa_id}&sort=cited_by_count:desc"
           f"&per-page=100&select=id,title,publication_year,"
           f"authorships,referenced_works,cited_by_count")
    return tracked_get(url)


def broad_brazil_search():
    """Top-200 obras brasileiras em política industrial/regulação."""
    queries = [
        '"politica industrial" OR "industrial policy"',
        '"regulacao" OR "regulation"',
    ]
    out = []
    for q in queries:
        url = (f"{API}/works?filter=authorships.institutions.country_code:BR"
               f"&search={urllib.parse.quote(q)}"
               f"&sort=cited_by_count:desc&per-page=100"
               f"&select=id,title,publication_year,authorships,cited_by_count,doi")
        data = tracked_get(url)
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            if wid.startswith("W"):
                out.append({
                    "oa_id": wid, "title": (w.get("title") or "")[:160],
                    "year": w.get("publication_year"),
                    "cited_by": w.get("cited_by_count") or 0,
                    "query": q[:30],
                })
    return out


def main():
    print("== A.4 · Brazil full snowball ==")
    print(f"budget inicial: {read_budget()}/15000")

    rows = load_faganello()
    print(f"Faganello CSV: {len(rows)} obras")

    # resolve OA ids
    resolved = []
    print(f"\nresolving OA ids (DOI + title search)...")
    for i, r in enumerate(rows):
        wid = resolve_oa_id(r)
        resolved.append({**r, "oa_id": wid})
        if wid:
            pass  # quiet
    n_resolved = sum(1 for r in resolved if r["oa_id"])
    print(f"  resolved: {n_resolved}/{len(rows)} | budget: {read_budget()}/15000")

    # fetch citers for each resolved
    print(f"\nfetching citers (1 nível) for {n_resolved} resolved...")
    citer_data = {}
    for r in resolved:
        if not r["oa_id"]:
            continue
        data = fetch_brazil_citers(r["oa_id"])
        citers = []
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            citers.append({"oa_id": wid, "year": w.get("publication_year"),
                           "cited_by": w.get("cited_by_count") or 0})
        citer_data[r["oa_id"]] = citers
    print(f"  budget after citer fetches: {read_budget()}/15000")

    # broad search
    print(f"\nbroad BR search (industrial policy + regulation)...")
    broad_list = broad_brazil_search()
    print(f"  broad results: {len(broad_list)} | budget: {read_budget()}/15000")

    # build cross-axis network
    all_brazil_ids = set(r["oa_id"] for r in resolved if r["oa_id"]) | \
                     set(b["oa_id"] for b in broad_list)
    # global core
    cross_bg = json.load(open(CROSS_BRASIL, encoding="utf-8")) if os.path.exists(CROSS_BRASIL) else {}
    global_ids = set(cross_bg.get("global", []) if isinstance(cross_bg.get("global"), list) else [])

    # citation bridges: Brazil works whose citers OR refs hit global core
    citation_bridges = []
    for r in resolved:
        wid = r["oa_id"]
        if not wid:
            continue
        citers = citer_data.get(wid, [])
        # heurística simples: se ≥1 citante tem cited_by alto, é "ponte forte"
        n_high = sum(1 for c in citers if c.get("cited_by", 0) >= 100)
        citation_bridges.append({
            "oa_id": wid, "title": r["title"][:120],
            "n_citers_fetched": len(citers),
            "n_high_cite_citers": n_high,
        })
    citation_bridges.sort(key=lambda x: -x["n_high_cite_citers"])

    out = {
        "_generated": "A.4 · Brazil full snowball",
        "_budget_used": read_budget(),
        "n_faganello_seeds": len(rows),
        "n_resolved_oa": n_resolved,
        "n_broad_results": len(broad_list),
        "n_brazil_works_total": len(all_brazil_ids),
        "resolved": resolved,
        "broad_search": broad_list[:60],
        "citation_bridges_top30": citation_bridges[:30],
    }
    json.dump(out, open(OUTPUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT} ({os.path.getsize(OUTPUT)//1024} KB)")
    print(f"\nTop-5 Brasil citation bridges (citantes com cited_by≥100):")
    for cb in citation_bridges[:5]:
        print(f"  {cb['n_high_cite_citers']:2}× {cb['title']}")


if __name__ == "__main__":
    main()
