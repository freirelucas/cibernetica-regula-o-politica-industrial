# Sessão 2026-05-30 — Expansão dirigida (A.3 + A.4 + B.4 + B.5 + D.4)

## TL;DR

Combo de 5 deliverables: A.3 depth-2 snowball expande corpus 6.5×; A.4 Brasil completo resolve 73/73 Faganello; B.4 higher-order betweenness via random walks; B.5 Gould-Fernandez brokerage sobre coauthor graph de 14k autores; D.4 deck reveal.js com 20 slides. Budget OA: 1568/15000 (10.5%). 36 testes verdes. Cache: 20 MB (1637 arquivos).

## API key — ganho decisivo

`OPENALEX_API_KEY` (via `~/.openalex_key` fallback em `src/oa.py`): fetch latency **15.5s → 0.41s** (38× speedup). Sem isso, expansão depth-2 era inviável em 5h.

## A.3 — Depth-2 snowball

`src/depth2_snowball.py`. Para os 600 level-1 works top-prioridade (de 880-1015 disponíveis), fetch `/works?filter=cites:{wid}&sort=cited_by_count&per-page=50`. 300 fetches feitos.

| Métrica | Antes | Depois | Δ |
|---|---|---|---|
| Works com authorships | 2005 | 13018 | +11013 (6.5×) |
| Autores únicos | 1202 | 16105 | +14903 (13.4×) |
| Level-2 únicos | — | 9309 | — |

## A.4 — Brazil full snowball

`src/brazil_snowball.py`. 73/73 Faganello resolvidas (DOI ou search title). 200 BR top-cited via broad search (filter `country_code:BR` + concepts policy/regulation). Top citation bridge: "Brazilian Industrial Policy: A Cluster Analysis…" com 67 citantes de alto-impacto.

Nova seção §12·5 "Corpus Brasil expandido" entre §12 e §13. Tabela métrica + callout top-30 citation bridges. Output `data/brazil_expanded.json`.

## B.4 — Higher-order betweenness

`src/higher_order_betweenness.py`. Random walks no hipergrafo (1000 walks × walk_length 8 × seed 42). Reconstrói 1300+ hiperarestas a partir do cache expandido.

Top-15 HO centrality (corpus expandido revela clássicos antes invisíveis):

| Rank | Obra | Eixo | HO score |
|---|---|---|---|
| 1 | Nelson & Winter · Evolutionary Theory | Cplx | 1.00 |
| 2 | Beer · Heart of Enterprise | Cyb | 0.73 |
| 3 | Systems Thinking, Systems Practice | Cyb | 0.65 |
| 4 | Brain of the firm | Cyb | 0.58 |
| 5 | North · Institutions, Institutional Change | — | 0.49 |
| 6 | David · Clio and the economics of QWERTY | — | 0.47 |
| 7 | Hood · Tools of Government | Reg | 0.47 |
| 8 | The Viable System Model | Cyb | 0.44 |
| 9 | Cohen & Levinthal · Absorptive Capacity | — | 0.44 |
| 10 | Soft Systems Methodology in Action | Cyb | 0.44 |

**Achado**: corpus expandido revela bridges-de-ordem-superior que eram invisíveis (North, David, Cohen-Levinthal, Penrose). Nelson & Winter sobe ao topo — a economia evolucionária É a ponte natural do hipergrafo.

Nova tag Rayyan `ponte de ordem superior`: top-20 com floor 0.05. **8 obras tagueadas** no set curado atual.

## B.5 — Gould-Fernandez brokerage

`src/brokerage_roles.py`. Classifica autores em 5 papéis G-F sobre coauthor graph expandido (14012 autores). Grupo = eixo primário do autor.

| Papel G-F | Triplets | N autores |
|---|---|---|
| coordinator (intra) | 5806 | 249 |
| gatekeeper (out→in) | 340 | 47 |
| representative (in→out) | 281 | 45 |
| liaison (entre 2 outros) | 12 | 5 |
| itinerant (3 grupos) | 13 | 6 |

