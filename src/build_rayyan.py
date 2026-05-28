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
AUTHORS = os.path.join(ROOT, "data", "author_works.json")
PRIORITY = os.path.join(ROOT, "data", "bridge_priority.json")
HYPEREDGES = os.path.join(ROOT, "data", "cocitation_hyperedges.json")
TAGS_MANIFEST = os.path.join(ROOT, "data", "rayyan_tags.json")
DADOS = os.path.join(ROOT, "docs", "dados")
PONTE = "ponte global×Brasil"
BRASIL_ROLE = "corpus Brasil (Faganello)"

AXMAP = {"Cyb": "Cibernética", "Reg": "Instrumentos de governo", "PolInd": "Política industrial"}

# ============================================================
# Catálogo de critérios de curadoria — cada tag (role) tem uma definição auditável
# e um limiar paramétrico. Adicionar um critério aqui é todo o esforço conceitual;
# a pipeline (consolidate + tag_*) o aplica e o manifest write_manifest() o expõe
# para o trio de triadores. Esta é a "arquitetura de tagging multinível" da §4 do
# plano de avaliação — fácil de auditar e estender.
# ============================================================
MIN_CROSS_AXIS_EDGES = 3       # tag higher_order_bridge: ≥N hiperarestas trans-eixo (XGI)
MIN_AXES_COVERED = 2           # tag obra-ponte: ≥N eixos por vocabulário
N_BRIDGE_PRIORITY = 25         # tag ponte a construir: top-N por bridge_priority

CRITERIA = {
    "obra-semente": ("Obra-semente canônica do funil global",
                     "scisci_results.json:seeds"),
    "mais citada": ("Top-20 não-semente por nº de citações",
                    "scisci_results.json:top20_nonfeed"),
    "obra-ponte": (f"Toca ≥{MIN_AXES_COVERED} eixos por vocabulário",
                   "scisci_results.json:top_bridges"),
    "rajada de citação": ("Burst de Kleinberg detectado",
                          "scisci_results.json:top_bursts"),
    "bela adormecida": ("Coeficiente de beleza (Ke et al., 2015)",
                        "scisci_results.json:sleeping_beauties"),
    BRASIL_ROLE: ("Revisão brasileira de C. Faganello",
                  "docs/material-brasil/dataset_politica_industrial_brasil.csv"),
    "complexidade (4º eixo)": ("Sonda do 4º eixo: economia da complexidade",
                               "data/cplx_works.json · src/experiment_cplx.py"),
    "obra de autor-semente": ("Snowball por autor-semente",
                              "data/author_works.json · src/author_snowball.py"),
    "cibernética organizacional": ("Vocabulário aplicado (MSV/Beer/Espejo…) — _ORG_CYB",
                                   "tag_cyb_subtype em build_rayyan.py"),
    "cibernética (geral)": ("Vocabulário fundacional (Wiener/Ashby/von Foerster) — _GERAL_CYB",
                            "tag_cyb_subtype em build_rayyan.py"),
    PONTE: ("Cruzamento Brasil × núcleo global por citação direta",
            "data/cross_brasil.json · src/cross_brasil.py"),
    "ponte a construir": (f"Top-{N_BRIDGE_PRIORITY} por prioridade de ponte (CB + comunidade)",
                          "data/bridge_priority.json · src/bridge_priority.py"),
    "higher_order_bridge": (f"Aparece em ≥{MIN_CROSS_AXIS_EDGES} hiperarestas trans-eixo (XGI; Landry, 2023)",
                            "data/cocitation_hyperedges.json · src/cocitation_hypergraph.py"),
}


def write_manifest(out_path=TAGS_MANIFEST):
    """Escreve `data/rayyan_tags.json` — catálogo auditável de todas as tags da síntese
    (descrição, fonte e limiar). É o que torna as escolhas conceituais explícitas."""
    manifest = {
        "tags": {t: {"description": d, "source": s} for t, (d, s) in CRITERIA.items()},
        "thresholds": {
            "MIN_CROSS_AXIS_EDGES": MIN_CROSS_AXIS_EDGES,
            "MIN_AXES_COVERED": MIN_AXES_COVERED,
            "N_BRIDGE_PRIORITY": N_BRIDGE_PRIORITY,
        },
    }
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    json.dump(manifest, open(out_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)


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
                               "rationale": {}, "type": "GEN", "oa_id": ""})
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
                 axes=["Economia da complexidade"],
                 roles=["complexidade (4º eixo)"]
                 + ([f"complexidade · {w['subtrad']}"] if w.get("subtrad") else []))

    if os.path.exists(AUTHORS):                    # snowball por autor-semente
        for w in json.load(open(AUTHORS, encoding="utf-8")):
            _add(store, w.get("title", ""), authors=w.get("authors") or [],
                 year=str(w.get("year") or ""), doi=w.get("doi", ""),
                 url=f"https://openalex.org/{w['oa_id']}" if w.get("oa_id") else "",
                 abstract=w.get("abstract", ""), type=w.get("type", "GEN"),
                 axes=w.get("axes") or [], roles=["obra de autor-semente"])

    return [store[k] for k in sorted(store, key=lambda k: (store[k]["year"] or "0"), reverse=True)]


_ORG_CYB = ("viable system", "vsm", "stafford beer", "espejo", "management cybernet",
            "organizational cybernet", "organizational systems", "syntegrity", "brain of the firm",
            "heart of enterprise", "diagnosing the system", "designing freedom", "cybersyn",
            "managing complexity", "soft systems", "systems thinking", "systems practice",
            "systems methodolog", "critical systems", "fifth discipline")
