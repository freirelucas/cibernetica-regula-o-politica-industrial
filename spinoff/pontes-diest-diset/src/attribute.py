"""Etapa 3 — identidade de autores e atribuição de diretoria pela produção.

1. Identidade: cada assinatura do repositório ("Sobrenome, Prenomes") vira um autor.
   Pesquisadores do quadro (roster.json) são casados (a) pelas variantes de nome que o
   próprio portal publica e (b) por (sobrenome, 1º prenome) quando esse par é único no
   quadro. Os demais autores ficam com a chave normalizada da assinatura.
2. Diretoria de cada obra: sinais editoriais (editora/unidade, série, DOI nt-diest,
   título alternativo "Nota Técnica (Diset)", boletins BAPI/Radar...) — ver common.py.
3. Diretoria de cada pesquisador: soma ponderada pela recência (meia-vida 4 anos) das
   obras rotuladas em que assina, contra as SEIS diretorias de pesquisa. Atribui a
   dominante se tiver ≥50% do peso e ≥2 obras rotuladas; o cargo explícito no perfil
   de Pessoa do repositório (person.jobTitle) prevalece quando existe.

Saída: data/authors.json  — {author_id: {name, roster, active, diretoria, confidence,
        dir_weights, n_items, n_tagged, first_year, last_year, ...}}
       data/items_tagged.json — obras com rótulo de diretoria e autores resolvidos
Uso:   python src/attribute.py
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import (FOCUS, NOW_YEAR, item_directorates, item_people, load_items,  # noqa: E402
                    load_json, loose_key, name_key, norm, save_json, year_of)

HALF_LIFE = 4.0
MIN_SHARE = 0.5
MIN_TAGGED = 2


def job_directorate(job):
    j = norm(job)
    for d, pats in (("DIEST", [r"\bdiest\b", r"estado, das instituicoes"]),
                    ("DISET", [r"\bdiset\b", r"politicas setoriais"]),
                    ("DISOC", [r"\bdisoc\b", r"politicas sociais"]),
                    ("DIRUR", [r"\bdirur\b", r"regionais, urbanas"]),
                    ("DIMAC", [r"\bdimac\b", r"macroeconomicas"]),
                    ("DINTE", [r"\bdinte\b", r"politicas internacionais"])):
        if any(re.search(p, j) for p in pats):
            return d
    return None


def build_resolver(roster, persons):
    exact, loose = {}, collections.defaultdict(set)
    for r in roster:
        rid = "ipea:" + r["id"]
        for v in r["name_variants"] + [r["name"]]:
            exact[name_key(v)] = rid
            loose[loose_key(v)].add(rid)
    # pessoas do repositório com cargo explícito: ganham id próprio se não estão no quadro
    jobs = {}
    for p in persons:
        names = p.get("name", []) + p.get("variants", [])
        d = next((job_directorate(j) for j in p.get("job", []) if job_directorate(j)), None)
        rid = None
        for n in names:
            rid = exact.get(name_key(n)) or (next(iter(loose[loose_key(n)]))
                                             if len(loose.get(loose_key(n), ())) == 1 else None)
            if rid:
                break
        if not rid and d:
            rid = "repo:" + p["uuid"]
            for n in names:
                exact[name_key(n)] = rid
                loose[loose_key(n)].add(rid)
        if rid and d:
            jobs[rid] = {"diretoria": d, "job": p.get("job", [""])[0],
                         "lattes": (p.get("lattes") or [None])[0],
                         "orcid": (p.get("orcid") or [None])[0]}

    def resolve(sig):
        k = name_key(sig)
        if k in exact:
            return exact[k]
        cands = loose.get(loose_key(sig), set())
        if len(cands) == 1:
            return next(iter(cands))
        return "ext:" + "|".join(k)
    return resolve, jobs


def main():
    roster = load_json("roster.json")
    persons = load_json("repo_persons.json")
    resolve, jobs = build_resolver(roster, persons)
    by_id = {"ipea:" + r["id"]: r for r in roster}

    authors = collections.defaultdict(lambda: {
        "names": collections.Counter(), "items": 0, "tagged": 0, "years": [],
        "w": collections.Counter(), "n_by_dir": collections.Counter()})
    items_out = []
    for it in load_items():
        people = item_people(it)
        if not people:
            continue
        y = year_of(it)
        dirs = item_directorates(it)
        ids = []
        for sig in people:
            aid = resolve(sig)
            if aid not in ids:
                ids.append(aid)
            a = authors[aid]
            a["names"][sig] += 1
            a["items"] += 1
            if y:
                a["years"].append(y)
            if dirs:
                a["tagged"] += 1
                w = 0.5 ** (max(0, NOW_YEAR - (y or 1990)) / HALF_LIFE)
                for d in dirs:
                    a["w"][d] += w / len(dirs)
                    a["n_by_dir"][d] += 1
        items_out.append({
            "uuid": it["uuid"], "title": (it.get("title") or [""])[0], "year": y,
            "type": (it.get("type") or [""])[0], "entity": (it.get("entity") or [""])[0],
            "dirs": dirs, "authors": ids,
            "vcipea": it.get("vcipea", []), "keywords": it.get("keywords", []),
            "classification": it.get("classification", []),
            "uri": (it.get("uri") or [""])[0],
            "abstract": ((it.get("abstract") or [""])[0])[:1200],
        })

    out = {}
    for aid, a in authors.items():
        tot = sum(a["w"].values())
        top, topw = (a["w"].most_common(1)[0] if a["w"] else (None, 0.0))
        share = topw / tot if tot else 0.0
        if aid in jobs:
            d, conf = jobs[aid]["diretoria"], "explicita"
        elif top and share >= MIN_SHARE and a["tagged"] >= MIN_TAGGED:
            d = top
            conf = "forte" if (share >= 0.7 and a["tagged"] >= 4) else "moderada"
        else:
            d, conf = None, ("fraca" if top else "sem_sinal")
        r = by_id.get(aid)
        ys = a["years"]
        out[aid] = {
            "name": r["name"] if r else a["names"].most_common(1)[0][0],
            "signatures": [n for n, _ in a["names"].most_common(5)],
            "roster": bool(r), "staff": aid.startswith(("ipea:", "repo:")),
            "active": bool(r) or (bool(ys) and max(ys) >= NOW_YEAR - 3),
            "diretoria": d, "confidence": conf, "share": round(share, 3),
            "dir_weights": {k: round(v, 3) for k, v in a["w"].most_common()},
            "n_by_dir": dict(a["n_by_dir"]), "n_items": a["items"], "n_tagged": a["tagged"],
            "first_year": min(ys) if ys else None, "last_year": max(ys) if ys else None,
            "areas": r["areas"] if r else [], "profile_url": r["url"] if r else None,
            **({k: v for k, v in jobs[aid].items() if k != "diretoria"} if aid in jobs else {}),
        }
    save_json("authors.json", out)
    save_json("items_tagged.json", items_out)

    focus = [a for a in out.values() if a["diretoria"] in FOCUS]
    c = collections.Counter((a["diretoria"], a["roster"], a["confidence"]) for a in focus)
    print(f"obras: {len(items_out)}  rotuladas: {sum(1 for i in items_out if i['dirs'])}", file=sys.stderr)
    print(f"autores: {len(out)}  quadro casado: {sum(1 for a in out.values() if a['roster'] and a['n_items'])}/{len(roster)}",
          file=sys.stderr)
    for k, v in sorted(c.items()):
        print(f"  {k}: {v}", file=sys.stderr)


if __name__ == "__main__":
    main()
