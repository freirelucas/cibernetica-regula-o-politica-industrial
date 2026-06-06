"""P3 — Smoke test que reroda o build e valida que todos os tokens foram substituídos.

Cobre regressão do tipo PR #21 (links para data/dados/X.json davam 404 porque o
arquivo não estava em docs/dados/). Aqui validamos algo mais simples mas igualmente
importante: TOKENS no template (XGI_*, AUTHORNET_*, BRASIL_*, BROK_*) devem ter
sido substituídos antes do HTML ir para produção. Se um JSON-fonte some, o token
fica sem valor e aparece literal no site.
"""
import os
import re
import subprocess
import sys


KNOWN_PREFIXES = ["XGI_", "AUTHORNET_", "BRASIL_", "BROK_", "SOLIDEZ_", "SEMBR_"]


def test_build_runs(root):
    """build_site.py roda sem erro e produz docs/index.html."""
    result = subprocess.run(
        [sys.executable, os.path.join(root, "src", "build_site.py")],
        cwd=root, capture_output=True, text=True, timeout=120,
    )
    assert result.returncode == 0, (
        f"build_site.py falhou (exit {result.returncode}):\n"
        f"STDOUT: {result.stdout[-500:]}\n"
        f"STDERR: {result.stderr[-500:]}"
    )
    index = os.path.join(root, "docs", "index.html")
    assert os.path.exists(index), "docs/index.html não foi gerado"


def test_no_unsubstituted_tokens(root):
    """Nenhum token do tipo PREFIXO_LETRAS deve sobreviver ao build."""
    index = os.path.join(root, "docs", "index.html")
    html = open(index, encoding="utf-8").read()
    bad = []
    for prefix in KNOWN_PREFIXES:
        # tokens são UPPER_CASE com letras e underscores; permite até 30 chars
        pat = re.compile(rf"\b{re.escape(prefix)}[A-Z_]{{1,30}}\b")
        for m in pat.finditer(html):
            tok = m.group(0)
            # exclui ocorrências dentro de <code>...</code> (são exemplos literais)
            start = max(0, m.start() - 60)
            ctx = html[start:m.end() + 20]
            if "<code>" in ctx and "</code>" in ctx:
                continue
            bad.append(tok)
    assert not bad, f"tokens não-substituídos no docs/index.html: {sorted(set(bad))}"


def test_critical_data_files_in_docs_dados(root):
    """Arquivos referenciados como dados/X.json no template devem existir em docs/dados/.
    Cobre o bug do PR #21 onde rayyan_tags.json estava em data/ mas não em docs/dados/."""
    template = open(os.path.join(root, "src", "site_template.html"), encoding="utf-8").read()
    referenced = set(re.findall(r'href="dados/([^"]+\.(?:json|csv|ris))"', template))
    missing = []
    for fname in referenced:
        path = os.path.join(root, "docs", "dados", fname)
        if not os.path.exists(path):
            missing.append(fname)
    assert not missing, f"referenciados em template mas ausentes em docs/dados/: {missing}"
