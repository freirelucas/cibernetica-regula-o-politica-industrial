# Plano de construção do redesenho

Este plano é para quem vai **construir**. O desenho já está decidido e está nesta pasta; aqui
está a ordem, os arquivos e a prova de que cada etapa terminou. Leia `CLAUDE.md` (raiz) antes.

- O que é o desenho e por quê: `design/README.md`.
- Peças: `design/sistema.css` (fichas e componentes, prefixo `sd-`) e `design/solidos.svg`.
- Como cada tela deve ficar: `design/prototipos/*.html` (abra no navegador). Os protótipos são
  gerados de `design/modelos/*.html` por `design/ferramentas/gera_prototipos.py`, com números
  reais. No modelo, cada número é um marcador `{{caminho}}`: o caminho é o do dado.

## Como trabalhar

1. **Uma etapa por vez, na ordem.** Não comece a seguinte com a anterior vermelha.
2. **Antes de mexer:** `pytest -q` e `python .claude/skills/run-scisci-ipea/driver.py` têm de
   passar. Se não passarem antes de você tocar em nada, pare e relate.
3. **Depois de mexer**, sempre os quatro comandos, nesta ordem:
   ```bash
   python src/build_site.py
   pytest -q
   python .claude/skills/run-scisci-ipea/driver.py      # termina em STATUS: OK
   python scripts/conferir_telas.py                     # mede em navegador, três tamanhos
   ```
4. **Um commit por etapa**, com `docs/` reconstruído no mesmo commit. Antes de commitar,
   `git status` não pode mostrar mudança em `docs/dados/`: se mostrar, falta `leidenalg`
   (ver `CLAUDE.md`, "docs canônico") — não commite `docs/` nesse caso.
5. **Nunca** edite `docs/` à mão, nunca digite número em modelo, nunca use CDN, nunca troque
   uma cor ou um tamanho por conta própria: use as fichas de `sistema.css`.
6. **Se travar duas vezes no mesmo ponto**, pare, desfaça o que não funciona e escreva o que
   tentou. Não "resolva" apagando teste nem afrouxando asserção.
7. Texto de interface em português, sem anglicismo (`tests/test_anglicismos.py` reprova), com
   vírgula decimal e ponto de milhar.

Cada etapa abaixo termina com **Feito quando**: é a lista de verificação. Os testes de
`tests/test_redesenho.py` marcados com o número da etapa ficam em espera (skip) e passam a
valer sozinhos quando a peça aparece.

---

## Etapa 1 — Fundação: o sistema chega a todas as telas, sem mudar nada à vista

**Objetivo.** Publicar `sistema.css` e o bloco de sólidos em todas as páginas. Como tudo no
sistema tem prefixo `sd-`, nenhuma tela muda de aparência nesta etapa.

**Passos**
1. Copie `design/sistema.css` para `src/sistema.css` e `design/solidos.svg` para
   `src/solidos.svg`, sem alterar um byte.
2. Em cada modelo (`src/site_template.html`, `src/explorador_template.html`,
   `src/triagem_template.html`, `src/espaco_template.html`):
   - logo depois de `<link rel="stylesheet" href="vendor/fonts.css">`, acrescente uma linha
     com o marcador `__SISTEMA__`;
   - logo depois da linha do `<body ...>`, acrescente uma linha com o marcador `__SOLIDOS__`.
3. Em `src/build_site.py`:
   - defina `SISTEMA_CSS` e `SOLIDOS_SVG` junto das outras constantes de caminho;
   - crie a função `comum(html)` que troca `__SISTEMA__` por
     `<link rel="stylesheet" href="sistema.css">` e `__SOLIDOS__` pelo conteúdo de
     `src/solidos.svg`;
   - aplique `comum(...)` às quatro páginas antes de gravar cada uma;
   - em `main()`, copie `src/sistema.css` para `docs/sistema.css` (`shutil.copy`).

**Feito quando**
- `tests/test_redesenho.py::test_etapa1_sistema_publicado` deixa de pular e passa;
- nenhuma página tem `__SISTEMA__` ou `__SOLIDOS__` sobrando;
- `python scripts/conferir_telas.py --capturas /tmp/antes` mostra as telas iguais às de antes
  (esta etapa não muda aparência; os avisos de alvo pequeno que já existiam continuam).

---

## Etapa 2 — Uma barra, as mesmas telas

**Objetivo.** Trocar a barra de abas atual (`.gnav`) pela do sistema (`.sd-barra`, `.sd-telas`),
igual em todas as páginas. Referência visual: o topo de qualquer protótipo.