**Top brokers cross-axis**:
- **Robert Costanza** (PolInd) — 42 gatekeeper + 30 representative + 3 itinerant (ecological economist como ponte)
- **Raúl Espejo** (Cyb) — 26 gate + 21 repr (Cybersyn legacy)
- **Cars Hommes** (PolInd) — 8 liaison (highest liaison count)
- **Florian Kern** (Reg) — sustainability transitions
- **Boulding** — 4 itinerant + 19 gate

**Achado**: coordinator domina amplamente (5806 vs 645 cross-axis triplets) — silo social robusto. Cross-brokerage é raro mesmo no corpus expandido.

Nova subtable em §10·6 ("Tipo de ponte por autor") com totais por papel.

## D.4 — Deck reveal.js

`docs/slides.html`. 20 slides via reveal.js 5.1 CDN (sem build step). Tema black + paleta dos eixos. Cobre: pergunta, método, corpus, silos (z≈80 + z=-50), pontes textuais rejeitadas → ordem superior → humanas, longue-durée 1980s, eco Cybersyn, Brasil, adjacent ausentes, brokerage G-F, HO BC, pipeline SR 14+ tags, implicações NIB, próximos passos, honestidade epistêmica. Link no menu via update do site_template.html (a fazer).

## Achados surpresa

1. **Tradições adjacentes EXISTEM no corpus expandido**: Polanyi 1→3, Schumpeter 2→15, Hirschman 0→9, complexity 3→10, governmentality 0→3. A "ausência" anterior era artefato do corpus pequeno. Ainda assim, presença minoritária (overlap ≤15/50).

2. **Ángela Espinosa** salta para top-2 cross-axis em author_network (era #N/A) — colaboradora histórica de Espejo no MSV/Cybersyn, agora visível por causa do corpus expandido.

3. **Robert Costanza emerge como top broker**: 75+ cross-axis triplets, principalmente como gatekeeper/representative. Ecological economist faz ponte real entre PolInd e Cyb via systems thinking. Não estava no foco anterior.

4. **Nelson & Winter coroa o HO_BC ranking** — economia evolucionária é mais central no hipergrafo do que parecia no pairwise. North e David (path dependency / QWERTY) também emergem.

5. **Coordinator triplets aumentam mais que cross-axis**: 5806 coordinator vs 645 cross. Razão ~9:1. Confirma silos social no plano expandido.

## Balanço de features (delta da Fase E)

| Feature | Antes Fase E | Pós Fase E |
|---|---|---|
| Corpus works c/ authorships | 880 | **13018** (6.5×) |
| Autores únicos | 817 | **16105** (13.4×) |
| Tag `ponte de ordem superior` | — | **8 obras** (B.4) |
| Tag `obra de autor-ponte` | 34 | 10 (top-30 deslocou) |
| Cache OA | 1.9 MB | **20 MB** (10×) |
| §10·6 brokerage subtable | — | nova |
| §12·5 Brasil expandido | — | nova |
| docs/slides.html (D.4) | — | 20 slides nova |

## Budget e segurança

- Fetches OA novos: **1568/15000** (10.5% do cap)
- Cache: **20 MB / 200 MB** (10%) · **1637 arquivos / 15000** (10.9%)
- Tempo: ~12 turnos efetivos (com paralelização)
- Sem merges para main, sem deleção de cache, sem modificação de scisci_results.json
- API key adicionada via `~/.openalex_key` (fora do repo)

## Caveats

1. **Random walks no HO BC são heurísticos** — Estrada-Vega exato seria via matrix powers. Para 220 nodes seria viável; aqui usei aprox.
2. **Brokerage para 14k autores levou ~30s** — escalável até corpus de ~100k.
3. **§10·6 ainda usa vocab em título** — extensão para concepts é próxima iteração.
4. **Adjacent traditions ainda <20% overlap** — para verdadeira integração, precisaríamos rerodar pipeline COM Polanyi/Schumpeter/Hirschman como sementes oficiais.

## Próximos passos

1. **Merge do PR pendente** (#19 Fase D + este novo PR) para main → deploy GH Pages
2. **Classificador via concepts** (próxima sondagem natural — corpus já está expandido)
3. **Adjacent traditions como sementes oficiais** — caso queira reframe completo
4. **Refinement do HO BC** — Estrada-Vega exato para corpus < 500 nodes
