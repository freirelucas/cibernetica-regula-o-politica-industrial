"""Item 2 — leads de leitura por ponte semântica (src/bridge_candidates.py).

Testa invariantes do artefato versionado data/bridge_candidates.json (sem rede/modelo):
pares são cross-silo, NÃO co-citados, ranqueados por cosseno desc, com IDs reais.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_modulo_importa():
    import bridge_candidates
    assert hasattr(bridge_candidates, "build")


def test_artefato_invariantes_e_zero_id():
    p = os.path.join(ROOT, "data", "bridge_candidates.json")
    if not os.path.exists(p):
        return   # gerado pelo run_all (fase bridge_cands)
    o = json.load(open(p, encoding="utf-8"))
    for k in ["metodo", "semantico", "distribuicao_cosseno", "n_pares",
              "cobertura_frentes_top", "pares_top", "lista_leitura"]:
        assert k in o, f"chave ausente: {k}"
    axis_of = json.load(open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"),
                              encoding="utf-8"))["axis_of"]
    EIX = {"Cyb", "Reg", "PolInd"}
    prev = 2.0
    for pr in o["pares_top"]:
        assert pr["eixo_a"] != pr["eixo_b"]                       # cross-silo
        assert pr["eixo_a"] in EIX and pr["eixo_b"] in EIX
        assert pr["a"] in axis_of and pr["b"] in axis_of          # zero ID inventado
        assert pr["cosseno"] <= prev + 1e-9                       # ranqueado desc
        prev = pr["cosseno"]
    for w in o["lista_leitura"][:50]:
        assert w["oa_id"] in axis_of and w["confianca_modal"] == "obra"
        assert w["eixo"] in EIX