**Passos**
1. `src/build_site.py`, função `global_nav(active)`: passe a devolver **só** isto (sem
   `<style>`; o CSS vem de `sistema.css`):
   ```html
   <nav class="sd-telas" aria-label="Telas do estudo"><a class="sd-tela" href="index.html" aria-current="page">Estudo</a><a class="sd-tela" href="espaco.html">Espaço 3D</a>...</nav>
   ```
   Ordem das telas: Estudo (`index.html`), A nota (`nota.html`, só a partir da etapa 3),
   Espaço 3D (`espaco.html`), Explorador (`explorador.html`), Triagem (`triagem.html`).
   `aria-current="page"` só na tela atual. Mantenha a regra de só listar tela que será gerada.
2. Em cada modelo, o elemento da barra passa a ser
   `<header class="topbar sd sd-barra">` contendo, nesta ordem:
   `<a class="sd-marca" href="index.html">Ipea/Diest</a>`, o marcador `__GLOBAL_NAV__` e, se a
   tela tiver ações próprias, `<div class="sd-barra-fim">...</div>`.
   - **Relatório:** dentro de `sd-barra-fim` vai o menu de seções. Troque
     `<details class="navmenu">` por `<details class="sd-secoes">`, com
     `<summary>Seções</summary>` e os links dentro de um único `<div>` (como no protótipo
     `entrada.html`). Apague as regras CSS `.navmenu` e `.navlist` do modelo, inclusive a
     `@media(min-width:901px)` que tentava mostrar a lista em linha: nos navegadores atuais
     ela deixa o menu invisível no computador. Copie do protótipo `entrada.html` o trecho de
     script que fecha o menu ao escolher um destino, ao tocar fora e com a tecla Esc.
   - **Explorador:** só marca e abas.
   - **Espaço 3D:** só marca e abas (a marca passa a ser a comum, "Ipea/Diest").
   - **Triagem:** a barra fica só com marca e abas. Os controles que hoje estão dentro da
     barra (curadoria, salvar, exportar, importar, limpar) vão para um
     `<div class="triagem-acoes">` logo abaixo da barra, com o CSS que a `.topbar` tinha
     (`display:flex;flex-wrap:wrap;align-items:center;gap:14px;padding:.6rem 1.1rem;`
     `border-bottom:1px solid var(--border-s);font-family:var(--mono);font-size:11px`).
     Ajuste `.bar2{top:...}` para a altura da nova barra (52 px).
3. Em cada modelo, apague a regra de base `.topbar{...}` e as `.topbar .brand{...}` (as fichas
   do sistema as substituem). **Mantenha** `.topbar` dentro de `@media print`.
4. Atualize os testes que citam a barra antiga:
   - `tests/test_espaco.py`, `test_navegacao_tem_a_aba_em_todas_as_telas`: a asserção da aba
     ativa passa a procurar `href="espaco.html" aria-current="page">Espaço 3D<`;
   - `tests/test_espaco.py`, `test_navegacao_cabe_no_celular_headless`: seletor `.sd-tela` no
     lugar de `.gnav-tab`; o número esperado de abas é o de telas existentes (4 nesta etapa,
     5 depois da etapa 3); acrescente a largura 320 à lista de larguras.

**Feito quando**
- `test_etapa2_barra_nova_em_todas_as_telas` deixa de pular e passa;
- `python scripts/conferir_telas.py` não acusa "abas cortadas" nem "rola para o lado" em
  nenhuma tela;
- no relatório, o botão "Seções" aparece e abre no computador **e** no celular (no celular
  ele flutua no canto inferior direito).

---

## Etapa 3 — A nota: a bibliografia do texto para discussão no mapa

**Objetivo.** Nova tela `docs/nota.html`. Referência: `design/prototipos/nota.html`.

**Passos**
1. Crie `src/nota.py` com:
   - `dados(cena)`: cópia **literal** de `dados_nota(cena)` de
     `design/ferramentas/gera_prototipos.py` (o teste compara os dois resultados);
   - as funções de montagem do mesmo arquivo, também literais: `br`, `esc`, `solido`, `selo`,
     `mistura`, `item_obra`, `item_fora`, `busca`, `monta`. Em `item_obra`, o link
     `../../docs/espaco.html#...` passa a ser `espaco.html#...`;
   - `pagina(modelo, cena, corpus)`: monta o contexto (`num`, `nota`, `corpus`) e os blocos
     (`obras_no_nucleo`, `obras_fora`, `atos`, `autores`, `chips_eixo`) e devolve o HTML.
