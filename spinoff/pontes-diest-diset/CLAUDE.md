# CLAUDE.md — pontes-diest-diset

Spinoff do projeto "Cibernética · Regulação · Política Industrial" (IPEA/DIEST-COGIT).
**Objetivo:** identificar os autores ativos da DIEST e da DISET, o perfil de produção de
cada diretoria, as **pontes epistêmicas** entre elas, as **zonas de convergência** e as
**colaborações (pares e equipes) em potencial** — usando hipergrafos.

## Regras inegociáveis
1. **Só dado real.** Todo nome, número e obra vem de `data/` (gerado pelos scripts). Nunca
   invente autor, lotação, obra ou id. Se faltar dado, diga que falta.
2. **Ressalva no ponto da afirmação.** Atribuição de diretoria é *inferida* pela produção —
   sempre mostre a coluna de confiança. Ver `METODO.md §5`.
3. **Pessoas reais.** São servidores públicos identificáveis. Trate o resultado como insumo
   para *convite à colaboração*, nunca como avaliação de desempenho individual. Não publique
   rankings de "produtividade" de pessoas.
4. **Prosa em português**, sem anglicismo quando houver termo corrente (corretor, não broker,
   no texto final).
5. Só stdlib no núcleo (`src/`). Bibliotecas pesadas (xgi, networkx, sentence-transformers)
   só em módulos opcionais, com o núcleo funcionando sem elas.

## Mapa
```
src/net.py            GET com cache gzip (data/cache/), NET_OFFLINE=1 = só cache
src/roster.py         1. diretório de pesquisadores ativos  → data/roster.json
src/harvest_repo.py   2. Repositório Ipea (DSpace REST)     → data/repo_items.jsonl.gz, data/repo_persons.json
src/attribute.py      3. identidade + diretoria pela produção → data/authors.json, data/items_tagged.json
src/analysis.py       4. hipergrafos, nulo, zonas, pares/equipes → data/results.json
src/report.py         5. RELATORIO.md
src/openalex_enrich.py 6. (opcional, OPENALEX_API_KEY) referências → acoplamento bibliográfico
src/run_all.py        orquestrador (--from attribute = só offline)
tests/test_core.py    testes offline
```

## Como rodar
```bash
python src/run_all.py --from attribute      # offline, a partir dos dados versionados (~1 min)
python src/run_all.py                       # re-colhe o que faltar (portal + repositório; ~40 min frio)
python -m pytest -q tests                   # ou: python tests/test_core.py
```

## Estado e próximos passos
Ver `docs/ORIENTACAO_CLAUDE_SCIENCE.md` — fila de trabalho priorizada com critérios de pronto.
