# Ordem F1 — Fechamento

**Objetivo.** Documentar as cinco telas, tirar o CSS que ficou sem uso e commitar o `docs/`
final. Depois desta ordem, a construção do redesenho está terminada.

**Arquivos que você pode mudar:** `README.md`, `METODOLOGIA.md`, `CLAUDE.md`,
`.claude/skills/run-scisci-ipea/SKILL.md`, `.claude/skills/run-scisci-ipea/driver.py`,
`src/site_template.html` (só para apagar CSS morto) e `docs/` (por reconstrução).

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py F1 --iniciar
```

## Passo 1 — documentação
1. `README.md`, seção "O site": na lista "As quatro telas" passam a ser cinco; acrescente,
   depois da linha de `index.html`:
   `- `nota.html` — a bibliografia do texto para discussão situada no mapa das tradições: cada obra com a tradição, com quem é cocitada e o que ler ao lado.`
   Troque "quatro telas" por "cinco telas" onde aparecer. Na árvore de arquivos de `docs/`,
   acrescente a linha de `nota.html`.
2. `METODOLOGIA.md`, no fim do §6, acrescente o parágrafo:
   `**Tela A nota.** `docs/nota.html` lista a bibliografia do texto para discussão com a posição de cada obra neste mapa. "Leia ao lado" traz as obras mais cocitadas com ela: o número é quantos trabalhos do corpus citam as duas. Registros duplicados da mesma obra são somados (`src/nota.py`).`
3. `.claude/skills/run-scisci-ipea/SKILL.md`: "four pages" vira "five pages"; acrescente a linha de `docs/nota.html` na lista, logo depois da linha de `docs/espaco.html`; no bloco de saída de exemplo, acrescente a linha `[nota]` copiada da saída real do driver.
4. `driver.py`: no docstring, a linha de uso que diz "verifica as 4" passa a "verifica as 5", e a lista de páginas ganha a nota; o `description=` do `argparse` (linha 138) passa a dizer "(index + nota + explorador + triagem + espaço 3D)".
5. `CLAUDE.md`: o `python -m pytest -q` da seção "Comandos" já está feito (commit 2321def): não o refaça. A seção "Tarefa em curso" vira:
   `**Redesenho construído.** As ordens de design/ordens/ estão todas feitas (python scripts/aceite.py --lista). Mudança nova de desenho começa por design/README.md.`

## Passo 2 — CSS morto do relatório
Em `src/site_template.html`, apague as regras cujos seletores não existem mais na marcação.
Para cada seletor da lista, confirme antes com uma busca que a classe **não aparece** fora do
`<style>`; se aparecer, **deixe a regra**:
`.masthead`, `.kicker`, `.subtitle`, `.authorline`, `.byline`, `.startmap`, `.starttools`, `.preliminar`,
e todas as regras cujo seletor é a classe `.hero3d` ou `.hero3d-leg` (inclusive `.hero3d.sem-cena`: nenhum elemento tem
essa classe; o estado `sem-cena` agora fica em `.entrada-cena`, coberto pela regra `.entrada-cena.sem-cena canvas` da R1).
`.startbox` já saiu com a caixa na R1: não há o que apagar.
Dentro de `@media print`, tire esses nomes das listas de seletores, sem apagar a regra inteira.

## Passo 3 — reconstruir e conferir tudo
```bash
python src/build_site.py
python scripts/aceite.py F1             # VEREDITO: APROVADA (as cinco telas limpas)
python scripts/aceite.py --lista        # todas as ordens como "feita"
```
A olho: capturas de celular e computador das cinco telas, uma última vez.

## Feito quando
O aceite aprovou. Commite os arquivos que ele listar, **com** `docs/`. Mensagem:
`Ordem F1: fechamento do redesenho`.

## Fica para decisão de quem responde pelo estudo (não é desta ordem)
Impressão do relatório em PDF; o diagrama do Modelo de Sistema Viável; a troca do "Q ≈ 0,59"
do resumo pelo valor reprodutível; desempate da inferência; registros duplicados na rede;
nomes e ordem dos autores.
