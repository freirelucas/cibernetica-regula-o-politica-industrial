"""Varredura de anglicismos na prosa autoral (site, README, notebook).

Exclui contextos legítimos: blocos de código, código inline, itálico (títulos
reais de referências em inglês), tabelas (sementes/referências) e o bloco de
Abstract em inglês do site.
"""
import json
import os
import re

BANNED = [
    "science of science", "smoke test", "snowball", "co-citation", "coupling",
    "betweenness", "burst", "beauty coefficient", "sleeping beaut", "trading zone",
    "pipeline", "checkpoint", "dashboard",
    r"\bseeds\b", r"\bclusters\b", r"\bbridges\b", r"\bpapers\b", r"\breport\b",
    r"\bqueries\b",
]


def _scan(text):
    low = text.lower()
    return [b for b in BANNED if re.search(b, low)]


def _strip_html(html):
    for pat in [r"<script.*?</script>", r"<style.*?</style>",
                r'<span class="src">.*?</span>', r'<ul class="refs">.*?</ul>',
                r'<pre class="code">.*?</pre>', r'<div class="abstract-en">.*?</div>']:
        html = re.sub(pat, " ", html, flags=re.S)
    return re.sub(r"<[^>]+>", " ", html)


def _strip_md(md):
    md = re.sub(r"```.*?```", " ", md, flags=re.S)   # blocos de código
    md = re.sub(r"`[^`]*`", " ", md)                  # código inline (nomes de arquivo/campo)
    md = re.sub(r"\*\*[^*]+\*\*", " ", md)            # negrito (rótulos)
    md = re.sub(r"\*[^*]+\*", " ", md)                # itálico (títulos de referência em inglês)
    md = re.sub(r"(?m)^\|.*\|\s*$", " ", md)          # linhas de tabela (sementes/referências)
    return md


def test_site_prose(root):
    html = open(os.path.join(root, "docs", "index.html"), encoding="utf-8").read()
    assert _scan(_strip_html(html)) == []


def test_readme_prose(root):
    md = open(os.path.join(root, "README.md"), encoding="utf-8").read()
    assert _scan(_strip_md(md)) == []


def test_notebook_prose(root):
    nb = json.load(open(os.path.join(root, "colab", "scisci_cibernetica_regulacao_PI_v2.ipynb"), encoding="utf-8"))
    md = "\n".join((c["source"] if isinstance(c["source"], str) else "".join(c["source"]))
                   for c in nb["cells"] if c["cell_type"] == "markdown")
    assert _scan(_strip_md(md)) == []
