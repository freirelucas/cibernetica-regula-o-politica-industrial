"""B.5 — Gould-Fernandez brokerage roles sobre o grafo de coautoria.

Classifica cada autor (que serve de intermediário num triplete A-B-C) num dos
5 papéis, definidos pelo eixo primário de cada um:
  - coordinator (todos no mesmo grupo: A=B=C — intra)
  - gatekeeper (B distinto; A=C, intermediário traz info para o grupo)
  - representative (B distinto; A=C, intermediário leva info do grupo)
  - consultant/itinerant (A≠C ≠ B, three diff groups)
  - liaison (B serve duas pessoas de grupos diferentes do dele)

Implementação: para cada autor B com vizinhos coautores no grafo, conta
quantos tripletes A-B-C (A,C coautores de B mas não entre si) caem em cada
papel. Grupo de cada autor = seu eixo primário (argmax n_per_axis).

Output: data/brokerage_roles.json + summary.
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AUTHOR_NETWORK = os.path.join(ROOT, "data", "author_network.json")
WORKS_PATH = None  # mined from author_network indirectly
OUTPUT = os.path.join(ROOT, "data", "brokerage_roles.json")


def primary_axis(n_per_axis):
    """Retorna eixo com max contagem, ou None se todos zero."""
    items = [(k, v) for k, v in n_per_axis.items() if v > 0]
    if not items:
        return None
    return max(items, key=lambda kv: kv[1])[0]


def reconstruct_coauthor_graph(authors_map):
    """A partir de authors_map (com work_ids), reconstrói coauthor graph:
    para cada work, cria arestas entre todos pares de autores que o assinaram."""
    work_to_authors = collections.defaultdict(set)
    for aid, ent in authors_map.items():
        for wid in ent.get("work_ids", []):
            work_to_authors[wid].add(aid)
    edges = collections.defaultdict(set)
    for wid, aids in work_to_authors.items():
        aids = list(aids)
        for i, a in enumerate(aids):
            for b in aids[i + 1:]:
                edges[a].add(b)
                edges[b].add(a)
    return edges


def classify_triplet(group_b, group_a, group_c):
    """Dado 3 grupos (eixos primários), retorna o papel de B no triplete A-B-C."""
    # B = intermediário
    if group_a == group_b == group_c:
        return "coordinator"
    if group_a == group_c and group_a != group_b:
        return "itinerant"  # intermediário entre 2 do mesmo outro grupo
    if group_a == group_b and group_b != group_c:
        return "representative"  # B e A no mesmo grupo, A→B→C externo
    if group_c == group_b and group_b != group_a:
        return "gatekeeper"  # externo A→B(grupo)→C(grupo), C dentro
    # 3 grupos distintos
    return "liaison"


def compute_brokerage(authors_map, edges):
    """Para cada autor B, computa contagens dos 5 papéis G-F."""
    roles_by_author = {}
    for b, neighbors in edges.items():
        ent_b = authors_map.get(b)
        if not ent_b:
            continue
        gb = primary_axis(ent_b.get("n_per_axis") or {})
        if gb is None:
            continue
        counter = collections.Counter()
        nbrs = list(neighbors)
        for i, a in enumerate(nbrs):
            ent_a = authors_map.get(a)
            if not ent_a:
                continue
            ga = primary_axis(ent_a.get("n_per_axis") or {})
            if ga is None:
                continue
            for c in nbrs[i + 1:]:
                # somente conta se A e C NÃO são coautores diretos (B é o intermediário)
                if c in edges.get(a, set()):
                    continue
                ent_c = authors_map.get(c)
                if not ent_c:
                    continue
                gc = primary_axis(ent_c.get("n_per_axis") or {})
                if gc is None:
                    continue
                role = classify_triplet(gb, ga, gc)
                counter[role] += 1
        if counter:
            roles_by_author[b] = {
                "display_name": ent_b.get("display_name", ""),
                "primary_axis": gb,
                "n_neighbors": len(neighbors),
                "roles": dict(counter),
                "total_triplets": sum(counter.values()),
            }
    return roles_by_author


def main():
    print("== B.5 · Gould-Fernandez brokerage ==")
    A = json.load(open(AUTHOR_NETWORK, encoding="utf-8"))
    authors_map = A["authors"]
    print(f"autores total: {len(authors_map)}")

    edges = reconstruct_coauthor_graph(authors_map)
    print(f"autores no coauthor graph: {len(edges)}")

    brokerage = compute_brokerage(authors_map, edges)
    print(f"autores com ≥1 triplete: {len(brokerage)}")

    # summary
    role_totals = collections.Counter()
    authors_per_role = collections.defaultdict(set)
    for aid, ent in brokerage.items():
        for role, count in ent["roles"].items():
            role_totals[role] += count
            authors_per_role[role].add(aid)

    summary = {
        "role_totals": dict(role_totals),
        "n_authors_per_role": {r: len(s) for r, s in authors_per_role.items()},
    }
    print("\nrole distribution (triplets count):")
    for r, n in role_totals.most_common():
        print(f"  {r:14}: {n:6} triplets · {len(authors_per_role[r]):4} autores")

    # top by liaison + itinerant (cross-axis types)
    cross_axis_roles = ("liaison", "itinerant", "gatekeeper", "representative")
    ranked = []
    for aid, ent in brokerage.items():
        cross_sum = sum(ent["roles"].get(r, 0) for r in cross_axis_roles)
        if cross_sum > 0:
            ranked.append((aid, ent, cross_sum))
    ranked.sort(key=lambda t: -t[2])

    print(f"\ntop-10 autores por brokerage cross-axis (liaison + itinerant + gatekeeper + representative):")
    for aid, ent, cs in ranked[:10]:
        r = ent["roles"]
        print(f"  {ent['display_name'][:28]:28} [{ent['primary_axis']:6}] | "
              f"L:{r.get('liaison',0):3} I:{r.get('itinerant',0):3} "
              f"G:{r.get('gatekeeper',0):3} R:{r.get('representative',0):3} "
              f"C:{r.get('coordinator',0):3}")

    out = {
        "_generated": "B.5 · Gould-Fernandez brokerage",
        "summary": summary,
        "top_by_cross_brokerage": [
            {"oa_id": aid, "display_name": ent["display_name"],
             "primary_axis": ent["primary_axis"], "roles": ent["roles"],
             "cross_brokerage_sum": cs}
            for aid, ent, cs in ranked[:60]
        ],
        "by_author": brokerage,
    }
    json.dump(out, open(OUTPUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT} ({os.path.getsize(OUTPUT)//1024} KB)")


if __name__ == "__main__":
    main()
