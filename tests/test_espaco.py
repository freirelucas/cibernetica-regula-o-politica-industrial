"""Espaço 3D — a regra da cena, os números que a página promete e a autocontenção.

A cena não é layout de forças: a posição de cada obra é a composição da sua vizinhança
de cocitação por tradição. Estes testes travam (i) que essa regra é a mesma da
inferência de eixo, (ii) que todo número exibido bate com o derivado de onde vem e
(iii) que a página não faz carga externa nem deixa texto sem valor.
"""
import json
import os
import pathlib
import re
import shutil
import subprocess

import pytest

import build_site
import espaco


@pytest.fixture(scope="module")
def cena():
    return espaco.dados(build_site.explorer_network())


def _json(root, nome):
    with open(os.path.join(root, "data", nome), encoding="utf-8") as f:
        return json.load(f)


def _telas(root):
    """As telas que existem em docs/, na ordem da barra."""
    return [n for n in ("index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html")
            if os.path.exists(os.path.join(root, "docs", n))]


# ── a regra ──

def test_eixo_inferido_e_um_vertice_mais_proximo(cena):
    """O rótulo inferido é um eixo de contagem máxima na vizinhança — logo, um vértice mais próximo.

    Com empate, a obra é equidistante de dois vértices e o rótulo publicado vem da ordem
    de leitura das arestas (``max`` sobre dicionário em build_site): a cena marca essas
    obras e a página declara quantas são, em vez de fingir que o vértice é único.
    """
    inferidas = [n for n in cena["nos"] if not n["o"] and n["a"] >= 0 and sum(n["k"])]
    erros = [n["i"] for n in inferidas if n["k"][n["a"]] != max(n["k"])]
    assert not erros, f"inferido fora dos vértices mais próximos: {erros[:5]}"
    for n in cena["nos"]:
        topo = [j for j in range(4) if sum(n["k"]) and n["k"][j] == max(n["k"])]
        assert n.get("e") == (topo if len(topo) > 1 else None), n["i"]
    empatadas = [n for n in inferidas if "e" in n]
    p = cena["num"]["prov"]
    assert p["empates"] == len(empatadas)
    assert p["empates_na_agenda"] == sum(1 for n in empatadas if n["g"])
    # nenhum rótulo OBSERVADO empata hoje; se passar a empatar, a contagem de "fora" e a
    # acurácia de infer_validation deixam de ser a mesma coisa e o teste seguinte acusa
    assert not [n["i"] for n in cena["nos"] if n["o"] and "e" in n]


def test_cena_e_o_retrato_da_validacao_do_inferidor(cena, root):
    """Obras observadas cuja vizinhança aponta outro eixo = os erros que infer_validation mede."""
    iv = _json(root, "infer_validation.json")
    p = cena["num"]["prov"]
    assert p["n_ouro"] == iv["conjunto_ouro"]["n"]
    assert round(p["acertos"] / p["n_ouro"], 3) == iv["acuracia_global"]
    assert p["sem_vizinhanca"] == iv["conjunto_ouro"]["sem_evidencia_de_vizinhanca"]


def test_todas_as_obras_tem_composicao_ou_estao_declaradas(cena):
    sem = [n["i"] for n in cena["nos"] if sum(n["k"]) == 0]
    assert len(sem) == cena["num"]["prov"]["sem_vizinhanca"] + sum(
        1 for n in cena["nos"] if not n["o"] and sum(n["k"]) == 0)


def test_titulo_cortado_e_sinalizado(cena, root):
    """O funil guarda 60 caracteres do título; a cena avisa com reticências em vez de exibir a palavra partida."""
    rede = {n["id"]: (n.get("label") or "") for n in _json(root, "network_4axis.json")["nodes"]}
    cortados = {i for i, r in rede.items() if len(r) >= espaco.CORTE_ROTULO}
    assert cortados, "nenhum rótulo no limite: conferir se o corte do funil mudou"
    for n in cena["nos"]:
        assert n["l"].endswith("…") == (n["i"] in cortados), n["i"]


