#!/usr/bin/env python3
"""Driver do site cienciométrico (GitHub Pages estático em docs/).

Constrói (opcional), serve docs/ num servidor HTTP efêmero e dirige o site
renderizado com Chromium headless (Playwright): captura erros de página/console,
conta os gráficos Chart.js, confere as seções e os spans de dados, e salva um
screenshot de página inteira.

Uso (caminhos relativos à RAIZ do repositório):
    python .claude/skills/run-scisci-ipea/driver.py                 # serve + verifica + screenshot
    python .claude/skills/run-scisci-ipea/driver.py --build         # regenera docs/ a partir do JSON antes
    python .claude/skills/run-scisci-ipea/driver.py --shot /tmp/s.png --path /

Saída: STATUS OK (código 0) quando não há erro de página, há 3 gráficos e todas
as 18 seções estão presentes; PROBLEMA (código 1) caso contrário.
Pré-requisito do caminho do agente:
    pip install playwright && python -m playwright install --with-deps chromium
"""
import argparse
import functools
import http.server
import os
import subprocess
import sys
import threading

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
DOCS = os.path.join(ROOT, "docs")

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos", "rede",
            "rajadas", "adormecidas", "citadas", "discussao", "brasil", "sementes", "repro", "dados",
            "limitacoes", "glossario", "referencias"]
META_SPANS = ["m-cocit", "m-coupling", "m-clusters", "m-pivotal", "m-pctrefs"]


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # silencia o log de acesso
            pass
    handler = functools.partial(Quiet, directory=directory)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def main():
    ap = argparse.ArgumentParser(description="Build/serve/drive o site estático.")
    ap.add_argument("--build", action="store_true", help="regenera docs/ via src/build_site.py antes de servir")
    ap.add_argument("--shot", default="/tmp/scisci_site.png", help="caminho do screenshot de página inteira")
    ap.add_argument("--path", default="/", help="caminho a carregar (ex.: /#discussao)")
    args = ap.parse_args()

    if args.build:
        print("== build ==")
        subprocess.run([sys.executable, os.path.join(ROOT, "src", "build_site.py")], check=True)

    if not os.path.exists(os.path.join(DOCS, "index.html")):
        print("ERRO: docs/index.html ausente — rode com --build."); return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERRO: Playwright ausente. Instale:\n"
              "  pip install playwright && python -m playwright install --with-deps chromium")
        return 1

    httpd, port = serve(DOCS)
    url = f"http://127.0.0.1:{port}{args.path}"
    page_errs, console_errs = [], []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1200, "height": 900})
            pg.on("pageerror", lambda e: page_errs.append(str(e)))
            pg.on("console", lambda m: console_errs.append(m.text) if m.type == "error" else None)
            pg.goto(url, wait_until="networkidle")
            pg.wait_for_timeout(2500)  # Chart.js desenha após document.fonts.ready
            charts = pg.evaluate("() => window.Chart ? Object.keys(Chart.instances || {}).length : 0")
            secs = pg.evaluate("() => [...document.querySelectorAll('section[id]')].map(s => s.id)")
            spans = pg.evaluate("(ids) => ids.filter(i => ((document.getElementById(i)||{}).textContent||'').length < 4)", META_SPANS)
            pg.screenshot(path=args.shot, full_page=True)
            b.close()
    finally:
        httpd.shutdown()

    missing = [s for s in SECTIONS if s not in secs]
    print(f"url:        {url}")
    print(f"screenshot: {args.shot}")
    print(f"charts:     {charts} (esperado 3)")
    print(f"sections:   {len(secs)}/{len(SECTIONS)}" + (f"  FALTAM: {missing}" if missing else ""))
    print(f"spans vazios: {spans if spans else 'nenhum'}")
    print(f"page errors:  {page_errs if page_errs else 'NENHUM'}")
    if console_errs:
        print(f"console errors (aviso): {console_errs}")
    ok = not page_errs and charts == 3 and not missing and not spans
    print("STATUS:", "OK" if ok else "PROBLEMA")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
