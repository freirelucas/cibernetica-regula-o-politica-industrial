# Avaliação do plano de construção — 13/11/2026

## O que havia para avaliar

Nenhum executor tinha construído nada: a `main` seguia no commit da entrega do desenho, sem
branch nem sessão derivada. Avaliou-se então o que decide o resultado: **se um executor
consegue seguir o plano**. O método foi um piloto, com conferência independente.

## O piloto

Um agente executor, numa cópia isolada do repositório, recebeu as etapas 1 e 2 do plano
antigo, sem nenhuma ajuda além do que está no repositório.

| medida | resultado |
|---|---|
| etapas concluídas | 2 de 2 |
| tempo | cerca de 10 minutos e meio |
| suíte, conferida fora do piloto | 111 passam; só as etapas seguintes em espera |
| telas, conferidas a olho em celular e computador | corretas: barra nova nas quatro telas, menu de seções funcionando, triagem com a faixa de ações |
| mudanças | limpas e dentro do pedido; testes alterados só onde o plano mandava |

**O plano era executável.** Mas o executor precisou decidir sozinho em dez pontos, e acertou
por competência, não porque o plano garantisse.

## O que o plano antigo tinha de errado

1. **Ponto de partida vermelho numa cópia nova.** `data/author_network.json` fica fora do git;
   sem ele, cinco testes falham antes de qualquer mudança. O plano mandava parar nesse caso, e
   a saída estava em outro arquivo.
2. **Critério que não se podia conferir.** "As telas ficam iguais às de antes" não tinha
   ferramenta. O executor escreveu um comparador de imagens por conta própria.
3. **Sobras não previstas.** Regras de CSS e um elemento que perderam o sentido depois da
   troca (em três modelos) não estavam na lista do que apagar.
4. **Teste pulado parecia verde.** No ambiente do piloto, dez testes eram pulados por falta de
   ferramenta e a suíte dizia "passou". Nada no plano acusava isso.
5. **Caminho fixo em `/tmp`**, contra a regra do ambiente de execução.
6. **Etapas 5 a 7 pediam julgamento**: classificar 26 destaques, escrever a frase de cada ato,
   escolher o vocabulário. É decisão de desenho, não de execução.
7. **Um erro de conteúdo, do autor do plano.** A etapa 4 mandava trocar "Q ≈ 0,59" e "z ≈ 80"
   pelos valores do derivado versionado, e havia teste exigindo a troca. A `METODOLOGIA.md`
   explica que 0,59 vem da rede interna de 600 nós do funil, outra rede. Um executor obediente
   teria corrompido o texto.
8. **Tudo em fila.** Sete etapas em sequência, embora quatro delas mexam em arquivos disjuntos.
9. **Nenhuma trava de escopo.** Nada impedia o executor de mexer em arquivo de outra etapa ou
   de commitar `docs/` divergente.

## O que mudou

| problema | resposta no plano novo |
|---|---|
| partida vermelha | `scripts/preparar.py`: confere bibliotecas, navegador e rede de coautoria; termina em AMBIENTE PRONTO |
| critério sem ferramenta, teste pulado, escopo | `scripts/aceite.py`: um comando, sete conferências, veredito APROVADA ou REPROVADA; reprova teste pulado sem motivo e arquivo fora da lista |
| sobras e ambiguidades | uma ordem por arquivo, com lista fechada de arquivos e trocas literais; as âncoras de cada troca foram conferidas contra os arquivos (81 trechos) |
| julgamento na mão do executor | decisões tomadas e escritas: papel de cada um dos 26 destaques, texto das sete capas de ato, vocabulário único |
| erro do 0,59 | ordem e teste agora **protegem** os números do corpo do relatório |
| fila | uma ordem de encaixes (O0) deixa quatro ordens rodarem ao mesmo tempo, sem tocar o mesmo arquivo |

## A prova do formato novo

A ordem O0 foi dada ao mesmo executor, no formato novo. Resultado: **aprovada na primeira
execução, nenhuma reprovação**, commit só com os cinco arquivos da ordem, `docs/` sem
mudança. Ele apontou quatro imprecisões na ordem e dois defeitos nas ferramentas; os dois
defeitos foram corrigidos.

## Onde ainda há risco

- **E1 e T1 são as mais longas** (dezenas de trocas em arquivos com linhas extensas). Se uma
  troca literal não bater, a ordem manda parar e relatar.
- **R2 depende de olho**: o alinhamento das capas de ato só se confere em captura.
- **O veredito não vê beleza.** O aceite garante estrutura, números e toque; não garante que
  ficou bom. Convém uma conferência a olho por alguém com critério na I1 e na F1.
- **A prosa da seção 10·6** tem muito termo em inglês que a varredura automática não pega
  ("caveats", "fetch", "top-K", "score"). Não é do redesenho; é revisão de texto.
