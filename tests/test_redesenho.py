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


# ───────────────────────── parte 2: a construção (cada teste acorda quando a ordem é feita) ─────────────────────────
# Os nomes seguem o quadro de ordens (design/ordens/quadro.json): test_<ordem>_...

def _docs(root, nome):
    return os.path.join(root, "docs", nome)


def _constroi():
    import build_site
    assert build_site.main() == 0
    return build_site


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


def test_b1_sistema_publicado(root):
    """B1: src/sistema.css é a cópia fiel de design/sistema.css, vai para docs/ e todas as telas o carregam."""
    if not os.path.exists(os.path.join(root, "src", "sistema.css")):
        pytest.skip("ordem B1 ainda não feita (src/sistema.css)")
    _constroi()
    assert _le(root, "src", "sistema.css") == _le(root, "design", "sistema.css")
    assert _le(root, "docs", "sistema.css") == _le(root, "src", "sistema.css")
    for nome in ("index.html", "explorador.html", "espaco.html", "triagem.html"):
        pagina = _le(root, "docs", nome)
        assert 'href="sistema.css"' in pagina, nome
        assert 'id="sd-sol-dodeca"' in pagina, f"{nome}: bloco de sólidos não embutido"


def _telas(root):
    return [n for n in ("index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html")
            if os.path.exists(_docs(root, n))]


def test_b2_barra_nova_em_todas_as_telas(root):
    """B2: a mesma barra do sistema, com as telas existentes na mesma ordem, em todas as páginas."""
    if 'class="sd-tela"' not in _le(root, "docs", "index.html"):
        pytest.skip("ordem B2 ainda não feita (barra sd-telas)")
    ordem = _telas(root)
    assert len(ordem) >= 4, ordem
    for nome in ordem:
        pagina = _le(root, "docs", nome)
        abas = re.findall(r'<a class="sd-tela"[^>]*href="([^"]+)"', pagina)
        assert abas == ordem, f"{nome}: {abas}"
        atual = re.findall(r'<a class="sd-tela"[^>]*href="([^"]+)"[^>]*aria-current="page"', pagina)
        assert atual == [nome], f"{nome}: tela atual marcada como {atual}"
        assert "gnav-tab" not in pagina, f"{nome}: sobrou a barra antiga"
        assert 'class="sd-marca"' in pagina, f"{nome}: sem a marca comum"


def test_o0_marcadores(root):
    """O0: qualquer modelo pode usar {{caminho}}; marcador sem dado derruba a construção, não passa calado."""
    if not os.path.exists(os.path.join(root, "src", "marcadores.py")):
        pytest.skip("ordem O0 ainda não feita (src/marcadores.py)")
    import marcadores
    ctx = {"num": {"rede": {"n": 6340}, "silos": {"Q": 0.515, "Q_acaso": -0.005}}, "lista": [10, 20], "t": "a<b"}
    assert marcadores.monta("x {{num.rede.n}} y {{num.silos.Q|3}} z {{lista.1}} w {{num.silos.Q_acaso|3}} {{t}}", ctx, {}) == \
        "x 6.340 y 0,515 z 20 w -0,005 a&lt;b"
    assert marcadores.monta("{{bloco:x}}", ctx, {"x": "<b>ok</b>"}) == "<b>ok</b>"
    with pytest.raises((KeyError, IndexError)):
        marcadores.monta("{{num.nao.existe}}", ctx, {})
    import build_site
    assert build_site.resolver("a {{num.rede.n}} b {{corpus.n}} c {{nota.n_obras}}").count("{{") == 0
    _constroi()
    for nome in _telas(root):
        assert "{{" not in _le(root, "docs", nome), f"{nome}: marcador sem valor"


def test_o0_dados_da_nota_iguais_a_referencia(root):
    """O0: src/nota.py devolve exatamente o que a referência de desenho devolve."""
    if not os.path.exists(os.path.join(root, "src", "nota.py")):
        pytest.skip("ordem O0 ainda não feita (src/nota.py)")
    import build_site
    import espaco
    import nota
    cena = espaco.dados(build_site.explorer_network())
    assert nota.dados(cena) == _prototipos(root).dados_nota(cena)


def test_n1_pagina_da_nota(root):
    """N1: docs/nota.html traz todas as obras, nenhum marcador sem valor e nenhuma carga externa."""
    if not os.path.exists(os.path.join(root, "src", "nota_template.html")):
        pytest.skip("ordem N1 ainda não feita (src/nota_template.html)")
    bs = _constroi()
    import espaco
    pagina = _le(root, "docs", "nota.html")
    n = _prototipos(root).dados_nota(espaco.dados(bs.explorer_network()))
    assert pagina.count('class="sd-obra"') == n["n_no_nucleo"]
    assert pagina.count("<li>") >= n["n_fora"] + n["n_atos"]
    assert not re.search(r"\{\{|__[A-Z_]+__", pagina), "marcador sem valor na página"
    assert not re.findall(r'<(?:script|link|img|iframe)[^>]*(?:src|href)="(?:https?:)?//[^"]+"', pagina)
    assert 'href="espaco.html#lente=nota"' in pagina and "../" not in re.sub(r"<svg.*?</svg>", "", pagina, flags=re.S)
    assert 'href="nota.html" aria-current="page"' in pagina
    assert 'href="nota.html"' in _le(root, "docs", "espaco.html"), "a lente da nota não leva à lista completa"
    assert _prosa_sem_anglicismo(pagina) == []


