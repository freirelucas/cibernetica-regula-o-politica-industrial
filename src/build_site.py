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
from token_injection import (  # noqa: E402
    inject_hypergraph_numbers, inject_author_network_numbers,
    inject_brazil_numbers, inject_brokerage_numbers,
)
import build_rayyan  # noqa: E402  (material de triagem para o Rayyan)
import sfi_methods  # noqa: E402  (lei de potência + CNM — métodos Clauset/Santa Fe)
import data_io  # noqa: E402  (PR-2 — leitura tolerante dos derivados em data/)

TEMPLATE = os.path.join(HERE, "site_template.html")
EXPLORER_TPL = os.path.join(HERE, "explorador_template.html")
TRIAGEM_TPL = os.path.join(HERE, "triagem_template.html")
JSON_SRC = data_io.data_path("scisci_results.json")
DOCS = os.path.join(ROOT, "docs")
DADOS = os.path.join(DOCS, "dados")

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos", "rede",
            "rajadas", "longue-duree", "adormecidas", "citadas", "candidatos", "autor-ponte", "brasil", "brasil-expandido", "analise-brasil", "discussao", "sintese", "leitura", "sementes", "repro", "dados",
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

    # comunidades DETECTADAS pela modularidade gulosa (Clauset–Newman–Moore, 2004),
    # SEM usar o vocabulário — valida os eixos sem circularidade: Q detectada e NMI.
    comm, Qd, ncomm = sfi_methods.cnm_communities(list(nodes), links)
    nmi = 0.0
    # ajuste de lei de potência da distribuição de citações (Clauset–Shalizi–Newman, 2009)
    powerlaw = sfi_methods.powerlaw_fit([nd.get("cited_by", 0) for nd in nodes.values()])
    if N:                                                  # NMI(detectada, eixo)
        import math
        ax = {nid: (nodes[nid].get("axis") or "—") for nid in nodes}
        cx, cy, cxy = {}, {}, {}
        for nid in nodes:
            cx[comm[nid]] = cx.get(comm[nid], 0) + 1
            cy[ax[nid]] = cy.get(ax[nid], 0) + 1
            cxy[(comm[nid], ax[nid])] = cxy.get((comm[nid], ax[nid]), 0) + 1
        H = lambda c: -sum((v / N) * math.log(v / N) for v in c.values())
        info = sum((v / N) * math.log((v / N) / ((cx[a] / N) * (cy[b] / N))) for (a, b), v in cxy.items())
        denom = H(cx) + H(cy)
        nmi = (2 * info / denom) if denom > 0 else 0.0
    return {
        "n": N, "e": E,
        "densidade": round(2 * E / (N * (N - 1)), 3),
        "modularidade": round(Q, 3),
        "modularidade_detectada": round(Qd, 3),
        "n_comunidades": ncomm,
        "nmi": round(nmi, 3),
        "powerlaw": powerlaw,
        "classif": classif,
        "intra": same, "inter": cross,
        "pct_intra": round(100 * same / classif) if classif else 0,
        "pct_inter": round(100 * cross / classif) if classif else 0,
        "pares": pares,
        "polind_cross": polind_cross,
        "by_axis": by_axis,
    }


def rayyan_works_js(works):
    """Serializa as obras da síntese para a triagem (uid estável + SINAIS por critério).

    PR-7: anexa a cada obra os sinais que a reforma de UX usa nos limiares ao vivo —
    prioridade de ponte (bridge_priority), HO-BC (higher_order_bc), nº de eixos e
    é-Brasil — e o ESPAÇO (placeholder) da solidez tripla (estrutural/latente/
    semântico) que a sessão de modelagem futura preenche (aqui fica None)."""
    import re
    prio = data_io.load_data("bridge_priority.json", required=False).get("by_oa_id", {})
    hobc = data_io.load_data("higher_order_bc.json", required=False).get("by_oa_id", {})
    out = []
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", ""))
        oid = e.get("oa_id") or (m.group(1) if m else "")
        uid = e["doi"] or oid or build_rayyan._norm(e["title"])[:60]
        roles = e["roles"]
        pe = prio.get(oid) or {}
        prio_score = pe.get("score", 0) if isinstance(pe, dict) else 0
        out.append({"uid": uid, "oa_id": oid, "title": e["title"], "authors": e["authors"],
                    "year": e["year"], "venue": e["venue"], "abstract": e["abstract"],
                    "doi": e["doi"], "url": e["url"], "type": e.get("type", "GEN"),
                    "axes": sorted(e["axes"]), "roles": sorted(roles), "n_axes": len(e["axes"]),
                    "brasil": ("corpus Brasil (Faganello)" in roles) or ("ponte global×Brasil" in roles),
                    "prioridade": round(float(prio_score or 0), 4),
                    "ho_bc": round(float(hobc.get(oid) or 0), 4),
                    # gancho da solidez tripla (PR-7) — a modelagem preenche os 3 escores
                    "solidez": {"estrutural": None, "latente": None, "semantico": None}})
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



