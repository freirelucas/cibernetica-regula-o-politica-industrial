# Plano de melhorias de engenharia — da auditoria ao que fazer

Data: 21/11/2026. Base: commit `34694db` do ramo `claude/jolly-wright-t5ga5c`, 27 commits à
frente de `origin/main`. Origem: auditoria geral de engenharia feita só por leitura, entre 14 e
21/11. **Nada deste plano foi executado.** Ele existe para ser retomado por outro agente.

Atualizado em 23/11/2026: entrou o item DT2, achado numa varredura de textos desatualizados. A
arrumação daquele dia está na seção 8 de `notes/2026-11-21-sessao.md`.

## 0. Como usar este plano

1. Leia `CLAUDE.md` (as regras que não se negociam) e `notes/2026-11-21-sessao.md` (estado,
   aprendizados e pendências). As regras de lá valem para cada item daqui.
2. Cada item traz **hoje** (o que foi medido, com arquivo e linha conferidos em `34694db`),
   **fazer**, **feito quando** (critério que se confere por comando) e **quem decide**.
3. "Quem decide: responsável" quer dizer que o item **não se executa sem autorização expressa**
   de quem coordena o projeto. Na dúvida, pergunte antes.
4. Antes de despachar um executor, transforme o item em ordem de serviço fechada (seção 11).
5. Um item por commit, só com os arquivos do item. `docs/` só entra em commit de item que
   manda reconstruir o sítio, e sempre no ambiente completo: `python scripts/preparar.py` tem
   de terminar em `AMBIENTE PRONTO`.
6. Ao concluir um item, atualize a coluna "situação" do quadro, com o commit.

O que **não** fazer por conta própria: push na `main`, reescrever histórico, apagar ramos,
regenerar o `CHANGELOG.md`, disparar coleta ou qualquer chamada à API do OpenAlex.

## 1. Quadro

| item | o quê | gravidade | quem decide | situação |
|---|---|---|---|---|
| PV1 | tirar o endereço pessoal do código | alta | agente (variante sem padrão) | aberto |
| PV2 | endereço pessoal no histórico do git | alta | responsável | aberto |
| PV3 | contatos de autores dentro de resumos publicados | média | agente | aberto |
| DT1 | slides com carga externa e sem gerador | média | responsável | aberto |
| DT2 | deck de status de junho, com fatos digitados e desatualizado | baixa | responsável | aberto |
| CI1 | publicar no Pages só com testes verdes | média | agente prepara, responsável confirma | aberto |
| CI2 | conferir o `docs/` canônico na CI | média | agente | aberto |
| CI3 | testes de navegador e conferência de telas na CI | média | agente | aberto |
| CI4 | suíte sem efeito colateral em `docs/` | média | agente | aberto |
| CI5 | ações do GitHub fixadas por SHA | baixa | agente | aberto |
| FD1 | registrar falha da API em vez de engolir | média | agente | aberto |
| FD2 | avisar de chave ilegível e de cache corrompido | média | agente | aberto |
| FD3 | derivado obrigatório não pode faltar em silêncio | média | agente | aberto |
| FD4 | teto de custo com falha aberta | baixa | responsável | aberto |
| FD5 | demais `except … pass` | baixa | agente | aberto |
| UI1 | escape de texto vindo dos dados | média | agente | aberto |
| CD1 | funções longas e complexas | média | agente, depois de CI2 | aberto |
| CD2 | auxiliares duplicados | baixa | agente | aberto |
| CD3 | `src/legacy/` | baixa | responsável | aberto |
| CD4 | caminhos fixos em `/tmp` | baixa | agente | aberto |
| CD5 | verificação estática do código | baixa | responsável | aberto |
| CD6 | dependências sem versões travadas | média | agente propõe, responsável confirma | aberto |
| RP1 | levar o redesenho à `main` | alta | responsável | aberto |
| RP2 | cache de 116 MB versionado | média | responsável | aberto |
| RP3 | gancho de pré-commit que adiciona arquivos sozinho | média | responsável | aberto |
| RP4 | ramos acumulados | baixa | responsável | aberto |
| RP5 | versão citável (etiqueta) | baixa | responsável | aberto |

## 2. Privacidade

### PV1 — Tirar o endereço pessoal do código