2. Crie `src/nota_template.html` a partir de `design/modelos/nota.html`:
   - `../../docs/vendor/fonts.css` vira `vendor/fonts.css`; a linha do `../sistema.css` vira
     o marcador `__SISTEMA__`; `{{svg:solidos}}` vira `__SOLIDOS__`;
   - a barra vira a da etapa 2 (`<header class="topbar sd sd-barra">` com `__GLOBAL_NAV__`);
   - `../../docs/espaco.html` vira `espaco.html`; tire "Protótipo — " do `<title>`;
   - os marcadores `{{...}}` ficam como estão: quem os resolve é `nota.pagina`.
3. `src/build_site.py`: constante `NOTA_TPL`; `global_nav` passa a incluir
   `("nota", "nota.html", "A nota")` logo depois de Estudo quando o modelo existe **e**
   `cena["nota"]` não é vazio; em `main()`, gere `docs/nota.html` (com `comum(...)` e
   `__GLOBAL_NAV__`) e imprima a linha `nota: ...` como as outras telas.
4. Ligações de chegada: no Espaço 3D, na lente da nota, acrescente o link "Ver a lista
   completa da bibliografia" para `nota.html`.
5. `.claude/skills/run-scisci-ipea/driver.py`: novo tipo `nota` (conta `.sd-obra`, exige mais
   que zero e nenhum erro de página); atualize a contagem de telas no texto e em `SKILL.md`.
   `README.md`: inclua a tela na lista de telas.

**Feito quando**
- `test_etapa3_dados_da_nota_iguais_a_referencia` e `test_etapa3_pagina_da_nota` deixam de
  pular e passam; `test_etapa2_...` continua passando, agora com cinco abas;
- `python scripts/conferir_telas.py docs/nota.html` dá `RESULTADO: OK`;
- o filtro por tradição esconde e mostra as obras; "Ver no espaço 3D" abre a cena com a obra
  selecionada.

---

## Etapa 4 — A entrada do relatório

**Objetivo.** O primeiro ecrã do relatório passa a dizer o achado e a oferecer três portas.
Referência: `design/prototipos/entrada.html`.

**Passos**
1. Números vivos. Em `src/token_injection.py`, crie `inject_entrada_numbers(html, cena, corpus)`
   com a família de marcadores `ENT_*`, um para cada `{{...}}` do modelo `entrada.html`
   (por exemplo `ENT_PCT_CRUZA` = `num.blocos.pct_inter_canonico` com uma casa,
   `ENT_Q` = `num.silos.Q` com três casas, `ENT_Q_ACASO`, `ENT_N_CONECTORES`, `ENT_N_TESTADAS`,
   `ENT_N_AGENDA`, `ENT_N_NUCLEO_AGENDA`, `ENT_N_ALEM`, `ENT_N_CAND`, `ENT_N_REDE`, `ENT_M_REDE`,
   `ENT_CORPUS`, `ENT_SEMENTES`, `ENT_N_OBRAS_NOTA`, `ENT_N_NOTA_NUCLEO`, `ENT_N_TRIADES_NOTA`).
   Formate com vírgula decimal e ponto de milhar. Sem o dado, avise em stderr (como os outros
   injetores) — nunca deixe marcador cru. Registre o injetor em `build_site.py`.
2. `src/site_template.html`:
   - apague o `<div class="preliminar" ...>`; o seu texto vai para dentro de
     `<details class="sd-estado"><summary>Versão de trabalho</summary><p>...</p></details>`,
     como no protótipo (mesma informação, sem as listras);
   - troque o conteúdo de `<header class="masthead">` pelo bloco `.entrada` do protótipo.
     **Mantenha os ids** `hero3d-link`, `hero3d`, `hero3d-n` e `gen-date`, que o script já
     usa; o canvas passa a aparecer também no celular (a regra que o escondia abaixo de
     560 px sai);
   - troque o `<aside class="startbox">` pelas duas faixas do protótipo: "Por onde entrar"
     (`.sd-portas`, três portas) e "O achado em números" (`.sd-numeros`). Destinos das
     portas: `nota.html`, `#pontes`, `#discussao`. Ferramentas: `espaco.html`,
     `explorador.html`, `triagem.html`;
   - copie o CSS de leiaute do `<style>` do protótipo (classes `.entrada*`) para o `<style>`
     do modelo e apague as regras `.masthead`, `.kicker`, `.subtitle`, `.byline`, `.hero3d*`,
     `.startbox*`, `.startmap`, `.starttools`, `.preliminar` que ficarem sem uso.
3. Números digitados na prosa. No resumo, "Q ≈ 0,59", "z ≈ 80" e "Q ≈ 0,5–0,6" estão escritos
   à mão e não batem com `data/modularity_check.json` (0,515 e 53,9). Troque-os por
   `ENT_Q`, `ENT_Z` e `ENT_Q_ACASO`. Não reescreva as frases: só os números.

