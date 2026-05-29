---
name: oa-budget
description: Diz quanto se gastou na API OpenAlex hoje e se cabe rodar uma fase nova, e aplica o teto diário (guarda-corpo do modo autônomo). Use ao perguntar "quanto gastei", "cabe rodar X?", "qual o teto", ao instrumentar custo, ou ao investigar por que oa.get parou de buscar.
---

# /oa-budget — custo das consultas OpenAlex instrumentado, com teto diário

Estado-alvo ("goal"): **todo fetch não-cacheado tem seu custo contado num livro
diário (`data/oa_budget.json`) e há um teto rígido (`OA_DAILY_CAP_USD`, padrão
US$1,00)** — dá para responder "quanto gastei / cabe rodar X?" e o modo autônomo
não estoura o orçamento (ao bater o teto, `oa.get()` para de buscar e devolve `{}`).

## O que é (PR-4)

- `src/budget.py` — o livro-razão. O OpenAlex devolve `meta.cost_usd` em cada
  resposta (filtro ~US$0.0001; **search ~10× mais caro**); `add_cost()` soma o custo
  dos fetches **não-cacheados** em `data/oa_budget.json` (`{date, used_usd,
  by_endpoint}`), que **reseta por dia**.
- `src/oa.py` `get()` — antes de buscar um não-cacheado, consulta `budget.over_cap()`;
  se já bateu o teto, devolve `{}` com aviso no stderr (não busca). Depois de um
  fetch bem-sucedido, chama `budget.add_cost(url, data)`. **Acertos de cache NÃO
  contam** (nem tocam a rede).
- `src/run_all.py` — antes de cada fase de REDE consulta `budget_status()` e pula a
  fase se o teto estourou; pré-estima volume com 1 `group_by` (custo de 1 filtro, §5.2).

`data/oa_budget.json` é **estado efêmero → gitignored**.

## Como usar

```bash
python src/budget.py                                  # resumo do dia (used/cap/restante/by_endpoint)
python -c "import sys;sys.path.insert(0,'src');import budget;print(budget.budget_status())"
OA_DAILY_CAP_USD=0.25 python src/run_all.py           # roda com teto menor (online)
python src/run_all.py --offline                       # zero rede, zero gasto (cache-only)
```

"Cabe rodar X?" → veja `remaining_usd` no `budget_status()`; para estimar X, rode 1
`group_by` (ex.: `cites:<semente>&group_by=publication_year`) — é o custo de 1
filtro e dá o volume de citantes antes de comprometer o crawl.

## Gotchas

- **OpenAlex não tem endpoint `/rate-limit`** (o handout supôs): `budget_status()`
  reporta o **livro local** (a fonte de verdade do teto); `probe_cost()` faz 1
  chamada barata real só para conferir o custo marginal/conectividade.
- **Reseta por dia** (campo `date`): o teto é diário, não acumulado.
- **Fail-open:** erro no livro nunca derruba o funil (`over_cap()` → `False`), então
  o teto é proteção, não ponto único de falha. Para parar de vez, use `--offline`.
- **Cache não conta:** reprocessar do cache é grátis; só o fetch novo soma.
- Verificado nesta sessão: soma `meta.cost_usd`, respeita o teto (mock acima do cap
  devolve `{}`), não conta acerto de cache; `data/oa_budget.json` no `.gitignore`.
