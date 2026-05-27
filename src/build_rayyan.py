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
CROSS = os.path.join(ROOT, "data", "cross_brasil.json")
CPLX = os.path.join(ROOT, "data", "cplx_works.json")
DADOS = os.path.join(ROOT, "docs", "dados")
PONTE = "ponte global×Brasil"
BRASIL_ROLE = "corpus Brasil (Faganello)"

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
                               "venue": "", "abstract": "", "axes": set(), "roles": set(),
                               "type": "GEN", "oa_id": ""})
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

    if os.path.exists(CPLX):                       # 4º eixo — economia da complexidade
        for w in json.load(open(CPLX, encoding="utf-8")):
            _add(store, w.get("title", ""), authors=w.get("authors") or [],
                 year=str(w.get("year") or ""), doi=w.get("doi", ""),
                 url=f"https://openalex.org/{w['oa_id']}" if w.get("oa_id") else "",
                 abstract=w.get("abstract", ""), type=w.get("type", "GEN"),
                 axes=["Economia da complexidade"], roles=["complexidade (4º eixo)"])

    return [store[k] for k in sorted(store, key=lambda k: (store[k]["year"] or "0"), reverse=True)]


def apply_enrich(works):
    """Completa cada obra a partir do cache do OpenAlex/Crossref (se houver): id canônico,
    DOI, resumo, título completo, autoria e tipo."""
    if not os.path.exists(ENRICH):
        return works
    enr = json.load(open(ENRICH, encoding="utf-8"))
    for e in works:
        d = enr.get(_norm(e["title"]))
        if not d:
            continue
        if d.get("oa_id"):
            e["oa_id"] = d["oa_id"]
            if not e["url"] or "openalex" not in e["url"]:
                e["url"] = f"https://openalex.org/{d['oa_id']}"
        if not e["doi"] and d.get("doi"):
            e["doi"] = d["doi"]
        if not e["abstract"] and d.get("abstract"):
            e["abstract"] = d["abstract"]
        if d.get("title") and len(d["title"]) > len(e["title"]):   # título canônico (sem truncar)
            e["title"] = d["title"]
        if d.get("authors") and len(d["authors"]) > len(e["authors"]):  # autoria completa
            e["authors"] = d["authors"]
        if d.get("type") and e["type"] == "GEN":                   # tipo real
            e["type"] = d["type"]
        if not e["year"] and d.get("year"):
            e["year"] = d["year"]
    return works


def tag_cross(works):
    """Marca as obras do cruzamento Brasil × núcleo global (ponte por citação) com um
    papel próprio — para filtrar na triagem e gerar o recorte rayyan_cruzamento."""
    if not os.path.exists(CROSS):
        return works
    c = json.load(open(CROSS, encoding="utf-8"))
    gids = set(c.get("global", []))
    boa = {b["oa_id"] for b in c.get("brasil", []) if b.get("oa_id")}
    bdois = {b["doi"] for b in c.get("brasil", []) if b.get("doi")}
    for e in works:
        oid = e.get("oa_id")
        if (oid and (oid in gids or oid in boa)) or (e.get("doi") and e["doi"] in bdois):
            e["roles"].add(PONTE)
    return works


def dedup_oaid(works):
    """Funde obras que compartilham o mesmo id OpenAlex (variantes do mesmo trabalho:
    títulos truncados, com/sem subtítulo, 'The X'/'X'). Une eixos e papéis."""
    out, byid = [], {}
    for e in works:
        oid = e.get("oa_id")
        if oid and oid in byid:
            t = byid[oid]
            t["axes"].update(e["axes"]); t["roles"].update(e["roles"])
            for fld in ("doi", "url", "venue", "abstract"):
                if not t[fld] and e[fld]:
                    t[fld] = e[fld]
            if len(e["title"]) > len(t["title"]):
                t["title"] = e["title"]
            if len(e["authors"]) > len(t["authors"]):
                t["authors"] = e["authors"]
            if t["type"] == "GEN" and e["type"] != "GEN":
                t["type"] = e["type"]
            if not t["year"] and e["year"]:
                t["year"] = e["year"]
        else:
            if oid:
                byid[oid] = e
            out.append(e)
    return out


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


