"""Valida estrutura e conteúdo da Fase D (author network completo + tag Rayyan)."""
import json
import os


def test_author_network_keys(root):
    p = os.path.join(root, "data", "author_network.json")
    assert os.path.exists(p), "data/author_network.json deve existir após Fase D"
    A = json.load(open(p, encoding="utf-8"))
    for k in ["n_authors", "n_cross_axis_strict", "n_cross_axis_loose",
              "n_communities", "n_works_analyzed", "top_cross_axis", "authors"]:
        assert k in A, f"chave ausente em author_network.json: {k}"
    assert isinstance(A["top_cross_axis"], list)
    assert len(A["top_cross_axis"]) >= 10, "top_cross_axis deve listar pelo menos 10"


def test_top_cross_axis_scored(root):
    p = os.path.join(root, "data", "author_network.json")
    A = json.load(open(p, encoding="utf-8"))
    top30 = A["top_cross_axis"][:30]
    # primeiro autor sempre tem score > 0 (do contrário não haveria ranking)
    assert top30[0]["cross_axis_score"] > 0, "top-1 deve ter score > 0"
    for entry in top30:
        assert "oa_id" in entry and entry["oa_id"].startswith("A"), \
            "cada autor no top-30 deve ter OA id válido (A...)"
        assert "n_per_axis" in entry
        assert set(entry["n_per_axis"].keys()) == {"Cyb", "Reg", "PolInd"}


def test_author_bridge_tag_applied(root):
    """Pelo menos uma obra exportada no Rayyan deve ter a tag obra de autor-ponte."""
    csv_path = os.path.join(root, "docs", "dados", "rayyan_sintese.csv")
    assert os.path.exists(csv_path)
    content = open(csv_path, encoding="utf-8").read()
    assert "obra de autor-ponte" in content, \
        "tag obra de autor-ponte deve aparecer em rayyan_sintese.csv"


def test_author_bridge_in_manifest(root):
    """O manifest deve documentar a tag obra de autor-ponte com sua fonte."""
    p = os.path.join(root, "data", "rayyan_tags.json")
    T = json.load(open(p, encoding="utf-8"))
    assert "obra de autor-ponte" in T["tags"]
    assert "TOP_N_AUTHOR_BRIDGES" in T["thresholds"]
    assert "MIN_CROSS_AXIS_SCORE" in T["thresholds"]


def test_snowball_and_adjacent_files(root):
    snow = os.path.join(root, "data", "author_snowball_expansion.json")
    adj = os.path.join(root, "data", "adjacent_tradition_probes.json")
    assert os.path.exists(snow), "snowball por autor (Fase D) deve estar persistido"
    assert os.path.exists(adj), "sondagem de tradições adjacentes (Fase D) deve estar persistida"
    S = json.load(open(snow, encoding="utf-8"))
    assert "by_author" in S and "summary" in S
    A = json.load(open(adj, encoding="utf-8"))
    assert "probes" in A
    for key in ["polanyi", "schumpeter", "hirschman",
                "complexity_economics", "governmentality"]:
        assert key in A["probes"], f"probe ausente: {key}"