- **Hoje:** `src/oa.py:25` usa um endereço pessoal como valor padrão de `OPENALEX_MAILTO`. Ele
  vai no `User-Agent` (`:36`) e no parâmetro `mailto=` de toda requisição (`:43`). Também há
  endereço de e-mail em `src/build_network.py`, em três arquivos de `src/legacy/`
  (`crosscheck_brasil.py`, `crosscheck_lange.py`, `enrich_openalex.py`) e no notebook de
  `colab/` (linha 21; o `funnel.yml:15-16` e `:29-30` dizem que o e-mail do funil fica na
  célula 2). Não foi conferido se esses outros são o mesmo endereço.
- **Fazer:** nenhum valor padrão embutido. Com a variável definida, usa; sem ela, não envia
  `mailto` nem contato no `User-Agent`. O mesmo nos demais arquivos. O notebook passa a ler a
  variável ou um campo vazio a preencher.
- **Feito quando:** um teste novo falha se houver padrão de e-mail em `src/`, `scripts/`,
  `colab/` e `.github/`, e `OA_OFFLINE=1 python src/run_all.py --offline` roda sem a variável.
- **Quem decide:** agente, na variante sem padrão. Qual contato institucional usar numa coleta
  é escolha do responsável.
- **Cuidado:** o ambiente tem um filtro de privacidade que recusa comando de shell que leia
  esses arquivos ou imprima o endereço. Use a ferramenta de leitura por faixa de linhas, edite
  sem repetir o valor e nunca o escreva em mensagem, commit ou nota.

### PV2 — Endereço pessoal no histórico do git

- **Hoje:** tirar do tronco (PV1) não tira do histórico, e o repositório é público.
- **Fazer:** só se o responsável quiser. Reescrever com `git filter-repo` exige push forçado em
  todos os ramos, quebra clones e muda os identificadores de commit citados nas notas.
- **Feito quando:** a decisão estiver registrada: reescrever ou aceitar.
- **Quem decide:** responsável.

### PV3 — Contatos de autores dentro de resumos publicados

- **Hoje:** dois resumos trazem, no próprio texto devolvido pelo OpenAlex, o contato dos
  autores: cinco endereços ao todo. Eles se repetem em 14 arquivos de `docs/`:
  `docs/triagem.html:215`, os 12 arquivos `docs/dados/rayyan_*` e
  `docs/material-brasil/dataset_politica_industrial_brasil.csv:47,90`. Um dos resumos está em
  `data/openalex_enrich.json:1242`, campo `abstract`. A auditoria tinha classificado isto como
  grave antes de achar a origem; medido, é dado bibliográfico público replicado, e a gravidade
  cai para média.
- **Fazer:** ao montar resumo para exportação e para a triagem, trocar padrão de e-mail por uma
  marca fixa, como `[e-mail suprimido]`. Pontos de entrada prováveis: `src/build_rayyan.py` e o
  trecho de `src/build_site.py` que alimenta a triagem e o material do Brasil. Não mexer em
  `data/oa_cache/`, que é a resposta bruta da API. Reconstruir `docs/`.
- **Feito quando:** um teste novo varre todos os arquivos de texto de `docs/` e não acha padrão
  de e-mail, e `git status` depois da construção só mostra os arquivos esperados.
- **Quem decide:** agente. A frase que avisa da supressão em `METODOLOGIA.md` é prosa: propor e
  deixar o responsável aprovar.

## 3. Doutrina

### DT1 — Slides com carga externa e sem gerador

- **Hoje:** `docs/slides.html` (`:7-9`, `:303`), `docs/slides-10.html` (`:7-9`, `:214`) e
  `docs/slides-metodologia.html` (`:7-9`, `:662`) carregam reveal.js 5.1.0 de
  `cdn.jsdelivr.net`. Não têm gerador em `src/` nem em `scripts/`. O relatório aponta para eles
  (`src/site_template.html:299-301`). Violam as regras 1 e 3 do `CLAUDE.md`. Já constava nas
  notas de 21/09 e de 10/11.
- **Opções:** (a) vendorizar o reveal.js em `docs/vendor/` e trocar as 12 referências, o que é
  biblioteca nova e também pede autorização pela regra 3; (b) tirar os três arquivos de `docs/`
  e os três links do modelo; (c) gerar os slides pelo funil, o que hoje não existe para HTML
  (`build_deck.py` gera `.pptx`).
- **Feito quando:** nenhum `<script src>` ou `<link href>` com `http` em `docs/**/*.html`, com
  um teste que cubra todos os HTML de `docs/`. Hoje nenhum teste olha os slides.
