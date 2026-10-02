"""Etapa 2 — colheita do Repositório do Conhecimento do Ipea (DSpace 9, API REST).

Baixa TODAS as entidades Publication, Book e Person (≈16,5 mil + 400) e guarda só os
campos úteis, compactados (data/repo_items.jsonl.gz, data/repo_persons.json). O corpus
inteiro do Ipea é colhido de propósito: (i) a atribuição de diretoria precisa ver a
produção nas OUTRAS diretorias (Disoc, Dirur, Dimac, Dinte) para não rotular como
DIEST quem só coassinou um boletim; (ii) os modelos nulos usam o instituto como base.

Uso: python src/harvest_repo.py          (retomável: páginas ficam no cache de net.py)
"""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net  # noqa: E402

API = "https://repositorio.ipea.gov.br/server/api/discover/search/objects"
OUT_ITEMS = os.path.join(net.ROOT, "data", "repo_items.jsonl.gz")
OUT_PERSONS = os.path.join(net.ROOT, "data", "repo_persons.json")
SIZE = 100

KEEP = {
    "dc.title": "title", "dc.title.alternative": "title_alt", "dc.date.issued": "date",
    "dc.type": "type", "dc.contributor.author": "authors", "dc.contributor.organizer": "organizers",
    "dc.contributor.editor": "editors", "dc.contributor.coordinator": "coordinators",
    "dc.contributor.other": "contrib_other", "dc.publisher": "publisher",
    "dc.description.serie": "serie", "dc.description.other": "desc_other",
    "dc.subject.vcipea": "vcipea", "dc.subject.keyword": "keywords",
    "ipea.classification": "classification", "dc.description.abstract": "abstract",
    "dc.identifier.uri": "uri", "dc.identifier.doi": "doi", "dc.language.iso": "lang",
    "dc.relation.ispartofseries": "series", "dc.identifier.citation": "citation",
    "dspace.entity.type": "entity",
}
PERSON_KEEP = {
    "person.name": "name", "person.name.variant": "variants", "person.givenName": "given",
    "person.familyName": "family", "person.jobTitle": "job", "person.description": "bio",
    "person.identifier.lattes": "lattes", "person.identifier.orcid": "orcid",
    "dc.subject.keyword": "keywords", "dc.identifier.uri": "uri",
    "relation.isPublicationOfAuthor": "pubs", "relation.isBookOfAuthor": "books",
}


def _compact(it, keep):
    md = it.get("metadata", {})
    rec = {"uuid": it["uuid"]}
    for k, short in keep.items():
        vals = [x["value"] for x in md.get(k, []) if x.get("value")]
        if vals:
            rec[short] = vals
    return rec


def _pages(entity):
    page = 0
    while True:
        url = net.url_with(API, {"dsoType": "ITEM", "f.entityType": f"{entity},equals",
                                 "size": SIZE, "page": page, "sort": "dc.date.accessioned,ASC"})
        d = net.get_json(url)
        sr = d["_embedded"]["searchResult"]
        objs = sr.get("_embedded", {}).get("objects", [])
        yield [o["_embedded"]["indexableObject"] for o in objs]
        tp = sr["page"]["totalPages"]
        print(f"  {entity}: página {page + 1}/{tp}", file=sys.stderr, flush=True)
        page += 1
        if page >= tp or not objs:
            break


def main():
    seen = set()
    n = 0
    with gzip.open(OUT_ITEMS, "wt", encoding="utf-8") as f:
        for ent in ("Publication", "Book"):
            for objs in _pages(ent):
                for it in objs:
                    if it["uuid"] in seen:
                        continue
                    seen.add(it["uuid"])
                    f.write(json.dumps(_compact(it, KEEP), ensure_ascii=False) + "\n")
                    n += 1
    persons = [_compact(it, PERSON_KEEP) for objs in _pages("Person") for it in objs]
    with open(OUT_PERSONS, "w", encoding="utf-8") as f:
        json.dump(persons, f, ensure_ascii=False, indent=0)
    print(f"itens: {n} → {OUT_ITEMS}\npessoas: {len(persons)} → {OUT_PERSONS}", file=sys.stderr)


if __name__ == "__main__":
    main()
