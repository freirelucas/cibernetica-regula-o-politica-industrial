#!/usr/bin/env python3
"""Mapeia ``data/scisci_results.json`` -> bloco JS consumido pelo modelo do site.

Biblioteca (sem dependências além da padrão) usada por ``build_site.py``:
reconstrói os ``const STATS/TEMPORAL/TOP20/...`` a partir dos resultados salvos,
sem rodar o funil (~45 min).
"""
import json


def _axis_of(ref):
    """Deriva o eixo temático da obra-semente a partir do texto da referência."""
    if any(x in ref for x in ("Beer", "Ashby", "Espejo")):
        return "Cyb"
    if any(x in ref for x in ("Hood", "Margetts")):
        return "Reg"
    return "PolInd"


def _pick(d, keys):
    return {k: d.get(k) for k in keys}


def _j(obj):
    return json.dumps(obj, ensure_ascii=False, default=str)


def build_js(results):
    """Mapeia scisci_results.json -> bloco JS consumido pelo modelo."""
    stats = {
        "corpus":        results.get("corpus_size"),
        "seeds":         results.get("n_seeds"),
        "axes2":         results.get("n_axes_2"),
        "axes3":         results.get("n_axes_3"),
        "cocit_n":       results.get("cocit_nodes"),
        "cocit_e":       results.get("cocit_edges"),
        "bursts":        results.get("n_bursts"),
        "bursting_refs": results.get("n_bursting_refs"),
        "generated":     results.get("generated"),
    }

    temporal = results.get("temporal", [])
    top20    = [_pick(r, ("year", "cited_by", "axes", "authors", "title")) for r in results.get("top20_nonfeed", [])]
    bridges  = [_pick(r, ("year", "cited_by", "axes", "authors", "title")) for r in results.get("top_bridges", [])]
    bursts   = [_pick(r, ("begin", "end", "weight", "title", "authors", "ref_id")) for r in results.get("top_bursts", [])]
    beauties = [_pick(r, ("year", "cited_by", "B", "t_m", "axes", "title")) for r in results.get("sleeping_beauties", [])]

    clusters = []
    for c in results.get("clusters_bc", []):
        if c.get("size", 0) < 3:
            continue
        clusters.append({
            "id":     c.get("cluster_id"),
            "label":  c.get("label"),
            "size":   c.get("size"),
            "papers": [_pick(p, ("title", "cited_by", "year")) for p in c.get("top_papers", [])],
        })
    stats["clusters"] = len(clusters)

    seeds = [{"id": s.get("id"), "ref": s.get("ref"), "axis": _axis_of(s.get("ref", ""))}
             for s in results.get("seeds", [])]

    return (f"const STATS={_j(stats)};\n"
            f"const TEMPORAL={_j(temporal)};\n"
            f"const TOP20={_j(top20)};\n"
            f"const BRIDGES={_j(bridges)};\n"
            f"const BURSTS={_j(bursts)};\n"
            f"const CLUSTERS={_j(clusters)};\n"
            f"const BEAUTIES={_j(beauties)};\n"
            f"const SEEDS={_j(seeds)};\n")
