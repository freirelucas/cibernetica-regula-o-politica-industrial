#!/usr/bin/env python3
"""Gera o site estático do GitHub Pages em ``docs/`` a partir das fontes
versionadas — sem reexecutar o funil (~45 min) e sem dependências externas.

Produz:
    docs/index.html              site acadêmico (injeta os dados no template)
    docs/dados/*.csv             os 8 conjuntos processados do funil
    docs/dados/scisci_results.json   resultados consolidados
    docs/.nojekyll               desativa o processamento Jekyll do Pages

Uso:
    python src/build_site.py
"""
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from report_from_json import build_report_from_json  # noqa: E402

TEMPLATE = os.path.join(HERE, "site_template.html")
JSON_SRC = os.path.join(ROOT, "data", "scisci_results.json")
RICH_REPORT = os.path.join(ROOT, "reports", "scisci_ipea.html")
DOCS = os.path.join(ROOT, "docs")
DADOS = os.path.join(DOCS, "dados")

# Nomes canônicos dos CSVs embutidos em reports/scisci_ipea.html
CSV_NAMES = {
    "log": "00_pipeline_log.csv", "top20": "02_top20_citados.csv",
    "bridges": "03_bridges_n_axes_gte2.csv", "bursts": "05_kleinberg_bursts.csv",
    "beauties": "06_sleeping_beauties.csv", "clusters": "07_clusters_top3.csv",
    "seeds": "08_seeds.csv", "temporal": "09_temporal.csv",
}

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos",
            "rajadas", "adormecidas", "citadas", "sementes", "repro", "dados",
            "glossario", "referencias"]


def extract_csvs(rich_report_path, out_dir):
    """Extrai os CSVs embutidos (``const CSVS = { ... }``) para arquivos reais."""
    html = open(rich_report_path, encoding="utf-8").read()
    block = re.search(r"const CSVS\s*=\s*\{(.*?)\n\};", html, re.S)
    if not block:
        raise RuntimeError("bloco 'const CSVS' não encontrado em " + rich_report_path)
    written = []
    for m in re.finditer(r'(\w+):\s*"((?:[^"\\]|\\.)*)"', block.group(1)):
        key, raw = m.group(1), m.group(2)
        csv = json.loads('"' + raw + '"')  # desescapa \n \" \uXXXX
        name = CSV_NAMES.get(key, key + ".csv")
        with open(os.path.join(out_dir, name), "w", encoding="utf-8") as f:
            f.write(csv)
        written.append(name)
    return written


def main():
    os.makedirs(DADOS, exist_ok=True)

    html = build_report_from_json(JSON_SRC, TEMPLATE)
    index = os.path.join(DOCS, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site:  {index}  ({os.path.getsize(index)//1024} KB)")

    csvs = extract_csvs(RICH_REPORT, DADOS)
    print(f"dados: {len(csvs)} CSVs em {DADOS}")
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
