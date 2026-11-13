# Ordem R1 — Relatório: a entrada

**Objetivo.** O primeiro ecrã do relatório passa a dizer o achado, mostrar a cena e oferecer
três portas. Como deve ficar: abra `design/prototipos/entrada.html` no navegador.

**Arquivo que você pode mudar:** `src/site_template.html`. Só ele. `docs/` não entra no commit.

Os marcadores `{{caminho}}` do protótipo já funcionam neste modelo (ordem O0): copie-os como
estão, sem trocar por número.

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py R1 --iniciar
```

## Passo 1 — o bloco do topo
Em `src/site_template.html`, apague **do** `<div class="preliminar" role="note">` **até** o
`</header>` que fecha `<header class="masthead">` (as duas pontas inclusive). No lugar, ponha:

```html
<div class="sd entrada-bloco">
  ...as três <section> que estão dentro de <main> em design/modelos/entrada.html...
</div>
```

Dentro do que você copiou, faça **só** estas trocas:

| de | para |
|---|---|
| `id="cena-elo" href="#"` | `id="hero3d-link" href="espaco.html"` |
| `<canvas id="cena" aria-hidden="true">` | `<canvas id="hero3d" aria-hidden="true">` |
| `<span>As {{num.rede.n}} obras do núcleo` | `<span><span id="hero3d-n">As {{num.rede.n}} obras</span> do núcleo` |
| na porta "O achado: três silos", `href="#"` | `href="#pontes"` |
| na porta "A agenda: onde construir", `href="#"` | `href="#discussao"` |
| em "Ferramentas", os três `href="#"`, na ordem | `espaco.html`, `explorador.html`, `triagem.html` |

E, dentro de `<details class="sd-estado">`, logo depois do `</p>`, acrescente
`<p><span id="gen-date"></span></p>` (o script do relatório escreve ali a data da execução).

Os ids `hero3d-link`, `hero3d`, `hero3d-n` e `gen-date` têm de existir uma vez cada: o script
que já está no modelo depende deles. **Não mexa no script.**

## Passo 2 — sai o "Comece por aqui"
Apague o bloco inteiro `<aside class="startbox" aria-label="Comece por aqui">` ... `</aside>`.
A `<section id="resumo" ...>` em volta e o que vem depois ficam como estão.

## Passo 3 — o CSS da entrada
No primeiro `<style>` do modelo, acrescente no fim as regras de leiaute do `<style>` de
`design/modelos/entrada.html` (as que começam por `.entrada`, mais as duas `@media`), **sem** a
regra `body{...}`. Acrescente também:

```css
.entrada-cena.sem-cena canvas{display:none}
```

Não apague CSS antigo nesta ordem (a limpeza é da ordem F1).

## O que NÃO é desta ordem
No resumo e no corpo há "Q ≈ 0,59" e "z ≈ 80" escritos por extenso. **Não troque.** São da rede
interna de 600 nós do funil (ver `METODOLOGIA.md`, "Verificação reprodutível"); os da entrada são
os da rede do repositório. Há teste que reprova se esses números sumirem.

## Feito quando
```bash
python scripts/aceite.py R1             # VEREDITO: APROVADA
```
E, a olho, em duas capturas
(`python scripts/conferir_telas.py docs/index.html --so-estrutura --capturas PASTA`):
1. computador: título e frase do achado à esquerda, cena à direita, três portas embaixo;
2. celular: a cena aparece depois do texto, as portas empilham, nada rola para o lado;
3. não há mais a faixa listrada "Material preliminar": no lugar, a linha "Versão de trabalho".

Commite só o arquivo que o aceite listar. Mensagem: `Ordem R1: entrada do relatório`.

## Se algo não bater
Não adapte o desenho nem mexa em outro arquivo. Pare e relate o que tentou e a mensagem de erro.
