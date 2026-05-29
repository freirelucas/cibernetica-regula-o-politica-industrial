"""PR-4 — instrumentação de custo da API (src/budget.py + guarda-corpo em oa.get).

Contrato: soma meta.cost_usd dos fetches NÃO-cacheados; respeita o teto diário
(OA_DAILY_CAP_USD); NÃO conta acertos de cache; o livro é estado efêmero diário.
"""
import pytest

import budget
import oa


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    """Redireciona o livro para um arquivo temporário (não toca data/oa_budget.json)."""
    monkeypatch.setattr(budget, "LEDGER", str(tmp_path / "oa_budget.json"))
    monkeypatch.delenv("OA_DAILY_CAP_USD", raising=False)
    return tmp_path / "oa_budget.json"


def test_add_cost_sums_meta_cost_usd(ledger):
    budget.add_cost("https://api.openalex.org/works?filter=cites:W1", {"meta": {"cost_usd": 0.0001}})
    budget.add_cost("https://api.openalex.org/works?search=foucault", {"meta": {"cost_usd": 0.001}})
    assert abs(budget.used_today() - 0.0011) < 1e-9
    st = budget.budget_status()
    assert st["by_endpoint"]["filter"] == 0.0001
    assert st["by_endpoint"]["search"] == 0.001
    assert st["cap_usd"] == budget.DEFAULT_CAP_USD


def test_classify_filter_vs_search():
    assert budget.classify("https://api.openalex.org/works?filter=cites:W1") == "filter"
    assert budget.classify("https://api.openalex.org/works?search=x") == "search"
    assert budget.classify("https://api.openalex.org/works?group_by=type") == "group_by"


def test_estimate_when_meta_absent(ledger):
    c = budget.add_cost("https://api.openalex.org/works?search=x", {})   # sem meta -> estima
    assert c > 0 and budget.used_today() == c


def test_cap_respected(ledger, monkeypatch):
    monkeypatch.setenv("OA_DAILY_CAP_USD", "0.0005")
    assert budget.over_cap() is False
    budget.add_cost("https://api.openalex.org/works?filter=x", {"meta": {"cost_usd": 0.001}})  # acima do teto
    assert budget.over_cap() is True


def test_oa_get_blocks_when_over_cap(monkeypatch):
    """Acima do teto e sem cache: oa.get devolve {} SEM tocar a rede."""
    monkeypatch.delenv("OA_OFFLINE", raising=False)
    monkeypatch.setattr(oa, "_read_cache", lambda cf: None)          # garante cache-miss
    monkeypatch.setattr(budget, "over_cap", lambda: True)
    assert oa.get("https://api.openalex.org/works?filter=cites:W999999999&_pr4=1") == {}


def test_oa_get_cache_hit_does_not_count_cost(monkeypatch):
    """Acerto de cache devolve o cacheado e NÃO chama budget.add_cost."""
    monkeypatch.setattr(oa, "_read_cache", lambda cf: {"results": [], "meta": {"cost_usd": 9.9}})
    called = {"n": 0}
    monkeypatch.setattr(budget, "add_cost", lambda *a, **k: called.__setitem__("n", called["n"] + 1))
    out = oa.get("https://api.openalex.org/works?filter=cites:W1")
    assert out == {"results": [], "meta": {"cost_usd": 9.9}}
    assert called["n"] == 0
