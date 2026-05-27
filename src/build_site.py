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
import math
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from report_from_json import build_js  # noqa: E402  (reúso dos consts de gráfico)
from report_template import inject_template  # noqa: E402
import build_rayyan  # noqa: E402  (material de triagem para o Rayyan)

TEMPLATE = os.path.join(HERE, "site_template.html")
EXPLORER_TPL = os.path.join(HERE, "explorador_template.html")
TRIAGEM_TPL = os.path.join(HERE, "triagem_template.html")
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


def write_network_csvs(net, out):
    """Exporta a rede de cocitação real (nós e arestas) em CSV (Excel/Gephi)."""
    def w(name, header, rows):
        with open(os.path.join(out, name), "w", encoding="utf-8", newline="") as f:
            cw = csv.writer(f, lineterminator="\n"); cw.writerow(header); cw.writerows(rows)
    nodes, links = net.get("nodes", []), net.get("links", [])
    if not nodes:
        return 0
    w("10_rede_nos.csv", ["id_openalex", "obra", "eixo", "citacoes", "ano", "semente"],
      [(n["id"], n.get("label", ""), n.get("axis", ""), n.get("cited_by", 0),
        n.get("year") or "", n.get("seed", False)) for n in nodes])
    # força de associação (cocitação normalizada): peso / sqrt(grau_a · grau_b)
    freq = {}
    for l in links:
        freq[l["source"]] = freq.get(l["source"], 0) + l.get("peso", 1)
        freq[l["target"]] = freq.get(l["target"], 0) + l.get("peso", 1)

    def assoc(l):
        d = freq.get(l["source"], 0) * freq.get(l["target"], 0)
        return round(l.get("peso", 1) / math.sqrt(d), 4) if d else 0
    w("11_rede_arestas.csv", ["origem", "destino", "tipo", "cocitacoes", "forca_associacao"],
      [(l["source"], l["target"], l.get("tipo", "cocita"), l.get("peso", 1), assoc(l)) for l in links])
    return 2


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
    "obra": "rótulo/título da obra (nó da rede)", "eixo": "eixo temático do nó (Cyb/Reg/PolInd)",
    "semente": "indica se é obra-semente (True/False)", "origem": "nó de origem da aresta (id OpenAlex)",
    "destino": "nó de destino da aresta (id OpenAlex)", "tipo": "tipo de ligação (cocita)",
    "cocitacoes": "número de vezes citadas em conjunto (peso da cocitação)",
    "forca_associacao": "cocitação normalizada: peso / raiz(grau_origem · grau_destino)",
}


