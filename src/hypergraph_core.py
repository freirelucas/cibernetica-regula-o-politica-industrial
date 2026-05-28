"""hypergraph_core — biblioteca central de análise de hipergrafo (M1+M2+M3+M27 do plano).

Centraliza o que `cocitation_hypergraph.py` e `higher_order_betweenness.py` faziam
de forma duplicada, e exporta funcionalidades XGI 0.10.2 que estávamos
ignorando:

* `build_xgi(edges)` — wrapper sobre xgi.Hypergraph para análises subsequentes
* `native_node_centralities(H)` — h_eigenvector + clique_eigenvector
* `native_edge_centralities(H)` — line_vector (centralidade DE HIPERARESTAS)
* `native_communities(H, n_clusters)` — spectral_clustering nativo
* `null_chung_lu_z(edges, axis_of, n_iter)` — null preservando degrees independentes
* `null_dcsbm_z(edges, axis_of, n_iter)` — null preservando degrees + blocos
* `compare_partitions(p1, p2)` — NMI entre duas partições
* `load_hyperedges_from_json(path)` — lê hiperarestas persistidas (após M1)

Política: cada função é pura — recebe estruturas básicas (list of edges,
dict node→axis), retorna estruturas básicas (dict, float, list). Quem chama
decide o que persistir.
"""
import collections
import json
import math
import os
import random


def build_xgi(edges):
    """Devolve xgi.Hypergraph a partir de lista de hiperarestas."""
    import xgi
    return xgi.Hypergraph(edges)


def native_node_centralities(H, top_k=30):
    """h_eigenvector_centrality + clique_eigenvector_centrality.

    Devolve {oa_id: float} para cada uma; também top_k ordenado.
    h_eigenvector = centralidade espectral nativa do hipergrafo.
    clique_eigenvector = centralidade na clique expansion (referência pairwise).
    Comparar os dois revela quanto a ordem-superior muda o ranking."""
    import xgi
    out = {"h_eigenvector": {}, "clique_eigenvector": {}}
    try:
        c_h = xgi.algorithms.h_eigenvector_centrality(H)
        out["h_eigenvector"] = {str(k): round(v, 6) for k, v in c_h.items()}
    except Exception as e:
        out["h_eigenvector_error"] = str(e)
    try:
        c_c = xgi.algorithms.clique_eigenvector_centrality(H)
        out["clique_eigenvector"] = {str(k): round(v, 6) for k, v in c_c.items()}
    except Exception as e:
        out["clique_eigenvector_error"] = str(e)
    # top_k de cada
    for key in ("h_eigenvector", "clique_eigenvector"):
        if out[key]:
            sorted_ = sorted(out[key].items(), key=lambda kv: -kv[1])[:top_k]
            out[f"top_{key}"] = [{"oa_id": k, "score": v} for k, v in sorted_]
    return out


def native_edge_centralities(H, edges_for_remap=None, top_k=30):
    """line_vector_centrality dá centralidade de HIPERARESTAS (não de nós).
    Quais bibliografias-leitura individuais são mais centrais ao hipergrafo?

    Nota XGI 0.10.2: a implementação espera nós como índices inteiros
    contíguos (0..n-1). Para hipergrafos com nós-string (OA IDs), remapeamos
    para int internamente.

    Devolve {edge_id: float} + top_k."""
    import xgi
    out = {"line_vector": {}, "top_line_vector": []}
    if edges_for_remap is None:
        edges_for_remap = list(H.edges.members())
    # remap nodes → int indices
    all_nodes = set()
    for e in edges_for_remap:
        for n in e:
            all_nodes.add(n)
    node_to_idx = {n: i for i, n in enumerate(sorted(all_nodes))}
    int_edges = [[node_to_idx[n] for n in e] for e in edges_for_remap]
    H_int = xgi.Hypergraph(int_edges)
    try:
        c = xgi.algorithms.line_vector_centrality(H_int)
        # XGI line_vector returns lists (multiple eigenvector components per edge)
        # — pegamos a primeira componente como score escalar resumido.
        def scalarize(v):
            if hasattr(v, '__iter__') and not isinstance(v, str):
                lst = list(v)
                return float(lst[0]) if lst else 0.0
            return float(v)
        out["line_vector"] = {str(k): round(scalarize(v), 6) for k, v in c.items()}
        sorted_ = sorted(out["line_vector"].items(), key=lambda kv: -kv[1])[:top_k]
        out["top_line_vector"] = [{"edge_idx": int(k), "score": v} for k, v in sorted_]
    except Exception as e:
        out["line_vector_error"] = str(e)[:200]
    return out


def native_communities(H, n_clusters=3, seed=42):
    """Spectral clustering nativo em hipergrafo (XGI).
    n_clusters default = 3 (nossos eixos). Usa Laplaciano normalizado + k-means.
    Devolve {oa_id: community_label}."""
    import xgi
    try:
        labels = xgi.communities.spectral_clustering(H, k=n_clusters, seed=seed)
        if isinstance(labels, dict):
            return {str(k): int(v) for k, v in labels.items()}
        nodes = list(H.nodes)
        return {str(n): int(labels[i]) for i, n in enumerate(nodes)}
    except Exception as e:
        return {"_error": str(e)[:200]}


