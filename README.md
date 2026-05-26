# Science of Science — Cibernética, Regulação e Política Industrial
## IPEA / DIEST-COGIT · Pacote de reprodutibilidade

---

## Conteúdo do pacote

```
.
├── README.md                          ← este arquivo
├── requirements.txt                   ← dependências fixadas
├── colab/
│   ├── scisci_cibernetica_regulacao_PI_v2.ipynb   ← notebook principal
│   └── html_template.html             ← template do report (carregar junto)
├── src/
│   ├── report_builder.py              ← gera o HTML a partir dos objetos vivos do pipeline
│   ├── report_template.py             ← resolução/injeção do template (sem dependências)
│   └── report_from_json.py            ← regenera o report offline a partir do JSON
├── reports/
│   ├── scisci_ipea.html               ← report publicação IPEA (contém 8 CSVs embutidos)
│   ├── scisci_visual.html             ← versão visual exploratória
│   └── scisci_report.html             ← report do template, regenerável via report_from_json.py
└── data/
    └── scisci_results.json            ← resultados da última execução (maio 2026)
```

---

## Como reproduzir

### No Google Colab (recomendado)

1. Suba **os dois arquivos** juntos:
   - `colab/scisci_cibernetica_regulacao_PI_v2.ipynb`
   - `colab/html_template.html`
2. Execute célula a célula em ordem
3. **Célula 3 (SMOKE TEST)** deve passar antes de prosseguir
4. Checkpoints salvos automaticamente em parquet — se o runtime cair, retome de onde parou
5. **Célula 11b** gera ZIP com todos os CSVs + HTML report
6. Tempo estimado total: ~45 min

> **Nota:** a Célula 11 importa `report_builder`, que agora depende de
> `report_template.py`. No Colab, suba **os dois** módulos de `src/` juntos.

### Localmente

```bash
pip install -r requirements.txt
jupyter notebook colab/scisci_cibernetica_regulacao_PI_v2.ipynb
```

### Regenerar só o report (sem rodar o pipeline)

Os resultados da última execução já estão em `data/scisci_results.json`. Para
reconstruir o HTML report a partir deles — **sem** as ~45 min de coleta e sem
nenhuma dependência além da biblioteca padrão:

```bash
python src/report_from_json.py
# -> reports/scisci_report.html
```

Útil para iterar no `html_template.html` ou reproduzir o report em qualquer
máquina. Não sobrescreve `scisci_ipea.html` nem `scisci_visual.html`.

---

## Seeds canônicos (IDs OpenAlex verificados em maio 2026)

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

---

## Referências metodológicas

- **Bola de neve**: Wohlin (2014) *Guidelines for snowballing in systematic literature studies*
- **Association strength**: Van Eck & Waltman (2009) *How to normalize cooccurrence data* · JASIST
- **Leiden clustering**: Traag, Waltman & van Eck (2019) *From Louvain to Leiden* · Scientific Reports
- **Betweenness centrality**: Brandes (2001) *A faster algorithm for betweenness centrality* · Journal of Mathematical Sociology
- **Burst detection**: Kleinberg (2003) *Bursty and Hierarchical Structure in Streams* · DMKD
- **Pivotal points**: Chen (2006) *CiteSpace II* · JASIST
- **Beauty Coefficient**: Ke et al. (2015) *Defining and identifying sleeping beauties in science* · PNAS 112:7426–7431

---

## Outputs gerados pelo pipeline

| Arquivo | Descrição |
|---------|-----------|
| `00_pipeline_log.csv` | Parâmetros e métricas da execução |
| `02_top20_citados.csv` | Top 20 papers mais citados (não-seed, n_axes≥1) |
| `03_bridges_n_axes_gte2.csv` | Trading zones (≥ 2 eixos temáticos) |
| `05_kleinberg_bursts.csv` | Eventos de burst detectados (Kleinberg 2003) |
| `06_sleeping_beauties.csv` | Beauty Coefficient por paper (Ke et al. 2015) |
| `07_clusters_top3.csv` | Top-3 papers por cluster Leiden |
| `08_seeds.csv` | Seeds com IDs OpenAlex |
| `09_temporal.csv` | Produção anual por eixo temático |
| `ckpt_phase1.parquet` | Corpus após fase 1 (queries de texto) |
| `ckpt_phase2.parquet` | Corpus após forward snowball |
| `ckpt_phase3.parquet` | Corpus após backward snowball |
| `ckpt_enriched.parquet` | Corpus com referenced_works enriquecidos |
| `ckpt_analysis.parquet` | Nós co-citation com métricas de rede |
| `ckpt_metrics.parquet` | Métricas finais: betweenness, burst, beauty |

---

## Limitações conhecidas

1. **OpenAlex / livros**: `referenced_works = []` para livros clássicos (Beer, Ashby, Hood 1983) — backward snowball desses seeds é nulo na API
2. **Cobertura de abstracts**: ~95% para artigos pós-1996; menor para pré-1996 e livros
3. **Campo `concepts` depreciado**: a API usa `topics` desde 2024; o pipeline usa ambos com fallback
4. **Filtro vocabular**: introduz viés de confirmação — papers relevantes com vocabulário não coberto são excluídos
5. **n_bridges = 10 é limite inferior**: outros bridges podem existir com vocabulário não previsto

---

## Contato

Lucas Freire · IPEA / DIEST-COGIT · Brasília  
Pipeline gerado em: 2026-05-25 17:33
