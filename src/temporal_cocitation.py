"""Longue-durée: trajetória temporal das três tradições e formação dos silos.

A rede de cocitação agregada não tem timestamp por aresta (cada aresta soma
sobre todos os citantes históricos). O que esta análise faz:

1. Usa R["temporal"] (49 anos × 3 eixos) para detectar o ano de emergência,
   o pico e o primeiro ano de co-presença das três tradições.
2. Toma snapshots por década do core cocitado (rede_explodida.json — 215 nós
   com year+axis). Para cada década, computa a fração intra-eixo no subgrafo
   formado por nós publicados até o fim da década. Se essa fração CRESCE no
   tempo, é evidência empírica de que os silos foram se cristalizando à
   medida que o núcleo cocitado se expandiu.

Output: data/temporal_cocitation.json. Uso: python src/temporal_cocitation.py
"""
import collections
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCISCI = os.path.join(ROOT, "data", "scisci_results.json")
NET = os.path.join(ROOT, "docs", "dados", "rede_explodida.json")
OUT = os.path.join(ROOT, "data", "temporal_cocitation.json")

AXES = ["Cyb", "Reg", "PolInd"]
DECADES = [(1960, 1969), (1970, 1979), (1980, 1989), (1990, 1999),
           (2000, 2009), (2010, 2019), (2020, 2029)]


def main():
    R = json.load(open(SCISCI, encoding="utf-8"))
    net = json.load(open(NET, encoding="utf-8"))

    # --- 1) série anual: emergência, pico, co-presença ---
    temporal = R.get("temporal", [])
    by_year = {t["year"]: t for t in temporal}
    years = sorted(by_year)

    cumul = {ax: 0 for ax in AXES}
    cumul_history = []
    for y in years:
        for ax in AXES:
            cumul[ax] += by_year[y].get(ax, 0)
        cumul_history.append({"year": y, **{ax: cumul[ax] for ax in AXES}})

    arrival = {ax: next((y for y in years if by_year[y].get(ax, 0) >= 3), None) for ax in AXES}
    peak = {ax: max(years, key=lambda y: by_year[y].get(ax, 0)) for ax in AXES}
    peak_val = {ax: by_year[peak[ax]].get(ax, 0) for ax in AXES}
    copresence = next((y for y in years if all(by_year[y].get(ax, 0) >= 3 for ax in AXES)), None)

    # --- 2) snapshots por década do core cocitado ---
    node_axis = {n["id"]: n.get("axis") for n in net["nodes"]}
    node_year = {n["id"]: n.get("year") for n in net["nodes"]}
    edges = net.get("links") or net.get("edges") or []

    decade_snaps = []
    for (lo, hi) in DECADES:
        nodes_in = {nid for nid, y in node_year.items() if y and lo <= y <= hi}
        nodes_cumul = {nid for nid, y in node_year.items() if y and y <= hi}
        if not nodes_cumul:
            continue
        ax_dist_new = collections.Counter(node_axis.get(nid) for nid in nodes_in)
        ax_dist_cumul = collections.Counter(node_axis.get(nid) for nid in nodes_cumul)

        intra = collections.Counter()
        cross = 0
        for e in edges:
            a, b = e.get("source"), e.get("target")
            if a in nodes_cumul and b in nodes_cumul:
                ax_a, ax_b = node_axis.get(a), node_axis.get(b)
                if ax_a and ax_b:
                    if ax_a == ax_b:
                        intra[ax_a] += 1
                    else:
                        cross += 1
        total = sum(intra.values()) + cross
        intra_frac = sum(intra.values()) / max(total, 1)

        decade_snaps.append({
            "decade": f"{lo}s", "low": lo, "high": hi,
            "n_new_nodes": len(nodes_in),
            "n_total_nodes": len(nodes_cumul),
            "axis_distribution_new": {k: v for k, v in ax_dist_new.items() if k},
            "axis_distribution_cumul": {k: v for k, v in ax_dist_cumul.items() if k},
            "n_edges_cumul": total,
            "n_intra_axis_edges": dict(intra),
            "n_cross_axis_edges": cross,
            "intra_axis_fraction": round(intra_frac, 4),
        })

    # silo crystallization: primeira década com intra_frac ≥ 0.80 e ≥50 arestas
    crystallization = next(
        (d["decade"] for d in decade_snaps
         if d["intra_axis_fraction"] >= 0.80 and d["n_edges_cumul"] >= 50),
        None)

    out = {
        "axis_arrival_year": arrival,
        "axis_peak_year": peak,
        "axis_peak_value": peak_val,
        "first_copresence_year": copresence,
        "silo_crystallization_decade": crystallization,
        "cumul_history": cumul_history,
        "decade_snapshots": decade_snaps,
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"-> {OUT}")
    print(f"\nEmergência (≥3 obras/ano): {arrival}")
    print(f"Pico (max anual):           {peak} → contagens {peak_val}")
    print(f"Co-presença (todos ≥3):     {copresence}")
    print(f"Silo cristalizado:          {crystallization}")
    print(f"\nFração intra-eixo por década (cumulativa):")
    for d in decade_snaps:
        if d["n_edges_cumul"] > 0:
            print(f"  {d['decade']}: intra={d['intra_axis_fraction']:.3f} "
                  f"({d['n_edges_cumul']:5d} arestas, {d['n_total_nodes']:3d} nós)")


if __name__ == "__main__":
    main()
