# Nota metodológica — como ler os achados (e onde NÃO confiar)

> Material preliminar. Este documento é a parte *honesta* do método: explica como
> cada heurística é construída, o que ela **de fato** mede, e onde a leitura ingênua
> dela seria circular ou exagerada. A regra do projeto é **só dado real** (OpenAlex,
> IDs verificados) e **divulgar a ressalva no ponto da afirmação**.

## 0. O reenquadramento (jun/2026)

O eixo **Regulação** passou a ser **regulação econômica** (Stigler, Peltzman, Posner,
Majone, Levi-Faur, Laffont-Tirole — captura, monopólio natural, antitruste, estado
regulador). A tradição *tools of government / nodalidade* (Hood, Margetts) — que antes
ocupava o eixo Reg — migrou para **Cyb**, como leitura cibernética do controle estatal.
Fonte única das sementes e do vocabulário: `src/minirun.py` (**20 por eixo, 60 no total**;
+4 da sonda de complexidade). Corpus reprocessado: **6.340 trabalhos**.

**Achado robusto ao reprocessamento.** A tese central — *as três tradições formam silos
de citação que se cristalizaram nos anos 1980* — sobrevive ao corpus 5× maior: a fração
de cocitação **intra-eixo** sobe 0,74 (1970s) → **0,83** (1980s) → 0,90 → 0,94. Mudou um
sub-resultado: as três tradições já são **copresentes no tempo desde 1979** (não 2005) —
ou seja, coexistir no tempo **não** é citar-se.

**Verificação reprodutível** (`src/modularity_check.py` → `data/modularity_check.json`).
Recomputa o achado dos silos com o **mesmo modelo nulo** do relatório (configuração,
preserva o grau): na rede do explorador, a partição por eixo tem **Q = 0,51** contra ≈0
no acaso (**z ≈ 50**) e **0 obras conectoras** significativas — os eixos são silos reais,
não artefato de amostragem. *(O §00 cita Q≈0,59 da rede interna de 600 nós do funil, que
não é exportada; 0,51 é o número **reprodutível a partir do repositório** — mesma
conclusão.)* **Ressalva H1, agora quantificada:** **46,8% dos nós cocitados ficam sem
eixo** — referências que o vocabulário não classifica — e são deixados **fora** da
partição (não viram uma "comunidade", o que distorceria Q para baixo).
**Robusto à reamostragem:** derrubar 20% dos nós (bootstrap, B=300) mantém **Q = 0,51 ±
0,02** (IC95 [0,47, 0,55]) — os silos não são artefato de quais obras entraram na rede. **Robusto também à seleção das
sementes:** tirar 20% das 60 sementes (×5, proxy de rede) mantém **Q ∈ [0,50, 0,52]** (média 0,51).

## 1. Crítica das heurísticas (o que cada uma esconde)

| # | Heurística | O que sugere | Como é construída | Onde a leitura ingênua falha | Tratamento |
|---|---|---|---|---|---|
| **H1** | Rótulo de eixo | "a obra pertence a 1 dos 3 eixos" | vocabulário sobre título+tópicos, **sem abstract** numa fração relevante; faltando, o eixo é herdado da **vizinhança** de cocitação | rótulo derivado da vizinhança torna a afirmação trans-eixo **parcialmente circular** | **MEDIDO** (H1 ✓): proveniência separada (`axis_obs`/`axis_all`/`axis_src`); inferidor validado (**acurácia 0,887**); réplica só-observados; ressalva no ponto da afirmação (§18b) |
| **H2** | Ponte trans-eixo | "a obra articula tradições" | hiperaresta que toca ≥2 eixos; hoje com **peso uniforme** | herda a circularidade de H1; uma ponte que toca 2 eixos conta igual a uma que toca 8 | ponderar **1/(s−1)**; reportar % dependente de inferido |
| **H3** | Brokerage / HO-BC (autores) | "humanos que atravessam silos" | mesmos rótulos de H1 sobre o grafo de coautoria | mesma dependência de H1 | idem H1 |
| **H4** | Solidez tripla | "a ponte é real" | nulo casado em **eixo+grau** (H4 ✓) + FDR; *holdout* temporal; faixa semântica | resta: a faixa semântica é **auto-referente** (percentis da própria amostra) | grau **casado** no nulo (feito); falta faixa vs **população de referência** |
| **H5** | Integração (ex-"DESIGN") | "a tríade integra os silos" | **condutância real** — ΔKf (redução da resistência efetiva ao realizar a face), POSICIONAL não-grau (H5 ✓) | — | **rebatizado** + Δ índice de Kirchhoff; achado: nada supera o nulo casado em grau (não há ponte latente) |
| **H6** | Rajadas · belas adormecidas · *longue-durée* | "quando/por que os silos se formaram" | cocitação transversal no tempo | soa **causal**; é **descritivo** | rotular explicitamente **descritivo, não causal** |
| **H7** | Reg = "instrumentos de governo" | "regulação" | AXMAP / vocabulário antigo | toda afirmação sobre "Regulação" era, na verdade, sobre *instrumentos* | **corrigido** no reenquadramento (Reg = regulação econômica) |

