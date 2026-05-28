"""Fase D — Author network completo (corpus expandido por authorships).

Constrói a rede de coautoria sobre TODOS os works do corpus cuja resposta OpenAlex
já tem authorships embebidos no cache (snowball dos citantes em
cocitation_hypergraph.py povoa 880+ works com autoria completa). Para cada
autor, computa:
  - n_works_total
  - n_works_por_eixo (Cyb / Reg / PolInd via vocabulário em título)
  - cross_axis_score (entropia normalizada da distribuição: 1 = perfeitamente
    balanceado nos 3 eixos; 0 = concentrado num eixo)
  - degree na rede de coautoria
  - community_id (Leiden sobre a rede de coautoria)

Eager-fetches /authors/{id} para enriquecer com h_index, works_count,
institutions e concepts (via src/oa.py — cache-respecting + atomic gravação).

Output: data/author_network.json + ranking top-30 cross-axis.

Tag derivada: obra de autor-ponte (em build_rayyan.py) materializa
"aproximação curatorial" sem metáfora — autores reais que demonstravelmente
coexistem nos 3 silos.
"""
import collections
import gzip
import json
import math
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
CACHE_DIR = os.path.join(ROOT, "data", "oa_cache")
OUTPUT_JSON = os.path.join(ROOT, "data", "author_network.json")
SNOWBALL_JSON = os.path.join(ROOT, "data", "author_snowball_expansion.json")
ADJACENT_JSON = os.path.join(ROOT, "data", "adjacent_tradition_probes.json")
BUDGET_FILE = os.path.join(ROOT, "data", "_budget_used.txt")

# Vocabulários por eixo — reutiliza/expande os de build_rayyan.py.
_VOCAB_CYB = (
    # organizacional
    "viable system", "vsm", "stafford beer", "espejo", "management cybernet",
    "organizational cybernet", "organizational systems", "syntegrity",
    "brain of the firm", "heart of enterprise", "diagnosing the system",
    "designing freedom", "cybersyn", "managing complexity", "soft systems",
    "systems thinking", "systems practice", "systems methodolog",
    "critical systems", "fifth discipline",
    # fundacional
    "ashby", "wiener", "requisite variety", "second-order", "von foerster",
    "introduction to cybernetics", "theory of communication", "general system",
    "von bertalanffy", "autopoiesis", "self-organ", "homeostat", "cybernetic",
)
_VOCAB_REG = (
    "tools of government", "policy instrument", "policy tool", "regulation",
    "regulatory", "governance", "public management", "new public management",
    "npm", "regulatory state", "rule by law", "hood", "margetts", "lascoumes",
    "le galès", "le gales", "nodality", "policy mix", "command and control",
    "incentive instrument", "soft law", "nudge", "behavioural insight",
    "rule of law", "policy design", "regulatory capture",
)
_VOCAB_POLIND = (
    "industrial polic", "industrial strategy", "industrial development",
    "mission-oriented", "entrepreneurial state", "state-led", "developmental state",
    "structural transformation", "structural change", "rodrik", "mazzucato",
    "industrialization", "industrialisation", "nelson and winter", "evolutionary",
    "innovation system", "national system of innovation", "production capabilit",
    "import substitution", "industrial upgrading", "economic complexity",
    "industrial policy", "economic theory of socialism", "economic cybernetic",
    "economic planning", "wholes and parts", "industrial restructuring",
    "manufacturing capabilit",
)
VOCAB = {"Cyb": _VOCAB_CYB, "Reg": _VOCAB_REG, "PolInd": _VOCAB_POLIND}


