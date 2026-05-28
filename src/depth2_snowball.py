"""A.3 — Depth-2 snowball: para cada citante level-1 já no cache, fetch seus
citantes (level-2). Expande corpus para autor_network capturar mais ricamente."""
import collections
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
CACHE_DIR = os.path.join(ROOT, "data", "oa_cache")
OUTPUT = os.path.join(ROOT, "data", "depth2_corpus.json")
BUDGET_FILE = os.path.join(ROOT, "data", "_budget_used.txt")

PER_PAGE = 50           # top-K citers per level-1 work
MAX_LEVEL1_TO_EXPAND = 600  # cap para evitar runaway (de 880 level-1 works)


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


def get_level1_ids():
    """Lista work IDs com authorships no cache (level-1 = citers of original seeds)."""
    ids = set()
    for root, _, files in os.walk(CACHE_DIR):
        for f in files:
            if not f.endswith(".json.gz"):
                continue
            try:
                data = json.loads(gzip.open(os.path.join(root, f), "rt").read())
            except Exception:
                continue
            results = data.get("results") if isinstance(data, dict) else None
            if isinstance(results, list):
                for w in results:
                    if w.get("authorships"):
                        wid = (w.get("id") or "").split("/")[-1]
                        if wid.startswith("W"):
                            ids.add(wid)
    return sorted(ids)


def fetch_level2(level1_ids, max_fetches):
    """Para cada level-1 work, fetch top-50 citers (level-2). Cap por max_fetches."""
    n_new = 0
    n_level2_unique = set()
    by_level1 = {}
    for wid in level1_ids:
        if n_new >= max_fetches:
            break
        url = (f"{API}/works?filter=cites:{wid}&sort=cited_by_count:desc"
               f"&per-page={PER_PAGE}&select=id,title,display_name,"
               f"publication_year,referenced_works,authorships,cited_by_count")
        was_cached = cache_hit(url)
        data = oa.get(url) or {}
        if not was_cached and data:
            n_new += 1
            bump_budget(1)
        l2_ids = []
        for w in (data.get("results") or []):
            l2_wid = (w.get("id") or "").split("/")[-1]
            if l2_wid.startswith("W"):
                l2_ids.append(l2_wid)
                n_level2_unique.add(l2_wid)
        by_level1[wid] = len(l2_ids)
    return n_new, n_level2_unique, by_level1


def mine_corpus_metrics():
    """Conta works com authorships e authors únicos no cache atual."""
    n_works_authorships = 0
    authors = set()
    for root, _, files in os.walk(CACHE_DIR):
        for f in files:
            if not f.endswith(".json.gz"):
                continue
            try:
                data = json.loads(gzip.open(os.path.join(root, f), "rt").read())
            except Exception:
                continue
            results = data.get("results") if isinstance(data, dict) else None
            if isinstance(results, list):
                for w in results:
                    if w.get("authorships"):
                        n_works_authorships += 1
                        for a in (w.get("authorships") or []):
                            aid = ((a.get("author") or {}).get("id") or "").split("/")[-1]
                            if aid.startswith("A"):
                                authors.add(aid)
    return n_works_authorships, len(authors)


def main():
    print(f"== A.3 · Depth-2 snowball ==")
    print(f"budget inicial: {read_budget()}/15000")

    # before metrics
    before_works, before_authors = mine_corpus_metrics()
    print(f"\nBEFORE: {before_works} works com authorships, {before_authors} authors únicos")

    # get level-1 ids
    level1 = get_level1_ids()
    print(f"level-1 ids identificados: {len(level1)}")
    target_set = level1[:MAX_LEVEL1_TO_EXPAND]
    print(f"expandindo {len(target_set)} (cap MAX_LEVEL1_TO_EXPAND={MAX_LEVEL1_TO_EXPAND})")

    # fetch level-2
    budget_left = 15000 - read_budget()
    max_per_run = min(budget_left, 300)  # turn cap
    print(f"\nfetching level-2 citers (cap {max_per_run} this turn)...")
    n_new, l2_unique, by_l1 = fetch_level2(target_set, max_per_run)
    print(f"  new fetches: {n_new} | budget: {read_budget()}/15000")
    print(f"  level-2 unique works seen: {len(l2_unique)}")

    # after metrics
    after_works, after_authors = mine_corpus_metrics()
    print(f"\nAFTER:  {after_works} works com authorships (+{after_works-before_works}), "
          f"{after_authors} authors únicos (+{after_authors-before_authors})")

    out = {
        "_generated": "A.3 · depth-2 snowball",
        "_budget_used": read_budget(),
        "before": {"works_with_authorships": before_works, "authors_unique": before_authors},
        "after": {"works_with_authorships": after_works, "authors_unique": after_authors},
        "delta": {
            "new_works": after_works - before_works,
            "new_authors": after_authors - before_authors,
            "new_level2_seen": len(l2_unique),
        },
        "level1_expanded": len(target_set),
        "level1_to_n_level2": dict(collections.Counter(by_l1.values())),
        "new_fetches_this_run": n_new,
    }
    json.dump(out, open(OUTPUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT}")


if __name__ == "__main__":
    main()