## 2. Limitações de dados (OpenAlex)

1. **Livros clássicos** (Beer, Ashby, Hood 1983): `referenced_works = []` na API — a bola
   de neve **regressiva** dessas sementes é nula.
2. **Cobertura de resumos**: alta para artigos pós-1996, menor para anteriores e livros —
   o que alimenta o problema H1 (rótulo sem abstract).
3. **Filtro vocabular**: introduz **viés de confirmação** — trabalho pertinente com
   vocabulário não coberto é excluído.
4. **Autoria**: metadados imperfeitos em alguns registros; sementes canônicas normalizadas,
   demais reproduzidas como obtidas.

## 3. Estado (o que já está honesto vs. pendente)

- **Feito:** reenquadramento de Reg (H7); auditoria de VAZIO/inferência; nulo anti-circular
  e BH-FDR no pairwise; **corpo de análises coerente** (re-run completo numa única janela,
  autores reprocessados); **peso 1/(s−1) na HO-BC** (H2 ✓); **nulo da solidez casado em grau** (H4 ✓);
  **integração = condutância real (ΔKf), rebatizada de "DESIGN"** (H5 ✓ — achado: nada supera o nulo casado em grau);
  **higiene de integridade** (8 obras-fantasma 404 + 2 agregados de periódico removidos; **reverificada ao
  vivo** — 451 IDs de nó resolvem no OpenAlex, 0 mortos, jun/2026); **Q reconfirmado na rede limpa**
  (Q ≈ 0,51, z ≈ 50, bootstrap 0,51 ± 0,02); **sensibilidade às sementes** (drop-20% das 60 ×5):
  **Q ∈ [0,50, 0,52]**, média 0,51 — robusta (proxy de rede); **H1 medido e divulgado no ponto da
  afirmação** (§4 desta nota; tokens `PROV_*` no §18b do relatório).
- **Pendente (backlog de rigor):** faixa semântica vs **população de referência** (resto do H4);
  vocabulário validado para a codificação por função (§5); §10·6 sobre o corpus re-semeado.
  *(Reforço opcional: re-snowball completo com 80% das sementes — a sensibilidade acima é proxy de rede.)*

> Em uma frase: **o achado dos silos é forte e robusto; as afirmações sobre *pontes*
> (quem conecta os silos) são as que mais dependem de rótulos inferidos — leia-as como
> limite inferior, não como medida final.**

## 4. Quanto custa a inferência de eixo (H1, medido)

Duas verificações reprodutíveis, ambas versionadas:

**`src/infer_validation.py`** → `data/infer_validation.json`. Aplica ao conjunto de rótulo
conhecido (133 nós: 64 sementes + 69 vocabulário) a MESMA regra que resolve os sem-eixo —
eixo dominante da vizinhança de cocitação. **Acurácia global 0,887**; por eixo: política
industrial 0,979 · regulação 0,947 · cibernética 0,854 · **complexidade 0,143 (n=7)**. O 4º
eixo é praticamente invisível à inferência — qualquer afirmação de ponte que o envolva é a
mais frágil do conjunto. *Controle:* os nós de fato inferidos têm evidência mediana 28
vizinhos rotulados contra 25 do conjunto-ouro, isto é, **não** são mais pobres — logo a
acurácia não é um teto otimista por escassez.

**`src/observed_only_check.py`** → `data/observed_only_check.json`. Roda a camada estrutural
das pontes duas vezes sobre as mesmas hiperarestas, trocando só o mapa de eixos. No espaço
elegível **sem o teto** de `max_candidatos` (com o teto, a comparação mediria o truncamento:
Jaccard 0,203 contra 0,378): 143.740 tríades com inferência contra **54.372** só-observado —
**62,2% do espaço depende de rótulo inferido**. Dos **84** alvos de agenda publicados, 69%
têm ao menos um membro inferido e **33 (39,3%) sobrevivem** sem inferência alguma: é o
**núcleo duro** da agenda, e é por ele que se deve começar a ler.

## 5. Codificação por função do MSV — exploratório, com veredito negativo parcial

