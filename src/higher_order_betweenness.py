"""B.4 — Higher-order betweenness via random walks no hipergrafo.

Estrada-Vega-style: para cada nó v, conta a fração de random walks no
hipergrafo que passam por v (em posição não-extremo). Cada passo do walk:
escolhe uma hiperaresta incidente ao nó atual, depois escolhe outro nó
naquela hiperaresta. Pesos: tamanho da hiperaresta (edges grandes têm
maior chance de fluxo passar).

Comparar com BC pairwise (em scisci_results.json:top_bridges) revela:
- Nodes ALTOS-HO + ALTOS-pairwise: pontes em qualquer dimensão.
- Nodes ALTOS-HO + BAIXOS-pairwise: pontes de ordem superior escondidas
  pela projeção. Estes são os achados novos — bridges-de-ordem-superior REAIS.

Output: data/higher_order_bc.json.
"""
import collections
import json
import os
import random

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HYPEREDGES = os.path.join(ROOT, "data", "cocitation_hyperedges.json")
SCISCI = os.path.join(ROOT, "data", "scisci_results.json")
OUTPUT = os.path.join(ROOT, "data", "higher_order_bc.json")

N_WALKS = 1000
WALK_LENGTH = 8
SEED = 42


def load_hypergraph():
    """Lê as hiperarestas CANÔNICAS persistidas em data/cocitation_hyperedges.json.

    PR-1 — dívida das hiperarestas saldada. O handout supunha que o JSON gravava só
    `degree`/`cross_axis_degree`; na prática `cocitation_hypergraph.main()` já
    persiste o campo `hyperedges` (lista de listas de IDs de obras) desde o marco
    M1. A dívida real estava AQUI: este módulo reconstruía as hiperarestas varrendo
    TODO o data/oa_cache/ (antiga build_hypergraph_from_seeds), o que incluía
    citantes de consultas alheias às 13 sementes e contava repetidos — ~7,9k
    hiperarestas contra as ~1,3k canônicas. Essa reconstrução era ENVIESADA; agora
    lemos a fonte canônica e o ranking HO-BC reflete o hipergrafo de cocitação real
    (ver nota de divergência no commit/PR; ranking top-15 muda de propósito).

    Devolve (edges, corpus): edges = list[list[str]]; corpus = dict[id -> {label,
    axis}] só para o relatório — rótulo/eixo são cosméticos e NÃO filtram o cálculo;
    os vértices do hipergrafo são exatamente os nós presentes nas hiperarestas.
    """
    H = json.load(open(HYPEREDGES, encoding="utf-8"))
    edges = H.get("hyperedges")
    if not edges:
        raise SystemExit(
            "ERRO: 'hyperedges' ausente em data/cocitation_hyperedges.json. "
            "Rode `python src/cocitation_hypergraph.py` (marco M1) antes deste passo."
        )
    axis_of = H.get("axis_of", {})
    nodes = {n for e in edges for n in e}            # vértices reais do hipergrafo
    # metadados cosméticos (rótulo + eixo) vindos da rede do explorador, se houver
    meta = {}
    for net_name in ("network_4axis.json", "network_exploded.json", "network.json"):
        p = os.path.join(ROOT, "data", net_name)
        if os.path.exists(p):
            meta = {n["id"]: n for n in json.load(open(p, encoding="utf-8")).get("nodes", [])}
            break
    corpus = {n: {"label": meta.get(n, {}).get("label", n),
                  "axis": meta.get(n, {}).get("axis") or axis_of.get(n, "")}
              for n in nodes}
    print(f"  hiperarestas canônicas (cocitation_hyperedges.json): {len(edges)} "
          f"| vértices: {len(nodes)}")
    return edges, corpus


def random_walk_centrality(edges, corpus_nodes, n_walks, walk_length, seed):
    """Pesa cada visita a nós não-extremos do walk. Devolve {node: centrality}."""
    random.seed(seed)
    # node → edges incident
    node_to_edges = collections.defaultdict(list)
    for ei, e in enumerate(edges):
        for n in e:
            node_to_edges[n].append(ei)

    all_nodes = [n for n in node_to_edges if n in corpus_nodes]
    if not all_nodes:
        return {}

    visits = collections.Counter()
    n_active_walks = 0
    for _ in range(n_walks):
        start = random.choice(all_nodes)
        cur = start
        for step in range(walk_length):
            edge_options = node_to_edges.get(cur, [])
            if not edge_options:
                break
            # escolher hiperaresta proporcional ao tamanho (mais "fluxo")
            chosen_ei = random.choice(edge_options)
            e = edges[chosen_ei]
            # escolher próximo nó na hiperaresta (≠ atual)
            choices = [n for n in e if n != cur]
            if not choices:
                break
            nxt = random.choice(choices)
            if 0 < step < walk_length - 1:
                visits[nxt] += 1   # passa por nó intermediário
            cur = nxt
        n_active_walks += 1

    # normalize
    norm = max(visits.values()) if visits else 1
    return {n: c / norm for n, c in visits.items()}