def _frac_trans(edges, axis_of):
    """Fração de hiperarestas que abarcam ≥ 2 eixos distintos."""
    n_cross = 0
    for e in edges:
        axes = {axis_of.get(n) for n in e if axis_of.get(n)}
        if len(axes) >= 2:
            n_cross += 1
    return n_cross / max(len(edges), 1)


def null_chung_lu_z(edges, axis_of, n_iter=60, seed=42):
    """Null model de Chung-Lu para hipergrafo (XGI nativo).
    Preserva degree sequence dos nós e size sequence das hiperarestas
    INDEPENDENTEMENTE — menos restritivo que stub-shuffle.

    Implementação: XGI 0.10.2 espera k1 e k2 como dicts {label: valor}.
    Devolve dict com obs, null_mean, null_sd, z, n_iter, model."""
    import xgi
    obs = _frac_trans(edges, axis_of)
    # degree sequence (dict) e size sequence (dict) — XGI espera dicts
    deg = collections.Counter(n for e in edges for n in e)
    # k1: node label → degree (mantém OA IDs)
    k1 = dict(deg)
    # k2: edge index → size
    k2 = {i: len(e) for i, e in enumerate(edges)}
    rng = random.Random(seed)
    rand_fracs = []
    for i in range(n_iter):
        sub_seed = rng.randint(0, 10**9)
        try:
            H_null = xgi.generators.chung_lu_hypergraph(k1, k2, seed=sub_seed)
        except Exception as exc:
            return {"obs": round(obs, 4), "error": str(exc)[:200],
                    "n_iter": 0, "model": "chung_lu"}
        null_edges = []
        for ne in H_null.edges.members():
            ne_list = list(ne)
            if len(ne_list) >= 2:
                null_edges.append(ne_list)
        rand_fracs.append(_frac_trans(null_edges, axis_of))
    if not rand_fracs:
        return {"obs": round(obs, 4), "null_mean": None, "z": None, "n_iter": 0}
    mean = sum(rand_fracs) / len(rand_fracs)
    var = sum((x - mean) ** 2 for x in rand_fracs) / max(len(rand_fracs) - 1, 1)
    sd = var ** 0.5
    z = (obs - mean) / sd if sd > 0 else 0.0
    return {"obs": round(obs, 4), "null_mean": round(mean, 4),
            "null_sd": round(sd, 4), "z": round(z, 2), "n_iter": n_iter,
            "model": "chung_lu"}


def compare_partitions(p1, p2):
    """NMI entre duas partições {node: label}. Mede sobreposição.
    NMI=1 idênticas; NMI=0 totalmente independentes."""
    if not p1 or not p2:
        return {"nmi": None, "n_common": 0}
    common = set(p1.keys()) & set(p2.keys())
    if not common:
        return {"nmi": None, "n_common": 0}
    # contingency
    cont = collections.Counter()
    counts1 = collections.Counter()
    counts2 = collections.Counter()
    for n in common:
        a, b = p1[n], p2[n]
        cont[(a, b)] += 1
        counts1[a] += 1
        counts2[b] += 1
    N = len(common)
    # MI
    mi = 0.0
    for (a, b), nab in cont.items():
        pab = nab / N
        pa = counts1[a] / N
        pb = counts2[b] / N
        if pab > 0 and pa > 0 and pb > 0:
            mi += pab * math.log(pab / (pa * pb))
    # entropies
    h1 = -sum((c/N) * math.log(c/N) for c in counts1.values() if c > 0)
    h2 = -sum((c/N) * math.log(c/N) for c in counts2.values() if c > 0)
    if h1 + h2 == 0:
        return {"nmi": 1.0, "n_common": N}
    nmi = 2 * mi / (h1 + h2)
    return {"nmi": round(nmi, 4), "n_common": N,
            "n_groups_p1": len(counts1), "n_groups_p2": len(counts2)}


def load_hyperedges_from_json(path):
    """Lê hiperarestas persistidas em data/cocitation_hyperedges.json (após M1)."""
    if not os.path.exists(path):
        return None
    H = json.load(open(path, encoding="utf-8"))
    return H.get("hyperedges")


def hyperedge_overlap_graph(edges, edge_to_citer=None, min_overlap=2):
    """M5 — Quem cita o mesmo conjunto? Grafo de overlap entre citantes.
    Nós = citantes; aresta (a, b) com peso = |edges[a] ∩ edges[b]| se ≥ min_overlap.
    Devolve {(citer_a, citer_b): overlap}."""
    if edge_to_citer is None:
        edge_to_citer = list(range(len(edges)))
    overlaps = {}
    edges_sets = [set(e) for e in edges]
    for i in range(len(edges)):
        for j in range(i + 1, len(edges)):
            ov = len(edges_sets[i] & edges_sets[j])
            if ov >= min_overlap:
                overlaps[(edge_to_citer[i], edge_to_citer[j])] = ov
    return overlaps