# ── os números da página vêm dos derivados ──

def test_nucleo_duro_bate_com_a_replica_so_observados(cena, root):
    oo = _json(root, "observed_only_check.json")
    a = cena["num"]["agenda"]
    assert a["n_agenda"] == oo["agenda_publicada"]["n"] == len(cena["triades"])
    assert a["n_nucleo"] == oo["agenda_publicada"]["n_sobrevivem_so_observado"]
    assert a["n_nucleo"] == sum(t["n"] for t in cena["triades"])
    # núcleo duro = nenhuma obra de rótulo inferido? não: = ao menos duas tradições OBSERVADAS
    for t in cena["triades"]:
        eixos = {cena["nos"][m]["a"] for m in t["m"] if cena["nos"][m]["o"] and cena["nos"][m]["a"] < 3}
        assert (len(eixos) >= 2) == bool(t["n"])


def test_triades_e_obras_sao_a_mesma_agenda(cena):
    """84 tríades e 56 obras são duas contagens do mesmo objeto, não dois números soltos."""
    obras = {m for t in cena["triades"] for m in t["m"]}
    assert len(obras) == cena["num"]["agenda"]["n_obras"]
    assert obras == {i for i, n in enumerate(cena["nos"]) if n["g"]}


def test_silos_e_blocos(cena, root):
    mc = _json(root, "modularity_check.json")["tres_eixos"]
    s = cena["num"]["silos"]
    assert (s["Q"], s["z"], s["n_conectores"]) == (mc["Q_obs"], mc["Q_z"], mc["n_conectores_significativos"])
    b = cena["num"]["blocos"]
    assert b["peso_intra"] + b["peso_inter"] == b["peso_total"]
    assert sum(b["matriz"][i][j] for i in range(4) for j in range(i, 4)) == b["peso_total"]
    r = cena["num"]["rede"]
    assert b["n_arestas_intra"] + b["n_arestas_inter"] + b["n_arestas_com_inferido"] == r["m"]
    assert r["densidade"] == round(2 * r["m"] / (r["n"] * (r["n"] - 1)), 3)


def test_decadas_citadas_na_frase_sao_as_certas(cena):
    """A frase da lente do tempo cita as décadas pelos índices 1 e 4: travar quais são."""
    d = cena["num"]["tempo"]["decadas"]
    assert d[1]["d"] == "1970s" and d[4]["d"] == "2000s"
    assert d[4]["f"] > d[1]["f"]


def test_listas_de_referencias(cena, root):
    li = cena["num"]["listas"]
    assert li["n_listas"] == len(_json(root, "cocitation_hyperedges.json")["hyperedges"])
    assert li["tocam_0"] + li["tocam_1"] + li["tocam_2"] + li["tocam_3"] == li["n_com_rotulo"]
    assert sum(c[4] for c in li["comps"]) == li["n_com_rotulo"]


def test_nota_so_usa_registros_da_rede(cena, root):
    """Zero id inventado: toda referência casada aponta para um nó que existe na rede."""
    if not cena["nota"]:
        pytest.skip("data/td_referencias.json ausente — lente da nota desligada")
    td = _json(root, "td_referencias.json")
    ids = {n["i"] for n in cena["nos"]}
    for r in td["referencias"]:
        assert set(r["oa"]) <= ids, r["ref"][:60]
        assert r["tipo"] in ("obra", "ato")
        assert not (r["tipo"] == "ato" and r["oa"])
    n = cena["nota"]
    assert n["n_obras"] + n["n_atos"] == n["n_refs"] == len(td["referencias"])
    assert n["n_rotulo_observado"] + n["n_rotulo_inferido"] == n["n_obras_na_rede"]
    assert sum(n["k"]) == n["n_rotulo_observado"]
    assert sum(1 for x in cena["nos"] if x["t"]) == n["n_registros"]


# ── a página ──