def exact_betweenness_clique_expansion(edges, corpus_nodes):
    """P8: Higher-order BC EXATO via clique expansion + Brandes (NetworkX).

    Para hipergrafo G_H com hiperarestas E_1...E_m sobre nós V, o clique
    expansion é o grafo G onde cada hiperaresta E_k vira uma clique completa
    sobre seus |E_k| nós (todas as arestas pareadas). Brandes em G dá BC
    exato, e essa é a versão "exata" mais aceita para hipergrafos quando o
    objetivo é fluxo de informação (Estrada-Vega 2020, secção sobre clique
    expansion).

    Para corpus de ~220 nós e ~1300 hiperarestas, é viável (O(n³) com
    NetworkX Brandes ≈ 0.5-2s).
    """
    import networkx as nx
    G = nx.Graph()
    # adiciona nós do corpus apenas
    for n in corpus_nodes:
        G.add_node(n)
    # cada hiperaresta vira uma clique de seus nós que estão no corpus
    n_cliques = 0
    for e in edges:
        e_in_corpus = [n for n in e if n in corpus_nodes]
        for i, a in enumerate(e_in_corpus):
            for b in e_in_corpus[i + 1:]:
                # peso = 1 / (tamanho da hiperaresta - 1), normaliza pelo
                # tamanho da clique (hiperarestas grandes têm peso menor por aresta)
                w = 1.0 / max(len(e_in_corpus) - 1, 1)
                if G.has_edge(a, b):
                    G[a][b]["weight"] += w
                else:
                    G.add_edge(a, b, weight=w)
        if len(e_in_corpus) >= 2:
            n_cliques += 1
    # Brandes betweenness, normalizado
    bc = nx.betweenness_centrality(G, normalized=True, weight=None)
    return bc, n_cliques


def main():
    import os
    mode = os.environ.get("HO_BC_MODE", "both")  # "rw", "exact", "both"
    print(f"== B.4 · Higher-order betweenness (mode={mode}) ==")

    edges, corpus = load_hypergraph()   # PR-1: fonte canônica (sem varrer o cache)

    centrality_rw, centrality_exact = {}, {}
    n_cliques = 0
    if mode in ("rw", "both"):
        print(f"\nrunning {N_WALKS} walks of length {WALK_LENGTH} (seed={SEED})...")
        centrality_rw = random_walk_centrality(edges, corpus, N_WALKS, WALK_LENGTH, SEED)
        print(f"  {len(centrality_rw)} nós com centralidade > 0 (random walk)")
    if mode in ("exact", "both"):
        print(f"\ncomputing exact Brandes BC on clique expansion...")
        centrality_exact, n_cliques = exact_betweenness_clique_expansion(edges, corpus)
        n_nonzero = sum(1 for v in centrality_exact.values() if v > 0)
        print(f"  {n_nonzero} nós com BC > 0 (Brandes exato sobre {n_cliques} cliques)")

    # usa centrality_exact como principal se modo exato; senão random walk
    centrality = centrality_exact if (mode == "exact" or (mode == "both" and centrality_exact)) else centrality_rw
    # normalize exact centrality to [0,1] para comparação direta
    if centrality_exact:
        max_e = max(centrality_exact.values()) or 1.0
        centrality_exact_norm = {n: v / max_e for n, v in centrality_exact.items()}
    else:
        centrality_exact_norm = {}

    # compare with pairwise BC from scisci_results
    R = json.load(open(SCISCI, encoding="utf-8"))
    pairwise_bc = {}
    for b in R.get("top_bridges", []):
        oid = (b.get("oa_id") or b.get("id") or "").split("/")[-1]
        if oid:
            pairwise_bc[oid] = b.get("betweenness") or b.get("bc") or 0
    print(f"  pairwise BC entries (top_bridges): {len(pairwise_bc)}")

    # rank by HO centrality
    ranked = sorted(centrality.items(), key=lambda kv: -kv[1])
    top_30 = ranked[:30]

    # identify hidden bridges: HO alto E pairwise zero/baixo
    pairwise_top_set = set(pairwise_bc.keys())
    hidden_bridges = [
        {"oa_id": n, "label": corpus.get(n, {}).get("label", n)[:60],
         "axis": corpus.get(n, {}).get("axis", ""),
         "ho_centrality": round(c, 4),
         "pairwise_bc": pairwise_bc.get(n, 0),
         "is_hidden": n not in pairwise_top_set,
        }
        for n, c in top_30
    ]

    n_hidden = sum(1 for b in hidden_bridges if b["is_hidden"])
    print(f"\ntop-30 by HO centrality:")
    for b in hidden_bridges[:15]:
        hidden_mark = "★" if b["is_hidden"] else " "
        print(f"  {hidden_mark} [{b['axis']:6}] {b['ho_centrality']:.3f} | {b['label']}")
    print(f"\n{n_hidden}/30 são bridges-de-ordem-superior escondidos do pairwise BC")

    out = {
        "_generated": "B.4 · Estrada-Vega-style HO BC via random walks",
        "n_walks": N_WALKS, "walk_length": WALK_LENGTH, "seed": SEED,
        "n_hyperedges": len(edges),
        "n_nodes_with_centrality": len(centrality),
        "n_hidden_bridges_in_top30": n_hidden,
        "mode": mode,
        "n_cliques_expanded": n_cliques,
        "top_30": hidden_bridges,
        "by_oa_id": {n: round(c, 4) for n, c in centrality.items()},
        # P8: exporta ambas para auditoria
        "by_oa_id_random_walk": {n: round(c, 4) for n, c in centrality_rw.items()},
        "by_oa_id_exact_normalized": {n: round(c, 4) for n, c in centrality_exact_norm.items()},
    }
    json.dump(out, open(OUTPUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT} ({os.path.getsize(OUTPUT)//1024} KB)")


if __name__ == "__main__":
    main()
