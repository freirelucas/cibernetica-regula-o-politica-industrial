#!/usr/bin/env python3
"""Regenera o HTML report a partir de ``data/scisci_results.json``, sem rodar o
pipeline completo (~45 min). Usa apenas a biblioteca padrão.

Fecha a lacuna de reprodutibilidade: ``report_builder.build_html_report`` exige
os objetos DataFrame vivos do pipeline; este módulo reconstrói os mesmos consts
JS consumidos pelo template a partir dos resultados salvos.

Uso:
    python src/report_from_json.py
    python src/report_from_json.py --json data/scisci_results.json \\
        --template colab/html_template.html --out reports/scisci_report.html
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from report_template import inject_template  # noqa: E402

SECTIONS = ["resumo", "temporal", "top20", "bridges", "bursts", "clusters", "beauties", "seeds"]


def _axis_of(ref):
    """Deriva o eixo temático do seed a partir do texto da referência."""
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
    """Mapeia scisci_results.json -> bloco JS consumido pelo template."""
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


def build_report_from_json(json_path, template_path=None):
    with open(json_path, encoding="utf-8") as f:
        results = json.load(f)
    return inject_template(build_js(results), template_path)


def main(argv=None):
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ap = argparse.ArgumentParser(description="Regenera o HTML report a partir do JSON de resultados.")
    ap.add_argument("--json", default=os.path.join(root, "data", "scisci_results.json"))
    ap.add_argument("--template", default=None, help="html_template.html (autodetecta se omitido)")
    ap.add_argument("--out", default=os.path.join(root, "reports", "scisci_report.html"))
    args = ap.parse_args(argv)

    html = build_report_from_json(args.json, args.template)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"HTML report salvo: {args.out}  ({os.path.getsize(args.out) // 1024} KB)")

    # Sanidade: seções presentes (mesma checagem da Célula 11 do notebook)
    missing = [s for s in SECTIONS if f'id="{s}"' not in html]
    for s in SECTIONS:
        print(f"  {'ok' if s not in missing else 'FALTA'}  #{s}")
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
