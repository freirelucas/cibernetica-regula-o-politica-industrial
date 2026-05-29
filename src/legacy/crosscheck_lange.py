#!/usr/bin/env python3
"""Teste de ponte: a recepção de Oskar Lange cruza os eixos? (uso único; requer rede)

Lange uniu cibernética, planejamento e socialismo em sua própria obra. Este teste
verifica se isso se sustenta na ESTRUTURA DE CITAÇÃO: classifica os trabalhos que
citam cada obra de Lange pelo vocabulário dos três eixos e mede quantos cruzam
cibernética × (política industrial/regulação). Fundamenta a nota da síntese.

Uso:  python src/crosscheck_lange.py
"""
import json
import urllib.request
from collections import Counter

UA = {"User-Agent": "scisci-ipea/1.0 (mailto:lucasfreire@gmail.com)"}
VOCAB = {
    "Cyb": ("cybernet", "viable system", "vsm", "stafford beer", "ashby", "requisite variety",
            "autopoiesis", "systems thinking", "feedback", "homeostas", "second-order"),
    "Reg": ("tools of government", "policy instrument", "policy mix", "nodality", "regulat",
            "governance", "policy design"),
    "PolInd": ("industrial policy", "developmental state", "state capacity", "entrepreneurial state",
               "mission-oriented", "planning", "socialism", "central plan", "economic cybernetic"),
}
LANGE = {
    "W4230710385": "Introduction to Economic Cybernetics (1971)",
    "W3130930004": "On the Economic Theory of Socialism (1936-38)",
    "W2063282131": "Wholes and Parts (1966)",
}


def axes(title):
    t = (title or "").lower()
    return {a for a, ks in VOCAB.items() if any(k in t for k in ks)}


def get(url):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=45))


def main():
    for wid, nm in LANGE.items():
        r = get(f"https://api.openalex.org/works?filter=cites:{wid}&per-page=120&select=title")
        cit = r.get("results", [])
        spread, cross = Counter(), 0
        for w in cit:
            ax = axes(w.get("title"))
            for a in ax:
                spread[a] += 1
            if "Cyb" in ax and ("PolInd" in ax or "Reg" in ax):
                cross += 1
        print(f"{nm} — citado por {r.get('meta', {}).get('count')} (amostra {len(cit)})")
        print(f"   eixos: {dict(spread)} | cruzam cibernética × (PI/Reg): {cross}")


if __name__ == "__main__":
    main()
