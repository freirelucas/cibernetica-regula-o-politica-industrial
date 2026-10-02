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
  validar a lista de membros com as chefias (é barato e decisivo) — ver §6.
- **Cobertura**: o repositório cobre a produção *editada pelo Ipea*; artigos em periódicos
  externos entram só parcialmente → camada OpenAlex.
- **Vocabulário**: VCIpea é controlado, mas palavras-chave são livres (sinonímia).
  Zonas são hipóteses para conversa, não fronteiras.
- **Nomes**: homônimos fora do quadro podem fundir pessoas; o casamento frouxo só opera
  contra o quadro do Ipea, onde (sobrenome, 1º prenome) é único.
- **Lotação muda**: DISET hoje é "Setoriais, de Inovação, **Regulação** e Infraestrutura";
  pessoas migram. A meia-vida de 4 anos privilegia a lotação recente.

## 6. Validação da lista de membros com as chefias (`src/membership.py`)

**Mudança de 2026-10-02 (item 1 da fila).** A atribuição por produção passou a ter uma via
de correção externa, porque é o alicerce de todo o resto e a §5 mostra por que não basta.

- `data/membership_overrides.json` guarda a palavra das chefias. Lido por `attribute.py`,
  **vence** a inferência: a pessoa fica com `confidence = "validada"` (ou `validada_fora`,
  quando a chefia diz que não é membro de diretoria de pesquisa). A inferência original fica
  preservada em `inferred_diretoria` / `inferred_confidence`, que é o que permite medir o erro.
  Arquivo ausente ou sem registros → o núcleo roda exatamente como antes. Registro com status
  fora da lista, ou `corrigido` sem diretoria, é **erro duro**: atribuir errado em silêncio é
  pior do que quebrar.
- `data/membership_validation.csv` (`python src/membership.py --export`) é a planilha que vai
  para as chefias: 280 linhas — 261 membros atribuídos (166 ativos) e 19 pessoas **com**
  produção DIEST/DISET que o método **não** conseguiu atribuir e podem ser membros perdidos.
  Cada linha traz a evidência que gerou a atribuição (obras rotuladas, peso dominante, pesos
  por diretoria, assinaturas) e três colunas em branco: `situacao`, `diretoria_correta`,
  `observacao`. Ordem: atribuídos ativos → atribuídos inativos → sem atribuição, por volume
  de obras rotuladas, para que as primeiras linhas sejam as que mais afetam o resultado.
  O grupo `sem_atribuicao` é filtrado por plausibilidade de quadro (diretório, cargo, ou
  ativo com ≥3 obras rotuladas); sem o filtro entram ~556 coautores externos de um único
  boletim e a revisão fica inviável. Instruções: `docs/VALIDACAO_MEMBROS.md`.
- `python src/membership.py --ingest <csv>` converte a planilha preenchida em overrides e
  revalida o que escreveu; `--audit` recalcula a precisão.
- **Precisão** (`data/membership_audit.json`, e `results.json` → `validation`): confirmados
  sobre decididos, por estrato de confiança inferida. `desconhecido` não entra no
  denominador; `fora` conta como erro (o método atribuiu quem não é membro). O §2 do
  relatório declara **Pendente** enquanto não houver nenhuma resposta — hoje é o caso:
  `validation.status = "pendente"`, `n_membros_focus = 261`, precisão **desconhecida**.

Sem efeito sobre os números atuais (nenhum override gravado): obras mistas 45, nulo
391,4 ± 23,0, z = −15,09, ativos 65/56 — idênticos aos de antes da mudança.

**Correção de verificação, mesma data.** `tests/test_core.py` não tinha executor: `python
tests/test_core.py` importava o módulo, não rodava teste nenhum e devolvia 0. O comando do
`CLAUDE.md` dava, portanto, uma falsa garantia. Agora há um executor de stdlib no fim do
arquivo; a suíte roda 8 testes (4 novos: override vence inferência, casamento por nome,
registro malformado quebra, precisão por estrato).
