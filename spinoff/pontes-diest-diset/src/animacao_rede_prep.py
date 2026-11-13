"""Prepara a cena de reconfiguração da rede (protótipo de animação, camada 4).

Lê data/authors.json e data/items_tagged.json, monta a rede de coautoria entre os
membros ativos da DIEST e da DISET (janela >= 2010) e recalcula o número de obras mistas
ANTES e DEPOIS de reclassificar UMA pessoa. A contagem de obras mistas usa a mesma
definição de analysis.py (rótulos de todos os autores), para bater com o relatório.

Isto é uma SIMULAÇÃO: nada é gravado em data/. As posições são calculadas por força
dirigida (Fruchterman-Reingold, semente fixa) nos dois rótulos, para que a animação
mostre a rede se reorganizando e não só mudando de cor.

Saída: data/animacao_rede.json  (usado por src/animacao_rede_cena.py)
Uso:   python src/animacao_rede_prep.py [--alvo "Nome Sobrenome"] [--para DIEST]
"""
import argparse
import collections
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, load_json, save_json  # noqa: E402

START = 2010


def layout(nodes, edges, labels, seed=7, iters=300):
    """Fruchterman-Reingold com coesão de rótulo: mesmo rótulo atrai levemente."""
    rnd = random.Random(seed)
    pos = {n: [rnd.uniform(-1, 1), rnd.uniform(-1, 1)] for n in nodes}
    k = 1.0 / math.sqrt(len(nodes))
    temp = 0.1
    for _ in range(iters):
        disp = {n: [0.0, 0.0] for n in nodes}
        for i, a in enumerate(nodes):
            for b in nodes[i + 1:]:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                d = math.hypot(dx, dy) or 1e-6
                f = k * k / d
                if labels[a] == labels[b]:
                    f *= 0.6  # coesão de rótulo (apenas empurra menos)
                    f -= 0.02 * d
                fx, fy = dx / d * f, dy / d * f
                disp[a][0] += fx; disp[a][1] += fy
                disp[b][0] -= fx; disp[b][1] -= fy
        for (a, b), w in edges.items():
            dx = pos[a][0] - pos[b][0]
            dy = pos[a][1] - pos[b][1]
            d = math.hypot(dx, dy) or 1e-6
            f = d * d / k * min(1 + 0.3 * w, 3)
            disp[a][0] -= dx / d * f; disp[a][1] -= dy / d * f
            disp[b][0] += dx / d * f; disp[b][1] += dy / d * f
        for n in nodes:
            dx, dy = disp[n]
            d = math.hypot(dx, dy) or 1e-6
            step = min(d, temp)
            pos[n][0] += dx / d * step
            pos[n][1] += dy / d * step
        temp *= 0.985
    xs = [p[0] for p in pos.values()]; ys = [p[1] for p in pos.values()]
    cx, cy = (max(xs) + min(xs)) / 2, (max(ys) + min(ys)) / 2
    s = 6.0 / max(max(xs) - min(xs), max(ys) - min(ys))
    return {n: [round((p[0] - cx) * s, 4), round((p[1] - cy) * s, 4)] for n, p in pos.items()}


def mixed_count(items, lab):
    n = 0
    for it in items:
        ds = {lab.get(a) for a in it["authors"]}
        if "DIEST" in ds and "DISET" in ds:
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--alvo", default="Mauro Santos Silva")
    ap.add_argument("--para", default="DIEST", choices=FOCUS)
    a = ap.parse_args()

    authors = load_json("authors.json")
    items = [i for i in load_json("items_tagged.json") if i["year"] and i["year"] >= START]

    ativos = {k: v for k, v in authors.items()
              if v["diretoria"] in FOCUS and v["active"] and (v["staff"] or v["n_tagged"] >= 3)}
    alvo_id = next((k for k, v in ativos.items() if v["name"] == a.alvo), None)
    if alvo_id is None:
        sys.exit(f"'{a.alvo}' não está no conjunto ativo DIEST/DISET; escolha outro --alvo")
    de = ativos[alvo_id]["diretoria"]
    if de == a.para:
        sys.exit(f"'{a.alvo}' já é {a.para}")

    nodes = sorted(ativos)
    lab0 = {k: v["diretoria"] for k, v in ativos.items()}
    lab1 = dict(lab0); lab1[alvo_id] = a.para

    edges = collections.Counter()
    for it in items:
        ids = sorted({x for x in it["authors"] if x in ativos})
        for i, x in enumerate(ids):
            for y in ids[i + 1:]:
                edges[(x, y)] += 1

    # mesma definição de analysis.py: rótulos de TODOS os autores, não só os ativos
    full0 = {k: v["diretoria"] for k, v in authors.items() if v["diretoria"]}
    full1 = dict(full0); full1[alvo_id] = a.para
    m0 = mixed_count(items, full0)
    m1 = mixed_count(items, full1)
    pos0 = layout(nodes, edges, lab0)
    pos1 = layout(nodes, edges, lab1)

    grau = collections.Counter()
    for (x, y), w in edges.items():
        grau[x] += w; grau[y] += w
    rotulos = [ativos[n]["name"] for n, _ in grau.most_common(6)]
    if ativos[alvo_id]["name"] not in rotulos:
        rotulos.append(ativos[alvo_id]["name"])

    out = {
        "alvo": {"id": alvo_id, "nome": ativos[alvo_id]["name"], "de": de, "para": a.para,
               "confianca": ativos[alvo_id]["confidence"],
               "obras_rotuladas": ativos[alvo_id]["n_tagged"]},
        "janela": {"inicio": START, "fim": max(i["year"] for i in items), "obras": len(items)},
        "contagem_obras_mistas": {"antes": m0, "depois": m1},
        "nos": [{"id": n, "nome": ativos[n]["name"], "grupo0": lab0[n], "grupo1": lab1[n],
                 "obras": ativos[n]["n_items"], "pos0": pos0[n], "pos1": pos1[n],
                 "rotulo": ativos[n]["name"] in rotulos}
                for n in nodes],
        "arestas": [{"a": x, "b": y, "w": w,
                     "mista0": {lab0[x], lab0[y]} == set(FOCUS),
                     "mista1": {lab1[x], lab1[y]} == set(FOCUS)}
                    for (x, y), w in edges.items()],
        "aviso": "SIMULAÇÃO: uma reclassificação hipotética. Não altera data/ nem resultado publicado.",
    }
    save_json("animacao_rede.json", out)
    print(f"{ativos[alvo_id]['name']}: {de} -> {a.para} | obras mistas {m0} -> {m1} | "
          f"nós {len(nodes)}, arestas {len(edges)}", file=sys.stderr)


if __name__ == "__main__":
    main()
