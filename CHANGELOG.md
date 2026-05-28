# CHANGELOG

Registro de mudanças desta branch, agrupado por tema (111 commits de trabalho). **Gerado** por `.claude/skills/changelog/changelog.py` — para atualizar após um novo commit, rode o script (ou use a skill `/changelog`).

## Integridade de dados

- Higiene x10: funde nós duplicados das redes (mesma obra sob vários ids) · `360cbd2` · 2026-05-27
- Higiene de integridade: remove 13 ids OpenAlex que não resolvem (404) · `ce29b86` · 2026-05-27
- Limpa a síntese do Rayyan: dedup por id, metadados ricos, zip de formato único · `2d08753` · 2026-05-27

## Triagem e exportação (Rayyan)

- Endurece cache, surfaceia silos no Resumo e arquitetura de tagging do Rayyan · `455c2b1` · 2026-05-28
- Recorte "pontes a construir": as 25 obras de maior prioridade de ponte · `2cd4747` · 2026-05-28
- Cache OpenAlex: gzip por arquivo (consolidação antes de explodir a rede) · `3384468` · 2026-05-28
- Triagem: curadoria mostra o conjunto de refs antes de exportar · `9ebf596` · 2026-05-27
- Rayyan: zip determinístico (data fixa na entrada) · `ca94d3c` · 2026-05-27
- README: declara o Objetivo do projeto (norte: diagnóstico, triagem, agenda) · `e12fc0d` · 2026-05-27
- Triagem: explicador recolhível do raciocínio + cor do 4º eixo · `3b2617f` · 2026-05-27
- Triagem: curadoria por tamanho de bloco (30/60/90/120) + badge Colab no README · `016b2ed` · 2026-05-27
- Explorador: subtipo de cibernética + modos de destaque; triagem como aba no topo · `6ae43c3` · 2026-05-27
- Diferencia cibernética geral × organizacional e cria o recorte-alvo (D) · `9b9a0a4` · 2026-05-27
- Reescreve o quadro do Rayyan: seletor de recorte + explica o conteúdo do ZIP · `ba6db74` · 2026-05-27
- Rayyan: 4º eixo no seletor, recorte só-Claucia e atalhos de UX · `c0bc5f2` · 2026-05-27
- 4º eixo (economia da complexidade) no explorador + blocos conceituais na triagem · `14dc374` · 2026-05-27
- Acelera a triagem: teclado, progresso visual e combinar decisões · `f219b1c` · 2026-05-27
- Agrupa os downloads e orienta a importação no Rayyan · `e7d5419` · 2026-05-27
- Adiciona EndNote/BibTeX, refina o casamento de títulos e amplia os resumos · `49b9bd8` · 2026-05-27
- Adiciona triagem de inclusão/exclusão no próprio site · `8097bc8` · 2026-05-27
- Alinha a exportação Rayyan aos exemplos oficiais e enriquece com resumos · `8d0fb6d` · 2026-05-27
- Garante a validade do RIS/CSV do Rayyan e documenta os formatos · `3f09278` · 2026-05-27
- Prepara a síntese para triagem no Rayyan e justifica a prosa · `4cc5de1` · 2026-05-27

## Explorador e visualizações

- Fase C — Longue-durée temporal: silos cristalizaram-se nos 1980s · `8d529bf` · 2026-05-28
- Explorador: resolve os 'sem eixo' por inferência e revela pontes de 2ª ordem · `fd5c2f7` · 2026-05-27
- Explorador: realça a estrutura — recua os 'sem eixo', destaca as pontes · `493dfc5` · 2026-05-27
- Explorador: disposição "por eixo" (silos visíveis) em vez do emaranhado · `a2cc1cf` · 2026-05-27
- Leva a rede explodida (251 nós, papéis P/z) ao explorador · `87a6a82` · 2026-05-27
- Exporta subrede do explorador e guarda a cobertura de resumos · `b7e15a4` · 2026-05-27
- Aprofunda o explorador: métricas vivas e comunidades detectadas · `619e12f` · 2026-05-27
- Torna o gráfico temporal clicável (detalhamento por ano) · `68d724a` · 2026-05-27
- Melhora a legibilidade do explorador (espaçamento e rótulos) · `6637ad7` · 2026-05-27
- Acrescenta lente "só cocitações entre eixos" ao explorador · `47fa10c` · 2026-05-27
- Adiciona explorador interativo (d3) e torna as visualizações clicáveis · `dbd87da` · 2026-05-27
- Adiciona a visualização da rede do núcleo intelectual (d3-force) · `854a413` · 2026-05-26
- Fase 2: interatividade desktop-first (filtros, busca, ordenação, legenda) · `e553c11` · 2026-05-26