def explorer_network():
    """Rede do explorador: a versão ampliada (network_exploded.json) anotada com a
    comunidade detectada (CNM), o coeficiente de participação e o papel de Guimerà-Amaral."""
    src_name = next((f for f in ("network_4axis.json", "network_exploded.json", "network.json")
                     if data_io.exists(f)), None)
    if src_name is None:                       # PR-2 — sem rede: explorador vazio, não quebra o build
        print("[build_site] aviso: nenhuma rede (network*.json) encontrada — explorador vazio",
              file=sys.stderr)
        return {"nodes": [], "links": []}
    net = data_io.load_data(src_name, required=False, default={"nodes": [], "links": []})
    nodes, links = net.get("nodes", []), net.get("links", [])
    ids = [n["id"] for n in nodes]
    comm, _, _ = sfi_methods.cnm_communities(ids, links)
    P, z = sfi_methods.participation_z(ids, links, comm)
    for n in nodes:
        n["comm"] = comm.get(n["id"], 0)
        n["part"] = round(P.get(n["id"], 0), 2)
        n["role"] = sfi_methods.ga_role(P.get(n["id"], 0), z.get(n["id"], 0))
        if n.get("axis") == "Cyb":            # subtipo: organizacional × geral/fundacional
            t = (n.get("label") or "").lower()
            ger = any(k in t for k in build_rayyan._GERAL_CYB)
            org = any(k in t for k in build_rayyan._ORG_CYB)
            n["sub"] = "geral" if (ger and not org) else "organizacional"

    # afinidade estrutural por cocitação: resolve os nós "sem eixo" pelo eixo
    # dominante da vizinhança (inferência, não vocabulário) e marca as PONTES —
    # nós cuja vizinhança liga ≥2 eixos (conectores de 2ª ordem: por onde as
    # comunidades epistêmicas se tocam).
    axis_of = {n["id"]: (n.get("axis") or "") for n in nodes}
    nbr_axes = {i: {} for i in ids}
    for l in links:
        s, t = l.get("source"), l.get("target")
        if t in nbr_axes and axis_of.get(s):
            nbr_axes[t][axis_of[s]] = nbr_axes[t].get(axis_of[s], 0) + 1
        if s in nbr_axes and axis_of.get(t):
            nbr_axes[s][axis_of[t]] = nbr_axes[s].get(axis_of[t], 0) + 1
    for n in nodes:
        d = nbr_axes.get(n["id"], {})
        n["reach"] = len(d)                       # nº de eixos distintos na vizinhança
        n["bridge"] = len(d) >= 2                 # liga ≥2 eixos → conector de 2ª ordem
        if not n.get("axis") and d:               # "sem eixo": eixo estruturalmente inferido
            n["axis_inf"] = max(d, key=lambda k: d[k])
    return {"nodes": nodes, "links": links}


