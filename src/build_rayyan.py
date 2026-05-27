#!/usr/bin/env python3
"""Gera o material de entrada para o Rayyan — a "grande síntese" para triagem.

Consolida, sem rede e a partir das fontes locais, todas as obras que o sistema
cienciométrico fez emergir (obras-semente, mais citadas, obras-ponte, rajadas e
belas adormecidas do núcleo global) com o corpus brasileiro de Claucia Faganello,
deduplica por título e anota cada referência com seu(s) eixo(s) e papel(éis).

Escreve em docs/dados/:
    rayyan_sintese.ris   formato RIS (importação recomendada no Rayyan)
    rayyan_sintese.csv   espelho em CSV (colunas compatíveis com o Rayyan)

Os três pesquisadores importam o arquivo no Rayyan (https://rayyan.ai) e fazem a
triagem colaborativa (incluir/excluir, etiquetas) já com eixo e papel anotados.

Uso:  python src/build_rayyan.py
"""
import csv
import json
import os
import re
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON_SRC = os.path.join(ROOT, "data", "scisci_results.json")
BRASIL = os.path.join(ROOT, "docs", "material-brasil", "dataset_politica_industrial_brasil.csv")
ENRICH = os.path.join(ROOT, "data", "openalex_enrich.json")
DADOS = os.path.join(ROOT, "docs", "dados")

AXMAP = {"Cyb": "Cibernética", "Reg": "Instrumentos de governo", "PolInd": "Política industrial"}


def _norm(t):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", (t or "").lower())).strip()


def _oneline(s):
    """Colapsa qualquer espaço em branco (inclusive quebras de linha) em um único
    espaço — garante que cada valor ocupe uma só linha lógica no RIS."""
    return re.sub(r"\s+", " ", (s or "")).strip()


def _axis_of_ref(ref):
    if any(x in ref for x in ("Beer", "Ashby", "Espejo")):
        return ["Cibernética"]
    if any(x in ref for x in ("Hood", "Margetts")):
        return ["Instrumentos de governo"]
    return ["Política industrial"]


def _axes(s):
    return [AXMAP[a] for a in (s or "").split(",") if a in AXMAP]


def _add(store, title, **kw):
    """Insere/funde uma obra no dicionário consolidado (dedup por título normalizado)."""
    key = _norm(title)
    if not key:
        return
    e = store.setdefault(key, {"title": title, "authors": [], "year": "", "doi": "", "url": "",
                               "venue": "", "abstract": "", "axes": set(), "roles": set(), "type": "GEN"})
    if len(title) > len(e["title"]):          # mantém o título mais completo
        e["title"] = title
    for fld in ("year", "doi", "url", "venue", "abstract"):
        if not e[fld] and kw.get(fld):
            e[fld] = kw[fld]
    if kw.get("type") and e["type"] == "GEN":
        e["type"] = kw["type"]
    if kw.get("authors"):
        e["authors"] = kw["authors"] if len(kw["authors"]) > len(e["authors"]) else e["authors"]
    e["axes"].update(kw.get("axes") or [])
    e["roles"].update(kw.get("roles") or [])


def consolidate():
    R = json.load(open(JSON_SRC, encoding="utf-8"))
    store = {}

    for s in R.get("seeds", []):
        m = re.match(r"^(.*?)\s*\((\d{4})\)\s*(.*)$", s.get("ref", ""))
        author, year, title = (m.group(1), m.group(2), m.group(3)) if m else ("", "", s.get("ref", ""))
        _add(store, title or s.get("ref", ""), authors=[author] if author else [], year=year,
             url=f"https://openalex.org/{s['id']}" if s.get("id") else "",
             axes=_axis_of_ref(s.get("ref", "")), roles=["obra-semente"])

    for r in R.get("top20_nonfeed", []):
        _add(store, r["title"], authors=[a.strip() for a in (r.get("authors") or "").split(";") if a.strip()],
             year=str(r.get("year") or ""), venue=r.get("venue", ""), axes=_axes(r.get("axes")),
             roles=["mais citada"])

    for r in R.get("top_bridges", []):
        _add(store, r["title"], authors=[a.strip() for a in (r.get("authors") or "").split(";") if a.strip()],
             year=str(r.get("year") or ""), axes=_axes(r.get("axes")), roles=["obra-ponte"])

    for r in R.get("top_bursts", []):
        _add(store, r["title"], authors=[a.strip() for a in (r.get("authors") or "").split(";") if a.strip()],
             url=f"https://openalex.org/{r['ref_id']}" if r.get("ref_id") else "", roles=["rajada de citação"])

    for r in R.get("sleeping_beauties", []):
        _add(store, r["title"], year=str(r.get("year") or ""), axes=_axes(r.get("axes")),
             roles=["bela adormecida"])

    if os.path.exists(BRASIL):
        ty = {"Journal Article": "JOUR", "Book": "BOOK", "Book Chapter": "CHAP", "Thesis": "THES"}
        for r in csv.DictReader(open(BRASIL, encoding="utf-8")):
            doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", (r.get("DOI") or "").strip(), flags=re.I)
            _add(store, r.get("Paper Title", ""),
                 authors=[a.strip() for a in (r.get("Author Names") or "").splitlines() if a.strip()],
                 year=(r.get("Publication Year") or "").strip(), doi=doi if doi.startswith("10.") else "",
                 url=(r.get("Paper Link") or "").strip(), venue=(r.get("Publication Title") or "").strip(),
                 abstract=(r.get("Abstract") or "").strip(),
                 type=ty.get((r.get("Publication Type") or "").strip(), "GEN"),
                 axes=["Política industrial"], roles=["corpus Brasil (Faganello)"])

    return [store[k] for k in sorted(store, key=lambda k: (store[k]["year"] or "0"), reverse=True)]