**Feito quando**
- `test_etapa4_numeros_da_abertura_vem_dos_derivados` deixa de pular e passa;
- `python scripts/conferir_telas.py docs/index.html` não acusa mais alvo pequeno **no trecho
  da entrada** (os do corpo do relatório saem na etapa 5);
- o driver segue em `STATUS: OK` (22 seções, 3 gráficos).

---

## Etapa 5 — O corpo do relatório: atos, argumento e aparato

**Objetivo.** Aplicar ao corpo as peças da galeria `design/prototipos/componentes.html`.
Sem reescrever prosa e sem mexer em número.

**Passos**
1. Capas de ato: cada `<details class="act">` ganha a classe `sd-ato`, e o `<summary>` passa
   a ter três partes — `<span class="sd-ato-n">Ato 2</span>`,
   `<span class="sd-ato-t">título</span>` e `<span class="sd-ato-r">resposta medida</span>`.
   A resposta medida de cada ato usa marcadores `ENT_*`/`PROV_*`/`SOLIDEZ_*` que já existem;
   onde não houver número pertinente, use uma frase sem número. Apague o CSS antigo de
   `details.act>summary`.
2. Registros: os atos "Aparato" e "Apêndices" recebem `sd-aparato` no conteúdo; os demais,
   `sd-argumento` nos blocos de prosa. Não mude a ordem das seções nem os ids.
3. Destaques: cada `.callout` recebe `sd-destaque` mais o papel (`sd-achado`, `sd-limite` ou
   `sd-como-ler`) e abre com a palavra correspondente em `<strong>`.
4. Tabelas: envolva cada tabela larga em `<div class="sd-rolagem">`; colunas numéricas com
   `sd-n`.
5. Alvos de toque: todo link ou botão do relatório com menos de 44 px de altura no celular
   ganha altura mínima (`min-height:var(--sd-alvo)` com `display:inline-flex` e
   `align-items:center`).

**Feito quando**
- `python scripts/conferir_telas.py docs/index.html` dá `RESULTADO: OK` nos três tamanhos;
- `pytest -q` verde; driver em `STATUS: OK`; as 22 seções continuam com os mesmos ids.

---

## Etapa 6 — Explorador e Triagem na mesma língua

**Objetivo.** As duas ferramentas passam a usar as peças e o vocabulário das outras telas.

**Passos**
1. Vocabulário único (hoje há três contagens chamadas "alvos"): em toda a interface,
   "tríades a construir" para as 84, "obras da agenda" para as 56 obras que entram nelas e
   "obras da síntese na agenda" para as da triagem. Os números vêm dos dados, não do texto.
2. Explorador: rótulos de bloco em frase curta e sem caixa-alta (`sd-sobre`); filtros de
   tradição como `sd-chip` com o sólido e a contagem "observadas + inferidas"; campo de busca
   `sd-campo`; botões `sd-botao`; painel de detalhe com a classe `sd-painel`, o selo da
   tradição e o link "Ver no espaço 3D" (`espaco.html#lente=silos&obra=ID`). A cena d3 não
   muda nesta etapa.
3. Triagem: cartões no padrão `sd-cartao` da galeria (selos no lugar das pílulas de cor,
   medidas com nome em `sd-medidas`, números com vírgula decimal); ações em `sd-botao`; a
   faixa "Comece por" com `sd-chip`.
4. Todos os alvos com 44 px no celular e no tablet.

**Feito quando**
- `python scripts/conferir_telas.py` dá `RESULTADO: OK` para as cinco telas;
- os testes `tests/test_triagem_ux.py` e o driver continuam passando (o driver conta
  `#graph circle` e `.card`: mantenha esses seletores válidos ou atualize o driver junto).

---

## Etapa 7 — Impressão e arremate

1. Impressão: atos abertos, barra e menus fora, sólidos com contorno preto, destaques e
   figuras sem quebra no meio (as regras `@media print` de `sistema.css` já cobrem as peças
   `sd-`; confira o que sobrar do CSS antigo).
2. Atualize `README.md`, `METODOLOGIA.md` (uma linha sobre a tela A nota) e
   `.claude/skills/run-scisci-ipea/SKILL.md`.
3. Rode a lista inteira de "Como trabalhar" uma última vez e commite.

---

## Fora deste plano (precisa de decisão de quem responde pelo estudo)

- Diagrama do Modelo de Sistema Viável sobre o arranjo real e a camada de cor para funções
  institucionais (pedidos na encomenda de 18/09): dependem da versão final do texto para
  discussão.
- Trocar o critério de desempate da inferência de tradição; fundir registros duplicados da
  rede; nomes e ordem dos autores; "NIB (2023)" contra a resolução de 22/01/2024.
- Trocar os círculos do explorador 2D por formas que acompanhem os sólidos.
