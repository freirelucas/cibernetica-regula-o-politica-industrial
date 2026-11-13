# Ordem T1 — Triagem com as peças e o vocabulário do sistema

**Objetivo.** Os cartões da triagem passam a mostrar a tradição por selo (sólido e nome), as
medidas com nome e vírgula decimal, e alvos de toque de 44 px. O comportamento não muda: os
cartões continuam com a classe `card` e os botões com os mesmos `id`. Peças: abra
`design/prototipos/componentes.html`, seção "Cartão de triagem".

**Arquivo que você pode mudar:** `src/triagem_template.html`. Só ele. `docs/` não entra no commit.

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py T1 --iniciar
```

## Trocas no CSS (cada regra inteira vira a que está escrita)

```css
.btn{display:inline-flex;align-items:center;justify-content:center;min-height:44px;padding:0 .9rem;border:1px solid var(--border-s);border-radius:6px;background:var(--paper);color:var(--ink);font:500 .875rem/1.2 var(--sans);cursor:pointer;white-space:nowrap}
.btn:hover{border-color:var(--ink)}
.btn.primary{background:var(--ink);border-color:var(--ink);color:var(--paper)}.btn.primary:hover{background:var(--cyb);border-color:var(--cyb)}
.chip{display:inline-flex;align-items:center;min-height:44px;padding:0 .8rem;border:1px solid var(--border-s);border-radius:22px;background:var(--paper);font:500 .875rem/1 var(--sans);cursor:pointer;user-select:none}
.thpanel h2{font:500 .875rem/1.3 var(--sans);color:var(--cyb);margin:0 0 .6rem}
```
(São as regras `.btn`, `.btn:hover`, `.btn.primary`, `.chip` e `.thpanel h2`. As demais, como
`.chip.on` e `.btn.cur-on`, ficam.) Na regra `.triagem-acoes`, `font-family:var(--mono);font-size:11px`
vira `font-family:var(--sans);font-size:.875rem`. Acrescente:
```css
.tags{display:flex;flex-wrap:wrap;align-items:center;gap:.2rem .9rem}
```

## Trocas no script

**1. Selo de tradição.** Logo depois da linha `const AXC = {...};`, acrescente:
```js
  const SOLT = {'Cibernética':['cib','icosa'], 'Regulação econômica':['reg','cubo'], 'Política industrial':['pi','tetra'], 'Economia da complexidade':['cplx','octa']};
  function selo(a){ const s=SOLT[a]; return s ? `<span class="sd-selo sd-eixo-${s[0]}"><svg class="sd-sol sd-eixo-${s[0]} sd-cheio" aria-hidden="true"><use href="#sd-sol-${s[1]}"/></svg>${esc(a)}</span>` : `<span class="sd-selo">${esc(a)}</span>`; }
  function fmtBR(v, casas){ return (+v || 0).toFixed(casas).replace('.', ','); }
```
Nos dois lugares em que as tradições viram etiqueta colorida:
- `w.axes.map(a=>`<span class="tag" style="background:${AXC[a]||'#9a948c'}">${esc(a)}</span>`).join('')` vira `w.axes.map(selo).join(' ')`;
- `(w.axes||[]).map(a=>`<span class="tag" style="background:${AXC[a]||'#9a948c'}">${esc(a)}</span>`).join(' ')` vira `(w.axes||[]).map(selo).join(' ')`.

**2. Vírgula decimal.**
- em `function sol`: `(+v).toFixed(2)` vira `fmtBR(v,2)`;
- `(+TH.prioridade).toFixed(2)` vira `fmtBR(TH.prioridade,2)`; `(+TH.ho_bc).toFixed(3)` vira `fmtBR(TH.ho_bc,3)`;
- `(100*x/n).toFixed(1)+'%'` vira `fmtBR(100*x/n,1)+'%'`.
Não mexa nos `toFixed(4)` e `toFixed(5)`: são valores de máquina (limiares e passo do controle).

**3. Medidas do cartão de decidir.** A constante `sig` inteira (do `` const sig = `<div class="sig">` `` até o `` + `</div>`; ``) vira:
```js
    const sig = `<dl class="sd-medidas">`
      + `<div><dt>Prioridade</dt><dd>${fmtBR(w.prioridade,2)}</dd></div>`
      + `<div><dt>Intermediação de ordem superior</dt><dd>${fmtBR(w.ho_bc,3)}</dd></div>`
      + `<div><dt>Integração (ΔKf)</dt><dd>${sol(w,'estrutural')}</dd></div>`
      + `<div><dt>Latente</dt><dd>${sol(w,'latente')}</dd></div>`
      + `<div><dt>Semântico</dt><dd>${sol(w,'semantico')}</dd></div>`
      + `</dl>`;
