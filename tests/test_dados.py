"""Integridade do JSON-fonte e dos CSV exportados (cabeçalhos em PT)."""
import build_site

REQUIRED_KEYS = [
    "generated", "corpus_size", "n_seeds", "n_axes_1", "n_axes_2", "n_axes_3",
    "pct_with_refs", "cocit_nodes", "cocit_edges", "coupling_nodes", "coupling_edges",
    "n_clusters_cc", "n_clusters_bc", "n_pivotal", "n_bursts", "n_bursting_refs",
    "seeds", "top20_nonfeed", "top_bridges", "top_bursts", "sleeping_beauties",
    "temporal", "clusters_bc",
]

EXPECTED_HEADERS = {
    "00_registro_execucao.csv": "parametro,valor,descricao",
    "02_mais_citados.csv": "ano,citacoes,eixos,n_eixos,autores,titulo,veiculo",
    "03_obras_ponte.csv": "ano,citacoes,eixos,autores,titulo",
    "05_rajadas_kleinberg.csv": "id_ref,inicio,fim,peso,titulo,autores",
    "06_belas_adormecidas.csv": "ano,citacoes,B,t_m,eixos,titulo",
    "07_agrupamentos.csv": "id_agrupamento,rotulo,tamanho,titulo,citacoes,ano",
    "08_obras_semente.csv": "chave,id_openalex,referencia",
    "09_serie_temporal.csv": "ano,Cyb,Reg,PolInd",
}


def test_json_required_keys(results):
    for k in REQUIRED_KEYS:
        assert k in results, f"chave ausente no JSON: {k}"


def test_json_consistency(results):
    assert results["corpus_size"] == 817
    assert results["n_seeds"] == 10 == len(results["seeds"])
    assert len(results["top20_nonfeed"]) == 20
    assert len(results["temporal"]) == 49
    assert all({"year", "Cyb", "Reg", "PolInd"} <= set(t) for t in results["temporal"])
    assert all({"cluster_id", "label", "size", "top_papers"} <= set(c) for c in results["clusters_bc"])


def test_csv_headers_pt(results, tmp_path):
    build_site.write_csvs(results, str(tmp_path))
    for name, header in EXPECTED_HEADERS.items():
        p = tmp_path / name
        assert p.exists(), f"CSV não gerado: {name}"
        first = p.read_text(encoding="utf-8").splitlines()[0]
        assert first == header, f"{name}: cabeçalho {first!r} != esperado {header!r}"


def test_csv_rows(results, tmp_path):
    build_site.write_csvs(results, str(tmp_path))
    counts = {
        "02_mais_citados.csv": 20, "03_obras_ponte.csv": 15,
        "05_rajadas_kleinberg.csv": 20, "06_belas_adormecidas.csv": 15,
        "08_obras_semente.csv": 10, "09_serie_temporal.csv": 49,
    }
    for name, n in counts.items():
        linhas = (tmp_path / name).read_text(encoding="utf-8").strip().splitlines()
        assert len(linhas) == n + 1, f"{name}: {len(linhas)-1} linhas != {n}"
