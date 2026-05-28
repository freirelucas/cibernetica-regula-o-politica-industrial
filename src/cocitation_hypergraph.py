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
import random
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402
import build_site as bs  # noqa: E402
import hypergraph_core as hc  # noqa: E402  (M27 — análises XGI nativas)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
SEEDS = ["W2048086870", "W1566478880", "W2154683088", "W2325487953", "W4244612406",
         "W1601629960", "W2126563689", "W4386803846", "W3124879925", "W1553746973",
         "W4230710385", "W3130930004", "W2063282131"]
CITERS_PER_SEED = int(os.environ.get("CITERS_PER_SEED", "200"))  # max OpenAlex per-page; env-overridable
AXN = {"Cyb": "cibernética", "Reg": "instrumentos de governo",
       "PolInd": "política industrial", "Cplx": "complexidade"}


def null_trans_axis_z(edges, axis_of, n_iter=60, seed=42):
    """Modelo nulo para o hipergrafo: preserva o tamanho de cada hiperaresta e o
    multiset de degrees dos nós (estilo *stub-shuffle*, análogo a Maslov–Sneppen pairwise).
    Compara a fração observada de hiperarestas trans-eixo (≥2 eixos) contra a aleatória —
    declara se o 40% supera o acaso (z). É o teste de significância que faltava ao XGI:
    sem ele o 40% é descritivo, não significância-testado."""
    rng = random.Random(seed)
    sizes = [len(e) for e in edges]
    stubs = [n for e in edges for n in e]  # multiset preservando o degree de cada nó

    def frac_trans(es):
        return sum(1 for e in es if len({axis_of.get(n) for n in e if axis_of.get(n)}) >= 2) / max(len(es), 1)

    obs = frac_trans(edges)
    rand_fracs = []
    for _ in range(n_iter):
        pool = stubs[:]
        rng.shuffle(pool)
        new_edges, i = [], 0
        for s in sizes:
            picked = set()
            # toma stubs evitando duplicatas dentro da hiperaresta; se esgotar, recicla
            while len(picked) < s and i < len(pool) * 4:
                picked.add(pool[i % len(pool)])
                i += 1
            new_edges.append(list(picked))
        rand_fracs.append(frac_trans(new_edges))
    mean = sum(rand_fracs) / max(len(rand_fracs), 1)
    var = sum((x - mean) ** 2 for x in rand_fracs) / max(len(rand_fracs) - 1, 1)
    sd = var ** 0.5
    z = (obs - mean) / sd if sd > 0 else 0.0
    return {"obs": round(obs, 4), "null_mean": round(mean, 4),
            "null_sd": round(sd, 4), "z": round(z, 1), "n_iter": n_iter}


