# Ciência da Ciência — Cibernética, Regulação e Política Industrial
## IPEA / DIEST-COGIT · Pacote de reprodutibilidade

Mapeamento cienciométrico da estrutura intelectual na interseção entre **cibernética
organizacional**, **instrumentos de governo / regulação** e **política industrial**.
O entregável canônico é o **site** em `docs/` (publicável no GitHub Pages),
construído a partir de uma fonte única de dados, `data/scisci_results.json`.

**▶ Rodar o funil completo (OpenAlex → dados → site) em 1 clique:**
[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/freirelucas/cibernetica-regula-o-politica-industrial/blob/main/colab/scisci_cibernetica_regulacao_PI_v2.ipynb)
— execute as células em ordem; ao final, a **Célula 13** regenera `docs/` com tudo
(relatório, explorador, triagem e exportações Rayyan). O notebook produz
`data/scisci_results.json` + `data/network.json` (a "fonte" que o site consome aqui).

---

## Objetivo

Mapear, com rigor cienciométrico e **apenas dados reais** (OpenAlex, verificados — sem
id inventado ou não-resolvível), a estrutura intelectual na interseção entre **cibernética
organizacional**, **instrumentos de governo / regulação** e **política industrial**, e
converter esse mapa em instrumento de pesquisa e de política. Três frentes:

1. **Diagnóstico honesto da (não-)convergência.** Testar, contra um modelo nulo, se as três
   tradições dialogam na estrutura de citação. O achado central: **são silos** (modularidade
   muito acima do acaso; nenhuma obra é conector significativo) — a convergência **não está
   latente, precisa ser construída**.
2. **Triagem sistemática para a equipe.** Entregar aos três pesquisadores uma síntese pronta
   para o Rayyan — recortes por eixo, cruzamento Brasil × global e curadoria por tamanho —,
   com decisões de inclusão/exclusão reprodutíveis.
3. **Agenda concreta.** Sobre o terreno comum que a análise revelou (teoria evolucionária e de
   capacidades da firma), formular uma **política industrial adaptativa de inspiração
   cibernética**: retroalimentação e capacidade estatal, composição de instrumentos (Hood) e
   missões (Mazzucato/Rodrik).

**Critérios de pronto:** funil reprodutível em um clique (Colab) sobre corpus real; site
`docs/` camera-ready (relatório + explorador + triagem); zero dado inventado ou não-resolvível;
suíte de testes verde; prosa sem anglicismo.

---

## Conteúdo do repositório

```
.
├── README.md
├── requirements.txt                  ← dependências do funil (Colab/local)
├── colab/
│   └── scisci_cibernetica_regulacao_PI_v2.ipynb   ← funil completo (OpenAlex → JSON)
├── src/
│   ├── build_site.py                 ← gera o site docs/ a partir do JSON (fonte única)
│   ├── site_template.html            ← modelo do site (prosa + gráficos + downloads)
│   ├── report_from_json.py           ← reconstrói os consts de gráfico a partir do JSON
│   ├── report_template.py            ← injeção do modelo (sem dependências)
│   └── enrich_openalex.py            ← enriquecimento pontual via OpenAlex (uso único)
├── docs/                             ← SITE (GitHub Pages)
│   ├── index.html
│   ├── vendor/                       ← Chart.js, d3 + fontes (sem CDN)
│   ├── dados/                        ← 8 CSV do funil (PT) + scisci_results.json + DICIONARIO
│   └── material-brasil/              ← revisão da literatura nacional (Faganello) + dados/mapas
├── data/
│   └── scisci_results.json           ← resultados consolidados (execução maio 2026)
├── tests/                            ← suite pytest (build, dados, anglicismos, integridade)
└── .claude/skills/run-scisci-ipea/   ← skill: build, serve e dirige o site headless
```

---

## O site (`docs/`)

Gerar o site a partir dos resultados consolidados (apenas biblioteca padrão, segundos):

```bash
python src/build_site.py
```

Servir localmente e abrir no navegador:

```bash
python3 -m http.server -d docs 8000   # http://127.0.0.1:8000/  · Ctrl-C para parar
```

Construir + servir + dirigir headless + screenshot (verifica gráficos e seções):

```bash
python .claude/skills/run-scisci-ipea/driver.py --build --shot /tmp/site.png
```

**Publicar:** no GitHub, *Settings → Pages → Source: branch + pasta `/docs`*.

---

## Reproduzir o estudo (funil completo)

### No Google Colab (recomendado)

1. Suba o notebook `colab/scisci_cibernetica_regulacao_PI_v2.ipynb`. Para gerar o site
   ao final (Célula 13), suba também os módulos de `src/` (`build_site.py`,
   `report_from_json.py`, `report_template.py`, `site_template.html`) e `docs/vendor/`.
2. Execute célula a célula em ordem.
3. A **Célula 3 (teste de sanidade)** deve passar antes de prosseguir.
4. Pontos de verificação são salvos em parquet — se a sessão cair, retoma de onde parou.
5. A **Célula 11b** exporta todos os CSV + ZIP; a **Célula 13** gera o site camera-ready.
6. Tempo total estimado: ~45 min.

