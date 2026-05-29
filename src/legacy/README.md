# src/legacy — scripts arquivados

Scripts preservados para auditoria e rastreio histórico. **Não rodar daqui** — se
precisar reativar, mova de volta para `src/` (os caminhos/imports assumem `src/`).

## A. Superados por implementações mais completas

| Script | Substituído por | Motivo |
|---|---|---|
| `coauthorship.py` | `src/author_network.py` (Fase D) | Cobertura limitada a 62 nós; author_network cobre 16k autores |
| `enrich_openalex.py` | `src/author_network.py` + `src/build_rayyan.py` | Enrich agora integrado nos scripts principais |
| `explode_snowball.py` | `src/depth2_snowball.py` (Fase E) | Depth-2 com chave de API é 38× mais rápido e cache-friendly |

## B. Pivôs de uso único — resultado já incorporado (PR-6)

Cada um rodou uma vez; o achado já está nos dados versionados, no `build_rayyan.py`
ou na prosa do relatório. Não estão no DAG do `run_all.py` nem são importados por
nenhum módulo vivo — por isso saíram de `src/`.

| Script | O que produziu | Onde o resultado ficou |
|---|---|---|
| `bridges_pairwise.py` | Caça a pontes indiretas (2ª/3ª ordem) sobre `network_exploded.json` | Superado pelo hipergrafo XGI (`cocitation_hypergraph.py`) + HO-BC (`higher_order_betweenness.py`) |
| `clean_dead_ids.py` | Higiene: removeu ids OpenAlex que dão 404 das fontes (lista DEAD, maio/2026) | Já aplicado aos dados versionados |
| `crosscheck_brasil.py` | Uso único (rede): o material brasileiro cita as obras-semente globais? | Fundamenta a nota da síntese (seção Brasil) |
| `crosscheck_lange.py` | Uso único (rede): a recepção de Oskar Lange cruza os eixos? | Fundamenta a nota da síntese |
| `cyb_split.py` | Análise (stdlib): cibernética geral × organizacional na estrutura da rede | Virou a distinção `_ORG_CYB`/`_GERAL_CYB` em `build_rayyan.py` + seção do relatório |
| `merge_dup_nodes.py` | Higiene: fundiu nós duplicados (mesma obra sob vários ids) nas redes | Já aplicado aos `network*.json` versionados |
| `paths_between.py` | Análise (stdlib): rotas mais curtas entre as comunidades e seus "degraus" | Relatório/síntese |
| `split_eecs2.py` | Normalizou o volume "EECS II" em capítulos (DOIs determinísticos) | `cplx_works.json` (4º eixo) + `eecs2_chapters.json` (gitignored) |

## C. Candidatos do handout MANTIDOS em `src/` (são vivos)

O handout (PR-6) listou também estes como candidatos a legacy. **Não foram movidos**
— o critério "vivo = lido por `run_all.py` ou `build_site`" os mantém em `src/`:

| Script | Por que é vivo |
|---|---|
| `cross_brasil.py` | Produz `data/cross_brasil.json`, consumido por `build_rayyan.tag_cross` (tag "ponte global×Brasil"); fase do DAG |
| `cplx_works.py` | Produz `data/cplx_works.json` (4º eixo), consumido por `build_rayyan.consolidate`; fase do DAG |
| `experiment_cplx.py` | Produz `data/network_4axis.json`, base do explorador e do `cocitation_hypergraph`; fase do DAG |
| `token_injection.py` | Importado por `build_site` (injeta os tokens XGI_/AUTHORNET_/BRASIL_/BROK_) |
| `minirun.py` | Importado por `experiment_cplx` (`import minirun as mr`) |
