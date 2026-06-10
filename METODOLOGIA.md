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
no acaso (**z ≈ 48**) e **0 obras conectoras** significativas — os eixos são silos reais,
não artefato de amostragem. *(O §00 cita Q≈0,59 da rede interna de 600 nós do funil, que
não é exportada; 0,51 é o número **reprodutível a partir do repositório** — mesma
conclusão.)* **Ressalva H1, agora quantificada:** **46,8% dos nós cocitados ficam sem
eixo** — referências que o vocabulário não classifica — e são deixados **fora** da
partição (não viram uma "comunidade", o que distorceria Q para baixo).
**Robusto à reamostragem:** derrubar 20% dos nós (bootstrap, B=300) mantém **Q = 0,51 ±
0,02** (IC95 [0,47, 0,55]) — os silos não são artefato de quais obras entraram na rede.

## 1. Crítica das heurísticas (o que cada uma esconde)

| # | Heurística | O que sugere | Como é construída | Onde a leitura ingênua falha | Tratamento |
|---|---|---|---|---|---|
| **H1** | Rótulo de eixo | "a obra pertence a 1 dos 3 eixos" | vocabulário sobre título+tópicos, **sem abstract** numa fração relevante; faltando, o eixo é herdado da **vizinhança** de cocitação | rótulo derivado da vizinhança torna a afirmação trans-eixo **parcialmente circular** | marcar nós **inferidos**; reportar *observado × inferido* |
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
  **higiene de integridade** (8 obras-fantasma 404 + 2 agregados de periódico removidos — o ex-"principal
  conector" W4285719527 era um registro vazio ligado a 95% dos nós) e **Q reconfirmado na rede limpa**
  (Q = 0,52, z = 48, bootstrap 0,51 ± 0,02 — os silos sobrevivem, ligeiramente mais limpos).
- **Pendente (backlog de rigor):** faixa semântica vs **população de referência** (resto do H4);
  **sensibilidade às sementes** (drop-20% ×5) — robustez da tese dos silos à seleção das sementes;
  *disclosure* dos inferidos **no ponto da afirmação** no relatório (observado × inferido por afirmação).

> Em uma frase: **o achado dos silos é forte e robusto; as afirmações sobre *pontes*
> (quem conecta os silos) são as que mais dependem de rótulos inferidos — leia-as como
> limite inferior, não como medida final.**
