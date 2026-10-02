"""Testes offline (sem rede): normalização, rótulo de diretoria, log-odds, grafo-linha s,
overrides de lotação e precisão da validação."""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "src"))
from analysis import log_odds, s_line_components  # noqa: E402
from common import item_directorates, loose_key, name_key  # noqa: E402
from membership import (apply_override, audit, load_overrides,  # noqa: E402
                        resolve_override)


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


def _overrides(records):
    path = os.path.join(tempfile.mkdtemp(), "membership_overrides.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"records": records}, f, ensure_ascii=False)
    return load_overrides(path)


def test_override_vence_inferencia_e_casa_por_nome():
    ovs = _overrides([
        {"author_id": "ipea:1", "status": "corrigido", "diretoria": "DISET"},
        {"name": "Gomide, Alexandre de Ávila", "status": "confirmado"},
        {"author_id": "ext:x", "status": "fora"},
    ])
    r = resolve_override(ovs, "ipea:1", "Qualquer, Nome")
    assert apply_override(r, "DIEST", "forte") == ("DISET", "validada")
    # casa pelo nome, inclusive em variante direta/invertida
    r = resolve_override(ovs, "ipea:9", "Alexandre de Ávila Gomide")
    assert apply_override(r, "DIEST", "moderada") == ("DIEST", "validada")
    r = resolve_override(ovs, "ext:x", "Alguém")
    assert apply_override(r, "DISET", "moderada") == (None, "validada_fora")
    # sem override e 'desconhecido' não mexem na inferência
    assert apply_override(None, "DIEST", "moderada") == ("DIEST", "moderada")
    r = resolve_override(_overrides([{"name": "X, Y", "status": "desconhecido"}]), "a", "X, Y")
    assert apply_override(r, "DIEST", "moderada") == ("DIEST", "moderada")


def test_override_malformado_quebra():
    for bad in ([{"author_id": "a", "status": "talvez"}],
                [{"author_id": "a", "status": "corrigido"}],  # sem diretoria
                [{"author_id": "a", "status": "corrigido", "diretoria": "DIXXX"}],
                [{"status": "confirmado"}]):  # sem chave
        try:
            _overrides(bad)
        except ValueError:
            continue
        raise AssertionError(f"deveria ter quebrado: {bad}")


def test_audit_precisao_por_estrato():
    authors = {
        "a": {"name": "A", "diretoria": "DIEST", "inferred_diretoria": "DIEST",
              "inferred_confidence": "forte", "validation": "confirmado"},
        "b": {"name": "B", "diretoria": "DISET", "inferred_diretoria": "DIEST",
              "inferred_confidence": "moderada", "validation": "corrigido"},
        "c": {"name": "C", "diretoria": None, "inferred_diretoria": "DISET",
              "inferred_confidence": "moderada", "validation": "fora"},
        "d": {"name": "D", "diretoria": "DISET", "inferred_diretoria": "DISET",
              "inferred_confidence": "moderada", "validation": "desconhecido"},
        "e": {"name": "E", "diretoria": "DIEST", "inferred_diretoria": "DIEST",
              "inferred_confidence": "forte", "validation": None},
    }
    a = audit(authors, save=False)
    assert a["n_decididos"] == 3 and a["n_confirmados"] == 1
    assert a["precisao"] == round(1 / 3, 3)
    assert a["por_confianca"]["forte"] == {"n": 1, "confirmados": 1, "precisao": 1.0}
    assert a["por_confianca"]["moderada"]["precisao"] == 0.0
    assert [x["name"] for x in a["corrigidos"]] == ["B"]
    assert [x["name"] for x in a["fora"]] == ["C"]
    assert a["n_desconhecido"] == 1 and a["status"] == "parcial"
    assert audit({k: dict(v, validation=None) for k, v in authors.items()},
                 save=False)["status"] == "pendente"


def test_s_line_components():
    edges = [{1, 2, 3}, {3, 4}, {2, 3, 5}, {9}]
    c1 = s_line_components(edges, 1)
    assert c1[0] == c1[1] == c1[2] and c1[3] != c1[0]
    c2 = s_line_components(edges, 2)
    assert c2[0] == c2[2] and c2[1] != c2[0]


def main():
    """Executor mínimo (só stdlib) para `python tests/test_core.py`, sem depender de pytest."""
    import traceback
    tests = [(n, f) for n, f in sorted(globals().items())
             if n.startswith("test_") and callable(f)]
    fails = 0
    for n, f in tests:
        try:
            f()
        except Exception:
            fails += 1
            print(f"FALHOU {n}", file=sys.stderr)
            traceback.print_exc()
    print(f"{len(tests) - fails}/{len(tests)} testes passaram", file=sys.stderr)
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