- **Quem decide:** responsável.

### DT2 — Deck de status de junho, com fatos digitados e desatualizado

- **Hoje:** `docs/apresentacao_status.pptx` é de 09/06 (`2082b5e`) e descreve o sítio de antes
  do redesenho. Nenhuma tela aponta para ele, mas ele é publicado com `docs/`. O gerador,
  `src/build_deck.py`, promete números lidos dos dados e traz fatos digitados: "17 estágios" e
  "80 testes" (`:174`), "As três telas" (`:204`), "De 250 nós" e outros nas linhas vizinhas. A
  suíte tem hoje 120 testes e o sítio tem cinco telas.
- **Opções:** (a) aposentar o deck e tirar o `.pptx` de `docs/`; (b) refazer o gerador para ler
  todo número dos derivados e descrever as cinco telas, e então regerar.
- **Feito quando:** ou o arquivo e o gerador saíram, ou nenhum número aparece digitado em
  `src/build_deck.py` e o `.pptx` foi regerado.
- **Quem decide:** responsável.

## 4. Integração contínua e publicação

### CI1 — Publicar no Pages só com testes verdes

- **Hoje:** `.github/workflows/pages.yml:4-5` publica `docs/` a cada push na `main`, sem
  depender de `ci.yml`. Um push com testes vermelhos vai ao ar.
- **Fazer:** condicionar a publicação ao fluxo `testes`, num fluxo só com `needs`, ou por
  `workflow_run` com conclusão `success`.
- **Feito quando:** o YAML mostra a dependência e uma execução na `main` confirma a ordem.
- **Quem decide:** agente prepara; o responsável confirma, porque muda como o sítio vai ao ar.

### CI2 — Conferir o `docs/` canônico na CI

- **Hoje:** `ci.yml:19-25` instala só pytest, numpy, scipy e networkx. Sem `python-igraph` e
  `leidenalg`, `src/author_network.py` usa a reserva `_louvain` (`:404`), que não é o algoritmo
  do canônico. Nenhum passo compara o que foi construído com o que está no git.
- **Fazer:** job novo, com igraph e leidenalg, que roda `OA_OFFLINE=1 python src/run_all.py
  --offline`, depois `python src/build_site.py`, e falha se `git status --porcelain docs/` não
  vier vazio.
- **Feito quando:** verde no commit atual e vermelho num commit de ensaio com um arquivo de
  `docs/dados/` adulterado. O ensaio fica em ramo descartável e não se mescla.
- **Quem decide:** agente.

### CI3 — Testes de navegador e conferência de telas na CI

- **Hoje:** cinco testes pulam sem Playwright (`tests/test_espaco.py:277,311,343`,
  `tests/test_triagem_ux.py:65`, `tests/test_smoke.py:12`) e o job que roda a suíte não o
  instala. `scripts/conferir_telas.py` não roda na CI.
- **Fazer:** instalar Playwright e Chromium no job da suíte e acrescentar
  `python scripts/conferir_telas.py`.
- **Feito quando:** o registro da CI não mostra teste pulado por falta de Playwright e mostra as
  20 combinações da conferência (5 telas em 4 larguras) sem problema.
- **Quem decide:** agente.

### CI4 — Suíte sem efeito colateral em `docs/`

- **Hoje:** `tests/test_build_smoke.py:20-21` e `tests/test_espaco.py:153` constroem o sítio
  dentro de `docs/`. Num ambiente sem igraph, rodar a suíte deixa `docs/` divergente. É por isso
  que o `CLAUDE.md` manda rodar `python src/build_site.py` por último. Pedido desde o plano de
  18/09 (item R3 de lá).
- **Fazer:** `build_site` aceita uma pasta de saída e os testes constroem em pasta temporária.
- **Feito quando:** `python -m pytest -q` seguido de `git status --short docs/` vazio, também
  num ambiente só com as dependências da CI.
- **Quem decide:** agente. Vem antes de CI2.

### CI5 — Ações do GitHub fixadas por SHA

- **Hoje:** `actions/checkout@v4`, `actions/setup-python@v5`, `actions/configure-pages@v5`,
  `actions/upload-pages-artifact@v3`, `actions/deploy-pages@v4` e
  `peter-evans/create-pull-request@v6` (`funnel.yml:105`, num fluxo com `contents: write`) são
  referidas por etiqueta móvel.
