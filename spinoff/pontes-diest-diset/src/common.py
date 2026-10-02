"""Utilidades compartilhadas: normalização de nomes, leitura do corpus, rótulo de diretoria."""
import gzip
import json
import os
import re
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
NOW_YEAR = 2026

SUFFIXES = {"junior", "jr", "filho", "neto", "sobrinho", "segundo"}
PARTICLES = {"de", "da", "do", "dos", "das", "di", "del", "van", "von", "e"}

# Sinais de diretoria em campos editoriais (NÃO no resumo: um resumo que cita a Diest
# não faz da obra uma obra da Diest). Todos sobre texto já normalizado (sem acento, minúsculo).
DIRECTORATE_PATTERNS = {
    "DIEST": [r"\bdiest\b", r"estado,? das instituicoes e da democracia",
              r"analise politico.institucional", r"nt-diest"],
    "DISET": [r"\bdiset\b", r"estudos e politicas setoriais", r"radar\W+tecnologia,? producao",
              r"nt-diset", r"inovacao,? regulacao e infraestrutura"],
    "DISOC": [r"\bdisoc\b", r"politicas sociais\W+acompanhamento", r"estudos e politicas sociais"],
    "DIRUR": [r"\bdirur\b", r"regionais,? urbanas e ambientais", r"boletim regional,? urbano"],
    "DIMAC": [r"\bdimac\b", r"carta de conjuntura", r"estudos e politicas macroeconomicas"],
    "DINTE": [r"\bdinte\b", r"relacoes economicas e politicas internacionais",
              r"boletim de economia e politica internacional"],
}
SIGNAL_FIELDS = ("publisher", "contrib_other", "serie", "title_alt", "doi", "series",
                 "desc_other")  # sem dc.title: "políticas setoriais" aparece em títulos comuns
FOCUS = ("DIEST", "DISET")


def norm(s):
    s = unicodedata.normalize("NFKD", s or "")
    s = "".join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", s.lower()).strip()


def name_key(author):
    """'Gomide, Alexandre de Ávila' → ('gomide', 'alexandre de avila')."""
    a = norm(re.sub(r"\(.*?\)", "", author))
    a = re.sub(r"[^a-z, .'-]", "", a)
    if "," in a:
        fam, given = a.split(",", 1)
    else:  # "Alexandre de Ávila Gomide" → família = último token (+ sufixo)
        toks = a.replace(".", " ").split()
        if not toks:
            return ("", "")
        k = len(toks) - 1
        if toks[-1] in SUFFIXES and len(toks) > 2:
            k -= 1
        if k > 1 and toks[k - 1] in PARTICLES - {"e"}:  # "Fernanda De Negri" → "de negri"
            k -= 1
        fam, given = " ".join(toks[k:]), " ".join(toks[:k])
    fam = re.sub(r"[.\s]+", " ", fam).strip()
    given = re.sub(r"[.\s]+", " ", given).strip()
    return (fam, given)


def loose_key(author):
    """(sobrenome, 1º prenome) — casamento frouxo, só usado contra o quadro do Ipea."""
    fam, given = name_key(author)
    first = given.split()[0] if given.split() else ""
    fam = " ".join(t for t in fam.split() if t not in PARTICLES)
    return (fam, first)


def year_of(item):
    for d in item.get("date", []):
        m = re.match(r"(\d{4})", d)
        if m:
            return int(m.group(1))
    return None


def item_directorates(item):
    blob = norm(" | ".join(v for f in SIGNAL_FIELDS for v in item.get(f, [])))
    return sorted(d for d, pats in DIRECTORATE_PATTERNS.items()
                  if any(re.search(p, blob) for p in pats))


def load_items():
    with gzip.open(os.path.join(DATA, "repo_items.jsonl.gz"), "rt", encoding="utf-8") as f:
        for line in f:
            yield json.loads(line)


def load_json(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def save_json(name, obj):
    with open(os.path.join(DATA, name), "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)


def item_people(item):
    """Autores + organizadores/editores/coordenadores (todos assinam a obra)."""
    out = []
    for f in ("authors", "organizers", "editors", "coordinators"):
        for a in item.get(f, []):
            if a not in out:
                out.append(a)
    return out
