"""B.5 Gould-Fernandez brokerage roles + B.4 higher-order BC tests (Fase E)."""
import json
import os


def test_brokerage_json_keys(root):
    p = os.path.join(root, "data", "brokerage_roles.json")
    assert os.path.exists(p), "data/brokerage_roles.json deve existir após B.5"
    B = json.load(open(p, encoding="utf-8"))
    for k in ["summary", "top_by_cross_brokerage", "by_author"]:
        assert k in B, f"chave ausente: {k}"
    assert "role_totals" in B["summary"]
    assert "n_authors_per_role" in B["summary"]


def test_brokerage_at_least_one_author_per_role(root):
    p = os.path.join(root, "data", "brokerage_roles.json")
    B = json.load(open(p, encoding="utf-8"))
    napr = B["summary"]["n_authors_per_role"]
    # com corpus expandido, todos os 5 papéis G-F aparecem
    for role in ["coordinator", "gatekeeper", "representative",
                  "liaison", "itinerant"]:
        assert napr.get(role, 0) >= 1, f"≥1 autor em {role}"


def test_higher_order_bc_keys(root):
    p = os.path.join(root, "data", "higher_order_bc.json")
    assert os.path.exists(p), "data/higher_order_bc.json deve existir após B.4"
    H = json.load(open(p, encoding="utf-8"))
    for k in ["n_walks", "walk_length", "n_hyperedges", "top_30", "by_oa_id"]:
        assert k in H, f"chave ausente em higher_order_bc.json: {k}"
    assert len(H["top_30"]) >= 10
    # top-1 sempre tem centralidade > 0
    assert H["top_30"][0]["ho_centrality"] > 0


def test_brazil_expanded_keys(root):
    p = os.path.join(root, "data", "brazil_expanded.json")
    assert os.path.exists(p), "data/brazil_expanded.json deve existir após A.4"
    B = json.load(open(p, encoding="utf-8"))
    for k in ["n_faganello_seeds", "n_resolved_oa", "n_broad_results",
              "citation_bridges_top30", "resolved"]:
        assert k in B
    assert B["n_resolved_oa"] >= 50, "≥50 obras Faganello devem ser resolvidas"


def test_depth2_corpus_keys(root):
    p = os.path.join(root, "data", "depth2_corpus.json")
    assert os.path.exists(p), "data/depth2_corpus.json deve existir após A.3"
    D = json.load(open(p, encoding="utf-8"))
    assert "before" in D and "after" in D and "delta" in D
    assert D["after"]["works_with_authorships"] > D["before"]["works_with_authorships"]


def test_ho_bridge_tag_in_manifest(root):
    """A tag ponte de ordem superior deve estar documentada no manifest."""
    p = os.path.join(root, "data", "rayyan_tags.json")
    T = json.load(open(p, encoding="utf-8"))
    assert "ponte de ordem superior" in T["tags"]
    assert "TOP_N_HO_BC" in T["thresholds"]
    assert "MIN_HO_BC_SCORE" in T["thresholds"]
