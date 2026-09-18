# Encomenda — artefato completo de desenho para o relatório SciSci/IPEA

**Projeto:** Cibernética Organizacional · Regulação Econômica · Política Industrial
**Cliente interno:** IPEA / DIEST-COGIT · **Data:** 2026-09-18
**Objeto:** sistema de desenho e peças visuais para a reforma do sítio `docs/`

---

## 1. Por que esta encomenda existe

O relatório está **tipograficamente maduro e argumentativamente incompleto**. Não se pede
embelezamento: pede-se resolver três problemas diagnosticados, que são de **desenho**, não de
gosto.

**Problema 1 — o clímax está soterrado.** O arco atual sobe até a síntese (§14, "ler a política
industrial como um sistema viável") e depois **desce para o aparato técnico**
(reprodutibilidade, descarga de dados, pontes de ordem superior). O leitor que chega ao fim
termina em infraestrutura, não em proposta.

**Problema 2 — o sítio mostra *o que há* e nunca *o que fazer*.** Todas as peças visuais hoje
são **descritivas**: séries temporais, rede de cocitação, agrupamentos, tabelas de obras. Não
existe uma única figura **propositiva**. O projeto agora tem uma proposta institucional
(arcabouço MSV sobre MDIC-NIB-agências) e nenhuma linguagem visual para ela.

**Problema 3 — aparato e argumento estão fundidos.** O Ato 4 mistura agenda ("pontes a
construir") com infraestrutura ("reprodutibilidade", "dados"). São dois registros de leitura e
compartilham o mesmo tratamento visual.

---

## 2. O que existe hoje (ponto de partida, a preservar)

| dimensão | estado |
|---|---|
| telas | 3 — Estudo (`index.html`), Explorador (d3), Triagem |
| relatório | 22 seções em 5 atos recolhíveis (`<details>`), ~46.000 px de altura |
| tipografia | Spectral (títulos) · DM Sans (corpo) · JetBrains Mono (dados) |
| cor | 3 cores de eixo (cibernética · regulação · política industrial) + neutros |
| gráficos | Chart.js (3) + rede em canvas; explorador em d3/SVG |
| entrega | estático, GitHub Pages, **tudo vendorizado em `docs/vendor/` — zero CDN** |
| construção | Python de biblioteca padrão, a partir de fonte única (`scisci_results.json`) |

**Isto está bom e não se quer refazer.** A tipografia, a paleta de eixos e a sobriedade são
patrimônio do projeto. A encomenda é **aditiva e estrutural**, não substitutiva.

---

## 3. A arquitetura-alvo (o que o desenho deve servir)

O relatório passa a ter **seis atos**, com o propositivo promovido ao fim:

| ato | conteúdo | registro |
|---|---|---|
| 1 · Como medimos | método e funil | aparato |
| 2 · A estrutura: os silos | **o achado central** | argumento |
| 3 · O que emerge | candidatos, autores-ponte | argumento |
| 4 · O caso brasileiro | instituições densas, lacuna na prática | argumento |
| **5 · Do diagnóstico ao desenho** | **§11 · §14 · §15 (novo)** | **proposta** |
| Aparato + Apêndices | repro, dados, pontes técnicas, glossário | aparato |

O **§15 — "Arcabouço institucional: a NIB como sistema viável"** é a seção nova, cujo conteúdo
está em `docs/material-brasil/texto-base-msv-nib.md`: as cinco funções do MSV mapeadas sobre
MDIC, NIB e agências reguladoras, com quatro componentes de intervenção e um quadro de
indicadores.

---

## 4. Transformações pedidas (cada uma com o benefício declarado)

### T1 — Distinguir visualmente **argumento** de **aparato**
Criar dois registros de tratamento: o que **defende uma tese** e o que **sustenta a
verificação**. Podem ser fundo, medida de coluna, densidade, marcação de ato — a decisão é do
desenho.
*Benefício:* o leitor deixa de confundir "como medimos" com "o que propomos"; e o aparato pode
encolher sem parecer que a pesquisa encolheu.

### T2 — Dar **corpo visual ao ato propositivo** (a peça central)
Produzir o **diagrama do Modelo de Sistema Viável** aplicado ao arranjo real. Requisitos de
conteúdo, não de estilo:

- as **cinco funções** (S1 Operações · S2 Coordenação · S3 Controle · S4 Inteligência ·
  S5 Política), mapeadas em instituições nomeadas: agências setoriais como S1; MDIC como
  metassistema (S3/S4/S5); Presidência no S5;
- **S3\* (auditoria/canal direto) visivelmente distinto do S3** — não é um segundo S3; é o
  canal que contorna a hierarquia. *(Este ponto já causou erro no texto; o desenho não pode
  reproduzi-lo.)*
- a **recursividade**: indicar que cada S1 é, internamente, um sistema viável completo;
- os **quatro componentes** propostos, legíveis **como intervenções** sobre o arranjo — não
  como caixas a mais: Câmara de Coordenação por Missão (S2), Plataforma de Inteligência
  Compartilhada (S4), Painel de Viabilidade (S3\*), Protocolo de Mandato de Missão (S5).

*Benefício:* é a **primeira figura do projeto que mostra o que fazer**. Hoje a proposta
institucional existe só em prosa e por isso não circula — um diagrama é o que sobrevive a uma
reunião no ministério.

### T3 — Ganhar **uma camada de cor** sem quebrar a que existe
A paleta atual codifica **eixos do campo intelectual** (descritiva). A camada nova codifica
**funções institucionais** (propositiva). Precisa conviver com a primeira sem competir nem se
confundir com ela.
*Benefício:* o leitor distingue "isto é o campo" de "isto é o desenho" pela cor, sem legenda.

### T4 — Transformar o comprimento em **hierarquia de dobra**
~46.000 px só funcionam com dobra deliberada: o **Ato 5 aberto por padrão**, o aparato
recolhido, e um modo de percorrer os atos sem rolagem cega.
*Benefício:* o documento passa de "longo" a "navegável"; o achado e a proposta ficam a um
gesto de distância.

### T5 — **Três portas de entrada** no topo
O "Comece por aqui" hoje oferece uma porta. Deve rotear três leitores reais: quem quer **o
achado** (os silos), quem quer **a proposta** (o arcabouço), quem vai **triar** literatura.
*Benefício:* o pesquisador, o gestor e o revisor param de ler o mesmo texto procurando coisas
diferentes.

### T6 — Sobreviver à **impressão**
Isto será impresso e circulará em PDF dentro do IPEA. O diagrama do MSV e os gráficos precisam
funcionar em **preto e branco**, e os atos recolhidos precisam **imprimir abertos**.
*Benefício:* a peça continua sendo um documento do IPEA quando sai do navegador.

### T7 — **Costurar texto e sítio**
O `.md` do arcabouço e a seção §15 devem ler-se como a mesma peça — mesma nomenclatura, mesmas
denominações de componentes, mesmo diagrama.
*Benefício:* acaba a duplicidade entre "o texto da Claucia" e "o site do projeto"; passam a ser
um argumento só.

---

## 5. Restrições invioláveis

1. **Zero CDN.** Tudo vendorizado em `docs/vendor/`. Já derrubou o sítio uma vez sob rede
   restrita: o *handshake* TLS falha e **todos os gráficos somem**.
2. **Sem dependência nova de execução.** O diagrama deve ser **SVG embutido** (ou Canvas já
   presente). Nada de biblioteca de diagramação adicional.
3. **Construção por biblioteca padrão.** O sítio é gerado por Python sem numpy/pandas, a partir
   de fonte única. O desenho não pode exigir passo de construção novo.
4. **Zero dado inventado.** Nenhum número, sigla ou instituição no diagrama que não esteja no
   texto verificado. Onde faltar confirmação documental, marcar — não preencher.
5. **Português sem anglicismo.** Há teste automatizado com lista de termos banidos. Rótulos de
   figura e de interface entram na varredura.
6. **Acessibilidade.** Nada codificado **só** por cor; contraste adequado; a figura precisa de
   descrição textual equivalente.
7. **Preservar** tipografia, paleta de eixos e a navegação de três telas.

---

## 6. Entregáveis

1. **Especificação do sistema** — escala tipográfica, cor (incluindo a camada nova de T3),
   espaçamento, tratamento de "argumento" vs "aparato", estados de dobra.
2. **Diagrama do MSV** — SVG embutido, claro/escuro, versão em preto e branco para impressão,
   com texto alternativo.
3. **Leiaute do §15** — como a seção se compõe: diagrama, os quatro componentes, o quadro de
   indicadores.
4. **Topo com três portas** (T5) — leiaute e microcópia.
5. **Mapa dos seis atos** — rótulos, numeração, estados padrão de abertura.
6. **Folha de impressão** — o que se recolhe, o que se expande, o que se omite.
7. **Nota de implementação** — onde cada peça entra em `src/site_template.html` e o que muda no
   `build_site.py`, se algo mudar.

---

## 7. Critérios de aceitação

- Um leitor que **só role até o fim** termina na **proposta**, não no aparato.
- O diagrama do MSV é compreensível **sem ler o §15** — e correto quanto ao S3\*.
- A seção nova **não aumenta a altura percebida**: a dobra compensa o acréscimo.
- Tudo funciona **sem rede** (`python3 -m http.server -d docs`) e **em preto e branco**.
- A suíte continua verde, inclusive a varredura de anglicismos sobre os rótulos novos.
- Um gestor do ministério consegue **levar o diagrama para uma reunião** sem precisar do sítio.

---

## 8. Fora de escopo

Redesenhar o Explorador (d3) e a Triagem; trocar tipografia ou a paleta de eixos; introduzir
estrutura de aplicação (framework de interface), animação ou dependência externa; alterar
qualquer número do corpo de evidências.

---

## 9. Dependência conhecida

A seção §10·6 (rede de coautoria) ainda deriva do recorte anterior do corpus — resíduo
declarado no banner *Material preliminar*. **Não bloqueia esta encomenda**: o desenho pode ser
produzido e integrado enquanto o resíduo é resolvido. Bloqueia apenas a **promoção à versão
final** do documento.

> Referências internas: `notes/2026-09-18-plano-consolidado.md` (plano de cinco frentes),
> `notes/2026-06-17-balanco.md` (estado do sítio), `docs/material-brasil/texto-base-msv-nib.md`
> (conteúdo do §15).