def apply_enrich(works):
    """Preenche resumo/DOI/url ausentes a partir do cache do OpenAlex (se houver)."""
    if not os.path.exists(ENRICH):
        return works
    enr = json.load(open(ENRICH, encoding="utf-8"))
    for e in works:
        d = enr.get(_norm(e["title"]))
        if not d:
            continue
        if not e["abstract"] and d.get("abstract"):
            e["abstract"] = d["abstract"]
        if not e["doi"] and d.get("doi"):
            e["doi"] = d["doi"]
        if not e["url"] and d.get("oa_id"):
            e["url"] = f"https://openalex.org/{d['oa_id']}"
    return works


def _note(e):
    src = "Brasil" if any("Brasil" in x for x in e["roles"]) else "núcleo global"
    return (f"Síntese cienciométrica IPEA · fonte: {src}"
            + (f" · eixos: {', '.join(sorted(e['axes']))}" if e["axes"] else "")
            + f" · papel: {', '.join(sorted(e['roles']))}")


def to_ris(works):
    out = []
    for e in works:
        out.append(f"TY  - {e['type']}")
        out.append(f"T1  - {_oneline(e['title'])}")
        for a in e["authors"]:
            out.append(f"AU  - {_oneline(a)}")
        if e["year"]:
            out.append(f"PY  - {_oneline(str(e['year']))}")
        if e["venue"]:
            out.append(f"JO  - {_oneline(e['venue'])}")
        if e["doi"]:
            out.append(f"DO  - {_oneline(e['doi'])}")
        if e["url"]:
            out.append(f"UR  - {_oneline(e['url'])}")
        if e["abstract"]:
            out.append(f"AB  - {_oneline(e['abstract'])}")
        for ax in sorted(e["axes"]):
            out.append(f"KW  - eixo: {ax}")
        for role in sorted(e["roles"]):
            out.append(f"KW  - papel: {role}")
        out.append(f"N1  - {_oneline(_note(e))}")
        out.append("ER  - ")
        out.append("")
    return "\n".join(out)


def to_csv(works, path):
    # colunas e convenções do exemplo oficial do Rayyan (autores separados por " and ");
    # keywords/notes ao final carregam eixo e papel para a triagem.
    cols = ["key", "title", "authors", "journal", "issn", "volume", "issue", "pages", "year",
            "publisher", "url", "abstract", "doi", "keywords", "notes"]
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(cols)
        for i, e in enumerate(works, 1):
            kw = "; ".join([f"eixo: {a}" for a in sorted(e["axes"])] + [f"papel: {r}" for r in sorted(e["roles"])])
            w.writerow([f"R{i:03d}", _oneline(e["title"]), " and ".join(_oneline(a) for a in e["authors"]),
                        _oneline(e["venue"]), "", "", "", "", e["year"], "", e["url"],
                        _oneline(e["abstract"]), e["doi"], kw, _note(e)])


def build(out=DADOS):
    works = apply_enrich(consolidate())
    os.makedirs(out, exist_ok=True)
    ris_path = os.path.join(out, "rayyan_sintese.ris")
    csv_path = os.path.join(out, "rayyan_sintese.csv")
    with open(ris_path, "w", encoding="utf-8") as f:
        f.write(to_ris(works))
    to_csv(works, csv_path)
    # contêiner .zip (formato aceito pelo Rayyan via "My Library")
    with zipfile.ZipFile(os.path.join(out, "rayyan_sintese.zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ris_path, "rayyan_sintese.ris")
        z.write(csv_path, "rayyan_sintese.csv")
    return works


def main():
    works = build()
    roles = {}
    for e in works:
        for r in e["roles"]:
            roles[r] = roles.get(r, 0) + 1
    print(f"Rayyan: {len(works)} obras consolidadas (dedup por título) em {DADOS}")
    for r, n in sorted(roles.items(), key=lambda x: -x[1]):
        print(f"  {n:>3} · {r}")
    com_doi = sum(1 for e in works if e["doi"])
    com_ab = sum(1 for e in works if e["abstract"])
    print(f"  com DOI: {com_doi} · com resumo: {com_ab}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