- **Fazer:** fixar cada uma por SHA, com a versão em comentário.
- **Feito quando:** `grep -n "uses:" .github/workflows/*.yml` só mostra SHA.
- **Quem decide:** agente.

## 5. Funil e dados

### FD1 — Registrar falha da API em vez de engolir

- **Hoje:** `oa.get` (`src/oa.py:110-114`) descarta erro HTTP e qualquer exceção e devolve `{}`
  depois de sete tentativas, sem uma linha de registro.
- **Fazer:** registrar em stderr a tentativa, o código e a URL **original**. A URL usada na
  requisição leva `mailto` e `api_key`; essa não se registra.
- **Feito quando:** um teste com `urlopen` substituído mostra a mensagem e o retorno `{}`.
- **Quem decide:** agente.

### FD2 — Avisar de chave ilegível e de cache corrompido

- **Hoje:** chave ilegível (`src/oa.py:34-35`) e cache corrompido (`:60-61`, `:66-67`) passam
  sem aviso. Cache corrompido leva a nova requisição, que custa orçamento.
- **Fazer:** avisar em stderr, com o caminho do arquivo.
- **Feito quando:** um teste com `.json.gz` truncado mostra o aviso.
- **Quem decide:** agente.

### FD3 — Derivado obrigatório não pode faltar em silêncio

- **Hoje:** `load_data` tem `required=False` por padrão (`src/data_io.py:40`). São 24 usos em
  seis módulos: `build_rayyan` 8, `build_site` 7, `solidity` 4, `data_io` 3, `espaco` 1,
  `observed_only_check` 1. Um derivado ausente vira seção vazia, com aviso só no stderr.
- **Fazer:** listar quais derivados alimentam número ou seção do relatório e marcá-los como
  obrigatórios. Os de fato opcionais continuam avisando.
- **Feito quando:** um teste remove, em cópia temporária, um derivado obrigatório, e
  `build_site` sai com erro que nomeia o arquivo.
- **Quem decide:** agente. Fica mais seguro depois de CI2.

### FD4 — Teto de custo com falha aberta

- **Hoje:** é decisão documentada (`src/budget.py:12-13`). Livro corrompido zera o gasto do dia
  (`:41-44`), e erro ao gravar é engolido (`:59-60`). Nos dois casos o teto deixa de valer sem
  aviso.
- **Fazer, se decidido:** bloquear a busca quando o livro não puder ser lido ou gravado.
- **Quem decide:** responsável. É troca de comportamento do funil.

### FD5 — Demais `except … pass`

- **Hoje:** `src/run_all.py:148-149` e `:232-233`; `src/author_network.py:101-102`.
- **Fazer:** registrar a exceção em stderr.
- **Feito quando:** `grep -n -A1 "except Exception" src/*.py` não mostra `pass` sozinho.
- **Quem decide:** agente.

## 6. Interface

### UI1 — Escape de texto vindo dos dados

- **Hoje:** título, autores e rótulo entram em `innerHTML` sem escape:
  `src/site_template.html:1177-1181`, `:1195-1199` e `:1446`;
  `src/explorador_template.html:332` (não foram conferidos `:350` e `:358`).
  `src/triagem_template.html:219` define um `esc` que não trata aspas e o usa dentro de
  atributo (`:234`). `src/espaco_template.html:348` tem o `esc` completo (não foram conferidos
  `:478` e `:510`). Os textos vêm do OpenAlex: o risco é latente, mas um título com marcação já
  quebra o leiaute.
- **Fazer:** um auxiliar de escape igual nas quatro telas, ou `textContent` onde só há texto,
  aplicado a todo campo que vem de `data/`.
- **Feito quando:** um teste de navegador com título sintético contendo `<b>` e aspas (em dado
  temporário, nunca em `data/`) mostra o texto literal; driver em `STATUS: OK`;
  `scripts/conferir_telas.py` sem problema novo. Reconstrói `docs/`.
- **Quem decide:** agente.

## 7. Código

### CD1 — Funções longas e complexas

- **Hoje:** por contagem aproximada de ramos na árvore sintática, 24 das 258 funções de `src/`
  têm complexidade 20 ou mais. As maiores: `espaco.py:153` `dados` (118 linhas, cerca de 68),
  `experiment_cplx.py:49` `main` (cerca de 64), `minirun.py:124` `main` (cerca de 58),
  `build_rayyan.py:165` `consolidate` (cerca de 43), `cocitation_hypergraph.py:71` `main` (152
  linhas, cerca de 41) e `build_site.py:422` `main` (122 linhas, cerca de 37).
