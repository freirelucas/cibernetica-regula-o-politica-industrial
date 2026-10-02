---
name: pontes
description: Roda, depura e interpreta o mapeamento DIEST × DISET (autores ativos, produção característica, hipergrafos de coautoria/vocabulário, zonas de convergência, colaboradores e equipes potenciais). Use ao pedir "rodar as pontes", "quem colabora com quem", "zonas de convergência", "atualizar relatório", ou ao mexer em src/attribute.py / src/analysis.py.
---

# /pontes — pipeline e leitura

Ordem canônica (cada etapa lê só o que a anterior escreveu):

| etapa | script | lê | escreve | rede? |
|---|---|---|---|---|
| 1 | roster.py | portal Ipea | data/roster.json | sim (cache) |
| 2 | harvest_repo.py | API DSpace | data/repo_items.jsonl.gz, data/repo_persons.json | sim (cache) |
| 3 | attribute.py | 1+2 | data/authors.json, data/items_tagged.json | não |
| 4 | analysis.py | 3 | data/results.json | não |
| 5 | report.py | 4 | RELATORIO.md | não |
| 6* | openalex_enrich.py | 3 | data/openalex_*.json | sim, exige OPENALEX_API_KEY |

```bash
python src/run_all.py --from attribute     # padrão: offline
python tests/test_core.py || python -m pytest -q tests
```

## Ao interpretar
- Sempre cite a **confiança** da atribuição; `moderada` = conferir com a chefia.
- z do nulo de hiperarestas mistas: **muito negativo = silos**; perto de 0 = mistura ao acaso.
- Par potencial é **hipótese de conversa**, nunca juízo sobre pessoas.
- Mudou um limiar (MIN_SHARE, HALF_LIFE, Jaccard 0,3)? Rode de novo e registre a
  sensibilidade em METODO.md — não troque o número no texto à mão.
