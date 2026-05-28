"""Higiene de integridade: remove das fontes de dados todo id OpenAlex que NÃO
resolve (HTTP 404) — verificado por lote contra a API. São referências penduradas
do grafo de cocitação (ids citados nunca enriquecidos, depois deletados/fundidos
pelo OpenAlex) e alguns ids corrompidos/sintéticos. Mantém apenas dados reais.

Lista DEAD obtida em src/clean_dead_ids.py (verificação por lote, maio/2026).
Reexecutável: tira nós + arestas incidentes das redes e limpa cross_brasil.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")

# 13 ids que retornam 404 no OpenAlex (verificados por lote). 11 são "thin"
# (referência pendurada, sem título); W7066150168/W7074557132 são duplicatas
# corrompidas de obras-semente reais (ids impossíveis, > W4.4 bi).
DEAD = {
    "W1601128533", "W1606189865", "W1984686904", "W2091579301", "W2096775067",
    "W2771086427", "W2993383518", "W4206762723", "W4255725700", "W4285719527",
    "W6637432206", "W7066150168", "W7074557132",
}

# Nós que RESOLVEM no OpenAlex mas não são obras: registros-agregados do próprio
# periódico (o nome da revista vira "obra" e aparece como hub falso — ex.: a
# "American Economic Review" com grau 16). Não representam um trabalho citável,
# distorcem a centralidade — podados como não-obras.
NON_WORK = {
    "W1513281941",  # American Economic Review (agregado)
    "W1517701247",  # Harvard Business Review (agregado)
    "W4297081765",  # Harvard Business Review (agregado, variante)
}

REMOVE = DEAD | NON_WORK

NETWORKS = ["network.json", "network_4axis.json", "network_exploded.json", "network_cplx.json"]


def clean_network(path):
    d = json.load(open(path, encoding="utf-8"))
    n0, e0 = len(d["nodes"]), len(d["links"])
    d["nodes"] = [x for x in d["nodes"] if x.get("id") not in REMOVE]
    d["links"] = [l for l in d["links"]
                  if l.get("source") not in REMOVE and l.get("target") not in REMOVE]
    json.dump(d, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return n0, len(d["nodes"]), e0, len(d["links"])


def clean_cross(path):
    c = json.load(open(path, encoding="utf-8"))
    g0 = len(c.get("global", []))
    c["global"] = [g for g in c.get("global", []) if g not in DEAD]
    c["global_labels"] = {k: v for k, v in c.get("global_labels", {}).items() if k not in DEAD}
    kept, dropped = [], []
    for b in c.get("brasil", []):
        cita = [x for x in b.get("cita", []) if x not in DEAD]
        if cita:                       # ainda faz ponte com obra global REAL
            b["cita"] = cita
            kept.append(b)
        else:                          # única ponte era a fantasma → não é cruzamento real
            dropped.append(b.get("oa_id"))
    c["brasil"] = kept
    json.dump(c, open(path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return g0, len(c["global"]), dropped


def main():
    print("=== HIGIENE: remoção de ids não-resolvíveis (404) ===")
    for fn in NETWORKS:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        n0, n1, e0, e1 = clean_network(p)
        print(f"  {fn:24s} nós {n0}->{n1} (-{n0-n1})  arestas {e0}->{e1} (-{e0-e1})")
    cp = os.path.join(DATA, "cross_brasil.json")
    if os.path.exists(cp):
        g0, g1, dropped = clean_cross(cp)
        print(f"  cross_brasil.json        global {g0}->{g1}; pontes BR descartadas (só citavam fantasma): {dropped or 'nenhuma'}")

    # verificação: nenhum DEAD remanescente; nenhum nó 'thin' restante
    leftover, thin = [], []
    for fn in NETWORKS + ["cross_brasil.json", "cplx_works.json", "scisci_results.json", "openalex_enrich.json"]:
        p = os.path.join(DATA, fn)
        if not os.path.exists(p):
            continue
        d = json.load(open(p, encoding="utf-8"))
        txt = json.dumps(d, ensure_ascii=False)
        for di in REMOVE:
            if di in txt:
                leftover.append((fn, di))
        if isinstance(d, dict) and "nodes" in d:
            for nd in d["nodes"]:
                lab = nd.get("label")
                if lab is None or str(lab) == str(nd.get("id")) or lab == "":
                    thin.append((fn, nd.get("id")))
    print(f"\n  ids 404 remanescentes: {leftover or 'NENHUM'}")
    print(f"  nós sem título (thin) remanescentes: {thin or 'NENHUM'}")


if __name__ == "__main__":
    main()