def write_dicionario(out):
    """Gera DICIONARIO.csv (arquivo, coluna, descrição) a partir dos CSV gerados."""
    import glob
    rows = []
    for fp in sorted(glob.glob(os.path.join(out, "[0-9][0-9]_*.csv"))):
        name = os.path.basename(fp)
        cols = open(fp, encoding="utf-8").readline().strip().split(",")
        rows += [(name, c, COLDOC.get(c, "")) for c in cols]
    with open(os.path.join(out, "DICIONARIO.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["arquivo", "coluna", "descricao"]); w.writerows(rows)


def net_stats(net):
    """Métricas estruturais da rede de cocitação real (calculadas do network.json)."""
    nodes = {n["id"]: n for n in net.get("nodes", [])}
    links = net.get("links", [])
    N, E = len(nodes), len(links)
    if N < 2:
        return {}
    by_axis = {}
    for n in nodes.values():
        by_axis[n.get("axis") or ""] = by_axis.get(n.get("axis") or "", 0) + 1
    same = cross = 0
    pares = {}
    polind_cross = 0
    for l in links:
        a = nodes.get(l["source"], {}).get("axis")
        b = nodes.get(l["target"], {}).get("axis")
        if a and b:
            if a == b:
                same += 1
            else:
                cross += 1
                k = " × ".join(sorted((a, b)))
                pares[k] = pares.get(k, 0) + 1
                if "PolInd" in (a, b):
                    polind_cross += 1
    classif = same + cross
    # modularidade Q da partição por eixo (cocitação ponderada): os eixos são
    # comunidades reais da estrutura, ou rótulo imposto?
    deg, m = {}, 0.0
    for l in links:
        w = l.get("peso", 1); m += w
        deg[l["source"]] = deg.get(l["source"], 0) + w
        deg[l["target"]] = deg.get(l["target"], 0) + w
    Q = 0.0
    if m > 0:
        within = sum(l.get("peso", 1) for l in links
                     if nodes[l["source"]].get("axis", "") == nodes[l["target"]].get("axis", ""))
        sumk = {}
        for nid, nd in nodes.items():
            a = nd.get("axis") or ""
            sumk[a] = sumk.get(a, 0) + deg.get(nid, 0)
        Q = within / m - sum((s / (2 * m)) ** 2 for s in sumk.values())
    return {
        "n": N, "e": E,
        "densidade": round(2 * E / (N * (N - 1)), 3),
        "modularidade": round(Q, 3),
        "classif": classif,
        "intra": same, "inter": cross,
        "pct_intra": round(100 * same / classif) if classif else 0,
        "pct_inter": round(100 * cross / classif) if classif else 0,
        "pares": pares,
        "polind_cross": polind_cross,
        "by_axis": by_axis,
    }


def rayyan_works_js(works):
    """Serializa as obras da síntese para a página de triagem (uid estável + campos de decisão)."""
    import re
    out = []
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", ""))
        uid = e["doi"] or (m.group(1) if m else None) or build_rayyan._norm(e["title"])[:60]
        out.append({"uid": uid, "title": e["title"], "authors": e["authors"], "year": e["year"],
                    "venue": e["venue"], "abstract": e["abstract"], "doi": e["doi"], "url": e["url"],
                    "type": e.get("type", "GEN"), "axes": sorted(e["axes"]), "roles": sorted(e["roles"])})
    return out


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

    rayyan = build_rayyan.build(DADOS)
    meta = build_meta(R)
    meta["rayyan_n"] = len(rayyan)
    js = build_js(R) + f"const META={json.dumps(meta, ensure_ascii=False)};\n"
    net_src = os.path.join(ROOT, "data", "network.json")
    net = json.load(open(net_src, encoding="utf-8")) if os.path.exists(net_src) else {"nodes": [], "links": []}
    js += f"const NETWORK={json.dumps(net, ensure_ascii=False)};\n"
    js += f"const NETMETA={json.dumps(net_stats(net), ensure_ascii=False)};\n"
    html = inject_template(js, TEMPLATE)
    index = os.path.join(DOCS, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site:  {index}  ({os.path.getsize(index)//1024} KB)")

    if os.path.exists(EXPLORER_TPL):
        with open(EXPLORER_TPL, encoding="utf-8") as f:
            expl = f.read().replace("__JS_DATA__", js)
        explorer = os.path.join(DOCS, "explorador.html")
        with open(explorer, "w", encoding="utf-8") as f:
            f.write(expl)
        print(f"expl:  {explorer}  ({os.path.getsize(explorer)//1024} KB)")

    if os.path.exists(TRIAGEM_TPL):
        works_js = f"const RAYYAN_WORKS={json.dumps(rayyan_works_js(rayyan), ensure_ascii=False)};"
        with open(TRIAGEM_TPL, encoding="utf-8") as f:
            tri = f.read().replace("__JS_DATA__", works_js)
        triagem = os.path.join(DOCS, "triagem.html")
        with open(triagem, "w", encoding="utf-8") as f:
            f.write(tri)
        print(f"triag: {triagem}  ({os.path.getsize(triagem)//1024} KB)")

    n = write_csvs(R, DADOS)
    n += write_network_csvs(net, DADOS)
    write_dicionario(DADOS)
    print(f"dados: {n} CSVs gerados a partir do JSON/rede em {DADOS}")
    print(f"rayyan: {len(rayyan)} obras em rayyan_sintese.ris/.csv")
    shutil.copy(JSON_SRC, os.path.join(DADOS, "scisci_results.json"))
    if os.path.exists(net_src):
        shutil.copy(net_src, os.path.join(DADOS, "rede_cocitacao.json"))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    missing = [s for s in SECTIONS if f'id="{s}"' not in html]
    for s in SECTIONS:
        print(f"  {'ok' if s not in missing else 'FALTA'}  #{s}")
    if "__JS_DATA__" in html:
        print("  ERRO: __JS_DATA__ não foi substituído"); return 1
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
