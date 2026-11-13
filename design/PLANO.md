# Plano de construção do redesenho — ordens de serviço

Este plano substitui o de sete etapas. O porquê está em `design/AVALIACAO.md`: um piloto com um
executor mostrou o que funcionava e o que deixava decisão na mão de quem não devia decidir.

## O princípio

**Quem executa não decide.** Cada ordem diz o que mudar, em quais arquivos e com quais trocas
literais. Um comando dá o veredito. Se a ordem não bater com o que está no arquivo, o executor
para e relata; não improvisa.

## O quadro

```bash
python scripts/aceite.py --lista
```

| ordem | onda | o que faz | arquivo da ordem |
|---|---|---|---|
| B1 | base | sistema de desenho em todas as telas | feita |
| B2 | base | uma barra, igual em todas as telas | feita |
| O0 | 0 | marcadores `{{caminho}}` em todos os modelos; gancho da tela A nota | feita |
| **N1** | **1** | tela nova: A nota | `design/ordens/N1-nota.md` |
| **R1** | **1** | relatório: a entrada | `design/ordens/R1-entrada.md` |
| **E1** | **1** | explorador com as peças do sistema | `design/ordens/E1-explorador.md` |
| **T1** | **1** | triagem com as peças do sistema | `design/ordens/T1-triagem.md` |
| I1 | integração | junta a onda 1 e reconstrói `docs/` | `design/ordens/I1-integracao.md` |
| R2 | 2 | relatório: o corpo | `design/ordens/R2-corpo.md` |
| F1 | 3 | fechamento | `design/ordens/F1-fechamento.md` |

As quatro ordens da onda 1 **podem rodar ao mesmo tempo**: cada uma mexe em arquivos que
nenhuma outra toca, e nenhuma commita `docs/`.

## Como se executa uma ordem (vale para todas)

```bash
python scripts/preparar.py                 # 1. tem de terminar em AMBIENTE PRONTO
python scripts/aceite.py ORDEM --iniciar   # 2. confere dependências e marca a partida
#                                            3. faça exatamente o que o arquivo da ordem manda
python scripts/aceite.py ORDEM             # 4. tem de terminar em VEREDITO: APROVADA
#                                            5. commite só os arquivos que o aceite listar
```

O aceite confere sete coisas: só mudaram os arquivos da ordem; o sítio constrói; `docs/dados/`
é o canônico; a suíte passa **sem teste pulado por falta de ferramenta**; o driver dá
`STATUS: OK`; nenhuma tela tem erro, rolagem lateral, aba cortada ou número vazio; e as telas
que a ordem fecha saem limpas da conferência completa, com alvos de toque de 44 px.

## Como despachar

**Um executor por ordem.** Três jeitos, do mais rápido ao mais simples:

1. **Orquestrado numa sessão.** Quem orquestra abre um agente por ordem da onda 1, cada um
   numa cópia isolada do repositório (worktree), confere o relatório e o veredito de cada um,
   e executa a I1. Foi assim que B1, B2 e O0 foram feitas.
2. **Sessões separadas.** Cada sessão recebe: *"Execute a ordem N1 de design/ordens/N1-nota.md.
   Leia CLAUDE.md antes."* Cada uma trabalha na sua branch, a partir do tronco. Quem integra
   segue a I1.
3. **Um executor só.** Faz N1, R1, E1 e T1 em sequência na mesma branch e depois a I1 (sem
   nada para juntar).

Depois da I1: R2, e então F1.

## O que o executor relata ao terminar

1. A saída inteira do último `python scripts/aceite.py ORDEM` e o hash do commit.
2. Onde a ordem não bastou: cada ponto ambíguo, incompleto ou errado, e o que decidiu.
3. Quantas vezes o aceite reprovou antes de aprovar, e por quê.

Esse relatório volta para quem escreveu a ordem: é assim que as ordens melhoram.

## Regras (as de `CLAUDE.md`, mais estas)

- Lista de arquivos é fechada. Precisou mexer em outro? Pare e relate.
- Não edite `scripts/aceite.py`, `scripts/preparar.py`, `design/ordens/quadro.json` nem
  `tests/test_redesenho.py` para passar.
- Não reescreva prosa nem troque número do relatório. Em especial, "Q ≈ 0,59" e "z ≈ 80" são
  da rede interna do funil e ficam como estão.
- Se o aceite reprovar duas vezes pelo mesmo motivo, pare e relate.

## Depois da construção: o que pede decisão de quem responde pelo estudo

O diagrama do Modelo de Sistema Viável sobre o arranjo real; trocar o "Q ≈ 0,59" do resumo
pelo valor reprodutível do repositório (0,515); o desempate da inferência de tradição; os
registros duplicados na rede; nomes e ordem dos autores; a impressão em PDF.