- **Fazer:** primeiro um teste de caracterização (a saída em `docs/dados/` e nos derivados fica
  idêntica); só depois extrair funções. `minirun.py` é a fonte única de sementes e vocabulário
  do funil: começa por ele.
- **Feito quando:** mesma saída, byte a byte, antes e depois.
- **Quem decide:** agente, depois de CI2. Sem pressa.

### CD2 — Auxiliares duplicados

- **Hoje:** `read_budget`, `bump_budget` e `cache_hit` estão copiados em
  `depth2_snowball.py:22,31,37`, `author_network.py:191,200,206` e
  `brazil_snowball.py:31,40,46`. Há duas funções `br` com assinaturas diferentes
  (`marcadores.py:10` e `build_deck.py:40`).
- **Fazer:** um módulo só para os três auxiliares; uma só `br`.
- **Feito quando:** suíte verde e `git grep -n "def read_budget"` com uma ocorrência.
- **Quem decide:** agente.

### CD3 — `src/legacy/`

- **Hoje:** 12 arquivos rastreados, nenhum importado. Três contêm e-mail, e
  `merge_dup_nodes.py:10,21` depende de `/tmp/found.json`.
- **Fazer:** apagar do tronco. Continua no histórico.
- **Quem decide:** responsável.

### CD4 — Caminhos fixos em `/tmp`

- **Hoje:** `src/build_deck.py:85-87`, `.claude/skills/run-scisci-ipea/driver.py:21,140,160-166`
  e `tests/test_smoke.py:14`. O `design/AVALIACAO.md:36` já registra.
- **Fazer:** `tempfile`, com o caminho informado na saída do comando.
- **Quem decide:** agente.

### CD5 — Verificação estática do código

- **Hoje:** não há `pyproject.toml`, configuração de ruff ou flake8, nem medição de cobertura.
- **Sugestão:** ruff só para verificar, sem reformatar, em `requirements-dev.txt` e na CI.
- **Quem decide:** responsável. É ferramenta de desenvolvimento e não entra em `docs/`, mas é
  dependência nova.

### CD6 — Dependências sem versões travadas

- **Hoje:** `requirements.txt` mistura `==` e `>=`. `ci.yml:25` e `funnel.yml:53-68` instalam
  conjuntos próprios. Não há arquivo de versões travadas. `pyvis`, `tqdm`, `pyarrow` e `pandas`
  não são importados por nenhum `.py`; o notebook não foi conferido linha a linha.
- **Fazer:** um arquivo de versões travadas para o ambiente canônico e separar o que é só do
  notebook.
- **Quem decide:** agente propõe, responsável confirma.

## 8. Repositório

### RP1 — Levar o redesenho à `main`

- **Hoje:** o ramo de trabalho está 27 commits à frente de `origin/main` e nenhum atrás. O push
  direto na `main` foi negado pelo classificador de ações automáticas da sessão e não foi
  contornado. O sítio público continua na versão de 10/11.
- **Fazer:** a mesclagem é do responsável, ou um pedido expresso de PR.
- **Quem decide:** responsável.

### RP2 — Cache de 116 MB versionado

- **Hoje:** 6.593 dos 6.864 arquivos rastreados são `data/oa_cache/`. O pacote do git tem
  123,4 MiB. É escolha de reprodutibilidade, com custo de clone e de crescimento a cada coleta.
- **Opções:** manter; LFS; anexo de release; um arquivo compactado por coleta.
- **Quem decide:** responsável.

### RP3 — Gancho de pré-commit que adiciona arquivos sozinho

- **Hoje:** `.githooks/pre-commit:6` regenera o `CHANGELOG.md` e o adiciona ao commit; `:8` faz
  `git add data/oa_cache` em todo commit. Ativado, contraria "um commit por ordem, só com os
  arquivos listados" e a decisão de não regenerar o CHANGELOG. Neste clone `core.hooksPath` não
  está definido, então o gancho está inativo.
- **Fazer:** tirar as duas adições automáticas, ou aposentar o gancho.
- **Quem decide:** responsável.

### RP4 — Ramos acumulados

