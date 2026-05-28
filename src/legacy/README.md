# src/legacy — scripts arquivados

Estes scripts foram superseded por implementações mais completas, mas são preservados aqui
para auditoria e rastreio histórico:

| Script | Substituído por | Motivo |
|---|---|---|
| `coauthorship.py` | `src/author_network.py` (Fase D) | Cobertura limitada a 62 nós; author_network cobre 16k autores |
| `enrich_openalex.py` | `src/author_network.py` + `src/build_rayyan.py` | Enrich agora integrado nos scripts principais |
| `explode_snowball.py` | `src/depth2_snowball.py` (Fase E) | Depth-2 com API key é 38× mais rápido e cache-friendly |

**Não rodar destes scripts**. Estão aqui apenas para auditoria. Se precisar reativar, mova de volta para `src/`.
