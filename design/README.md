# Redesenho do sítio — o que foi decidido e onde está

Pedido: dar ao sítio um tratamento visual à altura da cena 3D, melhorar as jornadas e fazer
dele o material de apoio para explorar a bibliografia da nota (o texto para discussão *Do
organograma ao sistema viável*), como um produto só. O desenho fica aqui; a construção segue
`design/PLANO.md`.

## Como ver

Abra no navegador, direto do repositório:

| arquivo | o que mostra |
|---|---|
| `design/prototipos/entrada.html` | o primeiro ecrã do relatório: achado, cena, três portas, números |
| `design/prototipos/nota.html` | a tela nova: a bibliografia da nota situada no mapa das tradições |
| `design/prototipos/componentes.html` | todas as peças do sistema, com a regra de uso de cada uma |

Os protótipos têm números reais. Para regerá-los depois de mudar um modelo ou um dado:
`python design/ferramentas/gera_prototipos.py`. Para conferi-los em navegador:
`python scripts/conferir_telas.py design/prototipos/nota.html`.

## A ideia

O estudo mede posição: cada obra tem um lugar dado pela mistura da sua cocitação entre quatro
tradições. O desenho leva essa ideia para todas as telas, em seis regras:

1. **Posição e forma são dado.** Nada é enfeite.
2. **Cada tradição tem um sólido e uma cor, sempre juntos**: icosaedro para cibernética, cubo
   para regulação, tetraedro para política industrial, octaedro para complexidade, dodecaedro
   para a nota. São os mesmos sólidos da cena 3D, gerados da mesma geometria
   (`design/ferramentas/gera_glifos.js`). A leitura sobrevive à impressão em preto e branco.
3. **Rótulo observado é cheio; rótulo inferido é vazado.** Em qualquer tela.
4. **Número com denominador.** Zero e número pequeno vêm sempre com o total: "0 de 126".
5. **Argumento e aparato têm tratamentos diferentes.** O que defende a tese é lido em corpo
   maior; o que sustenta a verificação vai em corpo menor, sobre superfície.
6. **Monoespaçada é para número e código.** Rótulo de interface vai em frase curta, sem
   caixa-alta e sem ponto mediano separando termos.

## O que muda para quem usa

- **Uma barra, cinco telas**: Estudo, A nota, Espaço 3D, Explorador, Triagem. Cabem numa
  linha de 320 px para cima. No relatório, o menu de seções vira um botão que funciona em
  qualquer largura (hoje ele some no computador) e, no celular, flutua ao alcance do polegar.
- **A entrada diz o achado** em uma frase com números vivos e oferece três portas: a
  bibliografia da nota, o achado (os silos) e a agenda (onde construir pontes). O aviso de
  versão de trabalho deixa de ser uma faixa listrada e vira uma linha discreta, com o detalhe
  a um toque.
- **A nota** é a tela nova: cada obra citada no texto para discussão aparece com a sua
  tradição, com quem é cocitada e o que ler ao lado. Dado que já sai dela: 57 das 84 tríades
  a construir envolvem ao menos uma obra citada na nota.
- **Explorador e Triagem** passam a usar as mesmas peças (selos, botões, campos, cartões) e o
  mesmo vocabulário: hoje três telas chamam de "alvos" três contagens diferentes.

## O que foi preservado

Tipografia (Spectral, DM Sans, JetBrains Mono, só nos pesos já vendorizados), as cores das
tradições, o papel e a sobriedade. As cores de marca não mudam; ganharam versões mais escuras
só para texto, porque o laranja (4,1:1) e o verde-água (3,0:1) não passavam no contraste.

## O que ficou de fora, e por quê

- O diagrama do Modelo de Sistema Viável sobre o arranjo real e a camada de cor para funções
  institucionais, pedidos na encomenda de 18/09: dependem da versão final do texto para
  discussão, que ainda vai a seminário.
- Trocar os círculos do explorador 2D por formas: mexe no desenho d3 e no verificador.

## Arquivos

```
design/
├── README.md                este arquivo
├── PLANO.md                 a construção, em sete etapas com critério de "feito quando"
├── sistema.css              fichas de cor, tipo e espaço; componentes com prefixo sd-
├── solidos.svg              os cinco sólidos (gerado; não editar à mão)
├── modelos/*.html           fonte dos protótipos, com marcadores {{caminho.do.dado}}
├── prototipos/*.html        protótipos gerados, com números reais
└── ferramentas/
    ├── gera_glifos.js       sólidos a partir de src/espaco3d.js
    └── gera_prototipos.py   protótipos a partir dos modelos e dos derivados;
                             traz a referência de dados da tela A nota (dados_nota)
```

Critérios executáveis do desenho: `tests/test_redesenho.py`. Conferência em navegador:
`scripts/conferir_telas.py`.
