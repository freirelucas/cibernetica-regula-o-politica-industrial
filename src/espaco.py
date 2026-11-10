#!/usr/bin/env python3
"""Espaço 3D — dados da cena em que cada obra ocupa o ponto de um tetraedro que
corresponde à mistura da sua cocitação entre as quatro tradições.

Regra, não física. A posição de uma obra é a COMPOSIÇÃO da sua vizinhança de
cocitação por tradição: a contagem de vizinhas com rótulo OBSERVADO em cada eixo,
dividida pelo total. É a mesma contagem que ``build_site.explorer_network`` usa para
inferir o eixo das obras sem rótulo de vocabulário — logo o eixo inferido é, por
construção, um vértice mais próximo, e a cena é o retrato geométrico da inferência
que ``infer_validation.py`` mede.

Empate. Quando duas tradições têm a mesma contagem máxima, a obra fica à mesma
distância de dois vértices e a regra de origem (``max`` sobre um dicionário) decide
pela ordem em que as arestas são lidas — reprodutível, porque a rede é versionada,
mas sem base de medida. A cena marca essas obras (campo ``e``) e a página diz
quantas são; o rótulo publicado não é alterado aqui.

Por que não um layout de forças: a rede tem 250 nós e 7.171 arestas (densidade
0,23); desenhada por física, é uma bola de pelos em que nenhum eixo quer dizer
coisa alguma. Aqui a posição é o dado.

Este módulo só lê derivados já versionados e devolve um dicionário pronto para
virar ``const ESPACO = ...`` na página. Nenhum número da página é digitado à mão.
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import data_io  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
AX = ["Cyb", "Reg", "PolInd", "Cplx"]          # ordem dos vértices do tetraedro
CANON = ("Cyb", "Reg", "PolInd")              # os três silos canônicos (Cplx é o 4º eixo)
TD_JSON = "td_referencias.json"
CORTE_ROTULO = 60    # o funil guarda só os 60 primeiros caracteres do título (experiment_cplx.py)


def _carrega(nome):
    return data_io.load_data(nome, required=False, default={}) or {}


def composicao(nodes, links):
    """id -> [n_Cyb, n_Reg, n_PolInd, n_Cplx]: vizinhas de cocitação com rótulo observado.

    Réplica exata da regra de ``build_site.explorer_network`` (contagem, não peso;
    cada aresta conta nos dois sentidos; só o rótulo OBSERVADO da vizinha entra).
    """
    obs = {n["id"]: (n.get("axis") or "") for n in nodes}
    comp = {n["id"]: [0, 0, 0, 0] for n in nodes}
    for l in links:
        s, t = l.get("source"), l.get("target")
        if t in comp and obs.get(s) in AX:
            comp[t][AX.index(obs[s])] += 1
        if s in comp and obs.get(t) in AX:
            comp[s][AX.index(obs[t])] += 1
    return obs, comp


def _blocos(links, obs):
    """Peso de cocitação entre tradições, só entre obras de rótulo observado."""
    peso = collections.Counter()
    cont = collections.Counter()
    for l in links:
        a, b = obs.get(l.get("source")), obs.get(l.get("target"))
        w = l.get("peso", 1)
        if a in AX and b in AX:
            i, j = sorted((AX.index(a), AX.index(b)))
            peso[(i, j)] += w
            cont["intra" if a == b else "inter"] += 1
        else:
            cont["com_inferido"] += 1
    total = sum(peso.values()) or 1
    intra = sum(v for (i, j), v in peso.items() if i == j)
    canon = [AX.index(k) for k in CANON]
    tot_c = sum(v for (i, j), v in peso.items() if i in canon and j in canon) or 1
    inter_c = sum(v for (i, j), v in peso.items() if i in canon and j in canon and i != j)
    return {
        "matriz": [[peso.get((min(i, j), max(i, j)), 0) for j in range(4)] for i in range(4)],
        "peso_total": total, "peso_intra": intra, "peso_inter": total - intra,
        "pct_inter": round(100 * (total - intra) / total, 1),
        "pct_inter_canonico": round(100 * inter_c / tot_c, 1),
        "n_arestas_intra": cont["intra"], "n_arestas_inter": cont["inter"],
        "n_arestas_com_inferido": cont["com_inferido"],
    }


def _listas(hyper, obs):
    """Listas de referências (hiperarestas) pela mistura das tradições que citam.

    É o dado SEM projeção: cada lista é a interseção das referências de um trabalho
    citante com o núcleo. Devolve as composições distintas com a sua contagem, e
    quantas listas tocam uma, duas ou três tradições canônicas (rótulo observado).
    """
    comps = collections.Counter()
    toca = collections.Counter()
    n_base = 0
    for he in hyper:
        k = [0, 0, 0, 0]
        for m in he:
            a = obs.get(m)
            if a in AX:
                k[AX.index(a)] += 1
        if sum(k) == 0:
            toca["sem_rotulo"] += 1
            continue
        n_base += 1
        comps[tuple(k)] += 1
        toca[sum(1 for i, a in enumerate(AX) if a in CANON and k[i] > 0)] += 1
    return {
        "n_listas": len(hyper), "n_com_rotulo": n_base, "n_sem_rotulo": toca["sem_rotulo"],
        "tocam_1": toca[1], "tocam_2": toca[2], "tocam_3": toca[3], "tocam_0": toca[0],
        "pct_tocam_3": round(100 * toca[3] / max(n_base, 1), 1),
        "pct_tocam_2mais": round(100 * (toca[2] + toca[3]) / max(n_base, 1), 1),
        "comps": [list(k) + [n] for k, n in sorted(comps.items(), key=lambda kv: (-kv[1], kv[0]))],
    }


def _nota(idx, obs, nodes):
    """Bibliografia do texto para discussão, se ``data/td_referencias.json`` existir."""
    td = _carrega(TD_JSON)
    refs = td.get("referencias") or []
    if not refs:
        return None
    k_obs = [0, 0, 0, 0]
    n_obs = n_inf = 0
    lista = []
    na_rede = set()
    for r in refs:
        nos = [idx[w] for w in r.get("oa", []) if w in idx]
        item = {"r": r["ref"], "t": r.get("tipo", "obra"), "doi": r.get("doi", ""),
                "n": nos, "obs": r.get("nota", "")}
        if nos:
            na_rede.update(nos)
            eixo = obs.get(nodes[nos[0]]["id"]) or ""
            if eixo in AX:                      # uma obra conta uma vez, mesmo com dois registros
                k_obs[AX.index(eixo)] += 1
                n_obs += 1
            else:
                n_inf += 1
        lista.append(item)
    obras = [r for r in refs if r.get("tipo", "obra") == "obra"]
    return {
        "titulo": td.get("titulo", ""), "autores": td.get("autores", []), "versao": td.get("versao", ""),
        "n_refs": len(refs), "n_obras": len(obras), "n_atos": len(refs) - len(obras),
        "n_obras_na_rede": sum(1 for r in obras if any(w in idx for w in r.get("oa", []))),
        "n_registros": len(na_rede), "n_rotulo_observado": n_obs, "n_rotulo_inferido": n_inf,
        "k": k_obs, "refs": lista, "nos": sorted(na_rede),
    }


def dados(net):
    """Monta o dicionário da cena a partir da rede do explorador (já anotada)."""
    nodes, links = net.get("nodes", []), net.get("links", [])
    idx = {n["id"]: i for i, n in enumerate(nodes)}
    obs, comp = composicao(nodes, links)

    sol = _carrega("solidity_bridges.json")
    oo = _carrega("observed_only_check.json")
    iv = _carrega("infer_validation.json")
    mc = _carrega("modularity_check.json")
    hy = _carrega("cocitation_hyperedges.json")
    tc = _carrega("temporal_cocitation.json")

    nota = _nota(idx, obs, nodes)
    na_nota = set(nota["nos"]) if nota else set()

    nos = []
    fora = sem_viz = empates = empates_agenda = 0
    for i, n in enumerate(nodes):
        eixo = n.get("axis") or n.get("axis_inf") or ""
        k = comp[n["id"]]
        tot = sum(k)
        topo = [j for j in range(4) if tot and k[j] == max(k)]   # vértices mais próximos (2+ = empate)
        if n.get("axis") in AX:
            if tot == 0:
                sem_viz += 1
            elif AX.index(n["axis"]) not in topo:
                fora += 1                           # vocabulário diz um eixo, a vizinhança aponta outro
        elif len(topo) > 1:
            empates += 1                            # rótulo inferido decidido pela ordem de leitura
            empates_agenda += 1 if n.get("agenda") else 0
        rot = n.get("label") or n["id"]
        if len(rot) >= CORTE_ROTULO:                # título cortado na origem: dizer que continua
            rot = rot.rstrip() + "…"
        no = {
            "i": n["id"], "l": rot,
            "a": AX.index(eixo) if eixo in AX else -1,
            "o": 1 if n.get("axis") else 0, "s": 1 if n.get("seed") else 0,
            "y": n.get("year") or 0, "c": n.get("cited_by") or 0,
            "g": 1 if n.get("agenda") else 0, "k": k, "t": 1 if i in na_nota else 0,
        }
        if len(topo) > 1:
            no["e"] = topo
        nos.append(no)

    arestas = []
    for l in links:
        s, t = idx.get(l.get("source")), idx.get(l.get("target"))
        if s is not None and t is not None and s != t:
            arestas.extend((s, t, int(l.get("peso", 1))))

    triades = []
    for c in sol.get("agenda") or []:
        mem = [idx[m] for m in c.get("membros", []) if m in idx]
        if len(mem) != 3:
            continue
        ax_obs = {obs.get(m) for m in c["membros"] if obs.get(m) in CANON}
        triades.append({
            "m": mem, "d": round(float(c.get("integracao", 0)), 2),
            "z": c.get("integracao_z"), "p": c.get("integracao_p"),
            "q": c.get("quadrante", ""),
            "n": 1 if len(ax_obs) >= 2 else 0,       # núcleo duro: sobrevive sem rótulo inferido
            "inf": [i for i, m in zip(mem, c["membros"]) if not obs.get(m)],
        })
    n_nucleo = sum(t["n"] for t in triades)
    esperado = (oo.get("agenda_publicada") or {}).get("n_sobrevivem_so_observado")
    if esperado is not None and esperado != n_nucleo:
        sys.stderr.write(f"AVISO: núcleo duro da cena ({n_nucleo}) difere de "
                         f"observed_only_check.json ({esperado}).\n")

    hyper = hy.get("hyperedges") or []
    tres = mc.get("tres_eixos") or {}
    boot = mc.get("robustez_bootstrap_3eixos") or {}
    prov = oo.get("proveniencia") or {}
    ouro = iv.get("conjunto_ouro") or {}
    n_ouro = ouro.get("n") or sum(1 for n in nodes if n.get("axis"))
    m = len(arestas) // 3
    n = len(nodes)

    num = {
        "rede": {"n": n, "m": m, "densidade": round(2 * m / max(n * (n - 1), 1), 3)},
        "silos": {"Q": tres.get("Q_obs"), "Q_acaso": tres.get("Q_rand"), "z": tres.get("Q_z"),
                  "n_nos": tres.get("n_nos"), "n_conectores": tres.get("n_conectores_significativos"),
                  "boot_Q": boot.get("Q_medio"), "boot_ic": boot.get("Q_ic95"), "boot_B": boot.get("B"),
                  "obs_minoria_propria": sum(
                      1 for x in nos if x["o"] and x["a"] >= 0 and sum(x["k"])
                      and x["k"][x["a"]] / sum(x["k"]) < 0.5),
                  "n_observadas": sum(1 for x in nos if x["o"])},
        "blocos": _blocos(links, obs),
        "tempo": {"copresenca": tc.get("first_copresence_year"),
                  "chegada": tc.get("axis_arrival_year") or {},
                  "decadas": [{"d": d.get("decade"), "f": d.get("intra_axis_fraction"),
                               "x": d.get("n_cross_axis_edges"), "e": d.get("n_edges_cumul")}
                              for d in (tc.get("decade_snapshots") or [])]},
        "prov": {"semente": (prov.get("contagem") or {}).get("semente"),
                 "vocabulario": (prov.get("contagem") or {}).get("vocabulario"),
                 "vizinhanca": (prov.get("contagem") or {}).get("vizinhanca"),
                 "pct_obs": prov.get("pct_observado"), "pct_inf": prov.get("pct_inferido"),
                 "acuracia": iv.get("acuracia_global"), "n_ouro": n_ouro,
                 "fora": fora, "sem_vizinhanca": sem_viz, "acertos": n_ouro - fora - sem_viz,
                 "empates": empates, "empates_na_agenda": empates_agenda,
                 "por_eixo": {k: v for k, v in (iv.get("acuracia_por_eixo") or {}).items()},
                 "evid_ouro": (iv.get("evidencia_comparada") or {}).get("ouro_mediana"),
                 "evid_inf": (iv.get("evidencia_comparada") or {}).get("inferidos_mediana")},
        "agenda": {"n_candidatas": sol.get("n_candidatas"), "n_alta": sol.get("n_alta_integracao"),
                   "n_agenda": len(triades), "alem_do_acaso": sol.get("alem_do_acaso"),
                   "n_obras": len({i for t in triades for i in t["m"]}),
                   "n_nucleo": n_nucleo,
                   "pct_nucleo": round(100 * n_nucleo / max(len(triades), 1), 1),
                   "elegiveis": (oo.get("espaco_completo") or {}).get("n_todos"),
                   "elegiveis_obs": (oo.get("espaco_completo") or {}).get("n_observado")},
        "listas": _listas(hyper, obs) if hyper else None,
        "hiper": {"n_citantes": hy.get("n_citers"), "obs": (hy.get("null_model") or {}).get("obs"),
                  "nulo": (hy.get("null_model") or {}).get("null_mean"),
                  "z": (hy.get("null_model") or {}).get("z")},
    }
    return {"eixos": AX, "nos": nos, "arestas": arestas, "triades": triades,
            "num": num, "nota": nota}


def heroi(cena):
    """Recorte mínimo para a abertura do relatório: eixo, proveniência, citações, composição."""
    return [[x["a"], x["o"], x["c"]] + x["k"] for x in cena["nos"]]


if __name__ == "__main__":
    import build_site
    d = dados(build_site.explorer_network())
    s = json.dumps(d, ensure_ascii=False, separators=(",", ":"))
    print(f"nós {len(d['nos'])} · arestas {len(d['arestas']) // 3} · tríades {len(d['triades'])} "
          f"(núcleo {d['num']['agenda']['n_nucleo']}) · {len(s) // 1024} KB")
    print(json.dumps({k: v for k, v in d["num"].items() if k != "listas"}, ensure_ascii=False, indent=1)[:2400])
    if d["num"]["listas"]:
        li = dict(d["num"]["listas"]); li["comps"] = f"{len(li['comps'])} composições distintas"
        print("listas:", li)
    if d["nota"]:
        print("nota:", {k: v for k, v in d["nota"].items() if k not in ("refs", "nos")})
