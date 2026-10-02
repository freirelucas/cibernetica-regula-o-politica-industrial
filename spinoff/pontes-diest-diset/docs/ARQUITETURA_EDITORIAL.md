# Arquitetura editorial — quatro camadas, sempre separadas

> Convenção de produto, não de sessão. Vale para o sítio, para cada ficha de tema, para
> o `RELATORIO.md` e para qualquer resposta em texto. Decidida em 2026-10-02.

O público são pesquisadores com doutorado e tomadores de decisão que querem **organizar
debates produtivos**. Esse público não precisa ser convencido; precisa saber de onde cada
afirmação vem para poder discordar dela com precisão. Daí a regra: as quatro camadas
abaixo nunca aparecem misturadas no mesmo parágrafo, no mesmo bloco ou na mesma tabela.

## 1. Factual

O que está registrado em fonte primária e é conferível por terceiros sem refazer conta
alguma. Obra, autor, ano, série, handle do Repositório, texto de lei, objetivo de plano
publicado. Cada item traz a referência ao lado, não em nota.

*Forma:* frase declarativa com fonte imediata. `Obra X, 2024, handle 11058/NNNNN.`
*Proibido:* adjetivo de magnitude ("muito", "pouco", "forte") — isso é camada 2 ou 3.

## 2. Estatística descritiva

Contagem, proporção, série temporal, composição. Tudo que sai de `data/` por operação
aritmética transparente e que outra pessoa reproduz com o mesmo arquivo.

*Forma:* número com denominador explícito e janela declarada. `201 obras desde 2010, das
quais 9 com assinante da DIEST.`
*Obrigatório:* o denominador. Percentual sem denominador é camada 3 disfarçada.
*Proibido:* teste, nulo, escore composto, agrupamento — isso é camada 3.

## 3. Enriquecimento analítico autônomo

O que exige escolha de método e, portanto, pode ser contestado no método e não só no dado:
modelo nulo e z, log-odds com prior, índice de equivalência, agrupamento por modularidade,
escore de equilíbrio, similaridade de perfil, predição. Também entra aqui toda
interpretação minha — "a porta de entrada do debate é por plataformas e trabalho" é
enriquecimento, não estatística.

*Forma:* afirmação + método + o que a derrubaria. Cada bloco desta camada declara a
sensibilidade conhecida: se o resultado muda com o limiar, o intervalo vai junto.
*Obrigatório:* marcação visível de que é interpretação, e não medida.

Exemplo da própria auditoria: o z de −15,2 das obras mistas é camada 3, não 2 — e carrega
que a regra de atribuição fabrica z mediano −3,24 em mundo sem silo (`data/audit_nulls.json`).

## 4. Rede com conexões verificáveis

A visualização não é ilustração das camadas anteriores: é um quarto objeto, com contrato
próprio. **Toda aresta tem de ser clicável até a evidência.** Aresta de coautoria leva à
obra que a produziu, pelo handle. Aresta de co-palavra leva à lista de obras em que os dois
termos co-ocorrem. Aresta entre tema e instrumento leva às obras que citam o instrumento.

*Obrigatório:* nenhuma aresta sem lastro navegável; nó sem evidência não entra no desenho.
*Obrigatório:* a legenda diz o que a aresta **é** (coassinatura, co-ocorrência, citação),
porque as três se parecem no desenho e significam coisas diferentes.
*Proibido:* aresta derivada de similaridade sem que o desenho a distinga visualmente das
arestas factuais — proximidade inferida e coassinatura observada não podem ter o mesmo traço.

## Por que esta separação, e não um texto corrido

Um debate improdutivo costuma travar porque os participantes discutem camadas diferentes
achando que discutem a mesma. Alguém contesta a interpretação; outro defende o dado. Com as
camadas separadas, a discordância fica endereçada: "discordo da camada 3, aceito a 2" é uma
frase que faz a conversa andar, e é exatamente a frase que este produto precisa permitir.

Consequência prática para quem escreve: se um parágrafo não couber inteiro numa camada, ele
tem de ser partido — e, quase sempre, isso revela que a afirmação estava fazendo duas coisas
ao mesmo tempo.