@pytest.fixture(scope="module")
def pagina(root):
    assert build_site.main() == 0
    with open(os.path.join(root, "docs", "espaco.html"), encoding="utf-8") as f:
        return f.read()


def test_pagina_construida_e_autocontida(pagina, root):
    assert "__ESPACO_DATA__" not in pagina and "__GLOBAL_NAV__" not in pagina
    assert "const ESPACO=" in pagina
    assert os.path.exists(os.path.join(root, "docs", "espaco3d.js"))
    cargas = re.findall(r'<(?:script|link|img|iframe)[^>]*(?:src|href)="(https?:)?//[^"]+"', pagina)
    assert not cargas, "carga externa na página do espaço 3D"
    motor = open(os.path.join(root, "docs", "espaco3d.js"), encoding="utf-8").read()
    assert not re.search(r"https?://", motor), "o motor não deve referir endereço externo"
    assert "WebGL" not in motor.replace("sem WebGL", "").replace("em vez de WebGL", "")


def test_todo_numero_do_texto_tem_origem(pagina, cena):
    """Cada [data-n] aponta para um caminho que existe nos dados: nenhum número é digitado."""
    raiz = dict(cena["num"])
    raiz["regra"] = {"teto": 5}
    raiz["nota"] = dict(cena["nota"] or {}, n_duplicadas=0)
    for caminho in set(re.findall(r'data-n="([^"]+)"', pagina)):
        if caminho.startswith("nota.") and not cena["nota"]:
            continue
        o = raiz
        for k in caminho.split("."):
            o = o[int(k)] if isinstance(o, list) else o.get(k) if isinstance(o, dict) else None
            assert o is not None, f"número sem origem: {caminho}"


def test_lentes_e_ligacoes(pagina):
    for lente in ("silos", "tempo", "prov", "agenda", "nota"):
        assert f'data-lente="{lente}"' in pagina
    for ancora in ("pontes", "longue-duree", "pontes-ordem-superior"):
        assert f'href="index.html#{ancora}"' in pagina
        assert ancora in build_site.SECTIONS
    assert 'aria-live="polite"' in pagina and "prefers-reduced-motion" in pagina
    assert 'role="img"' in pagina and "<noscript>" in pagina


def test_navegacao_tem_a_aba_em_todas_as_telas(pagina, root):
    for nome in _telas(root):
        h = open(os.path.join(root, "docs", nome), encoding="utf-8").read()
        assert 'href="espaco.html"' in h, nome
    assert 'href="espaco.html" aria-current="page">Espaço 3D<' in pagina


def test_prosa_sem_anglicismo(pagina):
    from test_anglicismos import _scan, _strip_html
    assert _scan(_strip_html(pagina)) == []


