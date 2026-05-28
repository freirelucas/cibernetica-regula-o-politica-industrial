"""Pivô Zajdela — a unidade fiel é o AUTOR, não a obra cocitada.

Pergunta: o silo é também *social*? Quantos autores atravessam eixos (publicam em
≥2 das comunidades)? Se quase nenhum, o silo de citação espelha um silo de
autoria — e reforça a tese de que a convergência precisa de interação prescrita
(o que a Zajdela mostra que catalisa colaboração).

Busca os autores das obras da rede (network_4axis) via OpenAlex COM CACHE (oa.py)
— ~5 requisições em lote, resumível. Saída: data/coauthor_bridges.json + relatório.
"""
import collections
import json
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import oa  # noqa: E402
import build_site as bs  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = "https://api.openalex.org"
AXN = {"Cyb": "cibernética", "Reg": "instrumentos de governo",
       "PolInd": "política industrial", "Cplx": "complexidade"}


def main():
    net = bs.explorer_network()
    # eixo de cada obra: vocabulário, senão o inferido pela vizinhança
    axis_of = {n["id"]: (n.get("axis") or n.get("axis_inf") or "") for n in net["nodes"]}
    label_of = {n["id"]: n.get("label") or n["id"] for n in net["nodes"]}
    ids = [n["id"] for n in net["nodes"]]

    auth_of = {}
    for i in range(0, len(ids), 50):
        chunk = ids[i:i + 50]
        flt = "openalex:" + "|".join(chunk)
        url = f"{API}/works?filter={urllib.parse.quote(flt, safe=':|')}&per-page=50&select=id,authorships"
        for w in (oa.get(url).get("results") or []):
            wid = (w.get("id") or "").split("/")[-1]
            auth_of[wid] = [(((a.get("author") or {}).get("id") or "").split("/")[-1],
                             (a.get("author") or {}).get("display_name") or "")
                            for a in (w.get("authorships") or [])]

    author_axes = collections.defaultdict(set)
    author_name, author_works = {}, collections.defaultdict(list)
    for wid, auths in auth_of.items():
        ax = axis_of.get(wid, "")
        for aid, name in auths:
            if not aid:
                continue
            author_name[aid] = name
            author_works[aid].append((wid, ax))
            if ax:
                author_axes[aid].add(ax)

    bridging = {aid: ax for aid, ax in author_axes.items() if len(ax) >= 2}
    n_auth = len(author_axes)
    print(f"obras com autoria: {len(auth_of)} | autores distintos (com eixo): {n_auth}")
    print(f"autores que ATRAVESSAM eixos (≥2): {len(bridging)} "
          f"({100*len(bridging)/max(n_auth,1):.1f}%)")
    rows = []
    for aid, ax in sorted(bridging.items(), key=lambda kv: (-len(kv[1]), author_name.get(kv[0], ""))):
        works = [(label_of.get(w, w), a) for w, a in author_works[aid]]
        rows.append({"author": author_name.get(aid, aid), "oa_id": aid,
                     "axes": sorted(AXN.get(a, a) for a in ax),
                     "works": [{"label": l, "axis": AXN.get(a, a)} for l, a in works]})
        print(f"  {author_name.get(aid,'')[:26]:26} {', '.join(sorted(AXN.get(a,a) for a in ax))}")
    json.dump(rows, open(os.path.join(ROOT, "data", "coauthor_bridges.json"), "w",
                         encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"\n{len(rows)} autores-ponte -> data/coauthor_bridges.json")


if __name__ == "__main__":
    main()
