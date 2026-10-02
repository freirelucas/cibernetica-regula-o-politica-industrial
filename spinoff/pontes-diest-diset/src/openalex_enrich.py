"""Etapa 6 (opcional, precisa de OPENALEX_API_KEY) — camada internacional + referências.

O repositório do Ipea não traz as REFERÊNCIAS das obras; o OpenAlex traz. Com elas
abre-se o terceiro hipergrafo, o mais "epistêmico":
  H_ref (acoplamento bibliográfico) — hiperaresta = obra CITADA; nós = autores DIEST/DISET
  que a citam. Uma obra citada pelos dois lados é uma ponte epistêmica (literatura comum),
  mesmo sem coautoria. É também a ponte com o projeto-mãe: as sementes de
  cibernética/regulação/política industrial (../../src/minirun.py) podem ser marcadas
  como hiperarestas e ver-se quem, na DIEST e na DISET, já as mobiliza.

Resolução de autor: ORCID do perfil de Pessoa do repositório quando houver; senão busca
por nome com filtro de instituição Ipea (OpenAlex I3131024195 / I4210107985 — verificar).
NUNCA aceita candidato sem afiliação Ipea na trajetória (last_known_institutions ou
affiliations). Casos ambíguos vão para data/openalex_review.json para revisão humana.

Saída: data/openalex_authors.json, data/openalex_works.json, data/openalex_review.json
Uso:   OPENALEX_API_KEY=... python src/openalex_enrich.py [--max 400]
"""
import argparse
import os
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net  # noqa: E402
from common import FOCUS, load_json, norm, save_json  # noqa: E402

API = "https://api.openalex.org"
IPEA_IDS = {"I3131024195", "I4210107985"}  # "Institute (for|of) Applied Economic Research" — conferir
KEY = os.environ.get("OPENALEX_API_KEY", "")
MAILTO = os.environ.get("OPENALEX_MAILTO", "")


def oa(path, **params):
    if KEY:
        params["api_key"] = KEY
    if MAILTO:
        params["mailto"] = MAILTO
    d = net.get_json(f"{API}/{path}?" + urllib.parse.urlencode(params))
    if "error" in d:
        raise RuntimeError(d.get("message", d["error"]))
    return d


def ipea_affiliated(a):
    ids = {i.get("id", "").rsplit("/", 1)[-1] for i in a.get("last_known_institutions") or []}
    ids |= {x.get("institution", {}).get("id", "").rsplit("/", 1)[-1] for x in a.get("affiliations") or []}
    return bool(ids & IPEA_IDS)


def resolve(v):
    if v.get("orcid"):
        orc = v["orcid"].rstrip("/").rsplit("/", 1)[-1]
        try:
            return oa(f"authors/orcid:{orc}"), "orcid"
        except Exception:
            pass
    d = oa("authors", search=v["name"], per_page=10)
    cands = [a for a in d.get("results", []) if ipea_affiliated(a)]
    if len(cands) == 1:
        return cands[0], "nome+ipea"
    if len(cands) > 1:
        tgt = norm(v["name"])
        exact = [a for a in cands if norm(a["display_name"]) == tgt]
        if len(exact) == 1:
            return exact[0], "nome_exato+ipea"
        return {"ambiguous": [a["id"] for a in cands]}, "ambiguo"
    return None, "nao_encontrado"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=400)
    ap.add_argument("--works-per-author", type=int, default=200)
    args = ap.parse_args()
    if not KEY:
        sys.exit("OPENALEX_API_KEY ausente: o pool grátis por IP costuma estar esgotado em nuvem. "
                 "Crie uma chave grátis em https://help.openalex.org/api/authentication/")
    authors = load_json("authors.json")
    targets = [(k, v) for k, v in authors.items()
               if v["diretoria"] in FOCUS and v["staff"] and v["active"]][: args.max]
    out, review, works = {}, {}, {}
    for aid, v in targets:
        a, how = resolve(v)
        if how in ("ambiguo", "nao_encontrado"):
            review[aid] = {"name": v["name"], "status": how, **(a or {})}
            continue
        out[aid] = {"openalex": a["id"], "how": how, "name": v["name"], "diretoria": v["diretoria"],
                    "works_count": a.get("works_count"), "cited_by_count": a.get("cited_by_count"),
                    "topics": [t["display_name"] for t in (a.get("topics") or [])[:15]]}
        cursor = "*"
        n = 0
        while cursor and n < args.works_per_author:
            d = oa("works", filter=f"author.id:{a['id'].rsplit('/', 1)[-1]}", per_page=100, cursor=cursor,
                   select="id,title,publication_year,referenced_works,primary_topic,authorships")
            for w in d.get("results", []):
                works.setdefault(w["id"], {"title": w.get("title"), "year": w.get("publication_year"),
                                           "refs": w.get("referenced_works", []),
                                           "topic": (w.get("primary_topic") or {}).get("display_name"),
                                           "authors": []})
                works[w["id"]]["authors"].append(aid)
                n += 1
            cursor = d.get("meta", {}).get("next_cursor")
            if not d.get("results"):
                break
        print(f"  {v['name']}: {how}, {n} obras", file=sys.stderr)
    save_json("openalex_authors.json", out)
    save_json("openalex_works.json", works)
    save_json("openalex_review.json", review)
    print(f"resolvidos {len(out)}/{len(targets)}; para revisão: {len(review)}; obras {len(works)}",
          file=sys.stderr)


if __name__ == "__main__":
    main()
