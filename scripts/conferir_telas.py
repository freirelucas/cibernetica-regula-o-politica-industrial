#!/usr/bin/env python3
"""Confere telas em navegador real: o que ler o código-fonte não mostra.

Para cada página e cada tamanho de tela (celular 390, tablet 820, computador 1440), mede:
  - erro de página ou de console;
  - requisição que falhou ou devolveu 400 ou mais;
  - página mais larga que a tela (rolagem lateral);
  - aba da barra de telas cortada ou fora da tela;
  - alvo de toque menor que 44 px (só nos tamanhos de toque);
  - número sem valor: elemento [data-n] vazio.
Sai com código 1 se houver qualquer problema. Opcionalmente salva capturas.

Uso (a partir da raiz do repositório):
    python scripts/conferir_telas.py                                  # as páginas de docs/ que existirem
    python scripts/conferir_telas.py docs/nota.html docs/index.html   # páginas escolhidas
    python scripts/conferir_telas.py design/prototipos/nota.html      # um protótipo de desenho
    python scripts/conferir_telas.py --capturas /tmp/telas            # também salva as imagens

Precisa do Playwright com um Chromium (o mesmo requisito do driver do run-scisci-ipea).
"""
import argparse
import functools
import http.server
import json
import os
import socketserver
import sys
import threading

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TAMANHOS = {"celular": (390, 844, True), "tablet": (820, 1180, True), "computador": (1440, 900, False)}
PADRAO = ["docs/index.html", "docs/nota.html", "docs/espaco.html", "docs/explorador.html", "docs/triagem.html"]

MEDE = """() => {
  const vis = e => e.getClientRects().length > 0 && getComputedStyle(e).visibility !== 'hidden';
  const larg = document.documentElement.clientWidth;
  const pequenos = {};
  for (const e of document.querySelectorAll('button, a[href], input, select, summary')) {
    if (!vis(e)) continue;
    const r = e.getBoundingClientRect();
    if (r.width >= 44 && r.height >= 44) continue;
    const rot = e.closest('label');
    if (e.tagName === 'INPUT' && rot && rot.getBoundingClientRect().height >= 44) continue;   // caixa dentro de rótulo alto
    const k = (e.textContent || e.getAttribute('aria-label') || e.id || e.tagName).trim().slice(0, 28) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height);
    pequenos[k] = (pequenos[k] || 0) + 1;
  }
  const abas = [...document.querySelectorAll('.gnav-tab, .sd-tela')].filter(vis).map(a => { const r = a.getBoundingClientRect(); return [a.textContent.trim(), r.left, r.right]; });
  return {
    pagina: document.documentElement.scrollWidth, janela: larg,
    cortadas: abas.filter(a => a[1] < -0.5 || a[2] > larg + 0.5).map(a => a[0]),
    pequenos: pequenos,
    vazios: [...document.querySelectorAll('[data-n]')].filter(e => !e.textContent.trim()).map(e => e.getAttribute('data-n')).slice(0, 8)
  };
}"""


def main():
    ap = argparse.ArgumentParser(description="Confere telas em navegador real, em três tamanhos.")
    ap.add_argument("paginas", nargs="*", help="caminhos relativos à raiz (padrão: as telas de docs/ que existirem)")
    ap.add_argument("--capturas", help="pasta onde salvar uma imagem por página e tamanho")
    ap.add_argument("--toque-estrito", action="store_true", help="também reprova alvo menor que 44 px no computador")
    args = ap.parse_args()
    paginas = args.paginas or [p for p in PADRAO if os.path.exists(os.path.join(RAIZ, p))]
    faltam = [p for p in paginas if not os.path.exists(os.path.join(RAIZ, p.split("#")[0]))]
    if faltam:
        print("ERRO: página inexistente:", ", ".join(faltam))
        return 1
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("ERRO: Playwright ausente. Instale: pip install playwright && python -m playwright install chromium")
        return 1
    if args.capturas:
        os.makedirs(args.capturas, exist_ok=True)

    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = socketserver.ThreadingTCPServer(("127.0.0.1", 0), functools.partial(Quieto, directory=RAIZ))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}/"
    ruins = 0
    try:
        with sync_playwright() as p:
            nav = p.chromium.launch()
            for pagina in paginas:
                for nome, (w, h, toque) in TAMANHOS.items():
                    erros = []
                    ctx = nav.new_context(viewport={"width": w, "height": h}, has_touch=toque, is_mobile=(nome == "celular"))
                    pg = ctx.new_page()
                    pg.on("pageerror", lambda e: erros.append("erro de página: " + str(e)[:160]))
                    pg.on("console", lambda m: erros.append("console: " + m.text[:160]) if m.type == "error" else None)
                    pg.on("requestfailed", lambda r: erros.append("requisição falhou: " + r.url[-70:]))
                    pg.on("response", lambda r: erros.append(f"resposta {r.status}: " + r.url[-70:]) if r.status >= 400 else None)
                    pg.goto(base + pagina, wait_until="load")
                    pg.wait_for_timeout(1200)
                    m = pg.evaluate(MEDE)
                    if args.capturas:
                        pg.screenshot(path=os.path.join(args.capturas, f"{os.path.basename(pagina).split('.')[0]}-{nome}.png"))
                    ctx.close()
                    problemas = list(erros)
                    if m["pagina"] > m["janela"]:
                        problemas.append(f"página com {m['pagina']} px numa tela de {m['janela']} px (rola para o lado)")
                    if m["cortadas"]:
                        problemas.append("abas cortadas: " + ", ".join(m["cortadas"]))
                    if m["vazios"]:
                        problemas.append("números sem valor: " + ", ".join(m["vazios"]))
                    if m["pequenos"] and (toque or args.toque_estrito):
                        problemas.append("alvos menores que 44 px: " + json.dumps(m["pequenos"], ensure_ascii=False)[:400])
                    ruins += bool(problemas)
                    print(f"{'PROBLEMA' if problemas else 'ok      '}  {pagina:34} {nome:10}" + ("" if not problemas else "\n          - " + "\n          - ".join(problemas)))
            nav.close()
    finally:
        srv.shutdown()
    print("\nRESULTADO:", "OK" if not ruins else f"{ruins} combinação(ões) com problema")
    return 1 if ruins else 0


if __name__ == "__main__":
    sys.exit(main())
