"""Cocitação como HIPERGRAFO (ordem superior — contribuição do Landry/XGI).

A rede de cocitação que temos é a projeção PARES. A estrutura real é de ordem
superior: a lista de referências de cada trabalho citante é uma HIPERARESTA — o
conjunto de obras do núcleo citadas JUNTAS. Pontes de ordem superior = hiperarestas
que abarcam ≥2 eixos, e as obras presentes em mais hiperarestas trans-eixo.

Recupera as hiperarestas com um crawl LIMITADO e CACHEADO (oa.py) dos citantes
das obras-semente; analisa com XGI. Roda aqui (xgi+numpy) ou no Colab — o cache
torna reexecutável e resumível.

Saída: data/cocitation_hyperedges.json + relatório. Uso: python src/cocitation_hypergraph.py
"""
import collections
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402
import build_site as bs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
SEEDS = ["W2048086870", "W1566478880", "W2154683088", "W2325487953", "W4244612406",
         "W1601629960", "W2126563689", "W4386803846", "W3124879925", "W1553746973",
         "W4230710385", "W3130930004", "W2063282131"]
CITERS_PER_SEED = 60
AXN = {"Cyb": "cibernética", "Reg": "instrumentos de governo",
       "PolInd": "política industrial", "Cplx": "complexidade"}


def main():
    net = bs.explorer_network()
    axis_of = {n["id"]: (n.get("axis") or n.get("axis_inf") or "") for n in net["nodes"]}
    label_of = {n["id"]: n.get("label") or n["id"] for n in net["nodes"]}
    corpus = set(axis_of)                       # obras do núcleo = "vértices" do hipergrafo

    # hiperarestas = (lista de refs de cada citante) ∩ núcleo, tamanho ≥ 2
    edges, seen_citers = [], set()
    for sid in SEEDS:
        url = (f"{API}/works?filter=cites:{sid}&sort=cited_by_count:desc"
               f"&per-page={CITERS_PER_SEED}&select=id,referenced_works")
        for w in (oa.get(url).get("results") or []):
            cid = (w.get("id") or "").split("/")[-1]
            if cid in seen_citers:
                continue
            seen_citers.add(cid)
            refs = {r.split("/")[-1] for r in (w.get("referenced_works") or [])}
            he = sorted(refs & corpus)
            if len(he) >= 2:
                edges.append(he)
    print(f"citantes únicos: {len(seen_citers)} | hiperarestas (≥2 do núcleo): {len(edges)}")

    import xgi
    H = xgi.Hypergraph(edges)
    sizes = [len(e) for e in edges]
    # hiperarestas que abarcam ≥2 eixos (pontes de ordem superior)
    def edge_axes(e):
        return {axis_of.get(n) for n in e if axis_of.get(n)}
    cross = [e for e in edges if len(edge_axes(e)) >= 2]
    # grau de ordem superior por obra; e em quantas hiperarestas trans-eixo cada obra aparece
    deg = collections.Counter(n for e in edges for n in e)
    cross_deg = collections.Counter(n for e in cross for n in e)
    print(f"XGI: {H.num_nodes} nós, {H.num_edges} hiperarestas | "
          f"tamanho médio {sum(sizes)/max(len(sizes),1):.1f}, máx {max(sizes) if sizes else 0}")
    print(f"hiperarestas trans-eixo (≥2 eixos): {len(cross)} "
          f"({100*len(cross)/max(len(edges),1):.0f}%)")
    print("\nobras em mais hiperarestas TRANS-EIXO (pontes de ordem superior):")
    top = [(n, c) for n, c in cross_deg.most_common(15)]
    for n, c in top:
        ax = AXN.get(axis_of.get(n, ""), "—")
        print(f"   {c:3d}× | {ax:22} | {label_of.get(n, n)[:44]}")

    out = {
        "n_citers": len(seen_citers), "n_edges": len(edges),
        "n_cross_axis_edges": len(cross),
        "mean_size": round(sum(sizes) / max(len(sizes), 1), 2),
        "top_higher_order_bridges": [
            {"oa_id": n, "label": label_of.get(n, n), "axis": AXN.get(axis_of.get(n, ""), ""),
             "cross_axis_hyperedges": c} for n, c in top],
        # mapa completo (oa_id -> nº de hiperarestas trans-eixo) para juntar à prioridade de ponte
        "cross_axis_degree": dict(cross_deg),
        "degree": dict(deg),
    }
    json.dump(out, open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> data/cocitation_hyperedges.json")


if __name__ == "__main__":
    main()
