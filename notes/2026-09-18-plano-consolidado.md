# Plano consolidado de ajustes — do diagnóstico ao desenho

**2026-09-18.** Consolida (a) o balanço de funcionalidade/estética/publicabilidade do site
e (b) a avaliação do texto-base da Claucia (MSV × NIB × Agências), num plano único em
cinco frentes: **repo · linguagem · metodologia · caminho do pensamento · UX**.

---

## 0. A articulação — por que este plano existe

O site e o texto são **as duas metades do mesmo argumento**, e hoje nenhum cita o outro.

| | o site (`docs/`) | o texto da Claucia |
|---|---|---|
| pergunta | as três tradições se falam? | o arranjo MDIC-NIB-agências é viável? |
| resposta | **não — são silos**; a convergência precisa ser *construída* | eis o **desenho institucional** que a constrói |
| nível | campo intelectual (literatura) | organizações reais (arranjo federal) |
| estado | diagnóstico + tese, sem carga institucional | proposta, sem lastro empírico do projeto |

A costura já está escrita no próprio site — só não foi puxada:

- **§14 (Síntese)** já propõe, literalmente: *"ler a política industrial como um **sistema
  viável**: capacidade, regulação, propósito e retroalimentação."* → **o texto da Claucia é
  exatamente essa leitura, instanciada na NIB.** Hoje §14 é uma promissória que o texto paga.
- **§12.5 (Lacunas e agenda)** nomeia a lacuna: *"mecanismos de coordenação
  interinstitucional"* → **é precisamente o Componente 1 (Câmara de Coordenação) do texto.**
- **§12.4** já cita *"regulação adaptativa inspirada em princípios cibernéticos, da qual o
  **ambiente regulatório experimental (sandbox) do Banco Central** é precedente"* → é o
  mesmo exemplo do §6.3 do texto, já em português.
- **§11** já mobiliza **Ashby/Beer** (capacidade), **Stigler/Majone/Levi-Faur** (regulação) e
  **Rodrik/Mazzucato** (missões) — o cânone que **falta inteiro no texto**.

**Conclusão operacional:** o ajuste não é inventar ponte, é **fechar um laço já meio
escrito** — em duas direções: o texto herda a evidência e o cânone do site; o site ganha o
ato propositivo que hoje não tem.

---

## 1. Repo

| # | ação | nota |
|---|---|---|
| **R1** | **Resolver o resíduo §10·6** — re-rodar a Fase D (`author_network.py`) sobre o corpus re-semeado | **bloqueia a versão final**; é o que o banner *Material preliminar* declara |
| **R2** | Fixar que o `docs/` canônico só se constrói no **ambiente completo** (igraph + leidenalg) | no mínimo, comunidades colapsam e `n_authors` muda; o aviso em stderr (já commitado) evita o build silencioso com tokens crus |
| **R3** | Tornar **hermético** o teste que reconstrói `docs/` (escrever em tmp) | hoje `pytest` **muta o artefato publicado** |
| **R4** | Publicar `author_network.json` como **artefato de release** | hoje é `.gitignore` (~15 MB); sem ele um clone mínimo não reproduz §10·6 |
| **R5** | **Trazer o texto da Claucia para o repo** — `docs/material-brasil/texto-base-msv-nib.md`, ao lado da `revisao_brasil.md` (mesma autora) | hoje o texto **não existe no repo**: o site não pode citá-lo nem o funil indexá-lo |
| **R6** | **Não regenerar o CHANGELOG** até decidir o histórico da branch | o script o encolheria de **173 → 111** entradas (62 commits existem mas não são alcançáveis do HEAD) |
| **R7** | **Reconciliar a data da NIB** | o site diz *"Nova Indústria Brasil (2023)"*; o texto diz *lançada em 22/01/2024, Decreto 11.964/2024*. Ambos concordam no alvo 11%→15% até 2033 |

---

## 2. Linguagem

O projeto tem critério declarado (*prosa sem anglicismo*) **com teste automatizado** — e
`trading zone` está na lista de termos banidos. Como está, **o texto quebraria a suíte ao
entrar no repo**.

O ponto que economiza trabalho: **a casa já traduziu tudo.** A tabela abaixo sai do próprio
site, não de preferência pessoal:

| no texto | termo da casa | fonte no site |
|---|---|---|
| *framework* (título + ~15×) | **arcabouço** | §14.2 "arcabouço integrador" |
| *trading zones* | **zonas de intercâmbio** | glossário §20 e título do §05 |
| *sandbox* | **ambiente regulatório experimental** | §12.4 (já com "(sandbox)" entre parênteses) |
| *pipeline* | **funil de coleta** | glossário §20 |
| *design* / *redesign* | **desenho** / **redesenho** | o texto hoje alterna os dois |
| *procurement* | **compras públicas** | — |
| *inputs* | **contribuições / insumos** | — |
| *co-criação* | **construção conjunta** | — |

- **L1** Aplicar a tabela, **a começar pelo título**: *"…Rumo a um **Arcabouço** Institucional
  Viável…"*.
- **L2** Seguir o estilo da casa: **termo em português + anglicismo em itálico entre
  parênteses na primeira ocorrência** (é o que §12.4 e o glossário já fazem).
- **L3** Estender `tests/test_anglicismos.py` para cobrir o novo `.md` quando ele entrar (R5).

---

## 3. Metodologia

- **M1 Declarar os dois níveis de diagnóstico** (nova seção em `METODOLOGIA.md`):
  **bibliometria** = estrutura do campo intelectual (dados públicos, OpenAlex);
  **MSV + protocolo** = estrutura do arranjo institucional (dados primários).
  São níveis distintos — **um não valida o outro**, e dizer isso protege os dois.
