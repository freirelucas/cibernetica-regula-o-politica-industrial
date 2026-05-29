"""PR-4 — instrumentação de custo da API OpenAlex (guarda-corpo do piloto automático).

O OpenAlex devolve `meta.cost_usd` em cada resposta (filtros ~US$0.0001; search ~10×
mais caro). Aqui acumulamos o custo das respostas NÃO-CACHEADAS num livro-razão
diário (data/oa_budget.json) e expomos um teto rígido (OA_DAILY_CAP_USD, padrão
1.00): ao ultrapassar, oa.get() para de buscar não-cacheados e devolve {} com aviso.

Contrato:
  - Acertos de cache NÃO contam (não tocam a rede) — a contagem é feita só por
    oa.get() após um fetch real bem-sucedido.
  - O livro reseta por DIA (campo `date`); é estado efêmero -> gitignored.
  - Falhas do livro são fail-open (não derrubam o funil): over_cap() devolve False
    em erro; add_cost() engole exceções. O teto é proteção, não ponto único de falha.

Divergência do handout (o código vence): o OpenAlex NÃO expõe um endpoint
`/rate-limit`; budget_status() reporta o livro LOCAL (fonte de verdade do teto).
probe_cost() faz 1 chamada barata real e devolve o meta.cost_usd marginal, quando
se quer confirmar custo/conectividade.
"""
import datetime
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEDGER = os.path.join(ROOT, "data", "oa_budget.json")
DEFAULT_CAP_USD = 1.00


def daily_cap():
    try:
        return float(os.environ.get("OA_DAILY_CAP_USD", DEFAULT_CAP_USD))
    except (TypeError, ValueError):
        return DEFAULT_CAP_USD


def _today():
    return datetime.date.today().isoformat()


def _load():
    try:
        d = json.load(open(LEDGER, encoding="utf-8"))
    except Exception:
        d = {}
    if not isinstance(d, dict) or d.get("date") != _today():   # reset diário
        d = {"date": _today(), "used_usd": 0.0, "by_endpoint": {}}
    d.setdefault("used_usd", 0.0)
    d.setdefault("by_endpoint", {})
    return d


def _save(d):
    try:
        os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
        tmp = LEDGER + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=1)
        os.replace(tmp, LEDGER)
    except Exception:
        pass


def classify(url):
    """Tipo de consulta — base do by_endpoint e da estimativa de custo."""
    u = url or ""
    if "group_by=" in u or "group-by=" in u:
        return "group_by"
    if "search=" in u:
        return "search"
    if "filter=" in u:
        return "filter"
    if "/authors/" in u or "/works/" in u:
        return "single"
    return "other"


# estimativa de fallback quando a resposta não traz meta.cost_usd
_EST = {"search": 0.001, "filter": 0.0001, "group_by": 0.0001, "single": 0.0001, "other": 0.0001}


def estimate_cost(url):
    return _EST.get(classify(url), 0.0001)


def add_cost(url, response=None):
    """Soma o custo de UM fetch não-cacheado ao livro do dia. Usa meta.cost_usd se
    presente; senão estima por tipo de consulta. Devolve o custo somado."""
    try:
        cost = None
        if isinstance(response, dict):
            meta = response.get("meta") or {}
            if isinstance(meta, dict) and isinstance(meta.get("cost_usd"), (int, float)):
                cost = float(meta["cost_usd"])
        if cost is None:
            cost = estimate_cost(url)
        d = _load()
        d["used_usd"] = round(d.get("used_usd", 0.0) + cost, 6)
        ep = classify(url)
        d["by_endpoint"][ep] = round(d["by_endpoint"].get(ep, 0.0) + cost, 6)
        _save(d)
        return cost
    except Exception:
        return 0.0


def used_today():
    return _load().get("used_usd", 0.0)


def over_cap():
    """True se o gasto do dia já alcançou o teto. Fail-open: erro -> False."""
    try:
        return used_today() >= daily_cap()
    except Exception:
        return False


def budget_status():
    """Resumo legível do livro do dia (local, sem rede)."""
    d = _load()
    cap = daily_cap()
    used = d.get("used_usd", 0.0)
    return {
        "date": d["date"],
        "used_usd": round(used, 6),
        "cap_usd": cap,
        "remaining_usd": round(max(cap - used, 0.0), 6),
        "over_cap": used >= cap,
        "by_endpoint": d.get("by_endpoint", {}),
    }


def probe_cost():
    """1 chamada barata real (/works?per-page=1&select=id) -> meta.cost_usd marginal.
    Útil para confirmar custo/conectividade. NÃO conta no livro (é diagnóstico)."""
    import sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import oa
    data = oa.get("https://api.openalex.org/works?per-page=1&select=id", use_cache=False)
    return (data.get("meta") or {}).get("cost_usd") if isinstance(data, dict) else None


if __name__ == "__main__":
    import json as _j
    print(_j.dumps(budget_status(), ensure_ascii=False, indent=2))