### Localmente

```bash
pip install -r requirements.txt
jupyter notebook colab/scisci_cibernetica_regulacao_PI_v2.ipynb
```

---

## Obras-semente canônicas (IDs OpenAlex verificados em maio 2026)

| Eixo | ID | Referência |
|------|----|-----------|
| Cyb | W2048086870 | Beer, S. (1972). Brain of the Firm |
| Cyb | W1566478880 | Beer, S. (1979). The Heart of Enterprise |
| Cyb | W2154683088 | Beer, S. (1985). Diagnosing the System |
| Cyb | W2325487953 | Ashby, W.R. (1956). Introduction to Cybernetics |
| Cyb | W4244612406 | Espejo & Reyes (2011). Organizational Systems |
| Reg | W1601629960 | Hood, C. (1983). The Tools of Government |
| Reg | W2126563689 | Hood & Margetts (2007). Tools of Government Digital Age |
| Reg | W4386803846 | Margetts, H. (2024). Rediscovering Nodality |
| PI  | W3124879925 | Rodrik, D. (2004). Industrial Policy for the 21C |
| PI  | W1553746973 | Mazzucato, M. (2013). The Entrepreneurial State |

(Os códigos de eixo `Cyb`/`Reg`/`PolInd` são um vocabulário controlado interno.)

---

## Referências metodológicas

- **Bola de neve**: Wohlin (2014) *Guidelines for snowballing in systematic literature studies*
- **Força de associação**: Van Eck & Waltman (2009) *How to normalize cooccurrence data* · JASIST
- **Agrupamento de Leiden**: Traag, Waltman & van Eck (2019) *From Louvain to Leiden* · Scientific Reports
- **Centralidade de intermediação**: Brandes (2001) *A faster algorithm for betweenness centrality* · J. Math. Sociology
- **Detecção de rajadas**: Kleinberg (2003) *Bursty and Hierarchical Structure in Streams* · DMKD
- **Pontos pivotais**: Chen (2006) *CiteSpace II* · JASIST
- **Coeficiente de beleza**: Ke et al. (2015) *Defining and identifying sleeping beauties in science* · PNAS 112:7426–7431

---

## Exportáveis

Conjuntos canônicos em `docs/dados/` (CSV, UTF-8, cabeçalhos em PT), gerados de
`scisci_results.json` por `build_site.py`:

| Arquivo | Descrição |
|---------|-----------|
| `00_registro_execucao.csv` | Parâmetros e métricas da execução |
| `02_mais_citados.csv` | Vinte obras mais citadas (não-semente, ≥1 eixo) |
| `03_obras_ponte.csv` | Obras-ponte (≥ 2 eixos temáticos) |
| `05_rajadas_kleinberg.csv` | Rajadas de citação detectadas (Kleinberg 2003) |
| `06_belas_adormecidas.csv` | Coeficiente de beleza por obra (Ke et al. 2015) |
| `07_agrupamentos.csv` | Três obras mais citadas por agrupamento de Leiden |
| `08_obras_semente.csv` | Obras-semente com IDs OpenAlex |
| `09_serie_temporal.csv` | Produção anual por eixo temático |

O funil no Colab (Célula 11b) exporta um superconjunto, incluindo o corpus completo
e os pontos de verificação em parquet (`ckpt_*.parquet`).

---

## Testes

```bash
pip install pytest
pytest -q          # build, integridade do JSON, cabeçalhos dos CSV, varredura de anglicismo
```

O smoke headless do site fica em `.claude/skills/run-scisci-ipea/driver.py`.

---

## Limitações conhecidas

1. **OpenAlex / livros**: `referenced_works = []` para livros clássicos (Beer, Ashby,
   Hood 1983) — a bola de neve regressiva dessas sementes é nula na API.
2. **Cobertura de resumos**: ~95% para artigos pós-1996; menor para anteriores e livros.
3. **Campo `concepts` depreciado**: a API usa `topics` desde 2024; o funil usa ambos.
4. **Filtro vocabular**: introduz viés de confirmação — trabalhos pertinentes com
   vocabulário não coberto são excluídos.
5. **Obras-ponte são lexicais**: identificadas por coocorrência de vocabulário, não por
   citação; o total é um limite inferior.
6. **Autoria do OpenAlex**: alguns registros têm metadados imperfeitos; a autoria das
   obras-semente canônicas (Beer, Ashby, Mazzucato) foi normalizada, e as demais são
   reproduzidas como obtidas.

---

## Autoria

**Bruno Queiroz · Lucas Freire · Claucia Faganello** · IPEA / DIEST-COGIT · Brasília.
Material preliminar, sujeito a revisão. A seção *O caso brasileiro* (site) e os arquivos
em `docs/material-brasil/` resumem a revisão da literatura nacional conduzida por
Claucia Faganello (busca em SciSpace/Google Scholar, abril/2026; 220 trabalhos),
complementando o mapeamento bibliométrico global (OpenAlex) das demais seções.

Execução de referência (corpus OpenAlex): 2026-05-25 17:33.
