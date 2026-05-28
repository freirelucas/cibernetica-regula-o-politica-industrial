"""Prioridade de ponte — adapta as métricas (Zajdela/XGI + estrutura) ao OBJETIVO
do trabalho: ranquear os papers a revisar em detalhe para CONSTRUIR as pontes
entre cibernética, regulação e política industrial.

Une, por obra (join por id OpenAlex), sinais REAIS já calculados:
  - interação trans-eixo (≈ "interação" de Zajdela; XGI): nº de hiperarestas de
    cocitação que cruzam eixos em que a obra aparece (data/cocitation_hyperedges.json);
  - alcance de eixos da vizinhança (axreach) — estrutura par-a-par (network_4axis);
  - alvo de catálise: peso a quem liga a CIBERNÉTICA (o eixo mais isolado, e o
    alvo do recorte) a outro eixo — construir a ponte que falta, não a que já existe;
  - papéis-ponte já marcados (obra-ponte, ponte global×Brasil, cibernética organizacional).

Score transparente (componentes guardados). Saída: data/bridge_priority.json.
Roda aqui (cache + numpy/XGI já presentes). Uso: python src/bridge_priority.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_rayyan  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
W = {"ho": 0.40, "reach": 0.30, "cyb": 0.15, "role": 0.15}   # pesos (transparentes)
BRIDGE_ROLES = {"obra-ponte", "ponte global×Brasil", "cibernética organizacional"}


def neighbor_axes():
    """Por nó da rede de 4 eixos: conjunto de eixos da vizinhança de cocitação."""
    net = json.load(open(os.path.join(DATA, "network_4axis.json"), encoding="utf-8"))
    axis = {n["id"]: (n.get("axis") or "") for n in net["nodes"]}
    nbr = {n["id"]: set() for n in net["nodes"]}
    for l in net["links"]:
        s, t = l.get("source"), l.get("target")
        if t in nbr and axis.get(s):
            nbr[t].add(axis[s])
        if s in nbr and axis.get(t):
            nbr[s].add(axis[t])
    return axis, nbr


def main():
    axis, nbr = neighbor_axes()
    hg = json.load(open(os.path.join(DATA, "cocitation_hyperedges.json"), encoding="utf-8"))
    cross_ho = hg.get("cross_axis_degree", {})
    ho_max = max(cross_ho.values()) if cross_ho else 1

    works = build_rayyan.build()
    rows = []
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", "") or "")
        oid = m.group(1) if m else None
        ho = cross_ho.get(oid, 0) if oid else 0
        nb = nbr.get(oid, set()) if oid else set()
        reach = len(nb)
        # liga a cibernética (eixo mais isolado / alvo) a algum outro eixo?
        own = axis.get(oid, "") if oid else ""
        cyb_link = 1.0 if (("Cyb" in nb and (nb - {"Cyb"})) or (own == "Cyb" and nb - {"Cyb"})) else 0.0
        role = 1.0 if (set(e["roles"]) & BRIDGE_ROLES) else 0.0
        score = (W["ho"] * (ho / ho_max) + W["reach"] * (reach / 4.0)
                 + W["cyb"] * cyb_link + W["role"] * role)
        rows.append({"oa_id": oid, "title": e["title"], "axes": sorted(e["axes"]),
                     "score": round(score, 4), "ho": ho, "reach": reach,
                     "cyb_link": cyb_link, "role": role,
                     "roles": sorted(e["roles"])})
    rows.sort(key=lambda r: -r["score"])
    out = {oid: r for r in rows if (oid := r["oa_id"])}   # mapa por id p/ o build_rayyan juntar
    json.dump({"weights": W, "ranking": rows, "by_oa_id": out},
              open(os.path.join(DATA, "bridge_priority.json"), "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"obras pontuadas: {len(rows)} | com sinal de rede (ho/reach): "
          f"{sum(1 for r in rows if r['oa_id'] and (r['ho'] or r['reach']))}")
    print("\nTOP-20 prioridade de ponte (papers a revisar para construir as pontes):")
    for r in rows[:20]:
        print(f"  {r['score']:.3f} | ho={r['ho']:2d} reach={r['reach']} cyb={r['cyb_link']:.0f} "
              f"role={r['role']:.0f} | {r['title'][:50]}")


if __name__ == "__main__":
    main()