_GERAL_CYB = ("ashby", "wiener", "requisite variety", "second-order", "von foerster",
              "introduction to cybernetics", "theory of communication", "general system",
              "von bertalanffy", "autopoiesis", "self-organ", "homeostat")


def tag_cyb_subtype(works):
    """Distingue cibernética ORGANIZACIONAL (MSV/Beer/sistemas aplicados) da GERAL/fundacional
    (Wiener/Ashby/teoria geral) — papel extra nas obras de cibernética. A estrutura da rede
    mostra que é a organizacional que faz fronteira com regulação e política industrial."""
    for e in works:
        if "Cibernética" not in e["axes"]:
            continue
        t = e["title"].lower()
        org = any(k in t for k in _ORG_CYB)
        ger = any(k in t for k in _GERAL_CYB)
        e["roles"].add("cibernética organizacional" if (org or not ger) else "cibernética (geral)")
    return works


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


def tag_bridge_priority(works, n=N_BRIDGE_PRIORITY):
    """Marca as N obras de maior PRIORIDADE DE PONTE (data/bridge_priority.json,
    gerado por src/bridge_priority.py) com o papel 'ponte a construir' — os papers
    a revisar em detalhe para construir as pontes entre os eixos."""
    if not os.path.exists(PRIORITY):
        return works
    ranking = json.load(open(PRIORITY, encoding="utf-8")).get("ranking", [])
    top_list = list(dict.fromkeys(r["oa_id"] for r in ranking
                                  if r.get("oa_id") and r.get("score", 0) > 0))[:n]
    top = set(top_list)
    score_by_id = {r["oa_id"]: r.get("score", 0) for r in ranking if r.get("oa_id") in top}
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", "") or "")
        if m and m.group(1) in top:
            e["roles"].add("ponte a construir")
            e.setdefault("rationale", {})["ponte a construir"] = (
                f"top-{n} de bridge_priority (score={score_by_id.get(m.group(1), '?')})")
    return works


def tag_higher_order_bridge(works):
    """Marca obras que aparecem em ≥MIN_CROSS_AXIS_EDGES hiperarestas trans-eixo.
    As hiperarestas (cada bibliografia citante é uma hiperaresta sobre o núcleo cocitado)
    vêm de `src/cocitation_hypergraph.py` (XGI; Landry, 2023). É a tag que materializa
    o caminho de ordem superior — a convergência que a projeção par-a-par esconde."""
    if not os.path.exists(HYPEREDGES):
        return works
    H = json.load(open(HYPEREDGES, encoding="utf-8"))
    cross_deg = H.get("cross_axis_degree", {})
    for e in works:
        m = re.search(r"openalex\.org/(W\d+)", e.get("url", "") or "")
        oid = e.get("oa_id") or (m.group(1) if m else None)
        n_cross = cross_deg.get(oid, 0) if oid else 0
        if n_cross >= MIN_CROSS_AXIS_EDGES:
            e["roles"].add("higher_order_bridge")
            e.setdefault("rationale", {})["higher_order_bridge"] = (
                f"{n_cross} hiperarestas trans-eixo (XGI)")
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
    base = (f"Síntese cienciométrica IPEA · fonte: {src}"
            + (f" · eixos: {', '.join(sorted(e['axes']))}" if e["axes"] else "")
            + f" · papel: {', '.join(sorted(e['roles']))}")
    ratl = e.get("rationale") or {}
    if ratl:
        base += " · razão: " + "; ".join(f"{k}={v}" for k, v in sorted(ratl.items()))
    return base


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
    ris_text = to_ris(works)
    with open(os.path.join(out, stem + ".ris"), "w", encoding="utf-8") as f:
        f.write(ris_text)
    to_csv(works, os.path.join(out, stem + ".csv"))
    with open(os.path.join(out, stem + ".enw"), "w", encoding="utf-8") as f:
        f.write(to_enw(works))
    with open(os.path.join(out, stem + ".bib"), "w", encoding="utf-8") as f:
        f.write(to_bib(works))
    # zip determinístico: data fixa na entrada, senão o mtime muda os bytes a cada build
    with zipfile.ZipFile(os.path.join(out, stem + ".zip"), "w", zipfile.ZIP_DEFLATED) as z:
        zi = zipfile.ZipInfo(stem + ".ris", date_time=(2026, 5, 25, 0, 0, 0))
        zi.compress_type = zipfile.ZIP_DEFLATED
        z.writestr(zi, ris_text)


def build(out=DADOS):
    works = tag_higher_order_bridge(
        tag_bridge_priority(tag_cyb_subtype(tag_cross(dedup_oaid(apply_enrich(consolidate()))))))
    os.makedirs(out, exist_ok=True)
    write_manifest()           # data/rayyan_tags.json — auditoria das escolhas conceituais
    emit(works, out, "rayyan_sintese")                    # opção A — abrangente (Claucia + 1º snowball)
    pontes = [e for e in works if "ponte a construir" in e["roles"]]   # opção E — a revisar p/ construir pontes
    if pontes:
        emit(pontes, out, "rayyan_pontes")
    cruz = [e for e in works if PONTE in e["roles"]]      # opção B — cruzamento (ponte por citação)
    if cruz:
        emit(cruz, out, "rayyan_cruzamento")
    brasil = [e for e in works if BRASIL_ROLE in e["roles"]]   # opção C — só as referências da Claucia
    if brasil:
        emit(brasil, out, "rayyan_brasil")
    # opção D — o alvo: cibernética ORGANIZACIONAL + regulação + política industrial
    org = [e for e in works if ("cibernética organizacional" in e["roles"])
           or ("Instrumentos de governo" in e["axes"]) or ("Política industrial" in e["axes"])]
    if org:
        emit(org, out, "rayyan_organizacional")
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
