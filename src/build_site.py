#!/usr/bin/env python3
"""Gera o site estático do GitHub Pages em ``docs/`` a partir de uma fonte
única — ``data/scisci_results.json`` — sem reexecutar o funil (~45 min) e sem
dependências externas.

Produz:
    docs/index.html              site acadêmico (injeta os dados no template)
    docs/dados/*.csv             os 8 conjuntos processados do funil
    docs/dados/scisci_results.json   resultados consolidados
    docs/.nojekyll               desativa o processamento Jekyll do Pages

Os arquivos de docs/vendor/ (Chart.js e fontes) são ativos versionados; este
script não os recria.

Uso:
    python src/build_site.py
"""
import csv
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from report_from_json import build_js  # noqa: E402  (reúso dos consts de gráfico)
from report_template import inject_template  # noqa: E402

TEMPLATE = os.path.join(HERE, "site_template.html")
JSON_SRC = os.path.join(ROOT, "data", "scisci_results.json")
DOCS = os.path.join(ROOT, "docs")
DADOS = os.path.join(DOCS, "dados")

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos",
            "rajadas", "adormecidas", "citadas", "discussao", "sementes", "repro", "dados",
            "limitacoes", "glossario", "referencias"]


def write_csvs(R, out):
    """Gera os 8 CSVs canônicos do funil a partir do JSON (fonte única)."""
    def w(name, header, rows):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
            cw = csv.writer(f, lineterminator="\n"); cw.writerow(header); cw.writerows(rows)

    w("00_pipeline_log.csv", ["parametro", "valor", "descricao"], [
        ("corpus_size", R["corpus_size"], "Total de trabalhos no corpus"),
        ("n_seeds", R["n_seeds"], "Obras-semente"),
        ("n_axes_1", R["n_axes_1"], "Trabalhos com pelo menos 1 eixo"),
        ("n_axes_2", R["n_axes_2"], "Trabalhos com 2 ou mais eixos (obras-ponte)"),
        ("n_axes_3", R["n_axes_3"], "Trabalhos com os 3 eixos"),
        ("cocit_nodes", R["cocit_nodes"], "Nos da rede de cocitacao"),
        ("cocit_edges", R["cocit_edges"], "Arestas da rede de cocitacao"),
        ("coupling_nodes", R["coupling_nodes"], "Nos da rede de acoplamento bibliografico"),
        ("coupling_edges", R["coupling_edges"], "Arestas da rede de acoplamento bibliografico"),
        ("n_clusters_cc", R["n_clusters_cc"], "Agrupamentos de cocitacao (Leiden CPM)"),
        ("n_clusters_bc", R["n_clusters_bc"], "Agrupamentos de acoplamento (Leiden modularidade)"),
        ("n_bursts", R["n_bursts"], "Rajadas de citacao detectadas (Kleinberg)"),
        ("n_bursting_refs", R["n_bursting_refs"], "Referencias com rajada"),
        ("pct_with_refs", R["pct_with_refs"], "Percentual de trabalhos com referencias"),
        ("gerado_em", R["generated"], "Carimbo de data/hora da execucao"),
    ])
    w("02_top20_citados.csv", ["year", "cited_by", "axes", "n_axes", "authors", "title", "venue"],
      [(r["year"], r["cited_by"], r["axes"], r.get("n_axes", ""), r.get("authors", ""),
        r["title"], r.get("venue", "")) for r in R["top20_nonfeed"]])
    w("03_bridges_n_axes_gte2.csv", ["year", "cited_by", "axes", "authors", "title"],
      [(r["year"], r["cited_by"], r["axes"], r.get("authors", ""), r["title"]) for r in R["top_bridges"]])
    w("05_kleinberg_bursts.csv", ["ref_id", "begin", "end", "weight", "title", "authors"],
      [(r["ref_id"], r["begin"], r["end"], r["weight"], r["title"], r.get("authors", "")) for r in R["top_bursts"]])
    w("06_sleeping_beauties.csv", ["year", "cited_by", "B", "t_m", "axes", "title"],
      [(r["year"], r["cited_by"], r["B"], r["t_m"], r.get("axes", ""), r["title"]) for r in R["sleeping_beauties"]])
    rows = [(c["cluster_id"], c["label"], c["size"], p["title"], p["cited_by"], p["year"])
            for c in R["clusters_bc"] for p in c["top_papers"]]
    w("07_clusters_top3.csv", ["cluster_id", "cluster_label", "cluster_size", "titulo", "citacoes", "ano"], rows)
    w("08_seeds.csv", ["chave", "openalex_id", "referencia"],
      [(s["key"], s["id"], s["ref"]) for s in R["seeds"]])
    w("09_temporal.csv", ["year", "Cyb", "Reg", "PolInd"],
      [(t["year"], t["Cyb"], t["Reg"], t["PolInd"]) for t in R["temporal"]])
    return 8


def build_meta(R):
    """Campos do JSON que não entram nos consts de gráfico, mas alimentam a prosa."""
    return {
        "n_axes_1": R["n_axes_1"],
        "coupling_n": R["coupling_nodes"], "coupling_e": R["coupling_edges"],
        "clusters_cc": R["n_clusters_cc"], "clusters_bc_total": R["n_clusters_bc"],
        "pivotal": R["n_pivotal"], "pct_refs": R["pct_with_refs"],
        "bursting_refs": R["n_bursting_refs"],
    }


def main():
    os.makedirs(DADOS, exist_ok=True)
    with open(JSON_SRC, encoding="utf-8") as f:
        R = json.load(f)

    js = build_js(R) + f"const META={json.dumps(build_meta(R), ensure_ascii=False)};\n"
    html = inject_template(js, TEMPLATE)
    index = os.path.join(DOCS, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site:  {index}  ({os.path.getsize(index)//1024} KB)")

    n = write_csvs(R, DADOS)
    print(f"dados: {n} CSVs gerados a partir do JSON em {DADOS}")
    shutil.copy(JSON_SRC, os.path.join(DADOS, "scisci_results.json"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    missing = [s for s in SECTIONS if f'id="{s}"' not in html]
    for s in SECTIONS:
        print(f"  {'ok' if s not in missing else 'FALTA'}  #{s}")
    if "__JS_DATA__" in html:
        print("  ERRO: __JS_DATA__ não foi substituído"); return 1
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
