# Sessão 2026-05-28/29 — Crítica brutal + Tier 1 XGI nativo + paradigma Zajdela

## TL;DR — onde paramos

3 PRs grandes mergeados em main nesta sessão (`PR #22`, `PR #23`, mais o `#21` da checagem). O projeto saiu de "usar XGI como import" para "usar XGI de verdade", expandiu o corpus 6.5× e identificou que estamos no estado da arte **descritivo** mas aquém do paradigma **causal-dinâmico** de Emma Zajdela.

Branch atual: `claude/tier1-xgi-melhorias` (sincronizada com main, zero diff). Tudo limpo para encerrar sessão com segurança.

## Trabalho mergeado nesta sessão

| Commit | PR | Tema |
|---|---|---|
| `c189d57` | #22 | P3+P4+P7: smoke test de tokens + rename pairwise + archive legacy |
| `bc0ba7d` | #22 | P5+P2: split build_site (token_injection) + classifier topics |
| `a28e839` | #22 | P6+P8: vocab adjacente + Estrada-Vega exato via clique expansion |
| `7bfaa03` | #23 | Tier 1 M1+M2+M3+M4+M27: usar XGI de verdade |
| `0997adc` | #23 | Tier 1 M14+M17+M8: 7 sementes faltantes + depth-2 + abstracts |
| `b0827c3` | #23 | M8 abstracts + trim author_network |

39 testes verdes ao longo. Cache: 20 MB → 73 MB (10×). Budget OA: 1829/15000 (12%).

## Aprendizados conceituais (a parte rica)

### 1. Usávamos XGI como import — agora usamos de verdade

**Antes**: `import xgi` aparecia em UM arquivo (`src/cocitation_hypergraph.py:96`) e a única chamada era o construtor `xgi.Hypergraph(edges)`. Construímos o hipergrafo e o jogamos fora.

**Agora** (pós M27 + M1-M4):
- `src/hypergraph_core.py` centraliza 7 funções XGI nativas
- `data/cocitation_hyperedges.json` PERSISTE as hiperarestas (antes só agregados)
- 3 modelos nulos (stub-shuffle + Maslov-Sneppen + Chung-Lu) testando significância
- Comunidades nativas (XGI spectral_clustering) comparadas com nossas Leiden
- Centralidades nativas (h_eigenvector + clique_eigenvector + line_vector_centrality)

**Achado inesperado**: NMI(nossos 3 eixos × XGI spectral communities) = **0.31**. As comunidades estruturais do hipergrafo NÃO se alinham com nossa classificação por vocabulário. Implicação: ou nossos eixos não captam a estrutura, ou XGI agrupa por algo diferente. Para discutir.

### 2. Sementes — Wiener era um buraco embaraçoso

Cienciometria da cibernética **sem Wiener nas sementes** durante quase todo o projeto. Corrigido (M14): 13 → 20 sementes adicionando Wiener (1948), Maturana-Varela (1980), von Foerster, Lascoumes & Le Galès, Salamon, Chang (Kicking Away the Ladder), Evans (Embedded Autonomy).

Justificativa de cada uma documentada em `data/scisci_results.json:seeds`.

### 3. Abstracts mudam a sensibilidade do classifier

`classify_axes(title, topics, abstract_inverted_index)` — três sinais combinados. Resultado: `n_cross_axis_loose` 103 → **397** autores (3.8×). Stiglitz, Jan vom Brocke e outros aparecem nos top-10 cross-axis com abstracts; sem abstracts eram invisíveis.

Lição: vocabulário em título é informacionalmente pobre (~100 chars). Abstract (~500-2000 chars) capta o tema que o título esconde. Pré-Tier 1 estávamos classificando com 10% do sinal disponível.

### 4. Chung-Lu confirma silos com z = −76 (vs stub-shuffle z = −50)

Modelo nulo mais informativo (preserva degree sequences independentes via `xgi.generators.chung_lu_hypergraph`). Z mais negativo = silos estatisticamente MAIS robustos que com null antigo. A estrutura é **dramaticamente mais siloed** do que qualquer null razoável produziria.

### 5. Emma Zajdela como paradigma rigoroso

Identificamos enfim quem é Emma Zajdela: matemática aplicada em Northwestern + Santa Fe Institute, coautora de Landry no XGI. Seu paper paradigmático (Zajdela et al. 2022) é sobre o **Princeton Catalysis Initiative** — um experimento natural de intervenção institucional que demonstra empiricamente que workshops cross-disciplinares aumentam coautoria nos anos seguintes.

A referência "interação prescrita" que aparece em vários callouts do nosso relatório vem dela. Estamos no estado da arte da análise descritiva higher-order, mas **aquém de Zajdela em três dimensões**:

| Critério Zajdela | Status nosso projeto |
|---|---|
| Hipergrafo nativo + null models | ✓ pós Tier 1 |
| Dinâmica temporal (modelo estocástico) | ✗ só descritivo por época |
| Treatment vs control (experimento natural) | ✗ puramente observacional |
| Mecanismo causal testado | ✗ correlações + narrativa |
| População unitária | ✗ Brasil é silo metodológico |
| Predição testável | ✗ descrevemos, não predizemos |

