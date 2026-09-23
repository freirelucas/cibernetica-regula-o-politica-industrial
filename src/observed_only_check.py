#!/usr/bin/env python3
"""Réplica só-observados (H1) — quanto das afirmações sobre PONTES sobrevive sem
rótulo inferido.

Motivação (METODOLOGIA.md, H1): 46,8% dos nós cocitados não são classificados pelo
vocabulário; quando falta, `build_site.py` infere o eixo da vizinhança de cocitação
(campo `axis_inf`). `cocitation_hypergraph.py` achatava observado+inferido num único
`axis_of`, que é o mapa que `solidity.py` usa — logo as afirmações sobre pontes
herdavam circularidade parcial. (O achado dos SILOS não herda: `modularity_check.py`
usa só `axis` e deixa os sem-eixo fora da partição.)

Este módulo roda a CAMADA ESTRUTURAL das pontes duas vezes, sobre as MESMAS
hiperarestas, mudando só o mapa de eixos:
  - braço `todos`    = observado ∪ inferido  (comportamento publicado)
  - braço `observado`= só rótulo observado (semente ou vocabulário)
e mede a sobrevivência. Não recomputa semântica nem holdout temporal (que não
dependem do rótulo de eixo para existir); compara onde o rótulo de fato entra:
a geração de tríades cross-silo e a integração (ΔKf).

Saída: data/observed_only_check.json   ·   Roda: python src/observed_only_check.py
"""
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_site as bs      # noqa: E402
import data_io               # noqa: E402
import solidity              # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "observed_only_check.json")


def provenance():
    """id -> semente | vocabulario | vizinhanca | sem_eixo, a partir da rede do explorador."""
    net = bs.explorer_network()
    src, axis_obs, axis_all = {}, {}, {}
    for n in net["nodes"]:
        i = n["id"]
        axis_obs[i] = n.get("axis") or ""
        axis_all[i] = n.get("axis") or n.get("axis_inf") or ""
        if n.get("axis"):
            src[i] = "semente" if n.get("seed") else "vocabulario"
        elif n.get("axis_inf"):
            src[i] = "vizinhanca"
        else:
            src[i] = "sem_eixo"
    return src, axis_obs, axis_all


def _full_candidates(edges, axis_map, pair_w, cfg):
    """Espaço ELEGÍVEL completo, sem o teto de `max_candidatos`.

    O teto é aplicado depois de uma ordenação determinística; como o conjunto
    elegível difere entre os braços (é o eixo que decide o que é cross-silo),
    comparar as listas truncadas mediria o truncamento, não a inferência.
    """
    wide = json.loads(json.dumps(cfg))          # cópia rasa e segura
    wide["poda"]["max_candidatos"] = 10 ** 9
    return solidity.gen_candidates(edges, axis_map, pair_w, wide)


def _arm(edges, axis_map, pair_w, cfg):
    """Camada estrutural capada (como publicado): tríades cross-silo + integração (ΔKf)."""
    cands = solidity.gen_candidates(edges, axis_map, pair_w, cfg)
    integ = solidity.integration_scores(cands, axis_map, pair_w, cfg) if cands else {}
    alto = sorted(cands, key=lambda c: -c.get("integracao", 0.0))
    return cands, integ, alto


