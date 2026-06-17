"""Camada de pontes de ordem superior — integração por condutância real (H5).

Fixtures sintéticas (sem rede/modelo) + invariantes do artefato versionado. Cobre:
candidata cross-silo de face ausente, INTEGRAÇÃO posicional (ΔKf: hub→≈0, ponte de gap→alto),
determinismo do nulo casado em grau, tiers da agenda (rebatizado, sem 'sólida'), validação
temporal sem dados, integridade do JSON (0 além do acaso) e zero ID inventado.
"""
import collections
import itertools
import json
import os

import pytest

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
    assert solidity.rank_agenda(cands, CFG) == (0, 0)


def test_candidata_cross_silo_face_ausente():
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd"}
    cands = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    assert len(cands) == 1 and cands[0]["membros"] == ["A", "B", "C"]


def test_integracao_posicional_hub_vs_ponte():
    """H5 — condutância real é POSICIONAL, não de grau: realizar a aresta de um HUB (já
    de baixa resistência) integra ~0; realizar uma aresta entre duas obras PERIFÉRICAS e
    distantes (gap real entre silos) integra muito mais."""
    pytest.importorskip("numpy")  # integration_scores usa numpy (ausente no build mínimo)
    pw = collections.Counter()
    for x in ("c1", "c2", "c3"):
        pw[frozenset(("HC", x))] = 5          # hub Cyb denso
    for x in ("r1", "r2", "r3"):
        pw[frozenset(("HR", x))] = 5          # hub Reg denso
    pw[frozenset(("HC", "HR"))] = 5           # silos ligados pelos hubs (baixa resistência)
    pw[frozenset(("c1", "PC"))] = 1           # PC periférica, elo fraco
    pw[frozenset(("r1", "PR"))] = 1           # PR periférica, elo fraco
    axis_of = {"HC": "Cyb", "c1": "Cyb", "c2": "Cyb", "c3": "Cyb", "PC": "Cyb",
               "HR": "Reg", "r1": "Reg", "r2": "Reg", "r3": "Reg", "PR": "Reg", "Z": "PolInd"}
    # 'Z' (PolInd) é isolada -> fica fora do componente gigante; só o par-chave conta
    ponte = {"membros": ["PC", "PR", "Z"], "eixos": ["Cyb", "PolInd", "Reg"]}
    hub = {"membros": ["HC", "HR", "Z"], "eixos": ["Cyb", "PolInd", "Reg"]}
    meta = solidity.integration_scores([ponte, hub], axis_of, pw, CFG)
    assert meta["n_nos_grafo"] >= 6
    assert ponte["integracao"] > hub["integracao"]        # gap periférico >> aresta de hub
    assert hub["integracao"] >= 0


def test_integracao_deterministica():
    """Mesma seed → mesmos integracao e integracao_z (nulo casado em grau reprodutível)."""
    pytest.importorskip("numpy")  # integration_scores usa numpy (ausente no build mínimo)
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}, {"A", "D"}, {"B", "D"}]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd", "D": "Reg"}
    c1 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    c2 = solidity.gen_candidates(edges, axis_of, _pair_w(edges), CFG)
    solidity.integration_scores(c1, axis_of, _pair_w(edges), CFG)
    solidity.integration_scores(c2, axis_of, _pair_w(edges), CFG)
    assert [c["integracao"] for c in c1] == [c["integracao"] for c in c2]
    assert [c["integracao_z"] for c in c1] == [c["integracao_z"] for c in c2]


def test_rank_agenda_tiers():
    """Rebatizado (H5): AGENDA = alta integração (top-ΔKf) E plausível (faixa). Sem 'sólida'.
    quadrante = costura_ouro (alto+plausível), agenda_pesquisa (alto, fora da faixa),
    fechamento_trivial (plausível, integra pouco), ruido_quimera (resto)."""
    def mk(integ, sem):
        return {"membros": ["A", "B", "C"], "eixos": ["Cyb", "Reg"], "latente": 0.0,
                "integracao": integ, "sem_na_faixa": sem}
    cands = [mk(10.0, True), mk(10.0, False), mk(1.0, True), mk(1.0, False)]
    n_agenda, n_alto = solidity.rank_agenda(cands, CFG)
    assert n_agenda == 1 and n_alto == 2
    assert [c["quadrante"] for c in cands] == \
        ["costura_ouro", "agenda_pesquisa", "fechamento_trivial", "ruido_quimera"]
    assert cands[0]["agenda"] is True and cands[1]["agenda"] is False


def test_temporal_validation_sem_dados(tmp_path, monkeypatch):
    """Poucos anos de citante → validated=False, sem exceção (resultado válido)."""
    edges = [{"A", "B"}, {"A", "C"}, {"B", "C"}]
    citers = ["c1", "c2", "c3"]
    axis_of = {"A": "Cyb", "B": "Reg", "C": "PolInd"}
    monkeypatch.setattr(data_io, "DATA_DIR", str(tmp_path))   # citer_years.json ausente
    r = solidity.temporal_validation(edges, citers, axis_of, CFG)
    assert r["validated"] is False and "n_train" in r and "n_test" in r


def test_artefato_integridade_e_zero_id_inventado():
    """O bloco versionado tem as chaves do método H5; agenda só com agenda=True; todo membro
    resolve no corpus; honestidade: alem_do_acaso é inteiro ≥ 0 (espera-se 0)."""
    p = os.path.join(ROOT, "data", "solidity_bridges.json")
    if not os.path.exists(p):
        return
    o = json.load(open(p, encoding="utf-8"))
    for k in ["metodo", "config", "integracao", "validacao_temporal", "semantico",
              "n_candidatas", "n_agenda", "n_alta_integracao", "alem_do_acaso", "status",
              "por_quadrante", "agenda", "candidatas"]:
        assert k in o, f"chave ausente: {k}"
    assert isinstance(o["alem_do_acaso"], int) and o["alem_do_acaso"] >= 0
    assert o["integracao"]["n_alem_do_acaso"] == o["alem_do_acaso"]
    assert all(c["agenda"] for c in o["agenda"])
    axis_of = json.load(open(os.path.join(ROOT, "data", "cocitation_hyperedges.json"),
                              encoding="utf-8"))["axis_of"]
    for c in o["candidatas"][:200]:
        for m in c["membros"]:
            assert m in axis_of, f"ID inventado/não-resolvível: {m}"
        assert c["quadrante"] in {"costura_ouro", "agenda_pesquisa", "fechamento_trivial", "ruido_quimera"}
        assert c["confianca_modal"] in {"obra", "autor", "conceito"}
