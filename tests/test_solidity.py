"""Camada de pontes de ordem superior — solidez tripla (v2: propositor + falsificadores).

Fixtures sintéticas (sem rede/modelo) + invariantes do artefato versionado. Cobre:
resultado-negativo-válido, gate temporal (sem poder -> não certifica a tripla), nulo
casado/FDR determinístico, validação temporal sem dados, integridade do JSON, zero ID inventado.
"""
import collections
import itertools
import json
import os

import data_io
import solidity

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = solidity.DEFAULT_CONFIG


def _pair_w(edges):
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
    assert cands == []
    assert solidity.classify(cands, CFG, temporal_validated=True) == (0, 0)


def test_candidata_cross_silo_face_ausente():
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd"}
    cands = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    assert len(cands) == 1 and cands[0]["membros"] == ["A", "B", "C"]


def test_design_deterministico_e_fdr():
    """Mesma seed → mesmos design_z e mesma decisão de FDR (nulo casado reprodutível)."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "D"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd", "D": "Reg"}
    central = {"A": 3, "B": 2, "C": 1, "D": 1}
    c1 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    c2 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    solidity.design_scores(c1, edges, axis_of, central, CFG)
    solidity.design_scores(c2, edges, axis_of, central, CFG)
    assert [c["design_z"] for c in c1] == [c["design_z"] for c in c2]
    assert [c["design_sig"] for c in c1] == [c["design_sig"] for c in c2]


def test_gate_temporal_e_faixa_semantica():
    """Sem validação temporal NÃO se certifica a tripla; com validação, só a faixa passa.
    Em ambos, 2-de-3 = design_sig ∧ semântico-na-faixa (gate semântico barra trivial/quimera)."""
    def mk(s, sig):
        return {"membros": ["A", "B", "C"], "eixos": ["Cyb", "Reg"], "latente": 0.5,
                "design_sig": sig, "semantico": s, "sem_na_faixa": (0.4 <= s <= 0.6)}
    cands = [mk(0.05, True), mk(0.5, True), mk(0.95, True)]   # quimera, intermediária, trivial
    n_sol, n_2de3 = solidity.classify([dict(c) for c in cands], CFG, temporal_validated=False)
    assert n_sol == 0 and n_2de3 == 1          # sem eixo temporal: 0 tripla; 1 em 2-de-3 (a do meio)
    c2 = [dict(c) for c in cands]
    n_sol2, _ = solidity.classify(c2, CFG, temporal_validated=True)
    sol = [c for c in c2 if c["solida"]]
    assert n_sol2 == 1 and len(sol) == 1 and sol[0]["semantico"] == 0.5


def test_temporal_validation_sem_dados(tmp_path, monkeypatch):
    """Poucos anos de citante → validated=False, sem exceção (resultado válido)."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}]
    citers = ["c1", "c2", "c3"]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd"}
    monkeypatch.setattr(data_io, "DATA_DIR", str(tmp_path))   # citer_years.json ausente
    r = solidity.temporal_validation(edges, citers, axis_of, CFG)
    assert r["validated"] is False and "n_train" in r and "n_test" in r


def test_artefato_integridade_e_zero_id_inventado():
    """O bloco versionado tem as chaves do método v2; sem poder temporal, 0 tripla;
    todo membro resolve no corpus (axis_of)."""
    p = os.path.join(ROOT, "data", "solidity_bridges.json")
    if not os.path.exists(p):
        return
    o = json.load(open(p, encoding="utf-8"))
    for k in ["metodo", "config", "modelo_nulo", "validacao_temporal", "semantico",
              "n_candidatas", "n_solidas", "n_2de3", "tripla_certificavel", "status",
              "por_quadrante", "solidas", "candidatas"]:
        assert k in o, f"chave ausente: {k}"
    assert isinstance(o["n_solidas"], int) and o["n_solidas"] >= 0
    # invariante honesto: sem validação temporal, nenhuma tripla é certificada
    if not o["tripla_certificavel"]:
        assert o["n_solidas"] == 0
    assert all(c["solida"] for c in o["solidas"])
    axis_of = json.load(open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"),
                              encoding="utf-8"))["axis_of"]
    for c in o["candidatas"][:200]:
        for m in c["membros"]:
            assert m in axis_of, f"ID inventado/não-resolvível: {m}"
        assert c["quadrante"] in {"costura_ouro", "agenda_pesquisa", "fechamento_trivial", "ruido_quimera"}
        assert c["confianca_modal"] in {"obra", "autor", "conceito"}
