# PR-3 — Derivados volumosos fora do versionamento (gitignore)

**Data:** 2026-05-29 · **Sessão:** infra/UX autônoma

## Decisão
Versiona-se o **insumo** (`data/oa_cache/` real + a fonte curada
`data/scisci_results.json`) e **não** os derivados grandes. Limiar: **> 1 MB**.

Único derivado > 1 MB hoje: **`data/author_network.json` (~8,3 MB)** → saiu do git
(`git rm --cached`, mantido em disco). Todos os demais derivados em `data/` são
< 500 KB e **seguem versionados** (baratos, úteis para diff/auditoria).

## Verificação de regenerabilidade (a salvaguarda do handout)
Antes de orfanizar, confirmei que `author_network.json` é **100 % regenerável só do
cache versionado**, sem fetch novo:

- Rodando o produtor em modo cache-only (`OA_OFFLINE=1 python src/author_network.py`)
  o relatório mostra **`new fetches: 0`** em todos os passos (títulos, topics,
  abstracts, autores, snowball, sondagens). Os ~94 k "misses" são autores nunca
  enriquecidos via `/authors/{id}` — ficam com `h_index=0` tanto no arquivo
  committado quanto no regenerado (nenhuma informação é perdida).
- Tempo: **~20 s**.

### Por que NÃO é byte-idêntico ao committado
O arquivo committado tinha `n_authors=94039`; o regenerado dá `94133` (+94, +0,1 %).
O cache **cresceu** depois da última geração do arquivo (outras fases cachearam mais
respostas com `authorships`), então o committado estava levemente **defasado** em
relação ao cache. O cache é a fonte de verdade; o derivado, descartável. O topo do
ranking (`top_cross_axis[0]` = Nam C. Nguyen, score 0.956) é estável.

## Como regenerar
```bash
OA_OFFLINE=1 python src/author_network.py     # só cache, sem rede, ~20s
```
`OA_OFFLINE` (novo em `src/oa.py`, PR-3): no cache-miss devolve `{}` na hora, sem
tocar a rede e sem dormir nos retries — primitivo que o `run_all --offline` (PR-5) e
o guarda-corpo de budget (PR-4) reutilizam.

## CI
`.github/workflows/ci.yml` ganhou um passo que regenera `author_network.json` do
cache (`OA_OFFLINE=1`) **antes** do `pytest` — assim `tests/test_author_network.py`
(que exige o arquivo) segue verde num checkout limpo, e a CI **prova a
regenerabilidade a cada push**. PR-8 substitui este passo pelo smoke completo
`run_all.py --offline`.

## Limite futuro (cache grande)
Quando o `data/oa_cache/` cruzar dezenas de milhares de arquivos e deixar o git
lento, selar fases em packs imutáveis (`data/oa_cache_sealed/fase_N.jsonl.gz`) —
ver §5 do handout. Não necessário nesta sessão.