- **M2 Reatribuir o "Protocolo ASC"** → metodologia de **Pérez Ríos** (VSMethodology) /
  **Espejo** (VIPLAN) + síntese de **Mariano (2022)**. Schwaninger e Pérez Ríos **já estão nas
  referências do texto**; a autoridade vaga ("a ASC") vira linhagem verificável.
- **M3 Assumir os limites da analogia** água→indústria: Mariano é **tese única**, sobre
  governança **territorial/federativa** de recursos hídricos; a NIB é **setorial/funcional por
  missões**. Um parágrafo honesto basta — e é exigido pelo padrão do projeto.
- **M4 Regime de dados muda**: entrevistas/Likert/oficinas com servidores de agências são
  **dados primários com pessoas** — consentimento e procedimento ético precisam constar.
  Até aqui o projeto só usou dado público verificável.
- **M5 Fidelidade ao MSV** (a metodologia depende disso): corrigir **S3\*** (o §2.2 do texto
  lista "Sistema 3" duas vezes) e a atribuição **Ashby × Beer** (*"only variety can absorb
  variety"* é fraseado de Beer; Ashby escreve *destroy*).
- **M6** Registrar em `METODOLOGIA.md §3` que **§10·6 é resíduo declarado** até R1 fechar.

---

## 4. Caminho do pensamento (arco narrativo)

**Diagnóstico do arco atual.** O clímax propositivo está **soterrado no meio**: §11
(Implicações) e §14 (Síntese) ficam no Ato 3, e o relatório **termina em aparato técnico**
(reprodutibilidade, dados, pontes de ordem superior). O arco sobe e depois desce para a
infraestrutura. O Ato 4 ainda **mistura dois registros** — agenda ("pontes a construir") e
aparato ("reprodutibilidade").

**Proposta — 6 atos, com o propositivo promovido ao fim:**

| ato | seções | função |
|---|---|---|
| 1 · Como medimos | 00–03 | método e funil |
| 2 · A estrutura: os silos | 04–08·5 | **o achado central** |
| 3 · O que emerge | 09–10·6 | candidatos, autores-ponte |
| 4 · O caso brasileiro | 12–13 | instituições densas, lacuna na prática |
| **5 · Do diagnóstico ao desenho** | **11 · 14 · §15 (novo)** | **o que fazer** ← carga do texto |
| Aparato + Apêndices | 15–18c · 19–21 | repro, dados, pontes técnicas, glossário |

- **C1** Mover **§11 e §14** para o ato final (hoje no Ato 3).
- **C2** Criar **§15 — "Arcabouço institucional: a NIB como sistema viável"**: o texto da
  Claucia condensado (S1–S5 sobre MDIC/NIB/agências, os 4 componentes, os indicadores).
- **C3** Separar **aparato** de **argumento** (hoje fundidos no Ato 4).
- **C4** **Fechar o laço nos dois sentidos**: o §15 responde citando a lacuna que o §12.5 já
  nomeou; e o texto **abre citando o achado dos silos** — *"a análise mostrou que essas
  tradições não se falam; este é o desenho da ponte que os dados dizem faltar."*

---

## 5. UX

- **U1 Manter 3 telas** (Estudo · Explorador · Triagem). O ato propositivo **não pede 4ª
  tela** — pede destaque dentro do Estudo.
- **U2 Ato 5 aberto por padrão** (`<details open>`); o **aparato fica recolhido**. Hoje o
  index tem ~46 mil px — a hierarquia de dobra é o que o torna legível.
- **U3 A primeira figura propositiva do site**: um **diagrama do MSV** (S1–S5 mapeados em
  agências / MDIC / Presidência). Todo o visual hoje é bibliométrico — mostra *o que há*,
  nunca *o que fazer*. SVG embutido, sem dependência nova (o padrão é `docs/vendor/`, sem CDN).
- **U4 Reescrever "Comece por aqui"**: hoje promete diagnóstico; deve prometer
  **diagnóstico _e_ desenho**.
- **U5 Triagem**: avaliar um recorte novo de curadoria — **"desenho institucional"** (obras de
  capacidades estatais / evolucionária, o terreno comum que o §14 identifica).
- **U6** Só depois de tudo: **retirar o banner _Material preliminar_** e o "não citar como
  versão final".

---

## 6. Sequenciamento (o que bloqueia o quê)

1. **R1 + R2** — resíduo §10·6 e build canônico. *Bloqueia qualquer promoção a versão final.*
   Exige o ambiente pesado (Colab "Célula 13" / Actions "funil-rerun"), **fora deste contêiner**.
2. **L1–L2 + M2/M3/M5** — correções no texto. Baratas, independentes, podem começar já.
3. **R5** — texto entra no repo → então **L3** (teste de anglicismo passa a cobri-lo).
4. **M1/M4/M6** — `METODOLOGIA.md` ganha os dois níveis e o regime de dados primários.
5. **C1–C4** — rearranjo narrativo + **§15**.
6. **U1–U5** — UX, incluindo o diagrama do MSV.
7. **U6 + R7** — banner e data da NIB reconciliada. **Fim: versão citável.**

> Itens 2–6 são acionáveis aqui. O item 1 não é — e é o único que **bloqueia** a publicação.
> Ou seja: dá para fazer o texto, a linguagem, a metodologia, o arco e a UX inteiros
> **enquanto** a Fase D não roda.