# ───────── work enrichment (titles + year) ─────────
def enrich_works_titles(works, max_fetches=50):
    """Os works do cache (vindos de URLs com select=id,authorships) não têm título.
    Batch-fetch /works?filter=openalex:W1|...|W50 com select rico para preencher.
    Cada batch ≤ 50 ids. Devolve nº de novos fetches."""
    missing_title = [wid for wid, w in works.items()
                     if not (w.get("title") or w.get("display_name"))]
    if not missing_title:
        return 0
    n_new = 0
    # also seed from secondary enrichment files (no fetches)
    enrich_path = os.path.join(ROOT, "data", "openalex_enrich.json")
    if os.path.exists(enrich_path):
        try:
            secondary = json.load(open(enrich_path, encoding="utf-8"))
            for _key, v in secondary.items():
                wid = v.get("oa_id") or ""
                if wid in works and not works[wid].get("title"):
                    works[wid]["title"] = v.get("title")
                    works[wid]["display_name"] = v.get("title")
                    if v.get("year"):
                        works[wid]["publication_year"] = v["year"]
        except Exception:
            pass
    missing_title = [wid for wid, w in works.items()
                     if not (w.get("title") or w.get("display_name"))]
    print(f"  missing title after secondary load: {len(missing_title)}")
    for i in range(0, len(missing_title), 50):
        if n_new >= max_fetches:
            break
        chunk = missing_title[i:i + 50]
        flt = "openalex:" + "|".join(chunk)
        url = (f"{API}/works?filter={urllib.parse.quote(flt, safe=':|')}"
               f"&per-page=50&select=id,display_name,title,publication_year,"
               f"authorships,referenced_works,cited_by_count")
        was_cached = cache_hit(url)
        data = oa.get(url) or {}
        if not was_cached and data:
            n_new += 1
            bump_budget(1)
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            if wid in works:
                # merge — keep existing authorships + new title/year
                works[wid].update({k: v for k, v in w.items() if v})
    return n_new


# ───────── budget tracking ─────────
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
    """True se a URL já está cacheada (não conta no budget)."""
    cf = oa._cache_file(url)
    return os.path.exists(cf)


def tracked_get(url):
    """Wrapper que conta como fetch novo apenas quando cache miss."""
    if cache_hit(url):
        return oa.get(url)
    data = oa.get(url)
    if data:  # successful fetch (non-empty)
        bump_budget(1)
    return data


# ───────── cache mining ─────────
def mine_cache_works():
    """Devolve {oa_id: work_dict} para todo work com authorships no cache."""
    works = {}
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
                        if wid.startswith("W") and wid not in works:
                            works[wid] = w
            elif isinstance(data, dict) and data.get("id", "").startswith("https://openalex.org/W"):
                if data.get("authorships"):
                    wid = data["id"].split("/")[-1]
                    if wid not in works:
                        works[wid] = data
    return works


# ───────── axis classification ─────────
def classify_axes(title):
    """Devolve set de eixos que o título toca via vocab match."""
    t = (title or "").lower()
    axes = set()
    for ax, vocab in VOCAB.items():
        if any(k in t for k in vocab):
            axes.add(ax)
    return axes


# ───────── author aggregation ─────────
def aggregate_authors(works):
    """Devolve {author_oa_id: {display_name, n_works_total, n_per_axis, work_ids, work_axes}}."""
    authors = collections.defaultdict(lambda: {
        "display_name": "", "n_works_total": 0,
        "n_per_axis": {"Cyb": 0, "Reg": 0, "PolInd": 0},
        "work_ids": [], "axes": set(),
    })
    for wid, w in works.items():
        title = w.get("title") or w.get("display_name") or ""
        axes = classify_axes(title)
        for a in (w.get("authorships") or []):
            aid_full = (a.get("author") or {}).get("id") or ""
            aid = aid_full.split("/")[-1]
            if not aid.startswith("A"):
                continue
            name = (a.get("author") or {}).get("display_name") or ""
            ent = authors[aid]
            if name and len(name) > len(ent["display_name"]):
                ent["display_name"] = name
            ent["n_works_total"] += 1
            ent["work_ids"].append(wid)
            for ax in axes:
                ent["n_per_axis"][ax] += 1
            ent["axes"].update(axes)
    # serializable
    for ent in authors.values():
        ent["axes"] = sorted(ent["axes"])
    return dict(authors)


# ───────── scoring ─────────
def cross_axis_score(n_per_axis):
    """Entropia normalizada da distribuição de works do autor entre os 3 eixos.
    1.0 = perfeitamente balanceado (1/3, 1/3, 1/3).
    0.0 = concentrado num único eixo.
    Penaliza ausência num eixo (entropia trata 0 como 0)."""
    total = sum(n_per_axis.values())
    if total == 0:
        return 0.0
    probs = [n / total for n in n_per_axis.values() if n > 0]
    if len(probs) < 2:
        return 0.0  # só 1 eixo => sem cross
    h = -sum(p * math.log(p) for p in probs)
    return h / math.log(3)  # normaliza para [0, 1]