def main():
    cfg = solidity.load_config()
    edges, citers, axis_pub, pair_w, _, _ = solidity.load_hobra()
    src, axis_obs, axis_all = provenance()

    n_src = collections.Counter(src.values())
    n_tot = max(len(src), 1)

    cand_all, integ_all, alto_all = _arm(edges, axis_all, pair_w, cfg)
    cand_obs, integ_obs, alto_obs = _arm(edges, axis_obs, pair_w, cfg)

    def key(c):
        return frozenset(c["membros"])

    # comparação estrutural no espaço COMPLETO (sem teto) — ver _full_candidates
    full_all = {key(c) for c in _full_candidates(edges, axis_all, pair_w, cfg)}
    full_obs = {key(c) for c in _full_candidates(edges, axis_obs, pair_w, cfg)}
    jac_full = len(full_all & full_obs) / max(len(full_all | full_obs), 1)
    capado = len(cand_all) >= cfg["poda"]["max_candidatos"]

    set_all, set_obs = full_all, full_obs
    inter = set_all & set_obs
    jac = len(inter) / max(len(set_all | set_obs), 1)

    # exposição: candidatas do braço publicado que dependem de ao menos um membro inferido
    def exposta(c):
        return any(src.get(m) == "vizinhanca" for m in c["membros"])

    n_exp = sum(1 for c in cand_all if exposta(c))

    # a agenda JÁ PUBLICADA sobrevive?
    pub = data_io.load_data("solidity_bridges.json", required=False, default={}) or {}
    agenda_pub = [c for c in (pub.get("agenda") or [])]
    ag_keys = {frozenset(c["membros"]) for c in agenda_pub}
    ag_exposta = sum(1 for c in agenda_pub
                     if any(src.get(m) == "vizinhanca" for m in c["membros"]))
    ag_sobrevive = len(ag_keys & set_obs)

    out = {
        "_doc": ("réplica só-observados (H1): a camada estrutural das pontes rodada duas vezes "
                 "sobre as MESMAS hiperarestas, mudando só o mapa de eixos. Mede quanto do "
                 "resultado sobrevive sem rótulo inferido da vizinhança."),
        "proveniencia": {
            "n_nos": n_tot,
            "contagem": dict(n_src),
            "pct_observado": round(100 * (n_src["semente"] + n_src["vocabulario"]) / n_tot, 1),
            "pct_inferido": round(100 * n_src["vizinhanca"] / n_tot, 1),
        },
        "braco_todos": {
            "_doc": "observado ∪ inferido — o comportamento publicado",
            "n_candidatas": len(cand_all),
            "alem_do_acaso": integ_all.get("n_alem_do_acaso"),
            "top10_integracao": [
                {"membros": c["membros"], "eixos": c.get("eixos"),
                 "integracao": c.get("integracao")} for c in alto_all[:10]],
        },
        "braco_observado": {
            "_doc": "só rótulo observado (semente ou vocabulário) — sem inferência",
            "n_candidatas": len(cand_obs),
            "alem_do_acaso": integ_obs.get("n_alem_do_acaso"),
            "top10_integracao": [
                {"membros": c["membros"], "eixos": c.get("eixos"),
                 "integracao": c.get("integracao")} for c in alto_obs[:10]],
        },
        "espaco_completo": {
            "_doc": ("tríades elegíveis SEM o teto de max_candidatos — é aqui que a "
                     "comparação é honesta; as listas capadas mediriam o truncamento"),
            "n_todos": len(full_all),
            "n_observado": len(full_obs),
            "n_interseccao": len(full_all & full_obs),
            "jaccard": round(jac_full, 3),
            "teto_atingido_no_braco_capado": capado,
            "max_candidatos_cfg": cfg["poda"]["max_candidatos"],
        },
        "sobrevivencia": {
            "n_interseccao": len(inter),
            "jaccard": round(jac, 3),
            "pct_do_publicado_que_sobrevive": round(100 * len(inter) / max(len(set_all), 1), 1),
            "n_candidatas_expostas_a_inferencia": n_exp,
            "pct_candidatas_expostas": round(100 * n_exp / max(len(cand_all), 1), 1),
        },
        "agenda_publicada": {
            "n": len(agenda_pub),
            "n_expostas_a_inferencia": ag_exposta,
            "pct_expostas": round(100 * ag_exposta / max(len(agenda_pub), 1), 1),
            "n_sobrevivem_so_observado": ag_sobrevive,
            "pct_sobrevivem": round(100 * ag_sobrevive / max(len(agenda_pub), 1), 1),
        },
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    p = out["proveniencia"]
    s = out["sobrevivencia"]
    a = out["agenda_publicada"]
    print(f"proveniência: {p['pct_observado']}% observado · {p['pct_inferido']}% inferido "
          f"({p['contagem']})")
    print(f"candidatas: todos={len(cand_all)} · só-observado={len(cand_obs)} "
          f"· Jaccard={s['jaccard']}")
    print(f"expostas à inferência: {s['n_candidatas_expostas_a_inferencia']} "
          f"({s['pct_candidatas_expostas']}%)")
    print(f"agenda publicada: {a['n']} alvos · {a['pct_expostas']}% expostos "
          f"· {a['pct_sobrevivem']}% sobrevivem só-observado")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
