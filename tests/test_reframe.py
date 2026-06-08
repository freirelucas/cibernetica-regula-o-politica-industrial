"""Trava o reframe 20/20/20 + Reg = REGULAÇÃO ECONÔMICA na fonte única (minirun).

Contexto: em jun/2026 o eixo ``Reg`` foi re-semeado como regulação econômica
(Stigler, Peltzman, Posner, Majone, Levi-Faur…) e a tradição "tools of government"
(Hood/Margetts/nodalidade) migrou para o eixo ``Cyb`` (leitura cibernética do
controle estatal). Estes testes impedem uma regressão silenciosa ao esquema
antigo — algo que os testes existentes (que checavam só ``n_seeds == 20``) não
pegavam. São offline (só leem ``src/minirun.py``).
"""
import collections

import minirun

CORE = ("Cyb", "Reg", "PolInd")


def test_seeds_sao_20_20_20():
    por_eixo = collections.Counter(ax for (_lbl, ax) in minirun.SEEDS.values())
    assert por_eixo["Cyb"] == 20, por_eixo
    assert por_eixo["Reg"] == 20, por_eixo
    assert por_eixo["PolInd"] == 20, por_eixo
    assert len(minirun.SEEDS) == 60


def test_reg_e_regulacao_economica():
    reg = " ".join(minirun.VOCAB["Reg"]).lower()
    assert "regulat" in reg
    assert any(k in reg for k in ("antitrust", "competition", "natural monopoly"))
    # a tradição "tools of government" NÃO pode estar no eixo Reg (migrou p/ Cyb)
    for proibido in ("nodality", "tools of government", "policy instrument"):
        assert proibido not in reg, proibido


def test_tools_of_government_migraram_para_cyb():
    cyb = " ".join(minirun.VOCAB["Cyb"]).lower()
    assert "tools of government" in cyb
    assert "nodality" in cyb


def test_axis_of_classifica_segundo_o_reframe():
    assert minirun.axis_of("Theories of economic regulation") == "Reg"
    assert minirun.axis_of("Antitrust and the regulatory state") == "Reg"
    assert minirun.axis_of("Brain of the firm: managerial cybernetics") == "Cyb"
    assert minirun.axis_of("The tools of government in the digital age") == "Cyb"
    assert minirun.axis_of("Industrial policy and the developmental state") == "PolInd"


def test_sementes_reg_sao_economistas_canonicos():
    reg_labels = " ".join(
        lbl for (lbl, ax) in minirun.SEEDS.values() if ax == "Reg"
    ).lower()
    for nome in ("stigler", "peltzman", "posner", "majone", "levi-faur"):
        assert nome in reg_labels, nome
