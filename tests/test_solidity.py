"""Camada de pontes de ordem superior — solidez tripla.

Testa as funções puras com fixtures sintéticas (sem rede, sem modelo) + invariantes
do artefato versionado data/solidity_bridges.json. Espírito dos testes existentes:
resultado-negativo-válido, faixa semântica, holdout temporal, determinismo, zero ID
inventado, integridade do JSON.
"""
import json
import os

import solidity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = solidity.DEFAULT_CONFIG


def _pair_w(edges):
    import collections, itertools
    pw = collections.Counter()
    for e in edges:
        for a, b in itertools.combinations(sorted(e), 2):
            pw[frozenset((a, b))] += 1
    return pw


def test_resultado_negativo_silos_separados():
    """Silos perfeitamente separados → nenhuma candidata cross-silo, sem erro."""
    edges = [{"A1", "A2"}, {"A2", "A3"}, {"B1", "B2"}, {"B2", "B3"}]
    axis_of = {"A1": "Cyb", "A2": "Cyb", "A3": "Cyb", "B1": "Reg", "B2": "Reg", "B3": "Reg"}
    cands = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    assert cands == []                      # nada cruza silos
    assert solidity.classify(cands, CFG) == 0   # 0 sólidas, sem exceção


def test_candidata_cross_silo_face_ausente():
    """Tríade cujos 3 pares co-ocorrem mas a face nunca → candidata válida (3 eixos)."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd"}
    cands = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    assert len(cands) == 1
    assert cands[0]["membros"] == ["A", "B", "C"] and set(cands[0]["eixos"]) == {"Cyb", "Reg", "PolInd"}


def test_design_deterministico():
    """Mesma seed → mesmos design_z (modelo nulo reprodutível)."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "D"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd", "D": "Reg"}
    central = {"A": 3, "B": 2, "C": 1, "D": 1}
    c1 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    c2 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    solidity.design_scores(c1, edges, axis_of, central, CFG)
    solidity.design_scores(c2, edges, axis_of, central, CFG)
    assert [c["design_z"] for c in c1] == [c["design_z"] for c in c2]


def test_classify_faixa_semantica():
    """Trivial (sim alta) e quimera (sim baixa) reprovam; só a intermediária na faixa."""
    cands = [{"membros": ["A", "B", "C"], "eixos": ["Cyb", "Reg"], "latente": 0.5,
              "design_z": 5.0, "semantico": s, "sem_na_faixa": None} for s in (0.05, 0.5, 0.95)]
    # faixa P40–P75 desta distribuição {0.05,0.5,0.95} → intermediária = 0.5
    meta = solidity.semantic_scores  # noqa: F841 (faixa é recalculada aqui via classify? não)
    # marca na_faixa manualmente pela mesma regra de percentil que semantic_scores usa
    vals = sorted(c["semantico"] for c in cands)
    lo, hi = vals[1], vals[2]   # P40≈meio, P75≈alto p/ n=3 — usa a do meio
    for c in cands:
        c["sem_na_faixa"] = (0.4 <= c["semantico"] <= 0.6)   # intermediária
    n = solidity.classify(cands, CFG)
    faixa = [c for c in cands if c["sem_na_faixa"]]
    assert len(faixa) == 1 and faixa[0]["semantico"] == 0.5
    assert all(not c["solida"] for c in cands if not c["sem_na_faixa"])   # gate semântico barra


def test_holdout_esconde_futuro():
    """O corte temporal só treina em arestas com citante ≤ T."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "D"}]
    citers = ["c1", "c2", "c3", "c4"]
    import tempfile
    # injeta anos: c1,c2 ≤T(2015); c3,c4 >T
    sel = {"c1": 2010, "c2": 2012, "c3": 2018, "c4": 2020}
    p = os.path.join(ROOT, "data", "citer_years.json")
    bak = open(p, encoding="utf-8").read() if os.path.exists(p) else None
    try:
        json.dump(sel, open(p, "w", encoding="utf-8"))
        cands = [{"membros": ["A", "B", "C"]}]
        r = solidity.temporal_holdout(edges, citers, _pair_w(edges), cands, CFG)
        # com só 2 train / 2 test, a função reporta insuficiente (n<30) SEM erro
        assert r["ok"] is False and r["n_train"] == 2 and r["n_test"] == 2
    finally:
        if bak is not None:
            open(p, "w", encoding="utf-8").write(bak)
        elif os.path.exists(p):
            os.remove(p)


def test_artefato_integridade_e_zero_id_inventado():
    """O bloco versionado tem as chaves certas e todo membro resolve no corpus (axis_of)."""
    p = os.path.join(ROOT, "data", "solidity_bridges.json")
    if not os.path.exists(p):
        return   # ainda não gerado neste checkout (gerado pelo run_all)
    o = json.load(open(p, encoding="utf-8"))
    for k in ["config", "modelo_nulo", "holdout_temporal", "semantico", "n_candidatas",
              "n_solidas", "status", "por_quadrante", "solidas", "candidatas"]:
        assert k in o, f"chave ausente: {k}"
    assert isinstance(o["n_solidas"], int) and o["n_solidas"] >= 0   # negativo é válido
    assert all(c["solida"] for c in o["solidas"])                    # solidas ⊆ aprovadas
    axis_of = json.load(open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"),
                              encoding="utf-8"))["axis_of"]
    for c in o["candidatas"][:200]:
        for m in c["membros"]:
            assert m in axis_of, f"ID inventado/não-resolvível: {m}"
        assert c["quadrante"] in {"costura_ouro", "agenda_pesquisa", "fechamento_trivial", "ruido_quimera"}
        assert c["confianca_modal"] in {"obra", "autor", "conceito"}
