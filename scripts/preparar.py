#!/usr/bin/env python3
"""Prepara e confere o ambiente antes de qualquer ordem de construção.

Roda os passos abaixo, na ordem, e para no primeiro que falhar, dizendo o conserto:
  1. bibliotecas Python (pytest, numpy, scipy, networkx, playwright, igraph, leidenalg);
  2. node (testes de geometria e gerador de glifos);
  3. o navegador do Playwright abre;
  4. data/author_network.json existe — fica fora do git; se faltar, é gerado aqui, offline;
  5. o sítio constrói e docs/dados/ não diverge do que está no git (prova de docs/ canônico).
Termina com "AMBIENTE PRONTO" e código 0. Sem isso, não comece ordem nenhuma: teste pulado por
falta de ferramenta parece verde e não é.

Uso (da raiz do repositório):  python scripts/preparar.py
"""
import importlib.util
import os
import shutil
import subprocess
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def falha(passo, conserto):
    print(f"\nPAROU no passo {passo}.\nConserto: {conserto}")
    sys.exit(1)


def main():
    os.chdir(RAIZ)
    faltam = [m for m in ("pytest", "numpy", "scipy", "networkx", "playwright", "igraph", "leidenalg")
              if importlib.util.find_spec(m) is None]
    if faltam:
        nomes = " ".join("python-igraph" if m == "igraph" else m for m in faltam)
        falha(1, f"python -m pip install {nomes}")
    print("1. bibliotecas Python: ok")

    if not shutil.which("node"):
        falha(2, "instale o Node.js (qualquer versão recente) e deixe 'node' no PATH")
    print("2. node: ok")

    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            nav = p.chromium.launch()
            versao = nav.version
            nav.close()
    except Exception as e:                                   # noqa: BLE001 — a mensagem do Playwright é o diagnóstico
        falha(3, "o navegador do Playwright não abriu. Se o ambiente já traz um Chromium, instale a versão "
                 "do pacote que combina com ele (python -m pip install 'playwright==X.Y.Z'); senão, "
                 "python -m playwright install chromium.\n          Erro: " + str(e).splitlines()[0][:200])
    print(f"3. navegador: ok (Chromium {versao})")

    rede = os.path.join(RAIZ, "data", "author_network.json")
    if not os.path.exists(rede):
        print("4. data/author_network.json ausente: gerando offline (cerca de meio minuto)...")
        r = subprocess.run([sys.executable, os.path.join("src", "author_network.py")],
                           env=dict(os.environ, OA_OFFLINE="1"), capture_output=True, text=True)
        if r.returncode != 0 or not os.path.exists(rede):
            falha(4, "OA_OFFLINE=1 python src/author_network.py falhou:\n" + (r.stderr or r.stdout)[-600:])
    print("4. data/author_network.json: ok")

    r = subprocess.run([sys.executable, os.path.join("src", "build_site.py")], capture_output=True, text=True)
    if r.returncode != 0:
        falha(5, "python src/build_site.py falhou:\n" + (r.stderr or r.stdout)[-800:])
    sujo = subprocess.run(["git", "status", "--porcelain", "--", "docs/dados"], capture_output=True, text=True).stdout.strip()
    if sujo:
        falha(5, "docs/dados/ divergiu do git depois da construção: data/author_network.json não é o canônico.\n"
                 "          Apague-o e rode este script de novo (ele o regenera com Leiden):\n"
                 "          rm data/author_network.json && python scripts/preparar.py\n" + sujo[:300])
    print("5. construção: ok, docs/dados/ igual ao do git")
    print("\nAMBIENTE PRONTO")
    return 0


if __name__ == "__main__":
    sys.exit(main())
