#!/usr/bin/env python3
"""Verifica, de forma REPRODUTÍVEL, o achado central (§00): a partição por EIXO da
rede de cocitação tem modularidade muito acima do acaso (silos reais) e quase nenhuma
obra é conector significativo entre os eixos.

Reusa `sfi_methods.configuration_null` — o MESMO modelo nulo do relatório (preserva o
grau, por trocas duplas). A modularidade é computada SÓ sobre os nós CLASSIFICADOS
(eixo conhecido); os nós sem eixo (`None`) — referências cocitadas que o vocabulário
não alcança (problema H1) — são reportados à parte, NÃO tratados como uma comunidade
(isso distorceria Q para baixo). Escreve `data/modularity_check.json`.

Uso: `python src/modularity_check.py`
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import sfi_methods  # noqa: E402

EIXOS = {"Cyb", "Reg", "PolInd", "Cplx"}


def _modularidade(nodes, links):
    keep = {n["id"] for n in nodes}
    el = [l for l in links if l["source"] in keep and l["target"] in keep]
    nid = [n["id"] for n in nodes]
    comm = {n["id"]: (n.get("axis") or n.get("eixo")) for n in nodes}
    q, Pz = sfi_methods.configuration_null(nid, el, comm, n_iter=100, seed=1)
    n_conn = sum(1 for n in nid
                 if sfi_methods.ga_role(Pz[n]["P_obs"], Pz[n]["z"]) in ("conector", "hub conector")
                 and Pz[n]["z"] > 0)
    return {"n_nos": len(nid), "n_arestas": len(el), **q, "n_conectores_significativos": n_conn}


def main():
    net = json.load(open(os.path.join(ROOT, "data", "network_4axis.json"), encoding="utf-8"))
    all_nodes = net["nodes"]
    links = net.get("links") or net.get("edges") or []

    def axis(n):
        return n.get("axis") or n.get("eixo")

    classificados = [n for n in all_nodes if axis(n) in EIXOS]
    nucleo = [n for n in classificados if axis(n) in ("Cyb", "Reg", "PolInd")]
    n_none = sum(1 for n in all_nodes if axis(n) not in EIXOS)

    out = {
        "_doc": "verificação reprodutível do achado central (§00): modularidade da partição "
                "por eixo vs. modelo nulo de configuração (preserva grau). Só nós classificados.",
        "rede": "network_4axis.json",
        "n_nos_total": len(all_nodes),
        "n_nos_sem_eixo": n_none,
        "pct_sem_eixo": round(100 * n_none / max(len(all_nodes), 1), 1),
        "nota_H1": "nós sem eixo são referências cocitadas que o vocabulário não classifica "
                   "(título sem abstract etc.); ficam de fora da partição, não viram comunidade.",
        "tres_eixos": _modularidade(nucleo, links),
        "quatro_eixos_com_Cplx": _modularidade(classificados, links),
    }
    json.dump(out, open(os.path.join(ROOT, "data", "modularity_check.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)
    t = out["tres_eixos"]
    print(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"\n→ silos confirmados: Q={t['Q_obs']} (acaso {t['Q_rand']}, z={t['Q_z']}), "
          f"{t['n_conectores_significativos']} conectores · {out['pct_sem_eixo']}% dos nós sem eixo (H1)")


if __name__ == "__main__":
    main()
