"""PR-2 — camada de I/O tolerante (src/data_io.py).

Contrato: derivado OPCIONAL ausente -> default ({} ou o informado) + aviso no
stderr; derivado OBRIGATÓRIO ausente -> erro claro e cedo (SystemExit citando o
arquivo). E o build (build_rayyan) sobrevive a opcional ausente, mas falha
explicitamente sem a fonte curada.
"""
import json

import pytest

import data_io


def test_load_optional_missing_returns_default_and_warns(capsys):
    obj = data_io.load_data("nao_existe_xyz.json", required=False)
    assert obj == {}                                   # default padrão
    assert "opcional ausente" in capsys.readouterr().err


def test_load_optional_missing_custom_default():
    assert data_io.load_data("nao_existe_xyz.json", required=False, default=[]) == []


def test_load_required_missing_raises_clear():
    with pytest.raises(SystemExit) as ei:
        data_io.load_data("nao_existe_obrigatorio.json", required=True)
    assert "nao_existe_obrigatorio.json" in str(ei.value)   # diz QUAL arquivo


def test_load_existing_reads_json():
    R = data_io.load_data("scisci_results.json", required=True)   # fonte curada sempre presente
    assert R.get("corpus_size") == 817


def test_save_data_atomic_roundtrip(tmp_path):
    p = tmp_path / "x.json"
    data_io.save_data(str(p), {"a": 1, "b": [2, 3]})    # caminho absoluto -> passthrough
    assert json.load(open(p, encoding="utf-8")) == {"a": 1, "b": [2, 3]}
    assert not (tmp_path / "x.json.tmp").exists()       # sem lixo do tmp


def test_consolidate_clear_error_when_source_missing(monkeypatch, tmp_path):
    """Sem scisci_results.json, build_rayyan.consolidate() falha CLARO (não opaco)."""
    import build_rayyan
    monkeypatch.setattr(data_io, "DATA_DIR", str(tmp_path))   # data/ vazio
    with pytest.raises(SystemExit) as ei:
        build_rayyan.consolidate()
    assert "scisci_results.json" in str(ei.value)


def test_build_rayyan_survives_missing_optional(monkeypatch):
    """Um derivado OPCIONAL ausente (aqui higher_order_bc.json) não quebra o build."""
    import build_rayyan
    real = data_io.load_data

    def fake(name, required=False, default=None):
        if str(name).endswith("higher_order_bc.json"):       # simula 1 opcional ausente
            return {} if default is None else default
        return real(name, required=required, default=default)

    monkeypatch.setattr(data_io, "load_data", fake)
    works = build_rayyan.tag_ho_bridge(build_rayyan.consolidate())
    assert isinstance(works, list) and len(works) > 0
