# Ordem E1 — Explorador com as peças e o vocabulário do sistema

**Objetivo.** O painel do explorador passa a usar as peças do sistema e a mesma língua das
outras telas. **A cena d3 não muda** (os círculos continuam círculos). Peças: abra
`design/prototipos/componentes.html`.

**Arquivo que você pode mudar:** `src/explorador_template.html`. Só ele. `docs/` não entra no commit.

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py E1 --iniciar
```

## Trocas (cada linha é uma troca literal; "de" está no arquivo exatamente assim)

**1. Painel.** `<aside class="panel">` vira `<aside class="panel sd">`.

**2. Rótulos de bloco, sem caixa-alta.** A regra CSS `.ctl>label.h{...}` inteira vira:
```css
.ctl>label.h{display:block;font:500 var(--sd-t0)/1.3 var(--sd-sem-serifa);color:var(--sd-apagado);margin-bottom:.5rem}
```

**3. Texto de abertura.** O parágrafo `<p class="lead">...</p>` inteiro vira:
```html
    <p class="lead">Rede de cocitação ampliada das quatro tradições, com __N_OBRAS__ obras (inclui a sondagem da economia da complexidade). Cada círculo é uma obra, maior quanto mais citada; cada linha é uma cocitação, mais grossa quanto mais frequente e vermelha quando liga tradições diferentes. Obras sem tradição atribuída pelo vocabulário aparecem na tradição inferida pela vizinhança, em tom mais leve. O botão abaixo mostra só as obras da agenda, as que entram em alguma tríade a construir. <a class="sd-botao sd-discreto" href="index.html#pontes">Como a rede foi construída</a></p>
```

**4. Botão da agenda.** A linha do `<button class="btn ponte-btn" id="pontesBtn" ...>` vira:
```html
      <button type="button" class="sd-botao" id="pontesBtn" aria-pressed="false" style="width:100%">Só as obras da agenda</button>
```
O conteúdo do parágrafo `id="pontesHint"` vira: `Mostra só as obras que entram em alguma tríade a construir e as cocitações entre elas.`
No script, dentro de `syncPontes`:
- `pBtn.textContent = pontesOnly ? '↩ Ver rede inteira' : ('◆ Só as pontes ('+nAgenda+' alvos)');`
  vira `pBtn.textContent = pontesOnly ? 'Ver a rede inteira' : ('Só as obras da agenda (' + nAgenda + ')');`
- as duas linhas `pBtn.style.background = ...` e `pBtn.style.color = ...` viram uma:
  `pBtn.classList.toggle('sd-primario', pontesOnly);`
Nos comentários do script, onde estiver escrito `Só as pontes` ou `só pontes`, escreva `só a agenda`.

**5. Opção do destaque.** `alvos de agenda (pontes a construir)` vira `obras da agenda (tríades a construir)` nas **duas** ocorrências (a opção do menu e um comentário do script).
No `<select id="destaque" style="...">`, apague o atributo `style` e ponha `class="sd-campo"`.

**6. Filtros de tradição com o sólido.** Antes da linha `const row=document.createElement('label'); row.className='axis-row';`, acrescente:
```js
    const SOL = {Cyb:['cib','icosa'], Reg:['reg','cubo'], PolInd:['pi','tetra'], Cplx:['cplx','octa']};
    const glifo = SOL[a]
      ? `<svg class="sd-sol sd-eixo-${SOL[a][0]} sd-cheio" aria-hidden="true"><use href="#sd-sol-${SOL[a][1]}"/></svg>`
      : `<svg class="sd-sol" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="8" fill="none" stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 2.5"/></svg>`;
```
Nessa mesma linha, `row.className='axis-row'` vira `row.className='sd-chip'`. E a linha seguinte
(`row.innerHTML=...`) vira:
```js
    row.innerHTML=`<input type="checkbox" checked data-ax="${a}">${glifo}${AXN[a]} <span class="sd-num">${counts[a]||0}</span>`;
```
O elemento que recebe essas linhas (o pai de `row`) ganha no CSS `display:flex;flex-wrap:wrap;gap:6px`.

**7. Busca, limiar e opções.**
- `<input type="text" id="search" ...>` ganha `class="sd-campo"`.
- No CSS, acrescente: `#wmin{width:100%;min-height:44px}` e
  `.toggle{min-height:44px}` e `.toggle input{width:20px;height:20px;flex:none}`.

**8. Botões.** `class="btn"` vira `class="sd-botao"` em `id="reset"`, `id="expSub"` e `id="detLink"`.
Em `detLink`, o texto `Abrir no OpenAlex &nearr;` vira `Abrir no OpenAlex (nova aba)`.
Apague as regras CSS `.btn{...}` e `.btn:hover{...}`.

**9. Do explorador para a cena 3D.** Na linha do `detLink`, logo depois dele e dentro do mesmo
`<div class="row">`, acrescente:
```html
<a class="sd-botao" id="det3d">Ver no espaço 3D</a>
```
No script, logo depois da linha que contém `link.href='https://openalex.org/'+d.id;`, acrescente:
```js
    const l3=document.getElementById('det3d');
    if (/^W\d+$/.test(d.id)){ l3.style.display=''; l3.href='espaco.html#lente=silos&obra='+d.id; } else { l3.style.display='none'; }
```
No CSS, `#detail .row` ganha `flex-wrap:wrap`.

**10. Fechar o painel.** `<span class="close" id="detClose" title="fechar">&times;</span>` vira
`<button type="button" class="close" id="detClose" aria-label="Fechar">&times;</button>`, e a regra
`#detail .close{...}` vira:
```css
#detail .close{position:absolute;top:0;right:0;width:44px;height:44px;display:flex;align-items:center;justify-content:center;background:none;border:0;cursor:pointer;color:var(--muted);font-size:18px;line-height:1}
```

**11. Painel de detalhe.** A linha do painel que começa por `+ (d.agenda ? ` contém
`★ <strong>alvo de agenda</strong> — ponte a construir (alta integração, ΔKf)`. Troque o trecho do texto por
`★ <strong>obra da agenda</strong> — tríade a construir (alta integração, ΔKf)`. Não mude o resto da linha.

## Feito quando
```bash
python scripts/aceite.py E1             # VEREDITO: APROVADA
```
O aceite confere a tela inteira em celular e tablet: se ele listar algum alvo menor que 44 px,
dê à regra CSS daquele elemento `min-height:44px` (com `display:inline-flex;align-items:center`
se for link) e rode de novo. Não mude a marcação por causa disso.

A olho, numa captura de computador e uma de celular: os filtros de tradição mostram sólido, nome
e contagem; a rede aparece; clicar numa obra abre o painel com os dois botões.

Commite só o arquivo que o aceite listar. Mensagem: `Ordem E1: explorador com as peças do sistema`.

## Se algo não bater
Se uma troca "de" não existir no arquivo exatamente como escrita, **não invente**: pare e relate
qual foi. Não mexa no desenho da rede nem em outro arquivo.