`src/vsm_coding.py` → `data/vsm_coding.json`. Classifica o corpus pelas cinco funções do
Modelo de Sistema Viável (proxy **léxico** sobre título+resumo, multirrótulo). Não usa o
rótulo de eixo, portanto **não herda o H1**.

Sobre 159 obras com resumo (54 não acionam função alguma): S5 política 42,1% · S2 coordenação
27,0% · S3 controle 21,4% · S1 operações 18,9% · S4 inteligência 5,7%.

**O teste de sensibilidade derruba parte do achado.** Removido o termo mais frequente de cada
função, a ordenação **muda**: S2 e S3 trocam de posição e S1 desaba de 30 para 7 (o termo
`implement` sozinho o sustentava). Sobrevivem aos dois cortes apenas as pontas: **S5 sempre
em primeiro e S4 sempre em último** (9 → 5), com listas de vocabulário de tamanho comparável
(14–17 termos), o que afasta artefato de lista.

**Leitura honesta:** sustenta-se que a literatura é rica em *propósito* e pobre em
*antecipação* (S4). **Não** se sustenta a leitura de que a coordenação (S2) esteja
desassistida — com vocabulário adequado ela aparece em 27% das obras. O meio da distribuição
não é separável com este instrumento. Enquanto não houver vocabulário validado externamente e
conferência manual de amostra, **isto não entra no relatório como achado** — fica como
derivado exploratório.

## 6. O espaço 3D — posição por regra, não por física

`docs/espaco.html` desenha as 250 obras do núcleo cocitado num tetraedro cujos vértices são
as quatro tradições. A posição de cada obra é a **composição da sua vizinhança de
cocitação**: a contagem de vizinhas de rótulo observado em cada tradição, dividida pelo
total (`src/espaco.py`, função `composicao`). É a mesma contagem da regra de inferência do
§4; por isso o rótulo inferido de uma obra é sempre um vértice mais próximo dela, e a cena
é o retrato geométrico do que `infer_validation.py` mede: as 14 obras de rótulo observado
que ficam longe do vértice da sua cor são exatamente os erros da validação (118 acertos em
133, mais uma obra sem vizinha rotulada).

**Por que não um layout de forças.** Com 250 nós e 7.171 arestas (densidade 0,23), a física
produz um novelo em que nenhum eixo quer dizer coisa alguma, e o desenho muda a cada
semente. Aqui a posição é o dado e é a mesma em qualquer execução. O único ajuste é um
afastamento determinístico, de no máximo 5% da aresta, para que as obras não se sobreponham.

**O que a cena codifica, e o que não.** Forma e cor dizem a tradição, de propósito
redundantes, para a leitura sobreviver à escala de cinza; sólido cheio ou vazado diz se o
rótulo é observado ou inferido; o tamanho acompanha as citações recebidas. A distância entre
duas obras **não** mede a cocitação entre elas: mede a diferença de mistura. A lente do tempo
troca a regra (ano no eixo horizontal, uma raia por tradição, altura igual à parcela da
vizinhança que está fora da própria tradição); a lente da origem separa observados e
inferidos em dois andares, na mesma posição horizontal.

**Empates — achado ao construir a cena.** Em 4 das 117 obras de rótulo inferido, duas
tradições empatam na contagem. A regra de origem (`max` sobre um dicionário, em
`build_site.explorer_network`) decide então pela ordem em que as arestas são lidas:
reprodutível, porque a rede é versionada, mas sem base de medida. Nenhuma das quatro entra
na agenda. Desempatar pelo peso somado de cocitação trocaria o rótulo de duas delas, de
cibernética para política industrial; como nenhum dos dois critérios é mais defensável do
que declarar o empate, a página declara — no painel da obra e na lente da origem — e o
rótulo publicado não foi alterado. O conjunto de validação não tem empates, de modo que a
acurácia do §4 não depende do critério.

**Lente da nota.** `data/td_referencias.json` é a transcrição curada da bibliografia do texto
para discussão — 74 referências, sendo 58 obras e 16 atos normativos —, com o identificador
OpenAlex das obras que estão no núcleo. Só entram identificadores que existem na rede (há
teste automatizado); 20 das 58 obras estão no núcleo, 13 com rótulo observado e 7 com rótulo
inferido. Remover o arquivo desliga a lente. A mesma lente mostra as listas de referências
do corpus sem projeção, que é o dado de origem da cocitação: das 1.383 listas, 13 (0,9%)
tocam as três tradições canônicas.

**Autocontenção.** O motor da cena (`src/espaco3d.js`) é próprio, em canvas 2D, com os cinco
sólidos de Platão construídos e conferidos numericamente (vértices, arestas, faces e relação
de Euler). Não há WebGL, não há biblioteca nova e a página não faz carga externa.
