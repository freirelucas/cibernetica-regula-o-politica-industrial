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

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos", "rede",
            "rajadas", "adormecidas", "citadas", "discussao", "brasil", "analise-brasil", "sintese", "leitura", "sementes", "repro", "dados",
            "limitacoes", "glossario", "referencias"]


def write_csvs(R, out):
    """Gera os 8 CSVs canônicos do funil a partir do JSON (fonte única)."""
    def w(name, header, rows):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
            cw = csv.writer(f, lineterminator="\n"); cw.writerow(header); cw.writerows(rows)

    w("00_registro_execucao.csv", ["parametro", "valor", "descricao"], [
        ("corpus", R["corpus_size"], "Total de trabalhos no corpus"),
        ("obras_semente", R["n_seeds"], "Obras-semente"),
        ("com_1_eixo", R["n_axes_1"], "Trabalhos com pelo menos 1 eixo"),
        ("com_2_eixos", R["n_axes_2"], "Trabalhos com 2 ou mais eixos (obras-ponte)"),
        ("com_3_eixos", R["n_axes_3"], "Trabalhos com os 3 eixos"),
        ("cocit_nos", R["cocit_nodes"], "Nos da rede de cocitacao"),
        ("cocit_arestas", R["cocit_edges"], "Arestas da rede de cocitacao"),
        ("acopl_nos", R["coupling_nodes"], "Nos da rede de acoplamento bibliografico"),
        ("acopl_arestas", R["coupling_edges"], "Arestas da rede de acoplamento bibliografico"),
        ("agrupamentos_cocit", R["n_clusters_cc"], "Agrupamentos de cocitacao (Leiden CPM)"),
        ("agrupamentos_acopl", R["n_clusters_bc"], "Agrupamentos de acoplamento (Leiden modularidade)"),
        ("rajadas", R["n_bursts"], "Rajadas de citacao detectadas (Kleinberg)"),
        ("refs_com_rajada", R["n_bursting_refs"], "Referencias com rajada"),
        ("pct_com_refs", R["pct_with_refs"], "Percentual de trabalhos com referencias"),
        ("gerado_em", R["generated"], "Carimbo de data/hora da execucao"),
    ])
    w("02_mais_citados.csv", ["ano", "citacoes", "eixos", "n_eixos", "autores", "titulo", "veiculo"],
      [(r["year"], r["cited_by"], r["axes"], r.get("n_axes", ""), r.get("authors", ""),
        r["title"], r.get("venue", "")) for r in R["top20_nonfeed"]])
    w("03_obras_ponte.csv", ["ano", "citacoes", "eixos", "autores", "titulo"],
      [(r["year"], r["cited_by"], r["axes"], r.get("authors", ""), r["title"]) for r in R["top_bridges"]])
    w("05_rajadas_kleinberg.csv", ["id_ref", "inicio", "fim", "peso", "titulo", "autores"],
      [(r["ref_id"], r["begin"], r["end"], r["weight"], r["title"], r.get("authors", "")) for r in R["top_bursts"]])
    w("06_belas_adormecidas.csv", ["ano", "citacoes", "B", "t_m", "eixos", "titulo"],
      [(r["year"], r["cited_by"], r["B"], r["t_m"], r.get("axes", ""), r["title"]) for r in R["sleeping_beauties"]])
    rows = [(c["cluster_id"], c["label"], c["size"], p["title"], p["cited_by"], p["year"])
            for c in R["clusters_bc"] for p in c["top_papers"]]
    w("07_agrupamentos.csv", ["id_agrupamento", "rotulo", "tamanho", "titulo", "citacoes", "ano"], rows)
    w("08_obras_semente.csv", ["chave", "id_openalex", "referencia"],
      [(s["key"], s["id"], s["ref"]) for s in R["seeds"]])
    w("09_serie_temporal.csv", ["ano", "Cyb", "Reg", "PolInd"],
      [(t["year"], t["Cyb"], t["Reg"], t["PolInd"]) for t in R["temporal"]])
    return 8


COLDOC = {
    "parametro": "nome do parâmetro/métrica", "valor": "valor", "descricao": "descrição do parâmetro",
    "ano": "ano de publicação", "citacoes": "total de citações (OpenAlex)",
    "eixos": "eixos temáticos tocados (Cyb/Reg/PolInd)", "n_eixos": "número de eixos tocados",
    "autores": "autores (até 3)", "titulo": "título da obra", "veiculo": "veículo/fonte",
    "id_ref": "identificador OpenAlex da referência", "inicio": "ano de início da rajada",
    "fim": "ano de fim da rajada", "peso": "peso da rajada (excesso de citações acumulado)",
    "B": "coeficiente de beleza (Ke et al. 2015)", "t_m": "anos até o pico de citações",
    "id_agrupamento": "identificador do agrupamento (Leiden)", "rotulo": "termos distintivos do agrupamento",
    "tamanho": "nº de trabalhos no agrupamento", "chave": "chave interna da obra-semente",
    "id_openalex": "identificador OpenAlex", "referencia": "referência bibliográfica da obra-semente",
    "Cyb": "trabalhos do eixo Cibernética no ano", "Reg": "trabalhos do eixo Regulação no ano",
    "PolInd": "trabalhos do eixo Política Industrial no ano",
}


def write_dicionario(out):
    """Gera DICIONARIO.csv (arquivo, coluna, descrição) a partir dos CSV gerados."""
    import glob
    rows = []
    for fp in sorted(glob.glob(os.path.join(out, "0*.csv"))):
        name = os.path.basename(fp)
        cols = open(fp, encoding="utf-8").readline().strip().split(",")
        rows += [(name, c, COLDOC.get(c, "")) for c in cols]
    with open(os.path.join(out, "DICIONARIO.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["arquivo", "coluna", "descricao"]); w.writerows(rows)


def build_meta(R):
    """Campos do JSON que não entram nos consts de gráfico, mas alimentam a prosa."""
    piv = (R.get("top_pivotal") or [{}])[0]
    return {
        "n_axes_1": R["n_axes_1"],
        "coupling_n": R["coupling_nodes"], "coupling_e": R["coupling_edges"],
        "clusters_cc": R["n_clusters_cc"], "clusters_bc_total": R["n_clusters_bc"],
        "pivotal": R["n_pivotal"], "pct_refs": R["pct_with_refs"],
        "bursting_refs": R["n_bursting_refs"],
        "pivotal_ref": piv.get("ref_id"), "pivotal_title": piv.get("title"),
        "pivotal_authors": piv.get("authors"), "pivotal_year": piv.get("year"),
        "pivotal_betw": round(float(piv.get("betweenness") or 0), 3),
        "pivotal_cit": piv.get("n_citations"),
    }


def main():
    os.makedirs(DADOS, exist_ok=True)
    with open(JSON_SRC, encoding="utf-8") as f:
        R = json.load(f)

    js = build_js(R) + f"const META={json.dumps(build_meta(R), ensure_ascii=False)};\n"
    net_src = os.path.join(ROOT, "data", "network.json")
    net = json.load(open(net_src, encoding="utf-8")) if os.path.exists(net_src) else {"nodes": [], "links": []}
    js += f"const NETWORK={json.dumps(net, ensure_ascii=False)};\n"
    html = inject_template(js, TEMPLATE)
    index = os.path.join(DOCS, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site:  {index}  ({os.path.getsize(index)//1024} KB)")

    n = write_csvs(R, DADOS)
    write_dicionario(DADOS)
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
