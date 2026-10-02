# Validação da lista de membros (item 1 da fila)

> Para as chefias da DIEST e da DISET. Tempo estimado: 20–30 minutos para o bloco
> prioritário. **Não é avaliação de ninguém** — é conferência de lotação.

## Por que pedir isso

Nenhuma lista de lotação por diretoria foi obtida de forma confiável: o filtro
`diretoria=` do diretório "Quem faz pesquisa no Ipea" é ignorado pelo servidor e devolve a
lista inteira (`METODO.md §1`). A diretoria de cada pessoa é, por isso, **inferida pela
produção**: pelos sinais editoriais das obras que ela assina (série "Nota Técnica
Diest/Diset", boletins BAPI e Radar, editora/unidade responsável), com peso de recência de
meia-vida de 4 anos, contra as seis diretorias de pesquisa.

Isso cria uma circularidade parcial (`METODO.md §5`): as obras definem a diretoria das
pessoas e as pessoas definem quais obras são conjuntas. O achado central do estudo — só
**45** obras assinadas pelas duas diretorias contra **≈391** esperadas ao acaso
(`data/results.json` → `structural.mixed_hyperedges`, `structural.null_mean`) — depende
dessa atribuição. Enquanto a lista não for conferida por quem sabe, a precisão do método é
desconhecida e todo o resto herda essa incerteza.

## O que fazer

1. Abrir `data/membership_validation.csv` (separador `;`, codificação UTF-8).
2. Preencher **três colunas** por linha:

| coluna | o que pôr |
|---|---|
| `situacao` | `confirmado`, `corrigido`, `fora` ou `desconhecido` |
| `diretoria_correta` | só quando `situacao` = `corrigido`: `DIEST`, `DISET`, `DISOC`, `DIRUR`, `DIMAC` ou `DINTE` |
| `observacao` | livre; útil sobretudo para migrações ("saiu da Diset para a Diest em 2023") |

Sentido de cada situação:

- **confirmado** — a `diretoria_inferida` está certa.
- **corrigido** — a pessoa é de outra diretoria (preencher `diretoria_correta`).
- **fora** — não é membro de nenhuma diretoria de pesquisa: assinou obras do Ipea por
  outro vínculo (consultoria, bolsa de outra unidade, coautoria externa, já saiu).
- **desconhecido** — não há como dizer. **Não** conta como erro; fica pendente.

Linhas em branco continuam pendentes, sem prejuízo: o cálculo usa só o que foi decidido.

## Ordem de prioridade

A planilha já vem ordenada para que as primeiras linhas sejam as que mais afetam o
resultado. Se o tempo for curto, basta o primeiro bloco:

1. `grupo` = `atribuido` e `ativo` = `sim` — quem entra nas zonas de convergência, nos
   pares e nas equipes sugeridas.
2. `grupo` = `atribuido` e `ativo` = `não` — afeta a contagem de obras mistas da janela.
3. `grupo` = `sem_atribuicao` — pessoas com produção DIEST ou DISET que o método **não**
   conseguiu atribuir. Se alguma for membro, é uma ponte que está faltando no mapa. Aqui a
   pergunta é a inversa: qual é a diretoria (use `corrigido` + `diretoria_correta`).

As colunas `confianca_inferida`, `obras_rotuladas`, `peso_dominante` e `evidencia_pesos`
mostram a força da evidência: `moderada` com 2 obras rotuladas é um palpite; `explicita`
vem do cargo no perfil de Pessoa do repositório. Vale conferir primeiro as `moderada`.

Pessoas que **não aparecem na planilha** e deveriam: acrescentar uma linha com o nome, a
diretoria em `diretoria_correta` e `situacao` = `corrigido`. O casamento é feito pelo nome;
o `author_id` pode ficar em branco. Quem não tem nenhuma obra no Repositório do Ipea não
entra na análise de coautoria de todo modo — vale registrar na observação.

## O que o agente faz com as respostas

```bash
python src/membership.py --ingest data/membership_validation.csv   # planilha → overrides
python src/run_all.py --from attribute                             # reatribui e refaz tudo
```

A resposta das chefias passa a **vencer** a inferência: em `data/authors.json` a pessoa
recebe `confidence = "validada"` (ou `validada_fora`), e o relatório ganha, no §2, a
precisão medida por estrato de confiança. A inferência original fica guardada em
`inferred_diretoria` / `inferred_confidence`, para que se possa medir onde o método erra.

Critério de pronto do item 1 (`docs/ORIENTACAO_CLAUDE_SCIENCE.md §3`): precisão registrada,
overrides aplicados, relatório regenerado.