```

**4. Cartão de "o que o algoritmo achou".** As três linhas do `return` dentro de `fruit.map` viram:
```js
      return `<div class="afcard sd-cartao"><h4 class="sd-cartao-t">${esc(w.title)}</h4><div class="tags">${tags}</div>`
        + `<div class="why">Por que entrou: ${role?`papel <b>${esc(role)}</b>; `:''}integra uma <b>tríade a construir</b>, de alta integração real (ΔKf) e plausível na faixa semântica.</div>`
        + `<dl class="sd-medidas"><div><dt>Integração (ΔKf)</dt><dd>${sol(w,'estrutural')}</dd></div><div><dt>Latente</dt><dd>${sol(w,'latente')}</dd></div><div><dt>Semântico</dt><dd>${sol(w,'semantico')}</dd></div><div><dt>Prioridade</dt><dd>${fmtBR(w.prioridade,2)}</dd></div></dl></div>`;
```

**5. Uma língua só.** Em todo o arquivo (marcação, `title` e script), a ideia "alvo de agenda"
muda de nome. Trocas literais:

| de | para |
|---|---|
| o parágrafo `<p class="lead">Das <b>${works.length}</b> obras da síntese, o funil destacou ... vá para <b>Decidir</b>.</p>` | `<p class="lead">Das <b>${works.length}</b> obras da síntese, <b>${fruit.length}</b> entram em tríades a construir: três obras que nunca foram citadas juntas e que, se passassem a ser, mais aproximariam as tradições (alta integração por condutância real, ΔKf, e plausíveis na faixa semântica). Não são pontes que já existem: são <em>onde construir</em>. Veja-as abaixo; para decidir o que entra na leitura, vá para <b>Decidir</b>.</p>` |
| `Nenhum alvo de agenda na modelagem atual.` | `Nenhuma obra da síntese entra em tríade a construir na modelagem atual.` |
| `nenhum alvo de agenda no filtro atual` | `nenhuma obra da agenda no filtro atual` |
| `alvo de construção` (no texto de ajuda) | `tríade a construir` |
| `>Alvo de agenda<` (aparece **duas** vezes: troque nas duas) | `>Obras da agenda<` |
| no `title` desse mesmo botão, `obras em alvos de construção da agenda` | `obras que entram em tríades a construir` |

Depois, procure no arquivo por `alvo de agenda` e `alvos de agenda` (com maiúscula ou minúscula):
não pode sobrar nenhuma ocorrência.

## Feito quando
```bash
python scripts/aceite.py T1             # VEREDITO: APROVADA
```
O aceite confere a tela inteira em celular e tablet: se ele listar algum alvo menor que 44 px,
dê à regra CSS daquele elemento `min-height:44px` (com `display:inline-flex;align-items:center`
se for link ou botão) e rode de novo. Não mude a marcação por causa disso.

A olho, numa captura de computador e uma de celular: os cartões mostram o selo com o sólido, as
medidas têm nome e vírgula, e os botões da faixa de ações estão maiores.

Commite só o arquivo que o aceite listar. Mensagem: `Ordem T1: triagem com as peças do sistema`.

## Se algo não bater
Se uma troca "de" não existir no arquivo exatamente como escrita, **não invente**: pare e relate
qual foi. Não mude o comportamento da triagem nem outro arquivo.