def test_r1_entrada(root):
    """R1: o primeiro ecrã do relatório diz o achado com números vivos e oferece três portas."""
    modelo = _le(root, "src", "site_template.html")
    if "sd-portas" not in modelo:
        pytest.skip("ordem R1 ainda não feita (entrada com as três portas)")
    bs = _constroi()
    pagina = _le(root, "docs", "index.html")
    assert 'class="preliminar"' not in pagina and "startbox" not in pagina
    assert pagina.count('class="sd-estado"') == 1 and pagina.count('class="sd-porta"') == 3
    for destino in ('href="nota.html"', 'href="#pontes"', 'href="#discussao"'):
        assert destino in pagina, destino
    for unico in ('id="hero3d"', 'id="hero3d-link"', 'id="hero3d-n"', 'id="gen-date"'):
        assert pagina.count(unico) == 1, unico
    import json
    mc = json.load(open(os.path.join(root, "data", "modularity_check.json"), encoding="utf-8"))["tres_eixos"]
    assert f"{mc['Q_obs']:.3f}".replace(".", ",") in pagina
    assert "{{" not in pagina
    for sid in bs.SECTIONS:
        assert f'id="{sid}"' in pagina, f"seção perdida: {sid}"
    # Q≈0,59 e z≈80 são da rede interna de 600 nós do funil (METODOLOGIA §0): NÃO são para trocar
    assert modelo.count("0,59") == 3 and modelo.count("≈&nbsp;80") == 2, "os números do corpo do relatório não são desta ordem"
    assert _prosa_sem_anglicismo(pagina) == []


def test_e1_explorador(root):
    """E1: o explorador usa as peças e o vocabulário do sistema, e a cena d3 continua de pé."""
    modelo = _le(root, "src", "explorador_template.html")
    if "sd-chip" not in modelo:
        pytest.skip("ordem E1 ainda não feita (explorador com sd-chip)")
    _constroi()
    pagina = _le(root, "docs", "explorador.html")
    assert "alvos)" not in modelo and "Só as pontes" not in modelo, "vocabulário antigo ('alvos', 'só as pontes')"
    assert "obras da agenda" in modelo
    assert "text-transform:uppercase" not in modelo, "rótulo em caixa-alta"
    assert "espaco.html#lente=silos&obra=" in modelo or "espaco.html#lente=silos&amp;obra=" in modelo
    for peca in ("sd-chip", "sd-campo", "sd-botao", "sd-sobre"):
        assert peca in pagina, peca
    assert 'id="graph"' in pagina and "{{" not in pagina


def test_t1_triagem(root):
    """T1: a triagem usa as peças e o vocabulário do sistema; os cartões continuam sendo .card."""
    modelo = _le(root, "src", "triagem_template.html")
    if "sd-cartao" not in modelo:
        pytest.skip("ordem T1 ainda não feita (triagem com sd-cartao)")
    _constroi()
    pagina = _le(root, "docs", "triagem.html")
    for peca in ("sd-cartao", "sd-selo", "sd-medidas", "sd-botao", "sd-chip"):
        assert peca in modelo, peca
    assert "text-transform:uppercase" not in modelo, "rótulo em caixa-alta"
    assert "function fmtBR" in modelo, "falta a função única de número com vírgula decimal"
    assert not re.search(r"toFixed\(\d\)\s*}</b>", modelo), "número exibido com ponto decimal"
    assert "alvos de agenda" not in modelo and "alvo de agenda" not in modelo, "vocabulário antigo"
    assert "class=\"card" in modelo or "'card" in modelo or '"card' in modelo
    assert "{{" not in pagina


def test_i1_cinco_telas_na_barra(root):
    """I1: depois da integração, as cinco telas existem e estão todas na barra."""
    if not (os.path.exists(_docs(root, "nota.html")) and "sd-portas" in _le(root, "docs", "index.html")):
        pytest.skip("ordem I1 ainda não feita (docs/ com a nota e a entrada)")
    assert _telas(root) == ["index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html"]
    for nome in _telas(root):
        assert len(re.findall(r'<a class="sd-tela"', _le(root, "docs", nome))) == 5, nome


def test_r2_corpo(root):
    """R2: capas de ato, registros e destaques do sistema, sem perder seção nem mexer em número."""
    modelo = _le(root, "src", "site_template.html")
    if "sd-ato" not in modelo:
        pytest.skip("ordem R2 ainda não feita (capas de ato)")
    bs = _constroi()
    pagina = _le(root, "docs", "index.html")
    atos = re.findall(r"<details[^>]*class=\"[^\"]*\bsd-ato\b[^\"]*\"[^>]*>\s*<summary>(.*?)</summary>", pagina, flags=re.S)
    assert len(atos) == 7, f"{len(atos)} capas de ato"
    for cap in atos:
        assert 'class="sd-ato-n"' in cap and 'class="sd-ato-t"' in cap, cap[:80]
    soltos = re.findall(r'class="callout(?![^"]*sd-destaque)[^"]*"', pagina)
    assert not soltos, f"destaque fora do sistema: {soltos[:3]}"
    assert pagina.count("sd-aparato") >= 2
    for sid in bs.SECTIONS:
        assert f'id="{sid}"' in pagina, f"seção perdida: {sid}"
    assert modelo.count("0,59") == 3 and modelo.count("≈&nbsp;80") == 2, "número do corpo alterado"
    assert "{{" not in pagina and _prosa_sem_anglicismo(pagina) == []


def test_f1_documentacao(root):
    """F1: a documentação conta as cinco telas e o plano aponta que a construção terminou."""
    leia = _le(root, "README.md")
    if "nota.html" not in leia:
        pytest.skip("ordem F1 ainda não feita (README com a tela A nota)")
    assert "nota.html" in _le(root, ".claude", "skills", "run-scisci-ipea", "SKILL.md")
    assert "A nota" in _le(root, "METODOLOGIA.md")
    for nome in ("index.html", "nota.html", "espaco.html", "explorador.html", "triagem.html"):
        assert os.path.exists(_docs(root, nome)), nome
