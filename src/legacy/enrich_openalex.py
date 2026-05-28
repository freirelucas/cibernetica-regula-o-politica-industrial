#!/usr/bin/env python3
"""Enriquecimento pontual via OpenAlex (uso único; requer rede).

Preenche o título do ponto pivotal e completa os títulos truncados das rajadas
em data/scisci_results.json. NÃO sobrescreve a autoria das rajadas (preserva as
correções canônicas já feitas) — atualiza apenas títulos e o registro pivotal.

Uso:  python src/enrich_openalex.py
"""
import json
import os
import time
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
JSON = os.path.join(ROOT, "data", "scisci_results.json")
API = "https://api.openalex.org/works"


def fetch(ids):
    out = {}
    for i in range(0, len(ids), 50):
        chunk = "|".join(ids[i:i + 50])
        url = f"{API}?filter=openalex:{chunk}&per-page=50&select=id,title,publication_year,authorships"
        req = urllib.request.Request(url, headers={"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"})
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.load(r)
        for w in data.get("results", []):
            wid = (w.get("id") or "").split("/")[-1]
            authors = [(a.get("author") or {}).get("display_name", "") for a in (w.get("authorships") or [])[:3]]
            out[wid] = {"title": w.get("title") or "", "year": w.get("publication_year"),
                        "authors": "; ".join(a for a in authors if a)}
        time.sleep(0.2)
    return out


def main():
    R = json.load(open(JSON, encoding="utf-8"))
    ids = [b["ref_id"] for b in R["top_bursts"]] + [p["ref_id"] for p in R.get("top_pivotal", [])]
    meta = fetch(sorted(set(ids)))
    print(f"recuperados {len(meta)} registros do OpenAlex")

    # rajadas: completar título (preserva autoria já corrigida)
    nb = 0
    for b in R["top_bursts"]:
        m = meta.get(b["ref_id"])
        if m and m["title"] and m["title"] != b["title"]:
            b["title"] = m["title"]; nb += 1
    # pivotal: preencher título/autoria/ano vazios
    np_ = 0
    for p in R.get("top_pivotal", []):
        m = meta.get(p["ref_id"])
        if m:
            if not p.get("title"): p["title"] = m["title"]
            if not p.get("authors"): p["authors"] = m["authors"]
            if not p.get("year"): p["year"] = m["year"]
            np_ += 1
    json.dump(R, open(JSON, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"títulos de rajada completados: {nb} | pivotal preenchido: {np_}")
    if R["top_pivotal"]:
        print("pivotal:", R["top_pivotal"][0]["title"], "·", R["top_pivotal"][0]["authors"])


if __name__ == "__main__":
    main()
