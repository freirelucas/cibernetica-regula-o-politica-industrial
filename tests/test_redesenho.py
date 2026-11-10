"""Redesenho — critérios de aceitação executáveis.

Os testes da primeira parte valem desde já: guardam o próprio sistema de desenho. Os da segunda
parte ficam em espera (skip) até a peça correspondente ser construída e passam a valer sozinhos
quando ela aparece. A ordem de construção está em design/PLANO.md; cada etapa diz qual teste
daqui deixa de pular quando ela termina.
"""
import importlib.util
import os
import re
import shutil
import subprocess

import pytest


def _le(root, *partes):
    with open(os.path.join(root, *partes), encoding="utf-8") as f:
        return f.read()


def _prototipos(root):
    """Carrega design/ferramentas/gera_prototipos.py: é a implementação de referência dos dados."""
    caminho = os.path.join(root, "design", "ferramentas", "gera_prototipos.py")
    spec = importlib.util.spec_from_file_location("gera_prototipos", caminho)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ───────────────────────── parte 1: o sistema de desenho (vale desde já) ─────────────────────────

def test_cores_de_texto_tem_contraste(root):
    """Toda ficha usada como cor de texto passa de 4,5:1 sobre papel e sobre superfície."""
    gp = _prototipos(root)
    cores = gp.fichas_de_cor(_le(root, "design", "sistema.css"))
    texto = [k for k in cores if k.endswith("-texto") or k in ("apagado", "tinta", "nota", "alerta")]
    assert len(texto) >= 8, texto
    fracas = {k: round(min(gp.contraste(cores[k], cores["papel"]), gp.contraste(cores[k], cores["superficie"])), 2) for k in texto}
    assert all(v >= 4.5 for v in fracas.values()), {k: v for k, v in fracas.items() if v < 4.5}


def test_sistema_so_usa_pesos_vendorizados(root):
    """DM Sans só existe em 300, 400 e 500 no sítio: pedir 600 ou 700 gera negrito falso."""
    css = re.sub(r"/\*.*?\*/", "", _le(root, "design", "sistema.css"), flags=re.S)
    for regra in re.findall(r"[^{}]+\{[^{}]*\}", css):
        seletor, corpo = regra.split("{", 1)
        pesos = [int(p) for p in re.findall(r"font(?:-weight)?:\s*(?:[a-z]+\s+)*?([1-9]00)\b", corpo)]
        serifa = "--sd-serifa" in corpo
        mono = "--sd-mono" in corpo
        for p in pesos:
            permitidos = (300, 400, 600) if serifa else (400, 500) if mono else (300, 400, 500, 600)
            assert p in permitidos, f"peso {p} em {seletor.strip()[:60]}"
            if p == 600:
                assert serifa, f"peso 600 fora da serifa em {seletor.strip()[:60]}"


def test_sistema_nao_carrega_nada_de_fora(root):
    css = _le(root, "design", "sistema.css")
    assert "@import" not in css and not re.search(r"url\(\s*['\"]?https?:", css)


