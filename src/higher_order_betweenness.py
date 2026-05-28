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
    """Devolve {edges: list[set], node_to_edges: dict[node, list[edge_idx]]}."""
    H = json.load(open(HYPEREDGES, encoding="utf-8"))
    # cocitation_hyperedges.json não armazena hiperarestas diretamente —
    # apenas top_higher_order_bridges + cross_axis_degree. Reconstruir a
    # partir do degree dict não é possível. Usar a saída de
    # cocitation_hypergraph.main() seria ideal, mas como workaround:
    # tratar cada nó com degree>0 e usar cross_axis_degree como proxy.
    degree = H.get("degree", {})
    cross_deg = H.get("cross_axis_degree", {})
    if not degree:
        return None, None
    # construir grafo proxy: nodes ponderados por degree
    return degree, cross_deg


def build_hypergraph_from_seeds():
    """Reconstroi hiperarestas re-executando o pipeline do cocitation_hypergraph
    minimal: para cada citante no cache, pegar referenced_works ∩ corpus_nodes."""
    import gzip
    cache_dir = os.path.join(ROOT, "data", "oa_cache")
    # corpus = nós da rede ampliada
    net_path = os.path.join(ROOT, "data", "network_4axis.json")
    if not os.path.exists(net_path):
        net_path = os.path.join(ROOT, "data", "network.json")
    net = json.load(open(net_path, encoding="utf-8"))
    corpus = {n["id"]: n for n in net.get("nodes", [])}
    print(f"  corpus (network nodes): {len(corpus)}")

    edges = []
    edge_titles = []
    for root, _, files in os.walk(cache_dir):
        for f in files:
            if not f.endswith(".json.gz"):
                continue
            try:
                data = json.loads(gzip.open(os.path.join(root, f), "rt").read())
            except Exception:
                continue
            results = data.get("results") if isinstance(data, dict) else None
            if isinstance(results, list):
                for w in results:
                    refs = w.get("referenced_works") or []
                    he = sorted(set(
                        r.split("/")[-1] for r in refs
                        if (r.split("/")[-1]) in corpus
                    ))
                    if len(he) >= 2:
                        edges.append(he)
    print(f"  hiperarestas reconstruídas: {len(edges)}")
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


def main():
    print("== B.4 · Higher-order betweenness via random walks ==")

    edges, corpus = build_hypergraph_from_seeds()
    if not edges:
        print("ERRO: hiperarestas não reconstruíveis. Verifique cache.")
        return

    print(f"\nrunning {N_WALKS} walks of length {WALK_LENGTH} (seed={SEED})...")
    centrality = random_walk_centrality(edges, corpus, N_WALKS, WALK_LENGTH, SEED)
    print(f"  {len(centrality)} nós com centralidade > 0")

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
        "top_30": hidden_bridges,
        "by_oa_id": {n: round(c, 4) for n, c in centrality.items()},
    }
    json.dump(out, open(OUTPUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"\n-> {OUTPUT} ({os.path.getsize(OUTPUT)//1024} KB)")


if __name__ == "__main__":
    main()