**Score: 4 de 10 critérios atendidos.**

### 6. Três hipóteses testáveis derivadas de Zajdela (próximas sessões)

**H1 — Catalisação institucional histórica**: eventos institucionais brasileiros (Cybersyn, CEPAL, encontros ANPEC, EAESP-FGV anos 1980, OCDE/ILPES) que reuniram pessoas dos 3 eixos aumentaram cocitação cross-axis 5 anos depois?

**H2 — IPEA como broker latente**: IPEA tem cross_axis_score mediano maior que outras instituições brasileiras (BNDES, CEPAL, FGV, USP-FEA)? Testaria empiricamente a tese "IPEA pode ser broker institucional" que hoje é especulativa.

**H3 — NIB 2023 como tratamento prospectivo**: monitorar cocitação cross-axis 2025-2030 para autores próximos à NIB. Protocolo de baseline + cadência trimestral.

## Riscos e dívidas reconhecidas

1. **Honestidade interpretativa**: §11 do site afirma "IPEA pode ser broker institucional" sem qualificar que é hipótese (H2 ainda não testada). Deveria ser qualificada.

2. **Brasil como silo metodológico**: 73 obras Faganello tratadas como corpus paralelo, não como núcleo. Reformulação séria para virar Tier 2 do plano.

3. **Cache cresceu rápido**: 20 MB → 73 MB com Tier 1. Tripwire SKILL marcava "dezenas de milhares de arquivos" como problema futuro. Estamos em 3705 arquivos. Confortável mas vale monitorar.

4. **Author_network.json filtrado** para 8.4 MB (era 33 MB raw). Filtro: n_works ≥ 2 OR cross_axis_score > 0 OR h_index ≥ 5. Excluímos autores de "um único work no corpus" para tamanho gerenciável.

5. **`higher_order_betweenness.py` ainda re-mina cache** em vez de usar `hypergraph_core.load_hyperedges_from_json`. Refator pendente para usar M1.

## Próximos passos sugeridos (em ordem de valor/custo)

### Tier R1 — Honestidade editorial imediata (~1h)
- §15 nova "Limites causais e Zajdela como horizonte" 
- §11 qualifica "IPEA broker" como hipótese
- §10·6 distingue identificação vs intervenção

### Tier R2 — Testar H1+H2 (~700-1000 fetches, 2 sessões)
- `src/zajdela_h1_eventos.py` — operacionalização H1
- `src/zajdela_h2_ipea.py` — operacionalização H2
- §16 nova com resultados

### Tier R3 — NIB 2023 como tratamento prospectivo (setup + ongoing)
- `docs/nib2023-monitoring-protocol.md`
- Script cron de re-cocitação trimestral
- `docs/nib-tracker.html` com timeline

### Tier R4 — Modelagem dinâmica (sem fetches, ~2 sessões)
- Adaptar XGI para modelo dinâmico estocástico
- Simular efeito de intervenção
- §17 nova com simulação

### Tier 2 (do plano de crítica brutal) — Brasil como núcleo
- **M15**: promover 5-7 obras Faganello a sementes BR oficiais
- **M28**: brazil_snowball roda como parte de build_site
- **M11+M12**: institutions + funders (IPEA, BNDES, Finep, CNPq)
- **M21**: author trajectories detalhadas

## Como recuperar em nova sessão

```bash
# do main:
git pull origin main
pytest                                  # deve dar 39 verdes
python src/cocitation_hypergraph.py     # roda M1+M2+M3+M4
python src/author_network.py            # roda M8 + classifier estendido
```

URL produção: https://freirelucas.github.io/cibernetica-regula-o-politica-industrial/ (PR #23 deploya automaticamente)

Documento detalhado da crítica brutal + balanço Zajdela completo:
`/root/.claude/plans/avaliar-unidade-conceitual-das-async-seal.md` (ephemeral — vai sumir quando o container reciclar; este aprendizado consolida o essencial).

## Estado para encerrar com segurança

| Item | Status |
|---|---|
| Trabalho da sessão em main | ✅ PRs #21, #22, #23 mergeados |
| Branch atual sincronizada | ✅ zero diff vs origin/main |
| Working tree limpo | ✅ sem uncommitted |
| Skills no `.claude/skills/` | ✅ 3 skills com frontmatter válido |
| Notes do repo | ✅ 4 sessões documentadas (28, 29, 30, 29-aprendizados) |
| Tests passando | ✅ 39/39 (1 skip) |
| GH Pages | ✅ live |
| API key (OPENALEX_API_KEY) | ✅ em `~/.openalex_key` (fora do repo, sobrevive container só durante sessão) |

**Pode desativar**. Próxima sessão começa pelo Tier R1 ou Tier 2 (Brasil como núcleo) — escolha do autor.
