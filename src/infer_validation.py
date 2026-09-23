#!/usr/bin/env python3
"""Validação cruzada do inferidor de eixo (H1) — qual é a taxa de erro real.

`build_site.py` resolve os nós "sem eixo" pelo eixo dominante da vizinhança de
cocitação. Isso torna as afirmações sobre pontes parcialmente circulares. Em vez de
apenas declarar a ressalva, aqui ela é MEDIDA: aplica-se a MESMA regra ao conjunto
de nós cujo eixo é conhecido (sementes + vocabulário), escondendo o rótulo, e
compara-se predição com verdade.

A regra replicada (build_site.py, bloco "afinidade estrutural por cocitação"):
    nbr[n][eixo_observado_do_vizinho] += 1   sobre cada aresta, nos dois sentidos
    predição = max(nbr[n])                   eixo dominante da vizinhança

Mede ainda, e isto é o essencial: a acurácia **em função da evidência disponível**
(nº de vizinhos rotulados) e se os nós realmente inferidos têm menos evidência que
os do conjunto-ouro — caso em que a acurácia medida é um LIMITE SUPERIOR.

Saída: data/infer_validation.json   ·   Roda: python src/infer_validation.py
"""
import collections
import json
import os
import statistics
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_site as bs      # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "infer_validation.json")


def neighbourhood(nodes, links):
    """id -> {eixo_observado_do_vizinho: contagem} — idêntico a build_site.py."""
    axis_obs = {n["id"]: (n.get("axis") or "") for n in nodes}
    nbr = {n["id"]: {} for n in nodes}
    for l in links:
        s, t = l.get("source"), l.get("target")
        if isinstance(s, dict):
            s = s.get("id")
        if isinstance(t, dict):
            t = t.get("id")
        if t in nbr and axis_obs.get(s):
            nbr[t][axis_obs[s]] = nbr[t].get(axis_obs[s], 0) + 1
        if s in nbr and axis_obs.get(t):
            nbr[s][axis_obs[t]] = nbr[s].get(axis_obs[t], 0) + 1
    return axis_obs, nbr


def _bin(n):
    return "0" if n == 0 else "1-2" if n <= 2 else "3-5" if n <= 5 else "6-10" if n <= 10 else "11+"


def main():
    net = bs.explorer_network()
    nodes, links = net["nodes"], net["links"]
    axis_obs, nbr = neighbourhood(nodes, links)

    gold = [n for n in nodes if n.get("axis")]
    inferidos = [n for n in nodes if not n.get("axis") and n.get("axis_inf")]

    acertos, conf = 0, collections.Counter()
    por_eixo = collections.defaultdict(lambda: {"n": 0, "acertos": 0})
    por_evid = collections.defaultdict(lambda: {"n": 0, "acertos": 0})
    sem_evidencia = 0

    for n in gold:
        d = dict(nbr.get(n["id"], {}))
        verdade = n["axis"]
        # já é leave-one-out por construção: o rótulo de um nó nunca entra na
        # contagem da sua PRÓPRIA vizinhança — só os rótulos dos vizinhos entram.
        evid = sum(d.values())
        if evid == 0:
            sem_evidencia += 1
            pred = None
        else:
            pred = max(d, key=lambda k: d[k])
        ok = (pred == verdade)
        acertos += int(ok)
        conf[(verdade, pred or "sem_predicao")] += 1
        por_eixo[verdade]["n"] += 1
        por_eixo[verdade]["acertos"] += int(ok)
        b = _bin(evid)
        por_evid[b]["n"] += 1
        por_evid[b]["acertos"] += int(ok)

    n_gold = max(len(gold), 1)
    evid_gold = [sum(nbr.get(n["id"], {}).values()) for n in gold]
    evid_inf = [sum(nbr.get(n["id"], {}).values()) for n in inferidos]

    out = {
        "_doc": ("validação cruzada do inferidor de eixo por vizinhança de cocitação (H1): "
                 "mesma regra de build_site.py aplicada ao conjunto de rótulo conhecido."),
        "conjunto_ouro": {
            "n": len(gold),
            "sementes": sum(1 for n in gold if n.get("seed")),
            "vocabulario": sum(1 for n in gold if not n.get("seed")),
            "sem_evidencia_de_vizinhanca": sem_evidencia,
        },
        "acuracia_global": round(acertos / n_gold, 3),
        "acuracia_por_eixo": {
            k: {"n": v["n"], "acuracia": round(v["acertos"] / max(v["n"], 1), 3)}
            for k, v in sorted(por_eixo.items())
        },
        "acuracia_por_evidencia": {
            k: {"n": v["n"], "acuracia": round(v["acertos"] / max(v["n"], 1), 3)}
            for k, v in sorted(por_evid.items(), key=lambda kv: (len(kv[0]), kv[0]))
        },
        "matriz_confusao": {f"{a}->{b}": c for (a, b), c in sorted(conf.items())},
        "evidencia_comparada": {
            "_doc": ("se os nós realmente inferidos têm MENOS vizinhos rotulados que o "
                     "conjunto-ouro, a acurácia acima é um LIMITE SUPERIOR"),
            "ouro_mediana": statistics.median(evid_gold) if evid_gold else 0,
            "inferidos_mediana": statistics.median(evid_inf) if evid_inf else 0,
            "ouro_media": round(statistics.mean(evid_gold), 1) if evid_gold else 0,
            "inferidos_media": round(statistics.mean(evid_inf), 1) if evid_inf else 0,
            "n_inferidos": len(inferidos),
        },
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"conjunto-ouro: {out['conjunto_ouro']['n']} nós "
          f"({out['conjunto_ouro']['sementes']} sementes + "
          f"{out['conjunto_ouro']['vocabulario']} vocabulário)")
    print(f"acurácia global do inferidor: {out['acuracia_global']}")
    for k, v in out["acuracia_por_eixo"].items():
        print(f"   {k:8} n={v['n']:3}  acurácia={v['acuracia']}")
    print("acurácia por evidência (nº de vizinhos rotulados):")
    for k, v in out["acuracia_por_evidencia"].items():
        print(f"   {k:5} n={v['n']:3}  acurácia={v['acuracia']}")
    e = out["evidencia_comparada"]
    print(f"evidência mediana — ouro={e['ouro_mediana']} vs inferidos={e['inferidos_mediana']}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
