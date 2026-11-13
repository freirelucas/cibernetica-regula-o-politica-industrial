# Ordem O0 — Encaixes

> **Feita** (commit a4c4fb4, aprovada na primeira execução). Fica aqui como registro e modelo de formato.
> O executor apontou: o gancho do passo 3.6 chama `nota.pagina`, que só passa a existir na ordem N1 (é
> inerte até lá); e sobraram no driver duas menções a "4" telas, corrigidas na ordem F1.

**Objetivo.** Deixar o tronco pronto para quatro ordens rodarem em paralelo sem tocar no mesmo
arquivo. Duas coisas: (1) qualquer modelo passa a poder usar marcadores `{{caminho.do.dado}}`,
os mesmos dos protótipos; (2) o gancho da tela A nota fica instalado, à espera do modelo.
**Nenhuma tela muda nesta ordem.**

**Arquivos que você pode mudar** (lista fechada; `aceite.py` reprova qualquer outro):
`src/marcadores.py` (novo), `src/nota.py` (novo), `src/build_site.py`, `tests/test_espaco.py`,
`.claude/skills/run-scisci-ipea/driver.py`. `docs/` não entra no commit.

## Antes
```bash
python scripts/preparar.py              # tem de terminar em AMBIENTE PRONTO
python scripts/aceite.py O0 --iniciar
```

## Passo 1 — `src/marcadores.py` (arquivo novo)
Copie **literalmente** de `design/ferramentas/gera_prototipos.py` as funções `br`, `esc`, `busca`
e `monta`, com os imports que elas usam (`html`, `re`). Acrescente no fim:

```python
def contexto(cena, corpus, nota):
    """O que os marcadores {{...}} enxergam: os números da cena, a nota e o tamanho do corpus."""
    return {"num": cena["num"], "nota": nota,
            "corpus": {"n": corpus["corpus_size"], "sementes": corpus["n_seeds"]}}
```

Comece o arquivo com um docstring de uma frase dizendo o que o módulo faz.

## Passo 2 — `src/nota.py` (arquivo novo, só os dados)
Copie **literalmente** do mesmo arquivo as constantes `EIXO`, `NOME`, `SOLIDO`, `N_VIZINHAS` e a
função `dados_nota`, **renomeada para `dados`**. Não mude uma linha do corpo da função: um teste
compara o resultado com o da referência. As funções de página ficam para a ordem N1.

## Passo 3 — `src/build_site.py`
1. Junto dos outros imports de módulos do projeto: `import marcadores` e `import nota`.
2. Junto das constantes de caminho: `NOTA_TPL = os.path.join(HERE, "nota_template.html")`.
3. Logo depois da função `comum`, acrescente:

```python
_CONTEXTO = None


def contexto():
    """Contexto dos marcadores {{...}}, calculado uma vez por execução."""
    global _CONTEXTO
    if _CONTEXTO is None:
        cena = espaco.dados(explorer_network())
        corpus = data_io.load_data("scisci_results.json", required=True)
        _CONTEXTO = marcadores.contexto(cena, corpus, nota.dados(cena) if cena["nota"] else {})
    return _CONTEXTO


def resolver(html, blocos=None):
    """Troca os marcadores {{caminho}} de um modelo pelos valores. Marcador sem dado é erro."""
    return marcadores.monta(html, contexto(), blocos or {})
```

4. Nos **quatro** pontos em que `main()` chama `comum(...)`, passe a chamar
   `comum(resolver(...))` (relatório, explorador, espaço 3D, triagem).
5. Em `global_nav`: logo depois de `tabs = [("estudo", "index.html", "Estudo")]`, acrescente

```python
    if os.path.exists(NOTA_TPL) and data_io.exists("td_referencias.json"):
        tabs.append(("nota", "nota.html", "A nota"))
```

6. Em `main()`, depois do bloco que grava `docs/espaco.html`, acrescente o gancho da tela nova
   (só roda quando o modelo existir, o que acontece na ordem N1):

```python
    if os.path.exists(NOTA_TPL) and contexto()["nota"]:      # tela A nota (ordem N1 traz o modelo)
        with open(NOTA_TPL, encoding="utf-8") as f:
            pag = nota.pagina(f.read(), contexto())
        pag = comum(pag.replace("__GLOBAL_NAV__", global_nav("nota")))
        nota_html = os.path.join(DOCS, "nota.html")
        with open(nota_html, "w", encoding="utf-8") as f:
            f.write(pag)
        print(f"nota:  {nota_html}  ({os.path.getsize(nota_html)//1024} KB, "
              f"{contexto()['nota']['n_no_nucleo']} obras no núcleo)")
```

## Passo 4 — `tests/test_espaco.py`
Os dois testes de navegação trazem a lista de páginas escrita à mão. Faça-os ler as telas que
existem, para a ordem N1 não precisar mexer neste arquivo:
1. Acrescente, perto do topo (depois de `_json`):

```python
def _telas(root):
    """As telas que existem em docs/, na ordem da barra."""
    return [n for n in ("index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html")
            if os.path.exists(os.path.join(root, "docs", n))]
```

2. Em `test_navegacao_tem_a_aba_em_todas_as_telas` e em `test_navegacao_cabe_no_celular_headless`,
   troque a tupla `("index.html", "explorador.html", "triagem.html", "espaco.html")` por
   `_telas(root)`.
3. Em `test_navegacao_cabe_no_celular_headless`, a comparação `len(m["abas"]) != 4` passa a ser
   `len(m["abas"]) != len(_telas(root))`.

## Passo 5 — `.claude/skills/run-scisci-ipea/driver.py`
Acrescente o tipo `nota`, nos mesmos três lugares em que existe o tipo `espaco`:
- em `drive`: `info["obras"] = pg.evaluate("() => document.querySelectorAll('.sd-obra').length")`
  e `ok = ok and info["obras"] > 0`;
- em `report`: uma linha `obras da nota: N`;
- em `main`: `pages.append(("nota", "/nota.html", "/tmp/scisci_nota.png"))`, dentro de um
  `if os.path.exists(os.path.join(DOCS, "nota.html"))`.
No docstring do topo, "QUATRO páginas" passa a "CINCO" e a lista ganha a linha da nota.

## Feito quando
```bash
python scripts/aceite.py O0             # VEREDITO: APROVADA
git status --short docs/                # não mostra nada: nenhuma tela mudou
```
Commite só os arquivos que o aceite listar. Mensagem: `Ordem O0: marcadores em todos os modelos
e gancho da tela A nota`, seguida de duas ou três linhas dizendo o que foi feito e o veredito.

## Se algo não bater
Não adapte o desenho nem mexa em outro arquivo. Pare e relate: o que tentou, a mensagem de
erro, e o que acha que está errado na ordem.
