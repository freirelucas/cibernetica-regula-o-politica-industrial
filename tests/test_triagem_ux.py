"""PR-7 — reforma de UX da triagem: limiares ao vivo, composição, solidez (gancho),
proveniência e SEM localStorage (estado no arquivo versionado rayyan_selection.json).
"""
import json
import os
import pathlib
import subprocess
import sys

import pytest

import build_rayyan
import build_site

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TPL = os.path.join(ROOT, "src", "triagem_template.html")


def test_no_localstorage():
    """Restrição do handout: estado NÃO no navegador."""
    assert "localStorage" not in open(TPL, encoding="utf-8").read()


def test_template_has_ux_controls():
    t = open(TPL, encoding="utf-8").read()
    for needle in ['id="thPrio"', 'id="thHo"', 'id="thEixos"', 'id="thBrasil"',
                   'id="expSel"', 'id="thCount"', 'id="comp"', 'RAYYAN_SELECTION',
                   'data-preset="solidez"', 'estrutural', 'latente', 'semantico']:
        assert needle in t, f"controle/elemento ausente no template: {needle}"
    # vendorizado, sem CDN (restrição mantida)
    assert "vendor/fonts.css" in t and "cdnjs" not in t and "googleapis" not in t


def test_rayyan_works_js_attaches_signals(tmp_path):
    works = build_rayyan.build(str(tmp_path))
    js = build_site.rayyan_works_js(works)
    assert js, "nenhuma obra serializada"
    w = js[0]
    for k in ("prioridade", "ho_bc", "n_axes", "brasil", "solidez"):
        assert k in w, f"sinal ausente: {k}"
    assert set(w["solidez"].keys()) == {"estrutural", "latente", "semantico"}
    assert all(w["solidez"][k] is None for k in w["solidez"])   # placeholder p/ a modelagem


def test_provenance_sidecar_written(tmp_path):
    build_rayyan.build(str(tmp_path))
    prov = tmp_path / "rayyan_sintese.provenance.json"
    assert prov.exists(), "proveniência da exportação não escrita"
    P = json.load(open(prov, encoding="utf-8"))
    assert "limiares" in P and "MIN_HO_BC_SCORE" in P["limiares"]
    assert "por_eixo" in P and "por_papel" in P


def test_selection_injected_into_built_site():
    """build_site injeta const RAYYAN_SELECTION na triagem (estado versionado)."""
    docs = os.path.join(ROOT, "docs", "triagem.html")
    if not os.path.exists(docs):
        subprocess.run([sys.executable, os.path.join(ROOT, "src", "build_site.py")],
                       cwd=ROOT, check=True, capture_output=True)
    assert "const RAYYAN_SELECTION=" in open(docs, encoding="utf-8").read()


def test_thresholds_filter_cards_headless():
    """Driver headless conta cartões PÓS-FILTRO: subir o limiar HO-BC reduz o conjunto."""
    pytest.importorskip("playwright", reason="Playwright não instalado")
    docs = os.path.join(ROOT, "docs", "triagem.html")
    if not os.path.exists(docs):
        subprocess.run([sys.executable, os.path.join(ROOT, "src", "build_site.py")],
                       cwd=ROOT, check=True, capture_output=True)
    from playwright.sync_api import sync_playwright
    url = pathlib.Path(docs).resolve().as_uri()
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            pg = b.new_page()
            pg.goto(url)
            pg.wait_for_timeout(700)
            n0 = pg.eval_on_selector_all(".card", "e=>e.length")
            pg.eval_on_selector("#thHo", "el=>{el.value=el.max; el.dispatchEvent(new Event('input'))}")
            pg.wait_for_timeout(250)
            n1 = pg.eval_on_selector_all(".card", "e=>e.length")
        finally:
            b.close()
    assert n0 > 100, f"poucos cartões no estado inicial: {n0}"
    assert n1 < n0, f"limiar HO-BC não filtrou ({n0} -> {n1})"
