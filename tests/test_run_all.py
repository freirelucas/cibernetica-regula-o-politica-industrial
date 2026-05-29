"""PR-5 — orquestrador (src/run_all.py): DAG bem-formado + guarda-corpos.

Os testes são leves (não rodam o funil pesado): validam a estrutura do DAG, a
lógica de pulo por "saída existe", a sanidade que aborta sem a fonte curada, e que
--list/--dry-run saem limpos. O caminho integral "run_all --offline -> reconstrói +
site -> driver headless" é exercido pelo smoke da CI (PR-8) e por test_smoke.py.
"""
import os
import subprocess
import sys

import pytest

import data_io
import run_all

SRC = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src")


def test_dag_well_formed():
    names = [p["name"] for p in run_all.PHASES]
    assert len(names) == len(set(names)), "nomes de fase duplicados no DAG"
    for p in run_all.PHASES:
        assert os.path.exists(os.path.join(SRC, p["script"])), f"script ausente: {p['script']}"
        assert p["writes"], f"fase sem saídas declaradas: {p['name']}"
        assert "network" in p
    # a última fase é o site e sempre roda (reconstrói docs/)
    assert run_all.PHASES[-1]["name"] == "site"
    assert run_all.PHASES[-1].get("always") is True


def test_is_stale_logic(tmp_path, monkeypatch):
    monkeypatch.setattr(data_io, "DATA_DIR", str(tmp_path))
    ph = {"name": "x", "script": "z.py", "writes": ["foo.json"], "network": False}
    assert run_all._is_stale(ph, force=False) is True       # saída ausente -> stale
    (tmp_path / "foo.json").write_text("{}")
    assert run_all._is_stale(ph, force=False) is False      # saída existe -> fresh
    assert run_all._is_stale(ph, force=True) is True        # --force -> stale
    always = {"name": "s", "writes": ["docs/x"], "network": False, "always": True}
    assert run_all._is_stale(always, force=False) is True   # always -> sempre stale


def test_sanity_check_clear_error_without_source(tmp_path, monkeypatch):
    monkeypatch.setattr(data_io, "DATA_DIR", str(tmp_path))   # data/ vazio
    with pytest.raises(SystemExit) as ei:
        run_all.sanity_check()
    assert "scisci_results.json" in str(ei.value)


def test_list_and_dry_run_exit_zero():
    r = subprocess.run([sys.executable, os.path.join(SRC, "run_all.py"), "--list"],
                       capture_output=True, text=True, timeout=60)
    assert r.returncode == 0 and "hypergraph" in r.stdout
    r2 = subprocess.run([sys.executable, os.path.join(SRC, "run_all.py"), "--offline", "--dry-run"],
                        capture_output=True, text=True, timeout=120)
    assert r2.returncode == 0 and "site" in r2.stdout
