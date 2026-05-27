"""Integridade do JSON-fonte e dos CSV exportados (cabeçalhos em PT)."""
import json
import os

import build_rayyan
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


def test_network_csv(root, tmp_path):
    net_src = os.path.join(root, "data", "network.json")
    if not os.path.exists(net_src):
        return
    net = json.load(open(net_src, encoding="utf-8"))
    assert build_site.write_network_csvs(net, str(tmp_path)) == 2
    nos = (tmp_path / "10_rede_nos.csv").read_text(encoding="utf-8").strip().splitlines()
    arr = (tmp_path / "11_rede_arestas.csv").read_text(encoding="utf-8").strip().splitlines()
    assert nos[0] == "id_openalex,obra,eixo,citacoes,ano,semente"
    assert arr[0] == "origem,destino,tipo,cocitacoes,forca_associacao"
    assert len(nos) - 1 == len(net["nodes"])
    assert len(arr) - 1 == len(net["links"])


def test_rayyan_export(tmp_path):
    import csv as _csv
    import re
    works = build_rayyan.build(str(tmp_path))
    assert len(works) > 100
    assert all(w["roles"] for w in works), "toda obra deve ter ao menos um papel"
    ris = (tmp_path / "rayyan_sintese.ris").read_text(encoding="utf-8")
    assert ris.count("TY  - ") == ris.count("ER  - ") == len(works)
    rows = list(_csv.DictReader(open(tmp_path / "rayyan_sintese.csv", encoding="utf-8")))
    assert len(rows) == len(works)
    assert {"title", "authors", "year", "doi", "keywords", "notes"} <= set(rows[0].keys())


def test_rayyan_ris_wellformed(tmp_path):
    """RIS válido para o Rayyan: toda linha não-vazia é uma tag; cada registro
    começa em TY e termina em ER (sem linha de continuação quebrada)."""
    import re
    build_rayyan.build(str(tmp_path))
    tag = re.compile(r"^([A-Z][A-Z0-9])  - ")
    rec_open = False
    for line in (tmp_path / "rayyan_sintese.ris").read_text(encoding="utf-8").splitlines():
        if line == "":
            continue
        assert tag.match(line), f"linha RIS inválida (continuação quebrada?): {line!r}"
        code = line[:2]
        if code == "TY":
            assert not rec_open, "novo TY antes de ER"
            rec_open = True
        elif code == "ER":
            assert rec_open, "ER sem TY"
            rec_open = False
        else:
            assert rec_open, f"tag {code} fora de um registro"
    assert not rec_open, "último registro sem ER"