def main():
    os.makedirs(DADOS, exist_ok=True)
    R = data_io.load_data("scisci_results.json", required=True)  # PR-2 — fonte curada obrigatória

    rayyan = build_rayyan.build(DADOS)
    meta = build_meta(R)
    meta["rayyan_n"] = len(rayyan)
    meta["rayyan_cruz_n"] = sum(1 for e in rayyan if build_rayyan.PONTE in e["roles"])
    meta["rayyan_brasil_n"] = sum(1 for e in rayyan if build_rayyan.BRASIL_ROLE in e["roles"])
    meta["rayyan_org_n"] = sum(1 for e in rayyan if ("cibernética organizacional" in e["roles"])
                               or ("Instrumentos de governo" in e["axes"]) or ("Política industrial" in e["axes"]))
    base = build_js(R) + f"const META={json.dumps(meta, ensure_ascii=False)};\n"
    net_src = data_io.data_path("network.json")
    net = data_io.load_data("network.json", required=False, default={"nodes": [], "links": []})
    js = base + f"const NETWORK={json.dumps(net, ensure_ascii=False)};\n"
    js += f"const NETMETA={json.dumps(net_stats(net), ensure_ascii=False)};\n"
    html = inject_template(js, TEMPLATE)             # index/#rede: núcleo limpo de 69 nós
    html = inject_hypergraph_numbers(html)           # XGI_* tokens ← data/cocitation_hyperedges.json
    html = inject_author_network_numbers(html)       # AUTHORNET_* tokens ← data/author_network.json
    html = inject_brazil_numbers(html)               # BRASIL_* tokens ← data/brazil_expanded.json
    html = inject_brokerage_numbers(html)            # BROK_* tokens ← data/brokerage_roles.json
    index = os.path.join(DOCS, "index.html")
    with open(index, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"site:  {index}  ({os.path.getsize(index)//1024} KB)")

    if os.path.exists(EXPLORER_TPL):                 # explorador: rede ampliada com papéis P/z
        expl_net = explorer_network()
        expl_js = base + f"const NETWORK={json.dumps(expl_net, ensure_ascii=False)};\n"
        expl_js += f"const NETMETA={json.dumps(net_stats(expl_net), ensure_ascii=False)};\n"
        with open(EXPLORER_TPL, encoding="utf-8") as f:
            expl = f.read().replace("__JS_DATA__", expl_js)
        explorer = os.path.join(DOCS, "explorador.html")
        with open(explorer, "w", encoding="utf-8") as f:
            f.write(expl)
        print(f"expl:  {explorer}  ({os.path.getsize(explorer)//1024} KB, {len(expl_net['nodes'])} nós)")

    if os.path.exists(TRIAGEM_TPL):
        # PR-7 — estado da triagem vem do arquivo VERSIONADO (não do navegador):
        # data/rayyan_selection.json (decisões + limiares). Ausente -> {} (UI usa padrões).
        sel = data_io.load_data("rayyan_selection.json", required=False, default={})
        works_js = (f"const RAYYAN_WORKS={json.dumps(rayyan_works_js(rayyan), ensure_ascii=False)};\n"
                    f"const RAYYAN_SELECTION={json.dumps(sel, ensure_ascii=False)};")
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
    expl_src = os.path.join(ROOT, "data", "network_exploded.json")
    if os.path.exists(expl_src):
        shutil.copy(expl_src, os.path.join(DADOS, "rede_explodida.json"))
    ax4_src = os.path.join(ROOT, "data", "network_4axis.json")
    if os.path.exists(ax4_src):
        shutil.copy(ax4_src, os.path.join(DADOS, "rede_4eixos.json"))
    # arquivos auxiliares acessíveis via GH Pages para auditoria dos achados
    for fname in ["rayyan_tags.json", "cocitation_hyperedges.json",
                  "author_network.json", "brokerage_roles.json",
                  "higher_order_bc.json", "brazil_expanded.json",
                  "temporal_cocitation.json", "depth2_corpus.json",
                  "author_snowball_expansion.json", "adjacent_tradition_probes.json"]:
        src = os.path.join(ROOT, "data", fname)
        if os.path.exists(src):
            shutil.copy(src, os.path.join(DADOS, fname))
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    missing = [s for s in SECTIONS if f'id="{s}"' not in html]
    for s in SECTIONS:
        print(f"  {'ok' if s not in missing else 'FALTA'}  #{s}")
    if "__JS_DATA__" in html:
        print("  ERRO: __JS_DATA__ não foi substituído"); return 1
    return 1 if missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
