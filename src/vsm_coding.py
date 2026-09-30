#!/usr/bin/env python3
"""Codificação do corpus pelas FUNÇÕES do Modelo de Sistema Viável (S1–S5).

Por que existe: o relatório classifica as obras por TRADIÇÃO (cibernética,
regulação, política industrial). Esta camada pergunta outra coisa — de que
FUNÇÃO de governo cada trabalho trata. A hipótese, vinda do arcabouço
institucional, é que a literatura serve bem umas funções e deixa outras a
descoberto; se a lacuna institucional diagnosticada (coordenação e inteligência)
estiver espelhada na base de conhecimento, isso é achado, não ilustração.

Vantagem metodológica: é uma classificação por função, sobre título+resumo, que
NÃO usa o rótulo de eixo — portanto **não herda a circularidade do H1**. É uma
perna probatória independente.

Limite declarado: é um proxy LÉXICO, não semântico. Não distingue a obra que
*trata* de coordenação daquela que apenas a menciona; é multirrótulo; e o
vocabulário abaixo é do projeto, não validado externamente. Por isso o módulo
roda um teste de sensibilidade: derruba o termo mais frequente de cada função e
verifica se a ordenação sobrevive.

Saída: data/vsm_coding.json   ·   Roda: python src/vsm_coding.py
"""
import collections
import csv
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "data", "vsm_coding.json")
SINTESE = os.path.join(ROOT, "docs", "dados", "rayyan_sintese.csv")
ENRICH = os.path.join(ROOT, "data", "openalex_enrich.json")

# Vocabulário controlado por função (PT/EN). Radicais, casados sem acento-sensibilidade.
FUNCOES = {
    "S1_operacoes": {
        "nome": "S1 · operações",
        "termos": ["implement", "enforc", "licen", "permitting", "complian", "operational",
                   "service delivery", "inspection", "certifica", "standard-setting",
                   "fiscaliza", "licenciamento", "outorga", "conformidade", "operacional"],
    },
    "S2_coordenacao": {
        "nome": "S2 · coordenação",
        "termos": ["coordinat", "inter-agency", "interagency", "harmoni", "cooperat",
                   "collaborat", "joint action", "alignment", "fragmentat", "silo",
                   "interoperab", "policy coherence",
                   "coordena", "interinstitucional", "articula", "cooperac", "fragmentac"],
    },
    "S3_controle": {
        "nome": "S3 · controle",
        "termos": ["monitor", "evaluat", "performance", "indicator", "accountab", "audit",
                   "oversight", "assessment", "budget", "allocat",
                   "monitora", "avaliac", "desempenho", "indicador", "auditoria", "supervis"],
    },
    "S4_inteligencia": {
        "nome": "S4 · inteligência",
        "termos": ["foresight", "anticipat", "horizon scanning", "prospective", "emerging",
                   "scenario", "uncertaint", "technology intelligence", "futures",
                   "prospec", "antecipa", "cenario", "emergente", "incerteza"],
    },
    "S5_politica": {
        "nome": "S5 · política/identidade",
        "termos": ["mission", "mandate", "purpose", "strateg", "goal", "vision",
                   "legitimacy", "identity", "prioriti",
                   "missao", "mandato", "proposito", "estrateg", "objetivo", "legitimidade"],
    },
}


def _norm(s):
    tr = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
                       "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC")
    return (s or "").translate(tr).lower()


def corpus():
    """Obras com resumo utilizável: síntese curada + resumos do enriquecimento."""
    absts = {}
    if os.path.exists(ENRICH):
        for k, v in (json.load(open(ENRICH, encoding="utf-8")) or {}).items():
            if isinstance(v, dict) and v.get("abstract"):
                absts[k] = v["abstract"]
    out = []
    for r in csv.DictReader(open(SINTESE, encoding="utf-8")):
        t = (r.get("title") or "").strip()
        a = (r.get("abstract") or "").strip() or absts.get((r.get("key") or "").strip(), "")
        if a and len(a) > 80:                      # exige resumo real, não só título
            out.append({"key": r.get("key"), "title": t, "text": _norm(t + " " + a)})
    return out