ENW_TYPE = {"JOUR": "Journal Article", "BOOK": "Book", "CHAP": "Book Section",
            "THES": "Thesis", "GEN": "Generic"}
BIB_TYPE = {"JOUR": "article", "BOOK": "book", "CHAP": "incollection",
            "THES": "phdthesis", "GEN": "misc"}


def to_enw(works):
    """EndNote (.enw) — formato aceito pelo Rayyan, com resumo (%X)."""
    out = []
    for e in works:
        out.append(f"%0 {ENW_TYPE.get(e['type'], 'Generic')}")
        out.append(f"%T {_oneline(e['title'])}")
        for a in e["authors"]:
            out.append(f"%A {_oneline(a)}")
        if e["venue"]:
            out.append(f"%J {_oneline(e['venue'])}")
        if e["year"]:
            out.append(f"%D {_oneline(str(e['year']))}")
        if e["doi"]:
            out.append(f"%R {_oneline(e['doi'])}")
        if e["url"]:
            out.append(f"%U {_oneline(e['url'])}")
        if e["abstract"]:
            out.append(f"%X {_oneline(e['abstract'])}")
        for ax in sorted(e["axes"]):
            out.append(f"%K eixo: {ax}")
        for role in sorted(e["roles"]):
            out.append(f"%K papel: {role}")
        out.append("")
    return "\n".join(out)


def _bibval(s):
    return _oneline(s).replace("{", "(").replace("}", ")").replace("\\", "")


def to_bib(works):
    """BibTeX (.bib) — formato aceito pelo Rayyan; inclui resumo (campo abstract)."""
    out = []
    for i, e in enumerate(works, 1):
        fields = [("title", e["title"]),
                  ("author", " and ".join(e["authors"])),
                  ("journal", e["venue"]), ("year", str(e["year"]) if e["year"] else ""),
                  ("doi", e["doi"]), ("url", e["url"]), ("abstract", e["abstract"]),
                  ("keywords", "; ".join([f"eixo: {a}" for a in sorted(e["axes"])]
                                         + [f"papel: {r}" for r in sorted(e["roles"])]))]
        body = ",\n".join(f"  {k} = {{{_bibval(v)}}}" for k, v in fields if v)
        out.append(f"@{BIB_TYPE.get(e['type'], 'misc')}{{scisci{i:03d},\n{body}\n}}")
    return "\n\n".join(out) + "\n"


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


def emit(works, out, stem):
    """Escreve um conjunto de obras em todos os formatos (ris/csv/enw/bib) + zip do RIS.
    O .zip contém só o RIS — o Rayyan importa todos os arquivos do arquivo compactado,
    e vários formatos gerariam registros duplicados na revisão."""
    ris = os.path.join(out, stem + ".ris")
    with open(ris, "w", encoding="utf-8") as f:
        f.write(to_ris(works))
    to_csv(works, os.path.join(out, stem + ".csv"))
    with open(os.path.join(out, stem + ".enw"), "w", encoding="utf-8") as f:
        f.write(to_enw(works))
    with open(os.path.join(out, stem + ".bib"), "w", encoding="utf-8") as f:
        f.write(to_bib(works))
    with zipfile.ZipFile(os.path.join(out, stem + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ris, stem + ".ris")


def build(out=DADOS):
    works = tag_cross(dedup_oaid(apply_enrich(consolidate())))
    os.makedirs(out, exist_ok=True)
    emit(works, out, "rayyan_sintese")                    # opção A — abrangente (Claucia + 1º snowball)
    cruz = [e for e in works if PONTE in e["roles"]]      # opção B — cruzamento (ponte por citação)
    if cruz:
        emit(cruz, out, "rayyan_cruzamento")
    brasil = [e for e in works if BRASIL_ROLE in e["roles"]]   # só as referências da Claucia
    if brasil:
        emit(brasil, out, "rayyan_brasil")
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