- **Hoje:** oito ramos remotos já estão contidos na `main`: `claude/adoring-fermat-3j2YJ`,
  `claude/checagem-e-deck-10`, `claude/compassionate-ramanujan-xsPcd`,
  `claude/expansao-dirigida`, `claude/fase-d-author-network`, `claude/happy-hypatia-7TS2F`,
  `claude/p2-p8-melhorias` e `claude/tier1-xgi-melhorias`. O ramo
  `claude/friendly-carson-41ska0`, de 13/11, não está contido e não foi examinado.
- **Fazer:** apagar os contidos; examinar o outro antes de decidir.
- **Quem decide:** responsável. Apagar ramo é destrutivo.

### RP5 — Versão citável

- **Hoje:** zero etiquetas, no clone e no remoto. Já apontado na nota de 21/09.
- **Fazer:** etiquetar depois de RP1 e da decisão sobre o aviso de versão de trabalho.
- **Quem decide:** responsável.

## 9. Sequenciamento

1. **Sem decisão e sem tocar `docs/`:** PV1, CI4, FD1, FD2, FD5, CD2, CD4, CI5. São
   independentes e podem ir em paralelo, cada um na sua cópia de trabalho.
2. **Sem decisão, reconstruindo `docs/`:** UI1 e PV3. Nunca em paralelo: os dois regeneram
   `docs/`. Um commit de integração para os dois, ou dois em sequência.
3. **Fluxos de CI, nesta ordem:** CI4, depois CI2, depois CI3, e CI1 por último, com
   confirmação.
4. **Depois de CI2:** FD3 e CD1, porque o job canônico acusa regressão de construção.
5. **Esperam decisão:** PV2, DT1, DT2, FD4, CD3, CD5, CD6, RP1 a RP5.

## 10. Decisões pedidas ao responsável

1. Mesclar o ramo de trabalho na `main`, ou pedir um PR (RP1).
2. Que contato institucional usar na coleta, e se o histórico será reescrito (PV1, PV2).
3. Slides: vendorizar, retirar ou gerar pelo funil (DT1). Deck de status: aposentar ou refazer
   (DT2).
4. Política do cache e do gancho de pré-commit (RP2, RP3).
5. Apagar `src/legacy/` e os ramos já contidos (CD3, RP4).
6. Teto de custo: manter a falha aberta ou bloquear (FD4).
7. Aceitar ferramenta de verificação estática e arquivo de versões travadas (CD5, CD6).

Pendências de desenho que vêm de antes e seguem abertas:

- Tabelas em 320 px: cartões empilhados ou manter a rolagem interna (a coluna de títulos fica
  estreita).
- A lente "A nota" publica título, autores e referências do texto para discussão: confirmar se
  pode ir a público antes do seminário (nota de 10/11, item 1).
- "Q ≈ 0,59" no relatório contra 0,515 no derivado: a regra 10 do `CLAUDE.md` manda manter; é
  decisão autoral.
- Não reverificadas nesta auditoria: desempate da inferência, registros duplicados na rede,
  autoria e "Como citar", data da Nova Indústria Brasil (nota de 10/11, itens 2, 3 e 5).

## 11. Como transformar um item em ordem de serviço

As ordens do redesenho (`design/ordens/`) funcionaram quando seguiram estas regras, e falharam
quando não seguiram. O detalhe de cada falha está em `notes/2026-11-21-sessao.md`.

1. Releia o trecho no commit-base e copie a âncora exata. Ordem escrita de memória erra.
2. Diga onde inserir ("depois da linha tal"), nunca "entre". Confira que o ponto não parte um
   `if`/`else`.
3. Meça antes e escreva o número medido na ordem (quantos alvos, quantas ocorrências).
4. Dê o veredito por comando: um teste que falha antes e passa depois. O executor não decide
   sozinho se terminou.
5. Liste os arquivos permitidos. `docs/` só em ordem de integração.
6. Substituição em lote vai com a contagem esperada conferida antes de gravar.
7. Um executor por cópia de trabalho, criada a partir do ramo remoto atual.
8. Correção do orquestrador depois da aprovação vai em commit próprio, com o achado medido.

## 12. O que a auditoria não cobriu

- O histórico do git quanto ao endereço pessoal (o valor não foi repetido em nenhum comando).
- O notebook de `colab/`, linha a linha.
- A configuração do Pages e as regras de proteção de ramo no GitHub.
- O conteúdo do ramo `claude/friendly-carson-41ska0`.
- A complexidade é contagem aproximada, não a métrica oficial.