def codificar(obras, ignorar=None):
    """Multirrótulo: quais funções cada obra aciona. `ignorar` remove termos (sensibilidade)."""
    ignorar = ignorar or set()
    cont = collections.Counter()
    por_obra = []
    for o in obras:
        hits = set()
        for fid, f in FUNCOES.items():
            for termo in f["termos"]:
                if termo in ignorar:
                    continue
                if termo in o["text"]:
                    hits.add(fid)
                    break
        for h in hits:
            cont[h] += 1
        por_obra.append(sorted(hits))
    return cont, por_obra


def termo_mais_frequente(obras, fid):
    c = collections.Counter()
    for o in obras:
        for termo in FUNCOES[fid]["termos"]:
            if termo in o["text"]:
                c[termo] += 1
    return c.most_common(1)[0] if c else (None, 0)


def main():
    obras = corpus()
    n = max(len(obras), 1)
    cont, por_obra = codificar(obras)

    ordem = [f for f, _ in cont.most_common()]
    dominantes = {fid: termo_mais_frequente(obras, fid) for fid in FUNCOES}

    # sensibilidade: derruba o termo mais frequente de CADA função e re-ordena
    drop = {t for t, _ in dominantes.values() if t}
    cont_s, _ = codificar(obras, ignorar=drop)
    ordem_s = [f for f, _ in cont_s.most_common()]

    n_sem = sum(1 for h in por_obra if not h)
    n_multi = sum(1 for h in por_obra if len(h) > 1)

    out = {
        "_doc": ("codificação do corpus pelas cinco funções do Modelo de Sistema Viável. "
                 "Proxy LÉXICO sobre título+resumo, multirrótulo. NÃO usa o rótulo de eixo, "
                 "logo não herda a circularidade do H1."),
        "_limite": ("não distingue obra que TRATA da função daquela que a MENCIONA; "
                    "vocabulário do projeto, sem validação externa; ver teste de sensibilidade."),
        "n_obras_com_resumo": len(obras),
        "n_sem_nenhuma_funcao": n_sem,
        "n_multirrotulo": n_multi,
        "contagem": {FUNCOES[f]["nome"]: cont.get(f, 0) for f in FUNCOES},
        "percentual": {FUNCOES[f]["nome"]: round(100 * cont.get(f, 0) / n, 1) for f in FUNCOES},
        "ordem": [FUNCOES[f]["nome"] for f in ordem],
        "termo_dominante_por_funcao": {
            FUNCOES[f]["nome"]: {"termo": t, "n": c} for f, (t, c) in dominantes.items()},
        "sensibilidade_sem_termo_dominante": {
            "_doc": "derruba o termo mais frequente de cada função e recompõe a ordenação",
            "termos_removidos": sorted(x for x in drop if x),
            "contagem": {FUNCOES[f]["nome"]: cont_s.get(f, 0) for f in FUNCOES},
            "ordem": [FUNCOES[f]["nome"] for f in ordem_s],
            "ordem_preservada": ordem == ordem_s,
        },
    }
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    print(f"obras com resumo: {len(obras)} | sem função: {n_sem} | multirrótulo: {n_multi}")
    for f in sorted(FUNCOES, key=lambda k: -cont.get(k, 0)):
        pct = 100 * cont.get(f, 0) / n
        print(f"  {FUNCOES[f]['nome']:26} {cont.get(f,0):4}  {pct:5.1f}%  {'#'*int(pct/2)}")
    s = out["sensibilidade_sem_termo_dominante"]
    print(f"\nsensibilidade (sem {', '.join(s['termos_removidos'])}):")
    for f in sorted(FUNCOES, key=lambda k: -cont_s.get(k, 0)):
        print(f"  {FUNCOES[f]['nome']:26} {cont_s.get(f,0):4}")
    print(f"ordem preservada: {s['ordem_preservada']}")
    print(f"-> {OUT}")


if __name__ == "__main__":
    main()
