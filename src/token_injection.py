"""Substituição de tokens vivos no template HTML.

Cada inject_*_numbers lê um JSON em data/ e substitui placeholders no HTML
de saída. Permite reescalar dados (rodar de novo XGI, author_network, etc.)
sem editar o template manualmente.

Tokens cobertos:
  XGI_*       — data/cocitation_hyperedges.json (hipergrafo + null model)
  AUTHORNET_* — data/author_network.json + author_snowball_expansion.json
  BRASIL_*    — data/brazil_expanded.json
  BROK_*      — data/brokerage_roles.json

`inject_all(html, root)` aplica tudo na ordem certa.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def inject_hypergraph_numbers(html, root=ROOT):
    """XGI_* tokens ← data/cocitation_hyperedges.json.

    Tokens cobertos: XGI_N_CITERS, XGI_N_EDGES, XGI_N_CROSS, XGI_PCT_CROSS,
    XGI_Z, XGI_NULL_MEAN_PCT, XGI_NULL_ITER.
    """
    path = os.path.join(root, "data", "cocitation_hyperedges.json")
    if not os.path.exists(path):
        return html
    H = json.load(open(path, encoding="utf-8"))
    null = H.get("null_model", {})
    subs = {
        "XGI_N_CITERS": str(H.get("n_citers", "?")),
        "XGI_N_EDGES":  str(H.get("n_edges", "?")),
        "XGI_N_CROSS":  str(H.get("n_cross_axis_edges", "?")),
        "XGI_PCT_CROSS": f"{(H.get('n_cross_axis_edges', 0)/max(H.get('n_edges',1),1))*100:.0f}",
        "XGI_Z":        f"{null.get('z', 0):.0f}",
        "XGI_NULL_MEAN_PCT": f"{null.get('null_mean', 0)*100:.0f}",
        "XGI_NULL_ITER": str(null.get("n_iter", "?")),
    }
    for tok, val in subs.items():
        html = html.replace(tok, val)
    return html


def inject_author_network_numbers(html, root=ROOT):
    """AUTHORNET_* tokens + tabela top-30 ← data/author_network.json."""
    a_path = os.path.join(root, "data", "author_network.json")
    s_path = os.path.join(root, "data", "author_snowball_expansion.json")
    if not os.path.exists(a_path):
        return html
    A = json.load(open(a_path, encoding="utf-8"))
    snow = {}
    if os.path.exists(s_path):
        snow = json.load(open(s_path, encoding="utf-8")).get("summary", {})
    # render top-30 table
    rows = ['<table class="tbl">',
            '<thead><tr><th>#</th><th>Autor</th><th>score</th>'
            '<th>n_works</th><th>C</th><th>R</th><th>P</th>'
            '<th>h-index</th><th>comm</th></tr></thead><tbody>']
    for i, a in enumerate(A.get("top_cross_axis", [])[:30], 1):
        ax = a["n_per_axis"]
        oid = a.get("oa_id", "")
        link = f'<a href="https://openalex.org/{oid}">{a["display_name"] or oid}</a>'
        rows.append(
            f'<tr><td>{i}</td><td>{link}</td>'
            f'<td>{a["cross_axis_score"]:.3f}</td>'
            f'<td>{a["n_works_total"]}</td>'
            f'<td>{ax.get("Cyb",0)}</td>'
            f'<td>{ax.get("Reg",0)}</td>'
            f'<td>{ax.get("PolInd",0)}</td>'
            f'<td>{a.get("h_index",0)}</td>'
            f'<td>{a.get("community_id",-1)}</td></tr>'
        )
    rows.append('</tbody></table>')
    top_table = "\n".join(rows)
    subs = {
        "AUTHORNET_N_AUTHORS": str(A.get("n_authors", "?")),
        "AUTHORNET_N_CROSS_STRICT": str(A.get("n_cross_axis_strict", "?")),
        "AUTHORNET_N_CROSS_LOOSE": str(A.get("n_cross_axis_loose", "?")),
        "AUTHORNET_N_COMMUNITIES": str(A.get("n_communities", "?")),
        "AUTHORNET_N_SNOWBALL_NEW": str(snow.get("n_new_works", "?")),
        "AUTHORNET_N_SNOWBALL_OVERLAP": str(snow.get("n_overlap", "?")),
        "AUTHORNET_TOP_TABLE": top_table,
    }
    for tok, val in subs.items():
        html = html.replace(tok, val)
    return html


def inject_brazil_numbers(html, root=ROOT):
    """BRASIL_* tokens ← data/brazil_expanded.json (Fase E A.4)."""
    p = os.path.join(root, "data", "brazil_expanded.json")
    if not os.path.exists(p):
        return html
    B = json.load(open(p, encoding="utf-8"))
    subs = {
        "BRASIL_N_FAGANELLO": str(B.get("n_faganello_seeds", "?")),
        "BRASIL_N_RESOLVED": str(B.get("n_resolved_oa", "?")),
        "BRASIL_N_BROAD": str(B.get("n_broad_results", "?")),
        "BRASIL_N_TOTAL": str(B.get("n_brazil_works_total", "?")),
    }
    for tok, val in subs.items():
        html = html.replace(tok, val)
    return html


def inject_brokerage_numbers(html, root=ROOT):
    """BROK_* tokens ← data/brokerage_roles.json (Fase E B.5)."""
    p = os.path.join(root, "data", "brokerage_roles.json")
    if not os.path.exists(p):
        return html
    B = json.load(open(p, encoding="utf-8"))
    rt = (B.get("summary") or {}).get("role_totals", {})
    napr = (B.get("summary") or {}).get("n_authors_per_role", {})
    subs = {
        "BROK_COORD": str(rt.get("coordinator", "?")),
        "BROK_GATE": str(rt.get("gatekeeper", "?")),
        "BROK_REP": str(rt.get("representative", "?")),
        "BROK_LIAISON": str(rt.get("liaison", "?")),
        "BROK_ITIN": str(rt.get("itinerant", "?")),
        "BROK_N_COORD": str(napr.get("coordinator", "?")),
        "BROK_N_GATE": str(napr.get("gatekeeper", "?")),
        "BROK_N_REP": str(napr.get("representative", "?")),
        "BROK_N_LIAISON": str(napr.get("liaison", "?")),
        "BROK_N_ITIN": str(napr.get("itinerant", "?")),
    }
    for tok, val in subs.items():
        html = html.replace(tok, val)
    return html


def inject_solidity_numbers(html, root=ROOT):
    """SOLIDEZ_* tokens + tabela das pontes sólidas ← data/solidity_bridges.json (modelagem)."""
    p = os.path.join(root, "data", "solidity_bridges.json")
    if not os.path.exists(p):
        return html
    S = json.load(open(p, encoding="utf-8"))
    q = S.get("por_quadrante", {})
    solidas = S.get("solidas", [])
    QN = {"costura_ouro": "costura de ouro", "agenda_pesquisa": "agenda de pesquisa",
          "fechamento_trivial": "fechamento trivial", "ruido_quimera": "ruído/quimera"}
    rows = ['<table class="tbl"><thead><tr><th>Membros (OpenAlex)</th><th>Eixos</th>'
            '<th>design z</th><th>latente</th><th>semântico</th><th>quadrante</th></tr></thead><tbody>']
    for c in solidas[:20]:
        mem = " · ".join(f'<a href="https://openalex.org/{m}">{m}</a>' for m in c.get("membros", []))
        rows.append(f'<tr><td>{mem}</td><td>{", ".join(c.get("eixos", []))}</td>'
                    f'<td>{c.get("design_z", "")}</td><td>{c.get("latente", "")}</td>'
                    f'<td>{c.get("semantico", "")}</td><td>{QN.get(c.get("quadrante"), c.get("quadrante", ""))}</td></tr>')
    if not solidas:
        rows.append('<tr><td colspan="6">Nenhuma ponte sólida no recorte atual — resultado válido por desenho.</td></tr>')
    rows.append("</tbody></table>")
    subs = {
        "SOLIDEZ_STATUS": str(S.get("status", "?")),
        "SOLIDEZ_N_CAND": str(S.get("n_candidatas", "?")),
        "SOLIDEZ_N_SOLIDAS": str(S.get("n_solidas", "?")),
        "SOLIDEZ_N_OURO": str(q.get("costura_ouro", 0)),
        "SOLIDEZ_N_AGENDA": str(q.get("agenda_pesquisa", 0)),
        "SOLIDEZ_TABLE": "\n".join(rows),
    }
    for tok, val in subs.items():
        html = html.replace(tok, val)
    return html


def inject_all(html, root=ROOT):
    """Aplica todos os injetores na ordem certa.
    Idempotente: chamadas múltiplas dão o mesmo resultado."""
    html = inject_hypergraph_numbers(html, root)
    html = inject_author_network_numbers(html, root)
    html = inject_brazil_numbers(html, root)
    html = inject_brokerage_numbers(html, root)
    html = inject_solidity_numbers(html, root)
    return html