def main():
    net = bs.explorer_network()
    axis_of = {n["id"]: (n.get("axis") or n.get("axis_inf") or "") for n in net["nodes"]}
    label_of = {n["id"]: n.get("label") or n["id"] for n in net["nodes"]}
    corpus = set(axis_of)                       # obras do núcleo = "vértices" do hipergrafo
    comm_of = {n["id"]: n.get("comm", -1) for n in net["nodes"]}   # comunidade CNM (sub-eixo Leiden)

    # hiperarestas = (lista de refs de cada citante) ∩ núcleo, tamanho ≥ 2
    edges, seen_citers = [], set()
    edge_to_citer, seed_of_citer = [], {}    # rastreio por citante p/ ranqueamento do SR (C2)
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
                edge_to_citer.append(cid)
                seed_of_citer[cid] = sid
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

    # modelo nulo: o 40% trans-eixo supera o acaso?
    null = null_trans_axis_z(edges, axis_of, n_iter=60, seed=42)
    print(f"\n== modelo nulo de configuração (stub-shuffle, {null['n_iter']} sorteios) ==")
    print(f"   trans-eixo: observado {100*null['obs']:.1f}% vs nulo {100*null['null_mean']:.1f}% "
          f"± {100*null['null_sd']:.1f}% → z={null['z']:+.1f}")

    print("\nobras em mais hiperarestas TRANS-EIXO (pontes de ordem superior):")
    top = [(n, c) for n, c in cross_deg.most_common(15)]
    for n, c in top:
        ax = AXN.get(axis_of.get(n, ""), "—")
        print(f"   {c:3d}× | {ax:22} | {label_of.get(n, n)[:44]}")

    # ranking de citantes p/ SR (C2 + C3): cada citante = uma hiperaresta;
    # ranqueia por eixos cobertos (3 > 2 > 1), comunidades CNM (sub-eixos Leiden)
    # e tamanho da hiperaresta. As tags entram no Rayyan via higher_order_bridge,
    # e a riqueza dos sub-eixos (comm) preserva o que a manchete "silos" achata.
    citer_summary = []
    for i, he in enumerate(edges):
        cid = edge_to_citer[i]
        axs = sorted(edge_axes(he))
        cms = sorted({comm_of.get(n, -1) for n in he if comm_of.get(n, -1) >= 0})
        citer_summary.append({
            "oa_id": cid, "seed_via": seed_of_citer[cid],
            "n_refs_in_corpus": len(he), "axes": axs, "n_axes": len(axs),
            "communities": cms, "n_communities": len(cms),
        })
    citer_summary.sort(key=lambda r: (-r["n_axes"], -r["n_communities"], -r["n_refs_in_corpus"]))
    top_citers = citer_summary[:30]
    print(f"\n== ranking de citantes p/ SR (top {len(top_citers)} por eixos × comunidades) ==")
    for r in top_citers[:10]:
        print(f"   eixos {r['n_axes']} · comms {r['n_communities']} · refs {r['n_refs_in_corpus']} | {r['oa_id']}")

    # M2+M3 — análises XGI nativas: centralidades + comunidades + null Chung-Lu
    print("\n== análises XGI nativas (M2+M3+M4) ==")
    H_xgi = hc.build_xgi(edges)
    node_cent = hc.native_node_centralities(H_xgi, top_k=30)
    print(f"   h_eigenvector top-3: "
          f"{', '.join(t['oa_id'][:10] for t in node_cent.get('top_h_eigenvector', [])[:3])}")
    print(f"   clique_eigenvector top-3: "
          f"{', '.join(t['oa_id'][:10] for t in node_cent.get('top_clique_eigenvector', [])[:3])}")
    edge_cent = hc.native_edge_centralities(H_xgi, edges_for_remap=edges, top_k=30)
    if edge_cent.get("top_line_vector"):
        print(f"   line_vector (centralidade de hiperarestas) top-3 edge_idx: "
              f"{[t['edge_idx'] for t in edge_cent['top_line_vector'][:3]]}")
    print("   spectral communities (k=3, alinhar com 3 eixos)...")
    xgi_comms = hc.native_communities(H_xgi, n_clusters=3, seed=42)
    nmi = hc.compare_partitions(axis_of, xgi_comms)
    print(f"   NMI(nossos 3 eixos × xgi spectral): {nmi.get('nmi')} (n_common={nmi.get('n_common')})")

    # null Chung-Lu (M4 — preserva degrees independentes, mais informativo que stub-shuffle)
    print("   null Chung-Lu (30 sorteios)...")
    null_cl = hc.null_chung_lu_z(edges, axis_of, n_iter=30, seed=42)
    print(f"   Chung-Lu: obs={null_cl.get('obs')}  null_mean={null_cl.get('null_mean')}  z={null_cl.get('z')}")

    out = {
        "n_citers": len(seen_citers), "n_edges": len(edges),
        "n_cross_axis_edges": len(cross),
        "mean_size": round(sum(sizes) / max(len(sizes), 1), 2),
        # significância: stub-shuffle preserva degrees + sizes; 60 sorteios
        "null_model": null,
        # M4 — null Chung-Lu alternativo (preserva degrees independentes)
        "null_model_chung_lu": null_cl,
        "top_higher_order_bridges": [
            {"oa_id": n, "label": label_of.get(n, n), "axis": AXN.get(axis_of.get(n, ""), ""),
             "cross_axis_hyperedges": c} for n, c in top],
        # candidatos à SR (C2): citantes ranqueados por cobertura (eixos × sub-eixos × refs)
        "top_citers_for_sr": top_citers,
        "citer_summary": citer_summary,
        # mapa completo (oa_id -> nº de hiperarestas trans-eixo) para juntar à prioridade de ponte
        "cross_axis_degree": dict(cross_deg),
        "degree": dict(deg),
        # M1 — persistência: hiperarestas + edge_to_citer + axis_of permite TODA
        # análise futura sem rerodar o crawler.
        "hyperedges": edges,
        "edge_to_citer": edge_to_citer,
        "axis_of": axis_of,
        # M2 — centralidades XGI nativas (eigen no hipergrafo + clique expansion)
        "node_centralities": {
            "top_h_eigenvector": node_cent.get("top_h_eigenvector", [])[:30],
            "top_clique_eigenvector": node_cent.get("top_clique_eigenvector", [])[:30],
        },
        "edge_centralities": {
            "top_line_vector": edge_cent.get("top_line_vector", [])[:30],
        },
        # M3 — comunidades espectrais nativas em hipergrafo + comparação com nossos eixos
        "xgi_communities": xgi_comms if "_error" not in xgi_comms else None,
        "xgi_communities_error": xgi_comms.get("_error") if "_error" in xgi_comms else None,
        "nmi_eixos_vs_xgi_communities": nmi,
    }
    json.dump(out, open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"), "w",
                        encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\n-> data/cocitation_hyperedges.json")


if __name__ == "__main__":
    main()
