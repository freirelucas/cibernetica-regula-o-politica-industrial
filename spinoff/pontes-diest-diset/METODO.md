# Método — pontes epistêmicas DIEST × DISET

> Regra herdada do projeto-mãe: **só dado real, verificável, com a ressalva no ponto da
> afirmação.** Nenhum número do relatório é digitado à mão; tudo sai de `data/results.json`.

## 1. Fontes (todas públicas, verificadas em 2026-10-02)

| Fonte | O que dá | Como |
|---|---|---|
| Diretório "Quem faz pesquisa no Ipea" (`ipea.gov.br/portal/pesquisadores-do-ipea`) | **quem está ativo** (~184 perfis), áreas de estudo, **variantes de nome usadas nas publicações**, minibiografia | `src/roster.py` (HTML) |
| Repositório do Conhecimento do Ipea (DSpace 9.2, `repositorio.ipea.gov.br/server/api`) | ~16,5 mil obras (Publication + Book) com autores, VCIpea (vocabulário controlado), palavras-chave, classificação, resumo, série, editora/unidade; ~400 entidades Pessoa (cargo, Lattes, ORCID) | `src/harvest_repo.py` (REST `discover/search/objects`) |
| OpenAlex (opcional, exige chave) | referências citadas, tópicos, produção fora do Ipea | `src/openalex_enrich.py` |

**Achado de engenharia (registrar):** o filtro `diretoria=` do diretório é ignorado pelo
servidor — devolve a lista toda e quebra a paginação. Daí a decisão de **atribuir a
diretoria pela produção** (§2), que também é mais defensável: mede onde a pessoa
*produz*, não onde está lotada no papel.

## 2. Atribuição de diretoria (`src/attribute.py`)

1. **Obra → diretoria**: sinais *editoriais* (editora/unidade responsável, `dc.contributor.other`,
   série "Nota Técnica Diest/Diset nº", DOI `nt-diest`, boletins BAPI e Radar). Título e resumo
   **não** contam — um texto *sobre* a Diest não é *da* Diest. Seis diretorias de pesquisa entram
   no cômputo (DIEST, DISET, DISOC, DIRUR, DIMAC, DINTE): sem o contraste, quem só coassinou um
   boletim seria rotulado errado.
2. **Pessoa → diretoria**: soma das obras rotuladas em que assina, com peso de recência
   (meia-vida 4 anos). Atribui se a dominante tem ≥50% do peso e ≥2 obras rotuladas.
   Confiança: `explicita` (cargo no perfil de Pessoa do repositório), `forte` (≥70%, ≥4 obras),
   `moderada`, `fraca`/`sem_sinal` (não atribuída).
3. **Ativo** = está no diretório do portal, ou publicou nos últimos 3 anos.
4. **Identidade**: variantes de nome do próprio portal → casamento exato; senão
   (sobrenome, 1º prenome) se único no quadro. Fora do quadro, cada assinatura normalizada é
   um autor (pode partir uma pessoa em duas — viés conservador para pontes).

## 3. Hipergrafos (`src/analysis.py`)

| Hipergrafo | Nó | Hiperaresta | Pergunta |
|---|---|---|---|
| **H_co** coautoria | autor | obra (todos que assinam) | quem *já* trabalha junto? |
| **H_sem** semântico | autor ativo | termo (VCIpea, palavra-chave, classificação, área de estudo) | quem *fala do mesmo*? |
| **H_ref** acoplamento (opcional, OpenAlex) | autor | obra citada | quem *lê o mesmo*? — a ponte epistêmica mais pura |

**Por que hipergrafo e não grafo de pares.** Uma nota técnica com 8 autores vira 28 laços no
grafo projetado — infla pontes "de coletânea". No hipergrafo a obra é *uma* relação de ordem
superior. Medidas usadas:
- **Hiperarestas mistas** (têm membro DIEST *e* DISET) contra **modelo nulo** de permutação de
  rótulos de diretoria (hipergrafo fixo, 1000 permutações) → z. z muito negativo = silos.
- **Peso de Newman** Σ 1/(|e|−1) para pares cruzados (desconta coletâneas) e contagem de pares
  que **só** existem via obras com ≥4 assinaturas.
- **Grafo-linha s** (s = 1, 2, 3): duas obras ligadas se partilham ≥ s autores. Se a ponte
  DIEST–DISET some em s=2, ela depende de indivíduos isolados, não de **equipes** recorrentes.
- **Corretores**: quem coassina com membros dos dois lados (√(n_D·n_S)); **pontes por
  trajetória**: quem tem ≥20% da produção rotulada em cada diretoria (mudou de diretoria).

**Produção característica**: log-odds com prior de Dirichlet informativo (Monroe, Colaresi &
Quinn 2008) sobre os termos das obras *exclusivas* de cada lado, prior = todo o Ipea na janela.

**Zonas de convergência**: termos de H_sem usados por ≥2 ativos de cada lado; escore =
equilíbrio (2·min/soma) × log(1+usuários); termos agrupados por Jaccard de usuários ≥ 0,3.

**Colaboradores potenciais**: pares DIEST×DISET ativos sem coautoria, ordenados por cosseno
TF-IDF dos perfis × (1 + 0,25·coautores comuns, até 4) — fechamento triádico: um coautor comum é
quem pode apresentar.

**Hiperarestas potenciais (equipes)**: por zona, 2 nomes DIEST + 2 DISET de maior peso nos termos
da zona + o primeiro corretor que já coassinou com alguém de cada lado. É uma *predição de
hiperaresta*, não de par — o objeto certo quando o produto é uma nota técnica coletiva.

## 4. Avaliação da ideia de hipergrafos (critério de decisão)

Vale o hipergrafo se (a) a fração de obras com ≥3 assinaturas é alta (ver §1 do relatório),
(b) muitos pares cruzados só existem via obras grandes, e (c) o grafo-linha s muda a
conclusão entre s=1 e s=2. Se nenhuma das três vale, o grafo de pares com peso de Newman
basta — e é mais fácil de explicar. O relatório traz os três números.

## 5. Ressalvas (onde NÃO confiar)

- **Circularidade parcial**: a diretoria da pessoa vem das obras rotuladas, e a obra mista é
  definida pela diretoria das pessoas. Obras de uma diretoria com coautor da outra *contam a
  favor* da diretoria dominante. Mitigação: o nulo permuta rótulos; a confiança é exposta;
  validar a lista de membros com as chefias (é barato e decisivo).
- **Cobertura**: o repositório cobre a produção *editada pelo Ipea*; artigos em periódicos
  externos entram só parcialmente → camada OpenAlex.
- **Vocabulário**: VCIpea é controlado, mas palavras-chave são livres (sinonímia).
  Zonas são hipóteses para conversa, não fronteiras.
- **Nomes**: homônimos fora do quadro podem fundir pessoas; o casamento frouxo só opera
  contra o quadro do Ipea, onde (sobrenome, 1º prenome) é único.
- **Lotação muda**: DISET hoje é "Setoriais, de Inovação, **Regulação** e Infraestrutura";
  pessoas migram. A meia-vida de 4 anos privilegia a lotação recente.
