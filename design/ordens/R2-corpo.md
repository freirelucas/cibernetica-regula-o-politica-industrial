# Ordem R2 — Relatório: o corpo

**Objetivo.** Aplicar ao corpo do relatório as capas de ato, o tratamento de aparato e os
papéis dos destaques, e levar todos os alvos de toque a 44 px. **Não se reescreve prosa e não
se mexe em número.** Peças: `design/prototipos/componentes.html`, seções "Ato, argumento e
aparato" e "Destaques".

**Arquivo que você pode mudar:** `src/site_template.html`. Só ele. `docs/` não entra no commit.

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py R2 --iniciar
```

## Passo 1 — as sete capas de ato
Cada linha `<details ... class="act"><summary>...</summary>` vira a linha da tabela. Mantenha
o `open` onde ele existe hoje. Os marcadores `{{...}}` e `AUTHORNET_*` ficam como estão escritos.

| ato | nova linha |
|---|---|
| Ato 1 | `<details open class="act sd-ato"><summary><span class="sd-ato-n">Ato 1</span><span class="sd-ato-t">Como medimos</span><span class="sd-ato-r">Teoria, método e funil. {{corpus.n}} trabalhos, a partir de {{corpus.sementes}} obras-semente.</span></summary>` |
| Ato 2 | `<details open class="act sd-ato"><summary><span class="sd-ato-n">Ato 2</span><span class="sd-ato-t">A estrutura do campo: os silos</span><span class="sd-ato-r">No núcleo de {{num.rede.n}} obras, {{num.silos.n_conectores}} de {{num.silos.n_nos}} testadas conectam as tradições.</span></summary>` |
| Ato 3 | `<details open class="act sd-ato"><summary><span class="sd-ato-n">Ato 3</span><span class="sd-ato-t">O que emerge do corpus</span><span class="sd-ato-r">Obras e autores. AUTHORNET_N_CROSS_STRICT de AUTHORNET_N_AUTHORS autores publicam nas três tradições.</span></summary>` |
| Ato 4 | `<details open class="act sd-ato"><summary><span class="sd-ato-n">Ato 4</span><span class="sd-ato-t">O caso brasileiro</span><span class="sd-ato-r">A literatura nacional e onde ela toca as três tradições.</span></summary>` |
| Ato 5 | `<details open class="act sd-ato"><summary><span class="sd-ato-n">Ato 5</span><span class="sd-ato-t">Do diagnóstico ao desenho</span><span class="sd-ato-r">{{num.agenda.n_agenda}} tríades a construir; {{num.agenda.alem_do_acaso}} de {{num.agenda.n_candidatas}} avaliadas superam o acaso.</span></summary>` |
| Aparato | `<details class="act sd-ato sd-aparato-ato"><summary><span class="sd-ato-n">Aparato</span><span class="sd-ato-t">Como verificar e reusar</span><span class="sd-ato-r">Leitura, sementes, reprodutibilidade e dados.</span></summary>` |
| Apêndices | `<details class="act sd-ato sd-aparato-ato"><summary><span class="sd-ato-n">Apêndices</span><span class="sd-ato-t">Limitações, glossário e referências</span><span class="sd-ato-r"></span></summary>` |

No CSS do modelo, **apague** estas cinco regras (elas brigam com as do sistema) e mantenha
`details.act{margin:0}`:
`details.act>summary{...}`, `details.act>summary::-webkit-details-marker{...}`,
`details.act>summary::after{...}`, `details.act:not([open])>summary::after{...}`,
`details.act>summary .act-n{...}`.

Acrescente no mesmo `<style>`:
```css
details.act.sd-ato>summary{max-width:960px;margin:0 auto;padding-left:2rem;padding-right:2rem}
@media(max-width:640px){details.act.sd-ato>summary{padding-left:1.25rem;padding-right:1.25rem}}
details.sd-aparato-ato{background:var(--sd-superficie)}
details.sd-aparato-ato .prose{font-size:.92rem}
```
(São a largura e o recuo da regra `.container` do modelo: a capa alinha com o texto das seções.)

## Passo 2 — os destaques ganham papel
Cada `class="callout"` ganha `sd-destaque` e, conforme a tabela, um papel. Identifique cada
destaque pelo começo do texto (ou pelo `id`). **Não mude o texto.**

| papel | classe final | destaques (começo do texto ou id) |
|---|---|---|
| achado | `callout sd-destaque sd-achado` | "Pontes epistêmicas"; "O silo é social"; "Ordem superior"; "Sondagem do 4º eixo"; "Os caminhos potenciais"; "Robustez em escala"; "Os silos cristalizaram-se"; "Pontes humanas estritas"; "Sondagens dirigidas"; "Achado."; "Top-5 obras BR"; "Tese."; `id="o-que-fica"` |
| limite | `callout sd-destaque sd-limite` | "Caveat do XGI"; "Caveats."; "Proveniência do rótulo"; "Nota." |
| como ler | `callout sd-destaque sd-como-ler` | "O número que importa"; "Como ler."; "Eco do Cybersyn."; `id="brasil-attr"`; `id="rayyan-callout"`; `id="como-citar"` |
| sem papel | `callout sd-destaque` | `id="temporal-detail"`; `id="net-stats"`; `id="pivotal-callout"` |

São 26 destaques: 13, 4, 6 e 3. Se a sua contagem não der 26, pare e relate.

A regra CSS `.callout{...}` do modelo vira (o sistema passa a dar fundo, borda e respiro):
```css
.callout{font-size:.9rem;text-align:justify;-webkit-hyphens:auto;hyphens:auto}
.callout.sd-destaque{max-width:none}
```

## Passo 3 — alvos de toque
```bash
python src/build_site.py
python scripts/conferir_telas.py docs/index.html
```
Para cada alvo que a conferência listar em celular ou tablet, acrescente à regra CSS daquele
elemento `min-height:44px` (com `display:inline-flex;align-items:center` se for link ou botão).
Rode de novo até `RESULTADO: OK`. Não mude a marcação por causa disso. Link no meio de frase
não é listado, e não é para engordar.

## O que NÃO é desta ordem
"Q ≈ 0,59" e "z ≈ 80" no texto: não troque (ver ordem R1). Ids de seção: não mude nenhum.
Tabelas e gráficos: não mexa.

## Feito quando
```bash
python scripts/aceite.py R2             # VEREDITO: APROVADA
```
A olho, em capturas de celular e computador: as capas de ato mostram número, título e resposta;
os dois últimos atos têm fundo mais escuro; os destaques têm a borda esquerda do seu papel.

Commite só o arquivo que o aceite listar. Mensagem: `Ordem R2: corpo do relatório`.

## Se algo não bater
Pare e relate o que tentou e a saída do aceite. Não reescreva texto para caber.
