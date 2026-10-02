"""Testes offline (sem rede): normalização, rótulo de diretoria, log-odds, grafo-linha s."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from analysis import log_odds, s_line_components  # noqa: E402
from common import item_directorates, loose_key, name_key  # noqa: E402


def test_name_key_inverted_and_direct_agree():
    assert name_key("Gomide, Alexandre de Ávila") == ("gomide", "alexandre de avila")
    assert name_key("Alexandre de Ávila Gomide") == ("gomide", "alexandre de avila")


def test_name_key_suffix_and_roles():
    assert name_key("Alberto Luis Araujo Silva Filho")[0] == "silva filho"
    assert name_key("Gomide, Alexandre de Ávila (Organizador)") == ("gomide", "alexandre de avila")
    assert loose_key("Gomide, Alexandre") == loose_key("Gomide, Alexandre de Ávila")
    assert name_key("Fernanda De Negri") == name_key("De Negri, Fernanda")
    assert loose_key("Negri, Fernanda De") == loose_key("De Negri, Fernanda")


def test_directorate_from_editorial_fields_only():
    nt = {"title_alt": ["Nota Técnica n. 62 (Diest) : Subsídios para uma reforma"]}
    assert item_directorates(nt) == ["DIEST"]
    radar = {"publisher": ["Diretoria de Estudos e Políticas Setoriais de Inovação, Regulação e Infraestrutura (Diset)"]}
    assert item_directorates(radar) == ["DISET"]
    # menção no título/resumo NÃO rotula
    assert item_directorates({"title": ["Políticas setoriais e a Diest"], "abstract": ["Diset"]}) == []


def test_log_odds_sign():
    a = {"regulacao": 30, "estado": 5}
    b = {"regulacao": 5, "estado": 30}
    z = log_odds(a, b, {"regulacao": 35, "estado": 35})
    assert z["regulacao"] > 2 and z["estado"] < -2


def test_s_line_components():
    edges = [{1, 2, 3}, {3, 4}, {2, 3, 5}, {9}]
    c1 = s_line_components(edges, 1)
    assert c1[0] == c1[1] == c1[2] and c1[3] != c1[0]
    c2 = s_line_components(edges, 2)
    assert c2[0] == c2[2] and c2[1] != c2[0]
