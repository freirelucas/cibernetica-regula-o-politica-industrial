# Como conduzir este projeto no Claude Science

> Este guia não depende de recursos específicos da interface. Ele diz **o que entregar ao
> agente, em que ordem e com que critério de pronto**. Se a ferramenta tiver um campo de
> "instruções do projeto", cole lá o **Prompt de abertura** (§2). Se ela ler o repositório,
> o `CLAUDE.md` e a skill `.claude/skills/pontes/` já carregam as regras.

## 1. Estado de partida (2026-10-02, tudo gerado por código, sem dado digitado à mão)

- **Corpus:** 16.509 obras do Repositório do Ipea (15.075 com autoria; 9.521 entre 2010 e 2026),
  407 perfis de Pessoa, 184 perfis do diretório "Quem faz pesquisa no Ipea".
- **Membros atribuídos pela produção:** DIEST 132, DISET 129. Ativos: 65 e 56 (incluem
  servidores fora do diretório e bolsistas com produção recente; ver coluna *fonte*).
- **Achado estrutural:** só **45 obras mistas** DIEST+DISET contra **≈391 esperadas** se a
  diretoria fosse indiferente à coautoria (z ≈ −15). São **silos**, como no projeto-mãe
  (cibernética × regulação × PI): a convergência **não está latente; precisa ser construída**.
- **Hipergrafo vale a pena?** Sim, com moderação: 31% das obras têm ≥3 assinaturas; **27
  dos 45 pares cruzados só existem via obras com ≥4 autores** (laço de coletânea); no grafo-linha
  a ponte cai de 1 componente gigante (s=1) para 4 (s=2) e 1 de 16 obras (s=3) → quase não há
  **equipes recorrentes** que atravessem as diretorias.
- **Zonas de convergência mais fortes:** pandemia/saúde; investimento público e
  infraestrutura; regulação (agências, AIR, governança regulatória: zona com **zero** obras
  mistas, o vazio mais nítido); mercado de trabalho e indústria; Agenda 2030; raça e desigualdade.
- **Corretores:** Danilo Santa Cruz Coelho, Fabiano Pompermayer, Mauro Santos Silva, Bernardo
  Furtado, Erivelton Guedes (Dirur/sem atribuição), Alexandre Gomide.

Ver `RELATORIO.md` (tabelas completas) e `METODO.md` (ressalvas).

## 2. Prompt de abertura (colar no início do projeto)

```
Você está assumindo o projeto pontes-diest-diset (pasta spinoff/pontes-diest-diset do repo
freirelucas/cibernetica-regula-o-politica-industrial, branch claude/friendly-carson-41ska0).
Leia, nesta ordem: CLAUDE.md, METODO.md, RELATORIO.md, docs/ORIENTACAO_CLAUDE_SCIENCE.md.

Objetivo: mapear pontes epistêmicas entre DIEST e DISET do Ipea: autores ativos, produção
característica, zonas de convergência e colaborações potenciais (pares e EQUIPES), com
hipergrafos.

Regras: (1) só dado real, vindo de data/ ou de fonte pública verificável; nunca invente
autor, lotação ou obra; (2) toda atribuição de diretoria é inferida, então mostre a confiança;
(3) são servidores públicos: o produto é convite à colaboração, nunca avaliação individual;
(4) português, sem anglicismo; (5) antes de afirmar qualquer número, rode
`python src/run_all.py --from attribute` e leia data/results.json.

Trabalhe pela fila do §3, um item por vez, com hipótese, teste e critério de pronto. Ao
fim de cada item, atualize METODO.md (o que mudou e por quê) e regenere RELATORIO.md.
```

## 3. Fila de trabalho priorizada (com critério de pronto)

| # | Tarefa | Por quê | Pronto quando |
|---|---|---|---|
| 1 | **Validar a lista de membros** com as chefias de DIEST e DISET (exportar `people` de results.json em planilha; marcar certo/errado/mudou) e gravar `data/membership_overrides.json`, lido por attribute.py | A atribuição é o alicerce; o erro aqui contamina tudo e há circularidade parcial (METODO §5) | precisão medida (% correto) registrada; overrides aplicados; relatório regenerado |
| 2 | **Teste de sensibilidade**: MIN_SHARE ∈ {0,4; 0,5; 0,6}, HALF_LIFE ∈ {3, 4, 6}, janela ≥2010 vs ≥2018 | Silos não podem ser artefato do limiar | z do nulo e top-10 de pares estáveis (Jaccard ≥0,6) ou instabilidade documentada |
| 3 | **Nulo mais forte**: permutar rótulos *dentro de estratos* (tipo de obra × período) e um nulo de configuração de hipergrafo (preserva grau e tamanho de hiperaresta) | A permutação simples ignora que boletins são intra-diretoria por construção | z sob os dois nulos no relatório |
| 4 | **Camada OpenAlex** (`OPENALEX_API_KEY`, chave grátis): rodar `openalex_enrich.py`, revisar `openalex_review.json`, construir **H_ref** (acoplamento bibliográfico) | Ponte epistêmica *pura*: ler a mesma literatura sem coassinar | ≥80% dos ativos resolvidos sem ambiguidade; obras citadas pelos dois lados listadas |
| 5 | **Ligar ao projeto-mãe**: marcar como hiperarestas as 60 sementes de `../../src/minirun.py` e ver quem as cita na DIEST/DISET | Responde "quem já mobiliza cibernética/regulação/PI aqui dentro" | lista por eixo (Cyb/Reg/PI) × diretoria |
| 6 | **Semântica dos resumos** (opcional): embeddings dos resumos (sentence-transformers) para similaridade de perfil, comparando com o TF-IDF de vocabulário | Palavra-chave livre tem sinonímia | correlação de ranking dos pares (Spearman) relatada; só adota se mudar conclusões |
| 7 | **Predição de hiperarestas** validada no tempo: treinar com ≤2021, ver se as equipes sugeridas anteveem as obras mistas 2022–2026 | Dá credibilidade às sugestões de equipe | precisão@k vs. linha de base (pares aleatórios da mesma zona) |
| 8 | **Produto**: página (site estático ou artefato) com zonas, equipes e pares, sem ranking de pessoas | Uso pela gestão | revisado pelas chefias antes de circular |

## 4. Como avaliar a ideia de hipergrafos (decisão a tomar no item 3)

Mantenha o hipergrafo como objeto principal **se** (a) obras com ≥3 autores forem ≥25%
(hoje: 31%), (b) a maioria dos pares cruzados vier de obras grandes (hoje: 27/45) e (c) o
grafo-linha s mudar a leitura entre s=1 e s=2 (hoje: muda). As três valem; o hipergrafo
fica. Use o grafo de pares com peso de Newman só para comunicação. Bibliotecas: `xgi`
(já usada no projeto-mãe, `src/hypergraph_core.py`) dá centralidades espectrais de
hipergrafo e agrupamento nativo; troque o union-find das zonas por `xgi` só se o resultado
mudar.

## 5. Armadilhas já conhecidas

- O filtro `diretoria=` do portal do Ipea **não funciona**: não tente reconstruir a lista por ele.
- O portal responde em *deflate* mesmo pedindo gzip (`net.py` já trata).
- O Repositório é lento (~10–20 s por página); a colheita fria leva ~40 min. Use o cache e
  `harvest_repo.py` retomável; páginas cruas ficam fora do git.
- Sobrenomes com partícula ("De Negri") e sufixo ("Cardoso Jr.") já têm teste; ao mexer em
  `name_key`, rode `tests/test_core.py`.
- O pool grátis do OpenAlex sem chave costuma estar esgotado em IP de nuvem.
