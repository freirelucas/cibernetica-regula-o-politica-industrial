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

## Ponto de extensão — a modelagem futura (§7 do handout; NÃO implementada)

A próxima sessão (semi-assistida, Lucas calibra) empilha SOBRE esta cadeia:

1. **Solidez tripla** (filtra candidatas trans-eixo): estrutural Δ-design (queda de
   condutância vs. modelo nulo), latente (fechamento harmônico de Benson 2018, holdout
   temporal, AUC-PR) e semântica (faixa-passa de embeddings/`topics`, ortogonal à
   citação). Resultado negativo (`S=∅`) é válido — nunca enfraquecer um teste.
2. **Cesta ótima** empilhada sobre `S` (submodular *greedy* 1−1/e, com cobertura dos
   3 pares de eixos + orçamento de leitura + custo de aquisição).

**Encaixes já prontos (esta sessão deixou):**
- `data_io` (PR-2) → novos JSONs (`closure/design/semantic/solidity/basket.json`)
  entram sem mexer em `build_site`.
- Cartão da triagem (PR-7) já reserva os **3 indicadores** (estrutural/latente/
  semântico) + o atalho "Passa nos três".
- `run_all.py` (PR-5) → as fases da modelagem encaixam como novos nós do DAG.
- **Preservar a confiança modal** (obra > autor > conceito) nos dados — a cesta
  vai querer ponderar por isso.

## Gotchas

- O `z` do modelo nulo é **negativo** (stub-shuffle ≈ −50; Chung-Lu ≈ −76): o
  observado trans-eixo está MUITO ABAIXO do acaso — estrutura de silos real, não +80.
- HO-BC roda com `seed=42` (determinístico). `bridge_priority` pesa `ho=0.40,
  reach=0.30, cyb=0.15, role=0.15`.
- Verificado nesta sessão: `run_all --offline` reconstrói + site, driver headless OK.