## Análise (cienciometria / Science of Science)

- Fase D snapshot 2: snowball top-15 + adjacent probes · `0291844` · 2026-05-28
- Snowball por autor-semente (estratégia mais ousada, via cache) · `bb1a0b1` · 2026-05-28
- 4º eixo: estrutura a literatura da complexidade por subtradição · `0a17659` · 2026-05-27
- Descobre os caminhos potenciais entre as comunidades epistêmicas · `dc2b097` · 2026-05-27
- Experimento do 4º eixo conclui: economia da complexidade é candidata a ponte · `39d0d7b` · 2026-05-27
- Adiciona o experimento do 4º eixo (economia da complexidade / SFI EECS-IV) · `d4ee7d5` · 2026-05-27
- Teste de significância (modelo nulo de configuração) das pontes · `ff92b18` · 2026-05-27
- Conectores entre comunidades por participação (corrige a leitura de intermediação) · `e0a688f` · 2026-05-27
- Caça às pontes epistêmicas de ordem superior (intermediação na rede explodida) · `65b75b2` · 2026-05-27
- Surfaceia o aprendizado do snowball explodido no #rede · `13a152a` · 2026-05-27
- Atualiza a rede explodida (metadados limpos) — estrutura confirmada em escala · `72d6dde` · 2026-05-27
- Adiciona a rede do snowball explodido (artefato de análise) · `6b9772c` · 2026-05-27
- Implementa métodos do Santa Fe (Clauset): lei de potência + CNM · `0f50b90` · 2026-05-27
- Cita e explica o jargão das métricas acrescentadas (modularidade, NMI…) · `927940d` · 2026-05-27
- Valida os eixos sem circularidade: comunidades detectadas + NMI · `50cefc6` · 2026-05-27
- Avalia o funil em Science of Science: modularidade e força de associação · `ca41b89` · 2026-05-27
- Quantifica a separação dos eixos na rede de cocitação real · `46d91d0` · 2026-05-27
- Testa empiricamente a ponte de Lange: recepção compartimentada (reforça a tese) · `37a15b6` · 2026-05-27
- Corrige (com mais rigor) a relação entre os corpora na análise independente · `7e63c01` · 2026-05-27

## Funil, dados e reprodutibilidade

- Reconcilia n_seeds 10→13 (alinha badge §03 ao §07 e ao crawl XGI) · `414d2ba` · 2026-05-28
- run-scisci-ipea: atualiza a skill (219 nós, 203 cartões, 26 testes, cache + crawls) · `12ef075` · 2026-05-28
- Versiona o raw das consultas OpenAlex (data/oa_cache) + skill /oa-cache · `0556215` · 2026-05-28
- Cache de consultas OpenAlex + desdobra EECS-II + corrige fillcolor do Plotly · `7b1c993` · 2026-05-28
- EECS-II: resolvedor por DOI determinístico (10.1201/9780429496639-N) · `ead3fea` · 2026-05-27
- Colab: banho de loja — tabela de células, referências e teste de sanidade · `f8d0c53` · 2026-05-27
- Deixa os crawls prontos para chave OpenAlex (secret) — pool polido + Premium · `39d255a` · 2026-05-27
- Endurece o fetch do experimento Cplx contra rate-limit (429) · `29575ed` · 2026-05-27
- Exporta a rede de cocitação real como dado baixável · `0a66383` · 2026-05-27
- Substitui a rede do site pela cocitação real (salto de valor) · `d168144` · 2026-05-27
- Refina a busca automatizada com Oskar Lange (ponte cibernética × planejamento) · `3eb877d` · 2026-05-27
- Funil: célula que exporta a rede de cocitação real para o site · `a0b24fd` · 2026-05-27
- Fase 1: metadados de citação, ponto pivotal nomeado e títulos completos · `f61b1bd` · 2026-05-26
- Normaliza autorias canônicas das obras-semente (correção de metadados OpenAlex) · `03607de` · 2026-05-26
- Deixa o notebook Colab camera-ready em PT-BR e integra a geração do site · `fe0da92` · 2026-05-26
- Traduz exportáveis para PT e aposenta os relatórios HTML redundantes · `0e94fcf` · 2026-05-26
- Descompacta o pacote no repo e adiciona regeneração offline do report · `2c9c680` · 2026-05-26

## Conteúdo acadêmico e autoria

