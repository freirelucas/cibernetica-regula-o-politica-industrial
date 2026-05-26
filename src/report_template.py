"""Resolução e injeção do html_template.html — sem dependências externas.

Fonte única usada por ``report_builder.py`` (caminho do pipeline vivo) e por
``report_from_json.py`` (regeneração offline a partir de scisci_results.json).
"""
import os

PLACEHOLDER = "__JS_DATA__"

def find_template(template_path=None):
    """Localiza o html_template.html em layouts Colab e de repositório."""
    candidates = [template_path] if template_path else []
    here = os.path.dirname(os.path.abspath(__file__))
    candidates += [
        "/home/claude/html_template.html",                        # Colab
        os.path.join(here, "..", "colab", "html_template.html"),  # repo: src/ -> colab/
        os.path.join(here, "html_template.html"),                 # ao lado do módulo
        os.path.join("colab", "html_template.html"),              # cwd = raiz do repo
        "html_template.html",                                     # cwd
    ]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None

def inject_template(js, template_path=None):
    """Injeta o bloco JS (``const STATS=...`` etc.) no template.

    Se o template não for encontrado, devolve um HTML mínimo com os dados
    embutidos — mesmo fallback do gerador original.
    """
    path = find_template(template_path)
    if path is None:
        return (f"<html><body><script>{js}</script>"
                "<p>Template nao encontrado. Dados JS embutidos.</p></body></html>")
    with open(path, encoding="utf-8") as f:
        html_template = f.read()
    return html_template.replace(PLACEHOLDER, js)
