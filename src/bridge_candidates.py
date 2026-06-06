#!/usr/bin/env python3
"""Leads de leitura por PONTE SEMÂNTICA — candidatos a revisão de bibliografia (item 2).

Coerente com a FUNÇÃO do repo: não decide nada — entrega uma fila de leitura. Acha
pares de obras de SILOS DIFERENTES (Cyb/Reg/PolInd) que **nunca foram citados juntos**
(buraco estrutural) mas que **falam de coisas próximas** (alta proximidade semântica de
título+abstract). Esse é o quadrante que o teste de solidez (solidity.py) NÃO enxerga,
porque seu gerador só vê quase-fechamentos; aqui a SEMÂNTICA propõe e a ESTRUTURA filtra.

Honesto por desenho: são LEADS para ler, não pontes validadas. Reporta a distribuição de
cossenos (o que "próximo" significa), a cobertura das 3 frentes, e a confiança modal.
Reusa src/solidity.py (load_hobra, enriquecimento, embeddings) e src/data_io.py.

Saída: data/bridge_candidates.json + docs/dados/14_pontes_semanticas.csv.
Uso: python src/bridge_candidates.py
"""
import csv
import itertools
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_io  # noqa: E402
import solidity  # noqa: E402  (reusa load_hobra, enrich_members, _embed, EIXOS)

ROOT = data_io.ROOT
EIXOS = solidity.EIXOS


def build(out_dados=None):
    out_dados = out_dados or os.path.join(ROOT, "docs", "dados")
    cfg = solidity.load_config()
    top_k = cfg.get("leitura", {}).get("top_pares", 150)
    edges, citers, axis_of, pair_w, _, central = solidity.load_hobra()
    corpus = [n for n, a in axis_of.items() if a in EIXOS]            # obras com silo canônico
    topics, absts = solidity.enrich_members(corpus)                  # reusa cache/enriquecimento
    have = [w for w in corpus if absts.get(w)]
    if len(have) < 2:
        data_io.save_data("bridge_candidates.json",
                          {"_generated": "leads de ponte semântica", "n_pares": 0,
                           "status": "sem abstracts suficientes", "lista_leitura": [], "pares_top": []})
        print("bridge_candidates: sem abstracts suficientes")
        return
    import numpy as np
    vecs, metodo = solidity._embed([absts[w] for w in have], cfg["semantico"]["metodo"])
    idx = {w: i for i, w in enumerate(have)}
    maxd = max(central.values()) if central else 1

    # pares CROSS-SILO, NÃO co-citados (buraco estrutural), ranqueados por cosseno
    pares = []
    for a, b in itertools.combinations(have, 2):
        ea, eb = axis_of[a], axis_of[b]
        if ea == eb:
            continue
        if pair_w.get(frozenset((a, b)), 0) > 0:        # já co-citados -> não é buraco
            continue
        cos = float(np.dot(vecs[idx[a]], vecs[idx[b]]))
        pares.append({"a": a, "b": b, "frente": " × ".join(sorted((ea, eb))),
                      "eixo_a": ea, "eixo_b": eb, "cosseno": round(cos, 4),
                      "centralidade": round((central.get(a, 0) + central.get(b, 0)) / (2 * maxd), 4)})
    pares.sort(key=lambda p: -p["cosseno"])
    cosv = sorted((p["cosseno"] for p in pares))

    def pct(p):
        if not cosv:
            return 0.0
        k = min(len(cosv) - 1, max(0, int(round(p / 100 * (len(cosv) - 1)))))
        return round(cosv[k], 4)

    # lista de leitura: por obra, melhor parceiro cross-silo (quão "ponteável" ela é)
    best = {}
    for p in pares:
        for w, par_eixo in ((p["a"], p["eixo_b"]), (p["b"], p["eixo_a"])):
            cur = best.get(w)
            if cur is None or p["cosseno"] > cur["melhor_cosseno"]:
                best[w] = {"oa_id": w, "eixo": axis_of[w], "melhor_parceiro_eixo": par_eixo,
                           "melhor_cosseno": p["cosseno"], "confianca_modal": "obra"}
            best[w]["n_pontes_potenciais"] = best[w].get("n_pontes_potenciais", 0) + 1
    leitura = sorted(best.values(), key=lambda w: -w["melhor_cosseno"])

    frentes = {}
    for p in pares[:top_k]:
        frentes[p["frente"]] = frentes.get(p["frente"], 0) + 1

    out = {
        "_generated": "leads de leitura por ponte semântica (item 2)",
        "metodo": "pares cross-silo NÃO co-citados, ranqueados por proximidade semântica "
                  "(buraco estrutural + ponte semântica). LEADS para ler, não pontes validadas.",
        "semantico": {"metodo": metodo, "n_obras_com_abstract": len(have), "n_corpus": len(corpus)},
        "distribuicao_cosseno": {"p10": pct(10), "p50": pct(50), "p90": pct(90),
                                 "p99": pct(99), "max": round(cosv[-1], 4) if cosv else 0.0},
        "n_pares": len(pares),
        "cobertura_frentes_top": frentes,            # as 3 frentes representadas no topo?
        "pares_top": pares[:top_k],
        "lista_leitura": leitura[:top_k],
    }
    data_io.save_data("bridge_candidates.json", out)
    os.makedirs(out_dados, exist_ok=True)
    with open(os.path.join(out_dados, "14_pontes_semanticas.csv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["obra_a", "eixo_a", "obra_b", "eixo_b", "frente", "cosseno", "centralidade"])
        for p in pares[:top_k]:
            w.writerow([p["a"], p["eixo_a"], p["b"], p["eixo_b"], p["frente"], p["cosseno"], p["centralidade"]])
    print(f"bridge_candidates: {len(pares)} pares cross-silo não-co-citados | "
          f"semântico={metodo} | cosseno p50={pct(50)} p90={pct(90)} max={out['distribuicao_cosseno']['max']} | "
          f"frentes(top)={frentes}")
    return out


if __name__ == "__main__":
    build()
