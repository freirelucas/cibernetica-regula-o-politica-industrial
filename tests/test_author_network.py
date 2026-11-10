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


# ── comunidades: o caminho sem igraph/leidenalg (é o da integração contínua) ──

def _dois_grupos():
    """Dois grupos de cinco autores, todos ligados entre si, unidos por uma única coautoria."""
    a = [f"A{i}" for i in range(5)]
    b = [f"B{i}" for i in range(5)]
    viz = {n: set() for n in a + b + ["SOZINHO"]}
    for g in (a, b):
        for x in g:
            viz[x] |= set(g) - {x}
    viz["A0"].add("B0")
    viz["B0"].add("A0")
    return a, b, viz


def test_reserva_separa_grupos_e_e_deterministica():
    """A reserva tem de ser detecção de comunidade de verdade e dar sempre a mesma resposta."""
    import author_network as an
    a, b, viz = _dois_grupos()
    nos = sorted(viz)
    c1 = an._louvain(nos, viz)
    assert len({c1[x] for x in a}) == 1 and len({c1[x] for x in b}) == 1
    assert c1[a[0]] != c1[b[0]], "dois grupos unidos por uma só coautoria não podem virar um"
    assert sorted(set(c1.values())) == [0, 1, 2]                 # numeração contígua
    assert (c1["A0"], c1["B0"], c1["SOZINHO"]) == (0, 1, 2)      # maior primeiro; empate pelo nome
    # a ordem em que as vizinhas chegam não pode mudar o resultado
    assert c1 == an._louvain(nos, {k: sorted(v, reverse=True) for k, v in viz.items()})
    assert c1 == an._louvain(nos, {k: sorted(v) for k, v in viz.items()})


def test_reserva_termina_em_escala():
    """A integração contínua roda sem leidenalg: a reserva não pode ser superlinear.

    Uma versão anterior (Clauset-Newman-Moore em Python puro) estourava os 30 minutos do
    run_all com ~147 mil autores. Aqui, 60 mil autores em grupos de seis, encadeados por uma
    coautoria, têm de fechar com muita folga; o teto de tempo é largo de propósito, só para
    acusar regressão de ordem. Não se exige um grupo por comunidade: a modularidade tem
    limite de resolução e junta grupos vizinhos numa cadeia longa (o Leiden faz o mesmo).
    Exige-se que nenhum grupo seja partido e que a cadeia não vire uma comunidade só.
    """
    import time
    import author_network as an
    viz, grupos = {}, []
    for g in range(10_000):
        grupo = [f"G{g:05d}_{i}" for i in range(6)]
        grupos.append(grupo)
        for x in grupo:
            viz[x] = set(grupo) - {x}
        if g:                                                    # uma ponte para o grupo anterior
            viz[grupo[0]].add(f"G{g - 1:05d}_0")
            viz[f"G{g - 1:05d}_0"].add(grupo[0])
    t0 = time.time()
    c = an._louvain(sorted(viz), viz)
    assert time.time() - t0 < 120
    assert all(len({c[x] for x in grupo}) == 1 for grupo in grupos), "um grupo coeso foi partido"
    assert 50 <= len(set(c.values())) <= 10_000
