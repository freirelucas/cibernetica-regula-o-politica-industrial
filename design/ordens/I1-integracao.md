# Ordem I1 — Integração da onda 1

**Objetivo.** Juntar o resultado das ordens N1, R1, E1 e T1 no tronco, reconstruir `docs/` uma
vez e conferir as cinco telas juntas. É a única ordem, antes do fechamento, que commita `docs/`.

**Arquivos que você pode mudar:** nenhum de código. Só `docs/`, por reconstrução.

## Passo 1 — juntar
- **Se as quatro ordens foram feitas em branches separadas:** estando no tronco, faça um
  `git merge --no-ff NOME_DA_BRANCH` para cada uma, nesta ordem: N1, R1, E1, T1. Cada ordem só
  mexeu nos próprios arquivos, então não deve haver conflito. **Se houver conflito, não
  resolva:** rode `git merge --abort`, pare e relate qual branch e qual arquivo.
- **Se as quatro foram feitas uma depois da outra na mesma branch:** não há o que juntar.

Confira: `python scripts/aceite.py --lista` tem de mostrar N1, R1, E1 e T1 como `feita`.

## Passo 2 — reconstruir e conferir
```bash
python scripts/preparar.py
python scripts/aceite.py I1 --iniciar
python src/build_site.py
python scripts/aceite.py I1             # VEREDITO: APROVADA
```

## Passo 3 — olhar
`python scripts/conferir_telas.py --capturas PASTA` e abra as capturas de celular e de
computador das cinco telas. Confira:
1. a barra tem cinco abas, iguais em todas as telas, com a atual sublinhada;
2. na entrada do relatório, a porta "A bibliografia da nota" abre a tela A nota;
3. na tela A nota, "Ver no espaço 3D" abre a cena com a obra selecionada.

O relatório ainda terá alvos de toque pequenos no corpo: são da ordem R2.

## Feito quando
O aceite aprovou e as três conferências a olho bateram. Commite **só** `docs/`
(`git add docs/`). Mensagem: `Ordem I1: integração da onda 1, docs/ com as cinco telas`.

## Se algo não bater
Não corrija código nesta ordem. Diga qual ordem (N1, R1, E1 ou T1) deixou o problema, com a
saída do aceite, e pare.
