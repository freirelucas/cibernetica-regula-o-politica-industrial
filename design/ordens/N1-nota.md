# Ordem N1 — Tela nova: A nota

**Objetivo.** Publicar `docs/nota.html`, a bibliografia do texto para discussão situada no mapa
das tradições. Como deve ficar: abra `design/prototipos/nota.html` no navegador.

**Arquivos que você pode mudar:** `src/nota.py`, `src/nota_template.html` (novo),
`src/espaco_template.html` (uma linha). `docs/` não entra no commit.

O gancho que gera a página já está em `src/build_site.py` (ordem O0): ele chama
`nota.pagina(modelo, contexto)` quando `src/nota_template.html` existe. Faltam o modelo e a função.

## Antes
```bash
python scripts/preparar.py
python scripts/aceite.py N1 --iniciar
```

## Passo 1 — `src/nota.py`: as funções de página
1. No topo, depois do docstring: `from marcadores import br, esc, monta`.
2. Copie **literalmente** de `design/ferramentas/gera_prototipos.py` as funções `solido`, `selo`,
   `mistura`, `item_obra` e `item_fora`. Uma única troca, dentro de `item_obra`:
   `../../docs/espaco.html` vira `espaco.html`.
3. Acrescente no fim:

```python
def pagina(modelo, ctx):
    """Monta docs/nota.html: resolve os marcadores do modelo com o contexto e os blocos desta tela."""
    n = ctx["nota"]
    blocos = {
        "obras_no_nucleo": "\n".join(item_obra(o) for o in n["obras"]),
        "obras_fora": "\n".join(item_fora(f) for f in n["fora"]),
        "atos": "\n".join(f"<li>{esc(a['ref'])}</li>" for a in n["atos"]),
        "autores": esc(", ".join(n["autores"])),
        "chips_eixo": "".join(
            f'<button type="button" class="sd-chip" data-eixo="{EIXO[a]}" aria-pressed="true"'
            + (" disabled" if not n["por_eixo"][a] else "")
            + f'>{solido(a)}{NOME[a]} <span class="sd-num">{n["por_eixo"][a]}</span></button>' for a in range(4)),
    }
    return monta(modelo, ctx, blocos)
```

Não mexa em `dados`: há teste que compara o resultado com o da referência.

## Passo 2 — `src/nota_template.html`
Copie `design/modelos/nota.html` para `src/nota_template.html` e faça **só** estas trocas:

| de | para |
|---|---|
| `<title>Protótipo — A nota: a bibliografia no mapa das tradições</title>` | `<title>A nota: a bibliografia no mapa das tradições</title>` |
| `<link rel="stylesheet" href="../../docs/vendor/fonts.css">` | `<link rel="stylesheet" href="vendor/fonts.css">` |
| `<link rel="stylesheet" href="../sistema.css">` | `__SISTEMA__` |
| a linha `{{svg:solidos}}` | `__SOLIDOS__` |
| `href="../../docs/espaco.html#lente=nota"` | `href="espaco.html#lente=nota"` |
| o bloco inteiro `<header class="sd-barra">` ... `</header>` | o bloco abaixo |

```html
<header class="topbar sd sd-barra">
  <a class="sd-marca" href="index.html">Ipea/Diest</a>
  __GLOBAL_NAV__
</header>
```

Os demais marcadores `{{...}}` ficam como estão: quem os resolve é `nota.pagina`.

## Passo 3 — `src/espaco_template.html`: a lente leva à lista
Logo depois da linha `<ul class="lista-obras" id="refs-rede"></ul>`, acrescente:

```html
      <p><a class="elo" href="nota.html">Ver a lista completa da bibliografia</a></p>
```

## Feito quando
```bash
python scripts/aceite.py N1             # VEREDITO: APROVADA
```
E, a olho, numa captura (`python scripts/conferir_telas.py docs/nota.html --capturas PASTA`):
1. a barra tem cinco abas e "A nota" está sublinhada;
2. cada obra tem sólido, selo, faixa de mistura e a lista "leia ao lado";
3. clicar num filtro de tradição esconde e mostra as obras daquela tradição.

Commite só os arquivos que o aceite listar. Mensagem: `Ordem N1: tela A nota`.

## Se algo não bater
Não adapte o desenho nem mexa em outro arquivo. Pare e relate o que tentou e a mensagem de erro.