# ───────── enrichment via /authors/{id} ─────────
def enrich_authors(authors, max_fetches):
    """Eager-fetch /authors/{id} para preencher h_index, works_count, institutions.
    Respeita max_fetches (cap do turno). Devolve nº de novos fetches feitos."""
    n_new = 0
    for aid, ent in authors.items():
        if n_new >= max_fetches:
            break
        if ent.get("h_index") is not None:
            continue  # já enriquecido (caso re-rodemos)
        url = f"{API}/authors/{aid}"
        if cache_hit(url):
            data = oa.get(url) or {}
        else:
            data = tracked_get(url) or {}
            if data:
                n_new += 1
        ent["h_index"] = (data.get("summary_stats") or {}).get("h_index") or 0
        ent["works_count"] = data.get("works_count") or 0
        ent["cited_by_count"] = data.get("cited_by_count") or 0
        ent["institutions"] = [
            i.get("display_name") or ""
            for i in (data.get("last_known_institutions") or [])
        ][:3]
        ent["concepts"] = [
            c.get("display_name") or ""
            for c in (data.get("x_concepts") or [])[:5]
        ]
        if data.get("display_name") and not ent["display_name"]:
            ent["display_name"] = data["display_name"]
    return n_new


# ───────── coauthorship graph ─────────
def build_coauthor_graph(works, min_score=0.0, authors=None):
    """Devolve {author_id: set(co_author_ids)} e degree counts.
    Se authors fornecido com cross_axis_score, restringe arestas a pares onde
    pelo menos um dos autores tem score > min_score."""
    edges = collections.defaultdict(set)
    for w in works.values():
        aids = [
            ((a.get("author") or {}).get("id") or "").split("/")[-1]
            for a in (w.get("authorships") or [])
        ]
        aids = [a for a in aids if a.startswith("A")]
        for i, a in enumerate(aids):
            for b in aids[i + 1:]:
                if a == b:
                    continue
                edges[a].add(b)
                edges[b].add(a)
    return edges


def leiden_communities(edges):
    """Detecção de comunidades. Usa python-igraph + leidenalg se disponível;
    senão, cai num algoritmo de connected-components como fallback."""
    try:
        import igraph as ig
        import leidenalg
        nodes = sorted(edges.keys())
        idx = {n: i for i, n in enumerate(nodes)}
        es = set()
        for a, neighbors in edges.items():
            for b in neighbors:
                if a < b:
                    es.add((idx[a], idx[b]))
        g = ig.Graph(n=len(nodes), edges=list(es), directed=False)
        part = leidenalg.find_partition(g, leidenalg.ModularityVertexPartition)
        return {nodes[i]: comm_id for comm_id, comm in enumerate(part) for i in comm}
    except ImportError:
        # fallback: connected components
        comm = {}
        cid = 0
        for start in edges:
            if start in comm:
                continue
            stack = [start]
            while stack:
                n = stack.pop()
                if n in comm:
                    continue
                comm[n] = cid
                stack.extend(edges[n])
            cid += 1
        return comm


# ───────── snowball: top-N authors → their works ─────────
def snowball_top_authors(authors_sorted, n_authors=15, per_author=50, corpus_ids=None):
    """Para cada um dos top-N autores por cross_axis_score, fetch /works
    filter=author.id:Aid&per-page=per_author&sort=cited_by_count:desc.
    Catalogue obras NOVAS (não no corpus atual) — não incorpore."""
    corpus_ids = corpus_ids or set()
    out = {}
    n_new = 0
    for aid, ent in authors_sorted[:n_authors]:
        url = (f"{API}/works?filter=author.id:{aid}&sort=cited_by_count:desc"
               f"&per-page={per_author}&select=id,title,display_name,"
               f"publication_year,cited_by_count,doi,authorships")
        was_cached = cache_hit(url)
        data = oa.get(url) or {}
        if not was_cached and data:
            n_new += 1
            bump_budget(1)
        new_works = []
        in_corpus = []
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            title = w.get("title") or w.get("display_name") or ""
            entry = {
                "oa_id": wid, "title": title,
                "year": w.get("publication_year"),
                "cited_by": w.get("cited_by_count") or 0,
                "doi": w.get("doi") or "",
                "axes_hit": sorted(classify_axes(title)),
            }
            if wid in corpus_ids:
                in_corpus.append(entry)
            else:
                new_works.append(entry)
        out[aid] = {
            "display_name": ent["display_name"],
            "cross_axis_score": round(ent["cross_axis_score"], 4),
            "h_index": ent.get("h_index", 0),
            "n_new_works_found": len(new_works),
            "n_in_corpus_overlap": len(in_corpus),
            "new_works": new_works,
            "in_corpus": in_corpus,
        }
    return out, n_new


