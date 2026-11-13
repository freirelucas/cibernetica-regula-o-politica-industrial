"""Troca os marcadores {{caminho.do.dado}} dos modelos de tela pelos números e trechos reais.

Os mesmos marcadores que design/ferramentas/gera_prototipos.py usa nos protótipos; aqui o
contexto é o da construção (ver build_site.contexto()).
"""
import html
import re


def br(x, casas=None):
    """Número à brasileira: ponto de milhar, vírgula decimal."""
    if x is None:
        return "—"
    if casas is None and isinstance(x, float) and x != int(x):
        casas = 1
    if casas is None:
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def esc(s):
    return html.escape(str(s), quote=True)


def busca(ctx, caminho):
    o = ctx
    for k in caminho.split("."):
        o = o[int(k)] if isinstance(o, list) else o[k]
    return o


def monta(modelo, ctx, blocos):
    def troca(m):
        corpo = m.group(1).strip()
        if corpo.startswith("bloco:"):
            return blocos[corpo[6:]]
        if corpo == "svg:solidos":
            return blocos["solidos"]
        caminho, _, casas = corpo.partition("|")
        v = busca(ctx, caminho)
        return esc(v) if isinstance(v, str) else br(v, int(casas) if casas else None)
    return re.sub(r"\{\{([^{}]+)\}\}", troca, modelo)


def contexto(cena, corpus, nota):
    """O que os marcadores {{...}} enxergam: os números da cena, a nota e o tamanho do corpus."""
    return {"num": cena["num"], "nota": nota,
            "corpus": {"n": corpus["corpus_size"], "sementes": corpus["n_seeds"]}}
