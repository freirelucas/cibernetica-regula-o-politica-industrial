"""Mapa de co-palavra do campo digital — MÓDULO OPCIONAL (networkx + matplotlib).

O núcleo (`src/run_all.py --from attribute`) não depende deste arquivo. Ele existe porque
a estrutura temática de um campo é a pergunta que **não** passa pela atribuição de
diretoria: a rede de co-palavra liga termos que aparecem na mesma obra, e portanto não
herda a circularidade do METODO §5. A lotação das pessoas entra só na cor dos nós, depois
que a estrutura já está desenhada.

Método (análise de co-palavra, instrumento corrente em bibliometria):
  nós    = termos de indexação do subcorpus com ≥ MIN_DF obras;
  laços  = co-ocorrência na mesma obra, pesada pelo **índice de equivalência** de Callon,
           e = c²/(c_i·c_j), que normaliza pela frequência dos dois termos e evita que
           termo frequente se ligue a todo mundo;
  grupos = modularidade gulosa sobre o peso de equivalência;
  cor    = lado que mais usa o termo (DIEST, DISET ou nenhum dos dois).

Uso:
    python src/coword.py --mapa     → docs/fig_coword_digital.png, data/coword_digital.json
"""
import collections
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, load_json, norm, save_json  # noqa: E402
from digital import hits_by_uuid, split_terms  # noqa: E402

MIN_DF = 4          # termo com menos de 4 obras não entra no mapa
MIN_CO = 2          # laço precisa de ao menos 2 obras em comum
MIN_EQUIV = 0.05    # índice de equivalência de Callon
MODE = "amplo"      # recorte: no estrito a DIEST tem 9 obras e o mapa fica unilateral
STOP = {"brasil", "ipea", ""}


def build(mode=MODE):
    lex = load_json("digital_lexicon.json")
    terms = [x["term"] for x in lex["lexico"]]
    tagged = load_json("items_tagged.json")
    authors = load_json("authors.json")
    dir_of = {a: v["diretoria"] for a, v in authors.items() if v["diretoria"]}
    hits = hits_by_uuid(terms, tagged, mode)
    win = [it for it in tagged if it["uuid"] in hits and it["year"] and it["year"] >= 2010]

    docs, sides = [], []
    for it in win:
        ts = {norm(t) for t in split_terms(it.get("vcipea", []) + it.get("keywords", []))}
        ts = {t for t in ts if t and t not in STOP and len(t) > 2}
        if not ts:
            continue
        s = {d for d in FOCUS if d in it["dirs"] or any(dir_of.get(a) == d for a in it["authors"])}
        docs.append(ts)
        sides.append(s)

    df = collections.Counter()
    for ts in docs:
        df.update(ts)
    keep = {t for t, n in df.items() if n >= MIN_DF}
    co = collections.Counter()
    for ts in docs:
        for a, b in itertools.combinations(sorted(ts & keep), 2):
            co[(a, b)] += 1
    edges = [(a, b, c * c / (df[a] * df[b]), c) for (a, b), c in co.items()
             if c >= MIN_CO and c * c / (df[a] * df[b]) >= MIN_EQUIV]
    use = collections.defaultdict(collections.Counter)
    for ts, s in zip(docs, sides):
        for t in ts & keep:
            for d in s:
                use[t][d] += 1
            if not s:
                use[t]["nenhuma"] += 1
    return {"df": df, "keep": keep, "edges": edges, "use": use,
            "n_obras": len(docs), "mode": mode}


def graph(b):
    import networkx as nx
    G = nx.Graph()
    for t in b["keep"]:
        G.add_node(t, n=b["df"][t])
    for a, c, e, n in b["edges"]:
        G.add_edge(a, c, weight=e, co=n)
    G.remove_nodes_from([n for n, d in G.degree() if d == 0])
    comms = list(nx.community.greedy_modularity_communities(G, weight="weight"))
    return G, comms


def dominant(use_t):
    d, s = use_t.get("DIEST", 0), use_t.get("DISET", 0)
    if d == 0 and s == 0:
        return "nenhuma"
    return "DIEST" if d > s else ("DISET" if s > d else "empate")


def export(b, G, comms):
    rows = []
    for i, c in enumerate(comms):
        for t in c:
            rows.append({"termo": t, "grupo": i + 1, "obras": b["df"][t],
                         "DIEST": b["use"][t].get("DIEST", 0),
                         "DISET": b["use"][t].get("DISET", 0),
                         "sem_membro": b["use"][t].get("nenhuma", 0),
                         "dominante": dominant(b["use"][t])})
    grupos = []
    for i, c in enumerate(comms):
        nd = sum(b["use"][t].get("DIEST", 0) for t in c)
        ns = sum(b["use"][t].get("DISET", 0) for t in c)
        grupos.append({"grupo": i + 1, "n_termos": len(c),
                       "usos_DIEST": nd, "usos_DISET": ns,
                       "equilibrio": round(2 * min(nd, ns) / (nd + ns), 3) if nd + ns else 0.0,
                       "termos": sorted(c, key=lambda t: -b["df"][t])})
    out = {"recorte": b["mode"], "n_obras": b["n_obras"], "parametros":
           {"MIN_DF": MIN_DF, "MIN_CO": MIN_CO, "MIN_EQUIV": MIN_EQUIV},
           "n_nos": G.number_of_nodes(), "n_lacos": G.number_of_edges(),
           "grupos": grupos, "termos": sorted(rows, key=lambda r: (r["grupo"], -r["obras"]))}
    save_json("coword_digital.json", out)
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--mapa" not in argv:
        print(__doc__, file=sys.stderr)
        return
    b = build()
    G, comms = graph(b)
    out = export(b, G, comms)
    print(f"[{b['mode']}] {b['n_obras']} obras · {out['n_nos']} nós · {out['n_lacos']} laços · "
          f"{len(comms)} grupos", file=sys.stderr)
    for gp in out["grupos"][:8]:
        print(f"  G{gp['grupo']}: {gp['n_termos']} termos, DIEST {gp['usos_DIEST']} / "
              f"DISET {gp['usos_DISET']} (equilíbrio {gp['equilibrio']}) — "
              f"{', '.join(gp['termos'][:5])}", file=sys.stderr)


if __name__ == "__main__":
    main()
