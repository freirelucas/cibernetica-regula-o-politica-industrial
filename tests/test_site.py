"""Build do site: seções, placeholder, gráficos e ausência de CDN."""
import json
import os

import build_site
import report_from_json
from report_template import inject_template

SECTIONS = ["resumo", "teoria", "metodo", "funil", "temporal", "pontes", "agrupamentos", "rede",
            "rajadas", "adormecidas", "citadas", "discussao", "brasil", "analise-brasil", "sintese", "leitura", "sementes", "repro", "dados",
            "limitacoes", "glossario", "referencias"]


def _html(results):
    js = report_from_json.build_js(results) + f"const META={json.dumps(build_site.build_meta(results))};\n"
    tpl = os.path.join(os.path.dirname(build_site.__file__), "site_template.html")
    return inject_template(js, tpl)


def test_all_sections(results):
    html = _html(results)
    faltando = [s for s in SECTIONS if f'id="{s}"' not in html]
    assert not faltando, f"seções ausentes: {faltando}"


def test_placeholder_replaced(results):
    assert "__JS_DATA__" not in _html(results)


def test_consts_present(results):
    html = _html(results)
    for c in ["const STATS=", "const TEMPORAL=", "const SEEDS=", "const CLUSTERS=", "const META="]:
        assert c in html, f"const ausente: {c}"


def test_charts_and_no_cdn(results):
    html = _html(results)
    for c in ["chartTemporal", "chartBridges", "chartClusters"]:
        assert f'id="{c}"' in html
    assert "vendor/chart.umd.min.js" in html
    assert "cdnjs" not in html and "googleapis" not in html, "referência a CDN externo"


def test_download_links_pt(results):
    html = _html(results)
    for f in ["00_registro_execucao.csv", "03_obras_ponte.csv", "08_obras_semente.csv"]:
        assert f"dados/{f}" in html


def _explorer_html(results):
    js = (report_from_json.build_js(results)
          + f"const META={json.dumps(build_site.build_meta(results))};\n")
    net_src = os.path.join(os.path.dirname(os.path.dirname(build_site.__file__)), "data", "network.json")
    net = json.load(open(net_src, encoding="utf-8")) if os.path.exists(net_src) else {"nodes": [], "links": []}
    js += f"const NETWORK={json.dumps(net, ensure_ascii=False)};\n"
    js += f"const NETMETA={json.dumps(build_site.net_stats(net), ensure_ascii=False)};\n"
    with open(build_site.EXPLORER_TPL, encoding="utf-8") as f:
        return f.read().replace("__JS_DATA__", js)


def test_explorer_built(results):
    html = _explorer_html(results)
    assert "__JS_DATA__" not in html
    assert "const NETWORK=" in html and "const NETMETA=" in html
    assert "vendor/d3.min.js" in html
    assert "cdnjs" not in html and "googleapis" not in html
    for ctl in ['id="axisFilters"', 'id="wmin"', 'id="search"', 'id="graph"']:
        assert ctl in html, f"controle ausente no explorador: {ctl}"


def test_explorer_linked_from_site(results):
    assert "explorador.html" in _html(results)


def test_net_stats_consistency(root):
    net_src = os.path.join(root, "data", "network.json")
    if not os.path.exists(net_src):
        return
    net = json.load(open(net_src, encoding="utf-8"))
    s = build_site.net_stats(net)
    assert s["n"] == len(net["nodes"]) and s["e"] == len(net["links"])
    assert s["intra"] + s["inter"] == s["classif"]
    assert 99 <= s["pct_intra"] + s["pct_inter"] <= 101
