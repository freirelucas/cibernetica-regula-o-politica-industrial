"""Resolução e injeção do modelo HTML do site — sem dependências externas.

Usado por ``build_site.py`` (que passa o caminho do modelo explicitamente) e
exposto para reuso.
"""
import os

PLACEHOLDER = "__JS_DATA__"


def find_template(template_path=None):
    """Localiza o modelo do site (site_template.html)."""
    here = os.path.dirname(os.path.abspath(__file__))
    candidates = [template_path] if template_path else []
    candidates += [
        os.path.join(here, "site_template.html"),    # ao lado do módulo (src/)
        os.path.join("src", "site_template.html"),   # cwd = raiz do repo
        "site_template.html",
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def inject_template(js, template_path=None):
    """Injeta o bloco JS (``const STATS=...`` etc.) no modelo.

    Se o modelo não for encontrado, devolve um HTML mínimo com os dados embutidos.
    """
    path = find_template(template_path)
    if path is None:
        return (f"<html><body><script>{js}</script>"
                "<p>Modelo nao encontrado. Dados JS embutidos.</p></body></html>")
    with open(path, encoding="utf-8") as f:
        html = f.read()
    return html.replace(PLACEHOLDER, js)
