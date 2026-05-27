#!/usr/bin/env python3
"""Driver do site cienciométrico (GitHub Pages estático em docs/).

Constrói (opcional), serve docs/ num servidor HTTP efêmero e dirige as TRÊS
páginas renderizadas com Chromium headless (Playwright):

  • index.html      — relatório: conta os gráficos Chart.js, confere as 22 seções
                      e os spans de dados; screenshot de página inteira.
  • explorador.html — rede de cocitação em d3 (SVG): confere que os nós desenharam.
  • triagem.html    — triagem inclusão/exclusão: confere que os cartões renderizaram.

Cada página captura erros de página/console e salva um screenshot.

Uso (caminhos relativos à RAIZ do repositório):
    python .claude/skills/run-scisci-ipea/driver.py                 # serve + verifica as 3 + screenshots
    python .claude/skills/run-scisci-ipea/driver.py --build         # regenera docs/ antes (build_site.py)
    python .claude/skills/run-scisci-ipea/driver.py --path /#sintese # mira uma seção do index
    python .claude/skills/run-scisci-ipea/driver.py --shot /tmp/s.png

Saída: STATUS OK (código 0) quando, em TODAS as páginas presentes, não há erro de
página e os marcadores batem (index: 3 gráficos + 22 seções + 5 spans preenchidos;
explorador: nós > 0; triagem: cartões > 0). PROBLEMA (código 1) caso contrário.
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
            "rajadas", "adormecidas", "citadas", "discussao", "brasil", "analise-brasil", "sintese",
            "leitura", "sementes", "repro", "dados", "limitacoes", "glossario", "referencias"]
META_SPANS = ["m-cocit", "m-coupling", "m-clusters", "m-pivotal", "m-pctrefs"]


def serve(directory):
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):  # silencia o log de acesso
            pass
    handler = functools.partial(Quiet, directory=directory)
    httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, httpd.server_address[1]


def drive(browser, url, shot, kind):
    """Carrega uma página, roda as verificações do seu tipo, salva screenshot.
    Devolve (ok, info). Cada página usa uma aba nova para isolar os erros."""
    errs, cerr = [], []
    pg = browser.new_page(viewport={"width": 1200, "height": 900})
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: cerr.append(m.text) if m.type == "error" else None)
    pg.goto(url, wait_until="networkidle")
    pg.wait_for_timeout(2800)  # Chart.js/d3 desenham após document.fonts.ready
    info = {"url": url, "errs": errs, "cerr": cerr}
    ok = not errs
    if kind == "index":
        info["charts"] = pg.evaluate("() => window.Chart ? Object.keys(Chart.instances || {}).length : 0")
        secs = pg.evaluate("() => [...document.querySelectorAll('section[id]')].map(s => s.id)")
        info["missing"] = [s for s in SECTIONS if s not in secs]
        info["spans"] = pg.evaluate(
            "(ids) => ids.filter(i => ((document.getElementById(i)||{}).textContent||'').length < 4)", META_SPANS)
        ok = ok and info["charts"] == 3 and not info["missing"] and not info["spans"]
    elif kind == "explorador":
        info["circles"] = pg.evaluate("() => document.querySelectorAll('#graph circle').length")
        ok = ok and info["circles"] > 0
    elif kind == "triagem":
        info["cards"] = pg.evaluate("() => document.querySelectorAll('.card').length")
        ok = ok and info["cards"] > 0
    pg.screenshot(path=shot, full_page=(kind == "index"))
    pg.close()
    return ok, info


def report(kind, ok, info):
    print(f"\n[{kind}]  {info['url']}")
    if kind == "index":
        print(f"  charts:   {info['charts']} (esperado 3)")
        print(f"  sections: {len(SECTIONS) - len(info['missing'])}/{len(SECTIONS)}"
              + (f"  FALTAM: {info['missing']}" if info["missing"] else ""))
        print(f"  spans vazios: {info['spans'] if info['spans'] else 'nenhum'}")
    elif kind == "explorador":
        print(f"  nós (círculos d3): {info['circles']}")
    elif kind == "triagem":
        print(f"  cartões: {info['cards']}")
    print(f"  page errors: {info['errs'] if info['errs'] else 'NENHUM'}")
    if info["cerr"]:
        print(f"  console errors (aviso): {info['cerr']}")
    print(f"  -> {'OK' if ok else 'PROBLEMA'}")


def main():
    ap = argparse.ArgumentParser(description="Build/serve/drive o site estático (index + explorador + triagem).")
    ap.add_argument("--build", action="store_true", help="regenera docs/ via src/build_site.py antes de servir")
    ap.add_argument("--shot", default="/tmp/scisci_site.png", help="screenshot do index (página inteira)")
    ap.add_argument("--path", default="/", help="caminho do index a carregar (ex.: /#sintese)")
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

    pages = [("index", args.path, args.shot)]
    if os.path.exists(os.path.join(DOCS, "explorador.html")):
        pages.append(("explorador", "/explorador.html", "/tmp/scisci_explorador.png"))
    if os.path.exists(os.path.join(DOCS, "triagem.html")):
        pages.append(("triagem", "/triagem.html", "/tmp/scisci_triagem.png"))

    httpd, port = serve(DOCS)
    results = []
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            for kind, path, shot in pages:
                ok, info = drive(b, f"http://127.0.0.1:{port}{path}", shot, kind)
                info["shot"] = shot
                results.append((kind, ok, info))
            b.close()
    finally:
        httpd.shutdown()

    for kind, ok, info in results:
        report(kind, ok, info)
    print("\nscreenshots:", ", ".join(i["shot"] for _, _, i in results))
    allok = all(ok for _, ok, _ in results)
    print("STATUS:", "OK" if allok else "PROBLEMA")
    return 0 if allok else 1


if __name__ == "__main__":
    raise SystemExit(main())