def test_glifos_saem_da_geometria_do_motor(root):
    """Os cinco sólidos do sistema são gerados de src/espaco3d.js, não desenhados à mão."""
    svg = _le(root, "design", "solidos.svg")
    assert sorted(re.findall(r'<symbol id="sd-sol-([a-z]+)"', svg)) == ["cubo", "dodeca", "icosa", "octa", "tetra"]
    node = shutil.which("node")
    if not node:
        pytest.skip("node ausente: não dá para regerar os glifos")
    r = subprocess.run([node, os.path.join(root, "design", "ferramentas", "gera_glifos.js")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert _le(root, "design", "solidos.svg") == svg, "design/solidos.svg foi editado à mão ou a geometria mudou: rode o gerador"


def test_prototipos_nao_trazem_numero_digitado(root):
    """Nos modelos, número é marcador {{caminho}}: o protótipo ensina a ler o dado, não a digitá-lo."""
    for nome in sorted(os.listdir(os.path.join(root, "design", "modelos"))):
        corpo = re.sub(r"<style>.*?</style>|<script>.*?</script>|<svg.*?</svg>", "", _le(root, "design", "modelos", nome), flags=re.S)
        texto = re.sub(r"<[^>]+>|\{\{[^{}]+\}\}", " ", corpo)
        soltos = [n for n in re.findall(r"(?<![\w.,])\d[\d.,]*\d|(?<![\w.,])\d(?![\w.,])", texto)
                  if n not in ("1", "2", "3", "5", "44", "68", "300", "400", "500", "320")]
        assert not soltos, f"{nome}: número fora de marcador {soltos[:6]}"


def test_dados_da_nota_fecham_com_a_cena(root):
    """A referência de dados da página A nota é coerente com a cena e com a bibliografia."""
    import build_site
    import espaco
    cena = espaco.dados(build_site.explorer_network())
    if not cena["nota"]:
        pytest.skip("data/td_referencias.json ausente")
    n = _prototipos(root).dados_nota(cena)
    assert n["n_no_nucleo"] + n["n_fora"] == n["n_obras"] and len(n["atos"]) == n["n_atos"]
    assert sum(n["por_eixo"]) == n["n_no_nucleo"] == n["n_observado"] + n["n_inferido"]
    ids = {x["i"] for x in cena["nos"]}
    for o in n["obras"]:
        assert set(o["ids"]) <= ids and o["id"] in o["ids"]
        assert len(o["viz"]) <= 4 and all(v["id"] not in o["ids"] for v in o["viz"])
        assert [v["peso"] for v in o["viz"]] == sorted((v["peso"] for v in o["viz"]), reverse=True)
    assert 0 < n["n_triades_sem_inferencia"] <= n["n_triades"] <= len(cena["triades"])


# ───────────────────────── parte 2: a construção (cada teste acorda quando a peça existe) ─────────────────────────

def _docs(root, nome):
    return os.path.join(root, "docs", nome)


def test_etapa1_sistema_publicado(root):
    """Etapa 1: src/sistema.css é a cópia fiel de design/sistema.css, vai para docs/ e todas as telas o carregam."""
    if not os.path.exists(os.path.join(root, "src", "sistema.css")):
        pytest.skip("etapa 1 ainda não construída (src/sistema.css)")
    import build_site
    assert build_site.main() == 0
    assert _le(root, "src", "sistema.css") == _le(root, "design", "sistema.css")
    assert _le(root, "docs", "sistema.css") == _le(root, "src", "sistema.css")
    for nome in ("index.html", "explorador.html", "espaco.html", "triagem.html"):
        pagina = _le(root, "docs", nome)
        assert 'href="sistema.css"' in pagina, nome
        assert 'id="sd-sol-dodeca"' in pagina, f"{nome}: bloco de sólidos não embutido"


def test_etapa2_barra_nova_em_todas_as_telas(root):
    """Etapa 2: a mesma barra do sistema, com as telas existentes na mesma ordem, em todas as páginas.
    Com a etapa 3 construída, a lista passa a ter cinco telas e este teste cobre também a nova."""
    if 'class="sd-tela"' not in _le(root, "docs", "index.html"):
        pytest.skip("etapa 2 ainda não construída (barra sd-telas)")
    ordem = [n for n in ("index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html")
             if os.path.exists(_docs(root, n))]
    assert len(ordem) >= 4, ordem
    for nome in ordem:
        pagina = _le(root, "docs", nome)
        abas = re.findall(r'<a class="sd-tela"[^>]*href="([^"]+)"', pagina)
        assert abas == ordem, f"{nome}: {abas}"
        atual = re.findall(r'<a class="sd-tela"[^>]*href="([^"]+)"[^>]*aria-current="page"', pagina)
        assert atual == [nome], f"{nome}: tela atual marcada como {atual}"
        assert "gnav-tab" not in pagina, f"{nome}: sobrou a barra antiga"
        assert 'class="sd-marca"' in pagina, f"{nome}: sem a marca comum"


def test_etapa3_dados_da_nota_iguais_a_referencia(root):
    """Etapa 3: src/nota.py devolve exatamente o que a referência de desenho devolve."""
    if not os.path.exists(os.path.join(root, "src", "nota.py")):
        pytest.skip("etapa 3 ainda não construída (src/nota.py)")
    import build_site
    import espaco
    import nota
    cena = espaco.dados(build_site.explorer_network())
    assert nota.dados(cena) == _prototipos(root).dados_nota(cena)


def test_etapa3_pagina_da_nota(root):
    """Etapa 3: docs/nota.html traz todas as obras, nenhum número vazio e nenhuma carga externa."""
    if not os.path.exists(os.path.join(root, "src", "nota_template.html")):
        pytest.skip("etapa 3 ainda não construída (src/nota_template.html)")
    import build_site
    import espaco
    assert build_site.main() == 0
    pagina = _le(root, "docs", "nota.html")
    n = _prototipos(root).dados_nota(espaco.dados(build_site.explorer_network()))
    assert pagina.count('class="sd-obra"') == n["n_no_nucleo"]
    assert not re.search(r"\{\{|__[A-Z_]+__", pagina), "marcador sem valor na página"
    assert not re.findall(r'<(?:script|link|img|iframe)[^>]*(?:src|href)="(?:https?:)?//[^"]+"', pagina)
    assert "espaco.html#lente=nota" in pagina
    assert _prosa_sem_anglicismo(pagina) == []


def _prosa_sem_anglicismo(pagina):
    """Varre a prosa da tela, sem as referências bibliográficas: título de obra em outra língua
    é citação, não anglicismo, e não pode ser "corrigido"."""
    from test_anglicismos import _scan, _strip_html
    prosa = re.sub(r'<p class="sd-obra-ref">.*?</p>|<ul class="sd-vizinhas">.*?</ul>|<ol class="nota-lista">.*?</ol>',
                   " ", pagina, flags=re.S)
    return _scan(_strip_html(prosa))


def test_prototipos_sem_anglicismo(root):
    """O que o construtor vai copiar já tem de passar na varredura do projeto."""
    for nome in sorted(os.listdir(os.path.join(root, "design", "prototipos"))):
        assert _prosa_sem_anglicismo(_le(root, "design", "prototipos", nome)) == [], nome


def test_etapa4_numeros_da_abertura_vem_dos_derivados(root):
    """Etapa 4: a modularidade e o escore z da abertura deixam de ser digitados no modelo."""
    modelo = _le(root, "src", "site_template.html")
    if "sd-portas" not in modelo:
        pytest.skip("etapa 4 ainda não construída (entrada com as três portas)")
    for digitado in ("0,59", "≈&nbsp;80", "0,5–0,6"):
        assert digitado not in modelo, f"número digitado na prosa do modelo: {digitado}"
    import json
    mc = json.load(open(os.path.join(root, "data", "modularity_check.json"), encoding="utf-8"))["tres_eixos"]
    pagina = _le(root, "docs", "index.html")
    assert f"{mc['Q_obs']:.3f}".replace(".", ",") in pagina
    assert "class=\"preliminar\"" not in pagina and "sd-estado" in pagina
