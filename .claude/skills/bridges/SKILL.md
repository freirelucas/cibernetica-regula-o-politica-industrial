---
name: bridges
description: Documenta a cadeia das pontes epistêmicas (hipergrafo de cocitação -> HO-BC -> prioridade/brokerage -> Rayyan -> site), a ordem canônica de execução e os JSONs lidos/escritos. Use ao rodar ou depurar a análise de pontes, ao perguntar "qual a ordem" ou "quem escreve qual JSON", ou ao planejar a modelagem futura (solidez tripla + cesta).
---

# /bridges — a cadeia das pontes entre cibernética × regulação × política industrial

Estado-alvo ("goal"): **a análise de pontes roda numa ordem canônica, cada etapa lê
e escreve JSONs declarados, e o orquestrador (`src/run_all.py`) a executa do insumo
ao site** — sem ordem tácita nas notas, sem reconstrução enviesada (dívida do PR-1
saldada).

## A cadeia (ordem canônica)

```
data/scisci_results.json + data/oa_cache/   (insumos versionados)
        │
        ├─ experiment_cplx.py     → network_4axis.json     (rede dos 4 eixos; base do explorador)
        ├─ cocitation_hypergraph.py → cocitation_hyperedges.json   (HIPERGRAFO: hyperedges + axis_of + null model)
        ├─ author_network.py      → author_network.json     (rede de coautoria; gitignored, regenerável)
        │
        ├─ higher_order_betweenness.py → higher_order_bc.json   (HO-BC sobre as hiperarestas canônicas)
        ├─ bridge_priority.py     → bridge_priority.json     (prioridade de ponte = HO + alcance + cyb + papel)
        ├─ brokerage_roles.py     → brokerage_roles.json     (papéis Gould-Fernandez de corretagem)
        │
        ├─ build_rayyan.py        → docs/dados/rayyan_*.{ris,csv,…} + rayyan_tags.json  (síntese p/ triagem)
        └─ build_site.py          → docs/{index,explorador,triagem}.html               (site + UX)
```

| Script | Lê | Escreve |
|---|---|---|
| `cocitation_hypergraph.py` | `network_4axis.json`, cache (`oa.get`) | `cocitation_hyperedges.json` (campo **`hyperedges`** + `edge_to_citer` + `axis_of`) |
| `higher_order_betweenness.py` | **`cocitation_hyperedges.json:hyperedges`** | `higher_order_bc.json` (`top_30`, `by_oa_id`) |
| `bridge_priority.py` | `cocitation_hyperedges.json`, `network_4axis.json`, `build_rayyan.build()` | `bridge_priority.json` (`ranking`, `by_oa_id`) |
| `brokerage_roles.py` | `author_network.json` | `brokerage_roles.json` |
| `build_rayyan.py` | os ~12 derivados (via `data_io`) | `rayyan_*.*`, `rayyan_tags.json`, `rayyan_sintese.provenance.json` |
| `build_site.py` | `scisci_results.json`, redes, derivados | `docs/*.html` (injeta sinais na triagem) |

## Rodar

```bash
python src/run_all.py --offline      # reconstrói tudo SÓ do cache (zero rede/budget) + site
python src/run_all.py --list         # mostra o DAG
python src/run_all.py --force        # re-roda tudo (online, p/ consistência total)
```
Pula fases cuja saída já existe; regenera só o que falta (ex.: `author_network.json`).

## Dívida do PR-1 — SALDADA

`higher_order_betweenness.py` agora **lê o campo `hyperedges`** de
`cocitation_hyperedges.json` (persistido desde o marco M1). Antes ele reconstruía as
hiperarestas varrendo TODO o `data/oa_cache/` — incluía citantes de consultas alheias
às 13 sementes e contava repetidos (~7,9k hiperarestas contra ~1,3k canônicas). Era
enviesado; o ranking HO-BC mudou de propósito (faz emergir Mazzucato, Beer, Kuhn,
North, Dosi). **Não reintroduza a varredura do cache aqui.**

## Camada de solidez tripla — v1 IMPLEMENTADA (`src/solidity.py`, fase `solidity`)

Prediz hiperarestas AUSENTES que costurariam os silos e reporta só as SÓLIDAS
(passam nos 3 testes independentes), gravando `data/solidity_bridges.json` (+ CSVs
12/13 em `docs/dados/` + seção `#pontes-ordem-superior` no site + os 3 escores no
cartão da triagem, atalho "Passa nos três"). Limiares calibráveis em
`data/solidity_config.json`.

  - **DESIGN** — ganho de integração candidata-específico (raridade do cruzamento ×
    centralidade cross-silo dos membros) z vs modelo nulo (`seed=42`).
  - **LATENTE** — fechamento simplicial (harmônica das 3 subfaces) + **holdout
    temporal** (`data/citer_years.json`, recrawl barato; treina ≤T, testa >T).
  - **SEMÂNTICO** — Jaccard de tópicos + embeddings fortes (sentence-transformers,
    enriquecendo só os membros das candidatas); **faixa intermediária** por percentis.
  - Quadrantes: `costura_ouro` / `agenda_pesquisa` / `fechamento_trivial` / `ruido_quimera`.
    **Resultado NEGATIVO é válido** (lista vazia, sem erro). Confiança modal exposta.

Decisões honradas: silos = `axis_of` (não Leiden novo); v1 = tríades obra-só; saída em
derivado próprio (scisci_results.json intocada); embeddings com **escores versionados**
→ `run_all --offline` PULA a fase (saída existe) e a CI não baixa o modelo.

**Falta para v2 (semi-assistida — Lucas calibra):** candidatas MULTIMODAIS
(`{autor, conceito, obra}` — a tabela de incidência + `confianca_modal` já preparam);
**cesta ótima** submodular (greedy 1−1/e, cobertura dos 3 pares de eixos + orçamento de
leitura + custo) empilhada SOBRE o conjunto sólido; calibração fina da faixa/limiares
contra o holdout.

## Gotchas

- O `z` do modelo nulo é **negativo** (stub-shuffle ≈ −50; Chung-Lu ≈ −76): o
  observado trans-eixo está MUITO ABAIXO do acaso — estrutura de silos real, não +80.
- HO-BC roda com `seed=42` (determinístico). `bridge_priority` pesa `ho=0.40,
  reach=0.30, cyb=0.15, role=0.15`.
- Verificado nesta sessão: `run_all --offline` reconstrói + site, driver headless OK.
