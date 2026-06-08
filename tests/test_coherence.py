"""Coerência CRUZADA entre os artefatos — guarda contra o estado 'Frankenstein'
(JSONs de janelas/recortes diferentes costurados).

Os números exatos vivem em test_dados/test_reframe; aqui o foco é a consistência
ENTRE os artefatos: o relatório e os derivados têm de partir do MESMO conjunto de
sementes (as 60 do minirun) e estar limpos. Offline (só lê data/).
"""
import json
import os

import minirun

CORE = {"Cyb", "Reg", "PolInd"}


def test_relatorio_usa_as_60_sementes_do_minirun(results):
    """As sementes do resumo têm de ser exatamente as 60 do eixo-núcleo do minirun."""
    core = {wid for wid, (_lbl, ax) in minirun.SEEDS.items() if ax in CORE}
    assert len(core) == 60
    assert {s["id"] for s in results["seeds"]} == core, \
        "as sementes do relatório divergem da fonte única (incoerência de recorte)"


def test_derivados_presentes_e_nao_vazios(root):
    """A cadeia de pontes + brokerage têm de existir e não estar vazias."""
    for name in ("cocitation_hyperedges.json", "higher_order_bc.json",
                 "bridge_priority.json", "brokerage_roles.json"):
        p = os.path.join(root, "data", name)
        assert os.path.exists(p), f"derivado ausente: {name}"
        with open(p, encoding="utf-8") as f:
            assert json.load(f), f"derivado vazio: {name}"


def test_resumo_sem_lixo_de_pandas(results):
    """Nenhum repr de pandas (Index/dtype) pode ter vazado para os campos string
    do resumo — ex.: o bug do sleeping_beauties[].axes (paper.axes)."""
    blob = json.dumps(results, ensure_ascii=False)
    assert "Index(" not in blob and "dtype=" not in blob, "lixo de pandas no resumo"