- Exporta o cruzamento Brasil × núcleo (opção B) e refina a síntese · `a2521ed` · 2026-05-27
- Ancora Lange no site: precedente histórico na síntese e na leitura recomendada · `472c506` · 2026-05-27
- Afia a síntese com o achado de citação (PI conecta via Rodrik; falta a cibernética) · `8aeb3b1` · 2026-05-27
- Quantifica por citação o elo entre o material brasileiro e o núcleo global · `4b5bddd` · 2026-05-27
- Enriquece a leitura recomendada com clássicos do corpus real · `618fc41` · 2026-05-27
- Atualiza o driver (22 seções) após os capítulos analíticos · `34b7a79` · 2026-05-27
- Acrescenta capítulos de Síntese e Leitura recomendada · `928fde7` · 2026-05-27
- Acrescenta capítulo de análise independente do material brasileiro · `8679ce0` · 2026-05-27
- Corrige a grafia do nome da coautora: Claucia Faganello · `de342cc` · 2026-05-27
- Integra a revisão brasileira na íntegra, unifica referências e reordena autoria · `fa1b1bc` · 2026-05-27
- Integra a revisão brasileira (Faganello), 3 coautores e tarja preliminar · `d127f1a` · 2026-05-26
- Acrescenta substância acadêmica e unifica a fonte de dados do site · `e16b37c` · 2026-05-26
- Adiciona site acadêmico do GitHub Pages (docs/) em PT-BR sem anglicismos · `1e7bba2` · 2026-05-26

## Site e publicação (GitHub Pages)

- Adiciona link aos slides no menu do site · `2014243` · 2026-05-28
- Fases 3-5: capa de impressão, dicionário de dados, skip-link, deploy Pages · `78fd859` · 2026-05-26
- Torna o site responsivo (mobile/tablet) — corrige navegação e overflow · `a7f4bc2` · 2026-05-26
- Adiciona fallback sem JavaScript e CI (pytest) ao site · `6ce543f` · 2026-05-26
- Adiciona skill run-scisci-ipea (build, serve e dirige o site headless) · `9889f80` · 2026-05-26
- Torna o site autossuficiente (sem CDN) e corrige bugs de UX no render · `a8fe2c6` · 2026-05-26

## Infraestrutura, testes e ferramentas

- Prioridade de ponte: métrica única que adapta Emma/XGI ao objetivo · `fcdacc2` · 2026-05-28
- CHANGELOG: regenera após a skill (inclui o próprio commit) · `a021925` · 2026-05-27
- Adiciona a skill /changelog e gera o CHANGELOG por tema · `b84f0b7` · 2026-05-27
- Atualiza a skill run-scisci-ipea (3 páginas + pipeline atual) · `292cc60` · 2026-05-27
- Fase 6: aposenta o gerador legado (report_builder + html_template) · `5ef5d20` · 2026-05-26
- README camera-ready em PT e suite de testes pytest · `828b302` · 2026-05-26

## Outros

- Fase E (A.3+A.4+B.4+B.5+D.4): corpus 6.5× expandido, brokerage G-F, HO BC, slides · `228cb2e` · 2026-05-28
- A.3 + setup api_key + slides D.4: depth-2 → 13k works / 16k autores · `88748ff` · 2026-05-28
- Fase D · Author network completo: tag obra de autor-ponte + §10·6 + sondagens · `98ae1cf` · 2026-05-28
- Fase D snapshot 1: author_network.py + enriquecimento de 817 autores · `fea88d6` · 2026-05-28
- Recovery note: balanço de features + roteiro + onde paramos · `2b86304` · 2026-05-28
- Honestifica o badge de rajadas: 760 brutos → 20 de alto impacto (top peso) · `5ac22a1` · 2026-05-28
- Source + data + docs do c673371 (sources que não entraram na primeira tentativa) · `0260722` · 2026-05-28
- Escala XGI 60→200 citantes/semente; bridges rank-based scale-invariant; injeção viva de números · `c673371` · 2026-05-28
- Reescreve §05 e E1 honestamente: z = -29 indica estrutura MAIS siloed que o acaso · `3ec4e46` · 2026-05-28
- Pipeline XGI → SR: citantes ranqueados, sub-eixos Leiden e nova seção 10·5 · `68b0b13` · 2026-05-28
- Ordem superior (XGI): cocitação como hipergrafo — 40% dos grupos cruzam eixos · `fac51da` · 2026-05-28
- Pivô Zajdela: o silo é social — só ~5% dos autores atravessam eixos · `a9f1e7a` · 2026-05-28
- Pruning: remove nós-agregados de periódico (hubs falsos) · `d962761` · 2026-05-27
- changelog: hook de pre-commit (automático, árvore limpa) · `a181304` · 2026-05-27
