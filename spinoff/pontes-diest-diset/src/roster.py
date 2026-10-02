"""Etapa 1 — quadro de pesquisadores ATIVOS do Ipea (fonte: portal do Ipea).

Fonte: "Quem faz pesquisa no Ipea" (https://www.ipea.gov.br/portal/pesquisadores-do-ipea).
De cada perfil extrai: nome, áreas de estudo, as **variantes de nome usadas nas
publicações** ("Pesquisadores - nome(s)") — chave para casar com o Repositório do Ipea
sem desambiguação heurística — e a minibiografia.

ATENÇÃO (verificado em 2026-10-02): o filtro `diretoria=` do portal é ignorado pelo
servidor (devolve a lista inteira, e quebra a paginação). Por isso colhemos a lista
completa (paginação `start=` SEM filtro) e a diretoria é ATRIBUÍDA depois pela produção
(src/attribute.py). Estar no diretório = critério de "pesquisador ativo".

Saída: data/roster.json  [{id, slug, name, areas[], name_variants[], bio, url}]
Uso:   python src/roster.py
"""
import html
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import net  # noqa: E402

BASE = "https://www.ipea.gov.br/portal/pesquisadores-do-ipea"
PROFILE = "https://www.ipea.gov.br/portal/pesquisadores-ipea/"
OUT = os.path.join(net.ROOT, "data", "roster.json")


def _text(fragment):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", "", fragment, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", "\n", t))
    return [ln.strip() for ln in t.split("\n") if ln.strip()]


def list_all():
    """Percorre a paginação (start=0,10,...) até não surgir perfil novo."""
    seen, out, start = set(), [], 0
    while True:
        page = net.get_text(net.url_with(BASE, {"start": start}) if start else BASE)
        ids = re.findall(r'href="/portal/pesquisadores-ipea/(\d+-[a-z0-9-]+)"', page)
        new = [i for i in dict.fromkeys(ids) if i not in seen]
        if not new:
            break
        for i in new:
            seen.add(i)
            out.append(i)
        start += 10
        if start > 2000:  # trava de segurança
            break
    return out


def parse_profile(slug):
    page = net.get_text(PROFILE + slug)
    lines = _text(page)
    try:
        k = lines.index("Pesquisadores do Ipea", lines.index("Conheça quem faz pesquisa no Ipea") + 2)
    except ValueError:
        k = 0
    name = lines[k + 1] if k else slug.split("-", 1)[1].replace("-", " ").title()
    areas, variants, bio = [], [], []
    mode = None
    for ln in lines[k + 2:]:
        if ln.startswith("Área de estudo - pesquisadores"):
            mode = "areas"; continue
        if ln.startswith("Pesquisadores - nome(s)"):
            mode = "variants"; continue
        if ln.startswith("Áreas de estudo:") or ln.startswith("Voltar ao topo"):
            break
        if mode == "areas":
            areas.append(ln.rstrip(";. ").strip())
        elif mode == "variants":
            if "," in ln and len(ln) < 120:
                variants.append(ln)
            else:
                mode = "bio"
                if ln != name:
                    bio.append(ln)
        elif mode == "bio":
            bio.append(ln)
    # variante "limpa": sem papéis editoriais entre parênteses
    clean = []
    for v in variants:
        v2 = re.sub(r"\s*\((Coordenador|Coordenadora|Editor|Editora|Organizador|Organizadora|Org\.?|Coord\.?|Ed\.?)[^)]*\)\s*$", "", v).strip()
        if v2 and v2 not in clean:
            clean.append(v2)
    return {"id": slug.split("-", 1)[0], "slug": slug, "name": name,
            "areas": [a for a in dict.fromkeys(areas) if a],
            "name_variants": clean, "bio": " ".join(bio).strip(), "url": PROFILE + slug}


def main():
    slugs = list_all()
    print(f"diretório: {len(slugs)} perfis", file=sys.stderr)
    roster = sorted((parse_profile(s) for s in slugs), key=lambda r: r["name"])
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(roster, f, ensure_ascii=False, indent=1)
    print(f"roster: {len(roster)} pesquisadores ativos → {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