# ───────── adjacent tradition probes ─────────
ADJACENT_PROBES = {
    "polanyi": "Karl Polanyi",
    "schumpeter": "Joseph Schumpeter",
    "hirschman": "Albert Hirschman",
    "complexity_economics": "complexity economics",
    "governmentality": "governmentality foucault",
}


def probe_adjacent(corpus_ids, per_probe=50):
    """Sondagem dirigida: 50 obras mais citadas por consulta para cada tradição
    adjacente. Catalogue overlap com corpus e candidatos novos. Não incorpore."""
    out = {}
    n_new = 0
    for key, query in ADJACENT_PROBES.items():
        url = (f"{API}/works?search={urllib.parse.quote(query)}"
               f"&sort=cited_by_count:desc&per-page={per_probe}"
               f"&select=id,title,display_name,publication_year,cited_by_count,doi")
        was_cached = cache_hit(url)
        data = oa.get(url) or {}
        if not was_cached and data:
            n_new += 1
            bump_budget(1)
        items = []
        in_corpus = 0
        for w in (data.get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            title = w.get("title") or w.get("display_name") or ""
            entry = {
                "oa_id": wid, "title": title[:120],
                "year": w.get("publication_year"),
                "cited_by": w.get("cited_by_count") or 0,
                "in_corpus": wid in corpus_ids,
                "axes_hit": sorted(classify_axes(title)),
            }
            items.append(entry)
            if wid in corpus_ids:
                in_corpus += 1
        out[key] = {
            "query": query, "n_results": len(items),
            "n_overlap_with_corpus": in_corpus,
            "items": items,
        }
    return out, n_new


# ───────── main pipeline ─────────
def main():
    print(f"== Fase D · Author network completo ==")
    print(f"budget inicial: {read_budget()}/10000")

    works = mine_cache_works()
    print(f"works com authorships no cache: {len(works)}")

    # enrich with titles via batch fetch (works in cache só têm id+authorships)
    print(f"\nenriching work titles via batch fetch (≤50 ids/batch)...")
    n_w = enrich_works_titles(works, max_fetches=30)
    print(f"  new fetches this step: {n_w} | budget after: {read_budget()}/10000")
    n_with_title = sum(1 for w in works.values() if (w.get("title") or w.get("display_name")))
    print(f"  works with title now: {n_with_title}/{len(works)}")

    authors = aggregate_authors(works)
    print(f"autores únicos no corpus: {len(authors)}")

    # compute scores
    for ent in authors.values():
        ent["cross_axis_score"] = cross_axis_score(ent["n_per_axis"])
        ent["n_axes_touched"] = sum(1 for v in ent["n_per_axis"].values() if v > 0)

    cross_strict = sum(1 for e in authors.values() if e["n_axes_touched"] >= 3)
    cross_loose = sum(1 for e in authors.values() if e["n_axes_touched"] >= 2)
    print(f"autores com ≥3 eixos: {cross_strict} · ≥2 eixos: {cross_loose}")

    # enrich ALL authors (eager)
    budget_left = 10000 - read_budget()
    per_turn = min(250, budget_left)
    print(f"\nenriching authors via /authors/{{id}}... (up to {per_turn} this turn)")
    n_new = enrich_authors(authors, max_fetches=per_turn)
    print(f"  new fetches this turn: {n_new} | budget after: {read_budget()}/10000")

    # coauthor graph + leiden
    edges = build_coauthor_graph(works)
    print(f"\nco-author graph: {len(edges)} authors with ≥1 co-author")
    comms = leiden_communities(edges)
    print(f"  communities: {len(set(comms.values()))}")

    # degree + community per author
    for aid, ent in authors.items():
        ent["degree"] = len(edges.get(aid, set()))
        ent["community_id"] = comms.get(aid, -1)

    # output
    sorted_by_cross = sorted(
        authors.items(),
        key=lambda kv: (-kv[1]["cross_axis_score"], -kv[1]["n_works_total"]),
    )
    out = {
        "_generated": "fase D · 2026-05-29",
        "_budget_used": read_budget(),
        "n_authors": len(authors),
        "n_cross_axis_strict": cross_strict,
        "n_cross_axis_loose": cross_loose,
        "n_communities": len(set(comms.values())),
        "n_works_analyzed": len(works),
        "vocab_sizes": {ax: len(v) for ax, v in VOCAB.items()},
        "top_cross_axis": [
            {
                "oa_id": aid, "display_name": e["display_name"],
                "n_works_total": e["n_works_total"],
                "n_per_axis": e["n_per_axis"],
                "n_axes_touched": e["n_axes_touched"],
                "cross_axis_score": round(e["cross_axis_score"], 4),
                "h_index": e.get("h_index", 0),
                "institutions": e.get("institutions") or [],
                "concepts": e.get("concepts") or [],
                "degree": e["degree"],
                "community_id": e["community_id"],
            }
            for aid, e in sorted_by_cross[:60]
        ],
        "authors": {
            aid: {
                "display_name": e["display_name"],
                "n_works_total": e["n_works_total"],
                "n_per_axis": e["n_per_axis"],
                "n_axes_touched": e["n_axes_touched"],
                "cross_axis_score": round(e["cross_axis_score"], 4),
                "h_index": e.get("h_index", 0),
                "works_count": e.get("works_count", 0),
                "institutions": e.get("institutions") or [],
                "concepts": e.get("concepts") or [],
                "degree": e["degree"],
                "community_id": e["community_id"],
                "work_ids": e["work_ids"],
            }
            for aid, e in authors.items()
        },
    }
    json.dump(out, open(OUTPUT_JSON, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT_JSON} ({os.path.getsize(OUTPUT_JSON)//1024} KB)")

    # ─ snowball: top-15 authors → catalog novas obras
    if read_budget() < 9500:
        print(f"\n== snowball top-15 cross-axis authors ==")
        corpus_ids = set(works.keys())
        snow, n_snow = snowball_top_authors(sorted_by_cross, n_authors=15,
                                            per_author=50, corpus_ids=corpus_ids)
        print(f"  new fetches: {n_snow} | budget: {read_budget()}/10000")
        total_new = sum(s["n_new_works_found"] for s in snow.values())
        total_overlap = sum(s["n_in_corpus_overlap"] for s in snow.values())
        print(f"  obras novas catalogadas: {total_new} | overlap c/ corpus: {total_overlap}")
        json.dump({"_generated": out["_generated"], "by_author": snow,
                   "summary": {"n_new_works": total_new, "n_overlap": total_overlap}},
                  open(SNOWBALL_JSON, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  -> {SNOWBALL_JSON} ({os.path.getsize(SNOWBALL_JSON)//1024} KB)")

    # ─ sondagem: adjacent traditions
    if read_budget() < 9500:
        print(f"\n== adjacent tradition probes ==")
        corpus_ids = set(works.keys())
        adj, n_adj = probe_adjacent(corpus_ids, per_probe=50)
        print(f"  new fetches: {n_adj} | budget: {read_budget()}/10000")
        for key, p in adj.items():
            print(f"  [{key:22}] {p['n_results']} items | overlap c/ corpus: {p['n_overlap_with_corpus']}")
        json.dump({"_generated": out["_generated"], "probes": adj},
                  open(ADJACENT_JSON, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print(f"  -> {ADJACENT_JSON} ({os.path.getsize(ADJACENT_JSON)//1024} KB)")
    print(f"\ntop-10 by cross_axis_score:")
    for i, (aid, e) in enumerate(sorted_by_cross[:10]):
        ax = e["n_per_axis"]
        print(f"  {i+1:2d}. {e['display_name'][:34]:34} | "
              f"score={e['cross_axis_score']:.3f} | "
              f"C={ax['Cyb']} R={ax['Reg']} P={ax['PolInd']} | "
              f"works={e['n_works_total']} | h={e.get('h_index',0)}")


if __name__ == "__main__":
    main()