def test_motor_tem_sintaxe_valida(root):
    node = shutil.which("node")
    if not node:
        pytest.skip("node ausente")
    r = subprocess.run([node, "--check", os.path.join(root, "src", "espaco3d.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


_CONFERE_SOLIDOS = r"""
const fs = require('fs'), vm = require('vm');
const ctx = { window: {} };
vm.runInNewContext(fs.readFileSync(process.argv[1], 'utf8'), ctx);
const E = ctx.window.Espaco3D, out = { solidos: {}, vertices: E.VERT, teto: E.TETO_AFASTA, formas: E.FORMA };
for (const nome of Object.keys(E.SOL)) {
  const S = E.SOL[nome], ar = new Map();
  for (const f of S.f) for (let i = 0; i < f.length; i++) {
    const a = f[i], b = f[(i + 1) % f.length];
    ar.set(a < b ? a + '-' + b : b + '-' + a, Math.hypot(S.v[a][0] - S.v[b][0], S.v[a][1] - S.v[b][1], S.v[a][2] - S.v[b][2]));
  }
  let dentro = 0;
  S.f.forEach((f, i) => { const c = [0, 0, 0]; f.forEach(j => { c[0] += S.v[j][0]; c[1] += S.v[j][1]; c[2] += S.v[j][2]; });
    if (c[0] * S.n[i][0] + c[1] * S.n[i][1] + c[2] * S.n[i][2] <= 0) dentro++; });
  out.solidos[nome] = { V: S.v.length, A: ar.size, F: S.f.length, lados: [...new Set(S.f.map(f => f.length))],
                        arestas: [...ar.values()], raios: S.v.map(v => Math.hypot(v[0], v[1], v[2])), normais_para_dentro: dentro };
}
console.log(JSON.stringify(out));
"""


def test_solidos_sao_os_cinco_de_platao_e_o_tetraedro_das_tradicoes_e_regular(root):
    """A forma é dado (cada tradição tem o seu sólido): conferir a geometria, não confiar no olho.

    Vértices, arestas e faces de cada sólido, relação de Euler, arestas todas iguais, vértices na
    esfera unitária e faces orientadas para fora (o sombreamento depende disso). E o tetraedro
    que posiciona as obras: quatro vértices equidistantes, com o centro na origem.
    """
    node = shutil.which("node")
    if not node:
        pytest.skip("node ausente")
    r = subprocess.run([node, "-e", _CONFERE_SOLIDOS, os.path.join(root, "src", "espaco3d.js")],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    d = json.loads(r.stdout)
    esperado = {"tetra": (4, 6, 4, 3), "cubo": (8, 12, 6, 4), "octa": (6, 12, 8, 3),
                "icosa": (12, 30, 20, 3), "dodeca": (20, 30, 12, 5)}
    assert set(d["solidos"]) == set(esperado)
    for nome, (v, a, f, lados) in esperado.items():
        s = d["solidos"][nome]
        assert (s["V"], s["A"], s["F"], s["lados"]) == (v, a, f, [lados]), nome
        assert s["V"] - s["A"] + s["F"] == 2, nome
        assert max(s["arestas"]) - min(s["arestas"]) < 1e-9, f"{nome}: arestas desiguais"
        assert all(abs(x - 1) < 1e-9 for x in s["raios"]), f"{nome}: vértice fora da esfera unitária"
        assert s["normais_para_dentro"] == 0, f"{nome}: face virada para dentro"
    assert d["formas"] == ["icosa", "cubo", "tetra", "octa"]      # na ordem dos eixos: Cyb, Reg, PolInd, Cplx
    vs = d["vertices"]
    dist = [sum((vs[i][k] - vs[j][k]) ** 2 for k in range(3)) ** 0.5 for i in range(4) for j in range(i + 1, 4)]
    assert max(dist) - min(dist) < 1e-9 and abs(dist[0] - 100) < 1e-9
    assert all(abs(sum(v[k] for v in vs)) < 1e-9 for k in range(3))
    assert d["teto"] == 5                                          # o teto de afastamento que a página declara

# ── no navegador (pulam sem Playwright, como os demais testes headless do repositório) ──

def _uri(root, nome):
    return pathlib.Path(os.path.join(root, "docs", nome)).resolve().as_uri()


def test_navegacao_cabe_no_celular_headless(pagina, root):
    """Quatro abas na barra do topo: nenhuma tela rola para o lado nem corta aba em 360 e 390 px.

    Com três abas a barra cabia; a quarta fez o relatório e o explorador passarem da largura
    do celular. Este teste trava a correção (abas compactas, marca recolhida, quebra de linha).
    """
    pytest.importorskip("playwright", reason="Playwright não instalado")
    from playwright.sync_api import sync_playwright
    ruins = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            for largura in (320, 360, 390):
                for nome in _telas(root):
                    ctx = b.new_context(viewport={"width": largura, "height": 800}, has_touch=True, is_mobile=True)
                    pg = ctx.new_page()
                    pg.goto(_uri(root, nome))
                    pg.wait_for_timeout(400)
                    m = pg.evaluate(
                        "() => ({pagina: document.documentElement.scrollWidth,"
                        " abas: [...document.querySelectorAll('.sd-tela')].map(a => {"
                        " const r = a.getBoundingClientRect(); return [a.textContent.trim(), r.left, r.right, r.height]; })})")
                    ctx.close()
                    if m["pagina"] > largura:
                        ruins.append(f"{nome}: página com {m['pagina']} px em tela de {largura} px")
                    if len(m["abas"]) != len(_telas(root)):
                        ruins.append(f"{nome}: {len(m['abas'])} abas em {largura} px")
                    for rotulo, esq, dire, alt in m["abas"]:
                        if esq < 0 or dire > largura + 0.5:
                            ruins.append(f"{nome}: aba {rotulo} cortada em {largura} px")
                        if alt < 44:
                            ruins.append(f"{nome}: aba {rotulo} com {alt:.0f} px de altura (alvo de toque < 44)")
        finally:
            b.close()
    assert not ruins, "; ".join(ruins)


def test_cena_abre_por_endereco_e_declara_empate_headless(pagina, root, cena):
    """O endereço guarda a vista: abrir com lente e obra no endereço restaura as duas; trocar de
    lente regrava o endereço; e a obra de rótulo inferido com empate diz que há empate."""
    pytest.importorskip("playwright", reason="Playwright não instalado")
    from playwright.sync_api import sync_playwright
    empatadas = [n["i"] for n in cena["nos"] if not n["o"] and "e" in n]
    if not empatadas:
        pytest.skip("nenhuma obra de rótulo inferido com empate nesta rede")
    erros = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            pg.on("pageerror", lambda e: erros.append(str(e)))
            pg.goto(_uri(root, "espaco.html") + "#lente=prov&obra=" + empatadas[0])
            pg.wait_for_timeout(900)
            lente = pg.evaluate("() => window.__espaco.lente()")
            selecao = pg.evaluate("() => { const s = window.__espaco.cena.selecao(); return s.t === 'no' ? window.__espaco.dados.nos[s.i].i : null; }")
            painel = pg.evaluate("() => { const d = document.getElementById('detalhe'); return d.hidden ? '' : d.textContent; }")
            vazios = pg.evaluate("() => [...document.querySelectorAll('[data-n]')].filter(e => !e.textContent.trim()).map(e => e.getAttribute('data-n'))")
            pg.click('#lentes button[data-lente="agenda"]')
            pg.wait_for_timeout(300)
            endereco = pg.evaluate("() => location.hash")
        finally:
            b.close()
    assert not erros, erros
    assert lente == "prov" and selecao == empatadas[0]
    assert "Empate na vizinhança" in painel
    assert not vazios, f"números sem valor na página: {vazios}"
    assert "lente=agenda" in endereco


def test_endereco_malformado_nao_quebra_headless(pagina, root):
    """Um link estragado (codificação inválida, lente ou obra que não existem) abre a cena no
    estado inicial em vez de derrubar a página."""
    pytest.importorskip("playwright", reason="Playwright não instalado")
    from playwright.sync_api import sync_playwright
    erros = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        try:
            pg = b.new_page(viewport={"width": 1280, "height": 800})
            pg.on("pageerror", lambda e: erros.append(str(e)))
            pg.goto(_uri(root, "espaco.html") + "#lente=nao-existe&obra=%E0%A4%A&peso=abc&sem=Foo,,&triade=-5&linhas=zzz&=x&solto")
            pg.wait_for_timeout(700)
            estado = pg.evaluate("() => ({lente: window.__espaco && window.__espaco.lente(), sel: window.__espaco && window.__espaco.cena.selecao().t,"
                                 " pintada: document.getElementById('cena').width > 0})")
            pg.click('#lentes button[data-lente="tempo"]')
            pg.wait_for_timeout(300)
            depois = pg.evaluate("() => window.__espaco.lente()")
        finally:
            b.close()
    assert not erros, erros
    assert estado == {"lente": "silos", "sel": "", "pintada": True}
    assert depois == "tempo"
