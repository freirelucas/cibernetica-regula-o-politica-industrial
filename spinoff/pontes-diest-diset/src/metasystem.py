"""Metassistema: instrumentos de planejamento de longo prazo do governo federal (só stdlib).

Por que este módulo existe. Os três eixos do produto editorial — transformação digital,
ecológica e demográfica — **não** vêm do Planejamento Estratégico Institucional do Ipea.
O PEI 2024-2031 tem quinze objetivos estratégicos e vinte e oito projetos de portfólio, e
neles "transformação digital" aparece uma única vez, no objetivo 6, como *modernização de
processos de trabalho* — gestão interna, não agenda de pesquisa (fonte: Plano Estratégico
de Inserção Internacional do Ipea, Relatório Institucional 2026, quadro 1, p. 8;
DOI 10.38116/RI-PEIIIPEA). A expressão "três transformações" devolve dois resultados no
Repositório, de 2007 e 2015, sem relação com a tríade.

Onde a tríade vive, então, é no **sistema federal de planejamento**: cada transformação é
eixo ou missão de um instrumento (PPA, Plano de Transformação Ecológica, Nova Indústria
Brasil, E-Digital e assim por diante). O Ipea atravessa esses instrumentos — assessora,
avalia e antecipa (objetivos 2, 3 e 4 do PEI) — e é nesse sentido que opera como
metassistema de temas.

O que este módulo faz: registra os instrumentos com suas variantes de nome, mede quanta
produção do Ipea trata de cada um (dado duro, do corpus local) e cruza com a diretoria que
assina. O campo `verificado` separa o que foi conferido em fonte oficial do que ainda é
candidato — nenhum número de presença depende dessa verificação, mas a descrição do
instrumento depende.

Uso:
    python src/metasystem.py --varredura   → data/metasystem.json
"""
import collections
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, load_items, load_json, norm, save_json, year_of  # noqa: E402

# Cada instrumento: variantes de nome como expressão regular sobre texto normalizado.
# `eixos` descreve a estrutura temática declarada do instrumento; fica NULO quando ainda
# não foi conferida em fonte oficial — não inventar estrutura.
INSTRUMENTOS = [
    dict(sigla="PPA", nome="Plano Plurianual 2024-2027", orgao="MPO", horizonte="2024-2027",
         verificado=False, eixos=None,
         pats=[r"plano plurianual"], neg=[r"power purchase"]),
    dict(sigla="EFD", nome="Estratégia Federal de Desenvolvimento", orgao="MPO/SPI",
         horizonte="2020-2031", verificado=False, eixos=None,
         pats=[r"estrategia federal de desenvolvimento", r"\befd\b"]),
    dict(sigla="PTE", nome="Plano de Transformação Ecológica", orgao="Ministério da Fazenda",
         horizonte="2023-", verificado=False, eixos=None,
         pats=[r"plano de transformacao ecologica"]),
    dict(sigla="NIB", nome="Nova Indústria Brasil", orgao="MDIC/CNDI", horizonte="2024-2033",
         verificado=False, eixos=None,
         pats=[r"nova industria brasil", r"\bnib\b"]),
    dict(sigla="E-Digital", nome="Estratégia Brasileira de Transformação Digital",
         orgao="MCTI", horizonte="2018-", verificado=False, eixos=None,
         pats=[r"estrategia brasileira de transformacao digital", r"e.digital"]),
    dict(sigla="EGD", nome="Estratégia de Governo Digital", orgao="MGI", horizonte="2024-2027",
         verificado=False, eixos=None,
         pats=[r"estrategia (nacional )?de govern(o|anca) digital", r"\begd\b"]),
    dict(sigla="PBIA", nome="Plano Brasileiro de Inteligência Artificial / EBIA",
         orgao="MCTI", horizonte="2024-2028", verificado=False, eixos=None,
         pats=[r"plano brasileiro de inteligencia artificial", r"\bpbia\b",
               r"estrategia brasileira de inteligencia artificial", r"\bebia\b"]),
    dict(sigla="ENCTI", nome="Estratégia Nacional de Ciência, Tecnologia e Inovação",
         orgao="MCTI", horizonte="2024-2030", verificado=False, eixos=None,
         pats=[r"estrategia nacional de ciencia,? tecnologia e inovacao", r"\bencti\b"]),
    dict(sigla="PlanoClima", nome="Plano Nacional sobre Mudança do Clima", orgao="MMA",
         horizonte="2024-2035", verificado=False, eixos=None,
         pats=[r"plano nacional sobre mudanca do clima", r"plano clima\b",
               r"politica nacional sobre mudanca do clima"]),
    dict(sigla="PNA", nome="Plano Nacional de Adaptação à Mudança do Clima", orgao="MMA",
         horizonte="2016-", verificado=False, eixos=None,
         pats=[r"plano nacional de adaptacao"]),
    dict(sigla="PNDU", nome="Política Nacional de Desenvolvimento Urbano", orgao="MCid",
         horizonte="2024-", verificado=False, eixos=None,
         pats=[r"politica nacional de desenvolvimento urbano", r"\bpndu\b"]),
    dict(sigla="PNC", nome="Política Nacional de Cuidados", orgao="MDS/MMulheres",
         horizonte="2024-", verificado=False, eixos=None,
         pats=[r"politica nacional de cuidados?", r"plano nacional de cuidados?",
               r"politica nacional do cuidado"]),
    dict(sigla="Agenda2030", nome="Agenda 2030 e Objetivos de Desenvolvimento Sustentável",
         orgao="ONU/CNODS", horizonte="2015-2030", verificado=False, eixos=None,
         pats=[r"agenda 2030", r"objetivos de desenvolvimento sustentavel", r"\bods\b"]),
    dict(sigla="NovoPAC", nome="Novo Programa de Aceleração do Crescimento", orgao="Casa Civil",
         horizonte="2023-2026", verificado=False, eixos=None,
         pats=[r"novo pac\b", r"programa de aceleracao do crescimento"]),
    dict(sigla="PNE", nome="Plano Nacional de Educação", orgao="MEC", horizonte="2014-2024",
         verificado=False, eixos=None,
         pats=[r"plano nacional de educacao", r"\bpne\b"]),
    dict(sigla="PLANTE", nome="Plano Nacional de Transição Energética", orgao="MME",
         horizonte="2024-", verificado=False, eixos=None,
         pats=[r"plano nacional de transicao energetica", r"\bplante\b"]),
    dict(sigla="PNRS", nome="Política Nacional de Resíduos Sólidos / Plano Nacional",
         orgao="MMA", horizonte="2010-", verificado=False, eixos=None,
         pats=[r"politica nacional de residuos solidos", r"\bpnrs\b", r"planares"]),
    dict(sigla="EstratSaude", nome="Complexo Econômico-Industrial da Saúde", orgao="MS/MDIC",
         horizonte="2023-", verificado=False, eixos=None,
         pats=[r"complexo economico.industrial da saude", r"\bceis\b"]),
]

# Vocabulário TEMÁTICO de cada instrumento — o assunto, não o plano. A distinção importa:
# 77 obras falam de "transição energética" e nenhuma cita o Plano Nacional de Transição
# Energética. Confundir as duas coisas transforma ausência de diálogo com o instrumento em
# presença.
PATS_TEMA = {
    "PTE": [r"transformacao ecologica", r"economia verde", r"descarbonizacao"],
    "PLANTE": [r"transicao energetica", r"energias? renovavel(is)?", r"hidrogenio verde"],
    "PlanoClima": [r"mudanca do clima", r"mudancas climaticas", r"politica climatica"],
    "PNA": [r"adaptacao (a mudanca do clima|climatica)", r"resiliencia climatica"],
    "PNRS": [r"residuos solidos", r"economia circular", r"reciclagem"],
    "E-Digital": [r"transformacao digital", r"digitalizacao", r"economia digital"],
    "EGD": [r"governo digital", r"governo eletronico", r"servicos publicos digitais"],
    "PBIA": [r"inteligencia artificial", r"aprendizado de maquina", r"algoritm"],
    "NIB": [r"politica industrial", r"neoindustrializacao", r"reindustrializacao"],
    "PPA": [r"plano plurianual", r"planejamento governamental", r"orcamento publico"],
    "EFD": [r"estrategia de desenvolvimento", r"desenvolvimento de longo prazo"],
    "ENCTI": [r"politica de (ciencia e tecnologia|inovacao)", r"ciencia,? tecnologia e inovacao"],
    "PNDU": [r"desenvolvimento urbano", r"politica urbana"],
    "PNC": [r"politica de cuidados?", r"economia do cuidado", r"cuidado de longa duracao"],
    "EstratSaude": [r"complexo (economico.)?industrial da saude", r"industria farmaceutica"],
    "Agenda2030": [r"desenvolvimento sustentavel"],
    "NovoPAC": [r"investimento publico em infraestrutura"],
    "PNE": [r"politica educacional", r"financiamento da educacao"],
}

# A qual transformação cada instrumento responde, segundo o próprio instrumento.
# Preenchido só depois da verificação; aqui entra como hipótese a conferir.
EIXO_HIPOTESE = {
    "PTE": ["ecologica"], "PlanoClima": ["ecologica"], "PNA": ["ecologica"],
    "PLANTE": ["ecologica"], "PNRS": ["ecologica"],
    "E-Digital": ["digital"], "EGD": ["digital"], "PBIA": ["digital"],
    "PNC": ["demografica"], "EstratSaude": ["demografica"],
    "NIB": ["digital", "ecologica", "demografica"],
    "PPA": ["digital", "ecologica", "demografica"],
    "EFD": ["digital", "ecologica", "demografica"],
    "ENCTI": ["digital", "ecologica"], "Agenda2030": ["ecologica", "demografica"],
    "NovoPAC": ["ecologica"], "PNDU": ["ecologica"], "PNE": ["demografica"],
}


def fields_blob(it):
    """Título, título alternativo, resumo, série e palavras-chave — tudo normalizado."""
    parts = []
    for f in ("title", "title_alt", "abstract", "serie", "series", "vcipea", "keywords"):
        parts.extend(it.get(f, []) or [])
    return norm(" | ".join(parts))


def sweep(start=2010, save=True):
    authors = load_json("authors.json")
    dir_of = {a: v["diretoria"] for a, v in authors.items() if v["diretoria"]}
    tagged = {it["uuid"]: it for it in load_json("items_tagged.json")}
    comp = {i["sigla"]: re.compile("|".join(i["pats"])) for i in INSTRUMENTOS}
    negs = {i["sigla"]: re.compile("|".join(i["neg"])) if i.get("neg") else None
            for i in INSTRUMENTOS}
    comp_t = {s_: re.compile("|".join(ps)) for s_, ps in PATS_TEMA.items()}

    res = {i["sigla"]: {"obras": 0, "obras_janela": 0, "tema": 0, "tema_janela": 0,
                        "tema_dir": collections.Counter(), "tema_mistas": 0,
                        "por_ano": collections.Counter(),
                        "por_diretoria": collections.Counter(),
                        "mistas_diest_diset": 0, "exemplos": []} for i in INSTRUMENTOS}
    n_total = 0
    co = collections.Counter()
    for it in load_items():
        n_total += 1
        blob = fields_blob(it)
        hit = [s_ for s_, c in comp.items()
               if c.search(blob) and not (negs[s_] and negs[s_].search(blob))]
        hit_t = [s_ for s_, c in comp_t.items() if c.search(blob)]
        if not hit and not hit_t:
            continue
        y = year_of(it)
        tg = tagged.get(it["uuid"])
        dirs_au = set()
        if tg:
            dirs_au = {dir_of.get(a) for a in tg["authors"]} & set(FOCUS)
        for s_ in hit_t:
            r = res[s_]
            r["tema"] += 1
            if y and y >= start:
                r["tema_janela"] += 1
                for d in dirs_au:
                    r["tema_dir"][d] += 1
                if len(dirs_au) == 2:
                    r["tema_mistas"] += 1
        for s_ in hit:
            r = res[s_]
            r["obras"] += 1
            if y and y >= start:
                r["obras_janela"] += 1
                r["por_ano"][y] += 1
                for d in dirs_au:
                    r["por_diretoria"][d] += 1
                if len(dirs_au) == 2:
                    r["mistas_diest_diset"] += 1
                if len(r["exemplos"]) < 5:
                    r["exemplos"].append({"title": (it.get("title") or [""])[0][:120],
                                          "year": y,
                                          "uri": (it.get("uri") or [""])[0],
                                          "diretorias": sorted(dirs_au)})
        for a, b in ((x, y2) for i, x in enumerate(sorted(hit)) for y2 in sorted(hit)[i + 1:]):
            co[(a, b)] += 1

    out = {"n_corpus": n_total, "janela": start,
           "instrumentos": [], "co_ocorrencia_entre_instrumentos": []}
    for i in INSTRUMENTOS:
        r = res[i["sigla"]]
        out["instrumentos"].append({
            **{k: v for k, v in i.items() if k != "pats"},
            "eixo_hipotese": EIXO_HIPOTESE.get(i["sigla"], []),
            "obras_instrumento": r["obras"], "instrumento_desde_2010": r["obras_janela"],
            "obras_tema": r["tema"], "tema_desde_2010": r["tema_janela"],
            "tema_por_diretoria": dict(r["tema_dir"].most_common()),
            "tema_mistas_diest_diset": r["tema_mistas"],
            "por_ano": dict(sorted(r["por_ano"].items())),
            "por_diretoria": dict(r["por_diretoria"].most_common()),
            "mistas_diest_diset": r["mistas_diest_diset"],
            "exemplos": r["exemplos"],
        })
    out["instrumentos"].sort(key=lambda x: -x["tema_desde_2010"])
    out["co_ocorrencia_entre_instrumentos"] = [
        {"a": a, "b": b, "obras": n} for (a, b), n in co.most_common(25)]
    if save:
        save_json("metasystem.json", out)
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--varredura" not in argv:
        print(__doc__, file=sys.stderr)
        return
    o = sweep()
    print(f"corpus {o['n_corpus']} obras · janela ≥{o['janela']}", file=sys.stderr)
    for i in o["instrumentos"]:
        d = i["por_diretoria"]
        dt = i["tema_por_diretoria"]
        print(f"  {i['sigla']:11s} inst {i['instrumento_desde_2010']:4d} | tema "
              f"{i['tema_desde_2010']:5d}  DIEST {dt.get('DIEST', 0):4d} / "
              f"DISET {dt.get('DISET', 0):4d}  mistas {i['tema_mistas_diest_diset']:3d}  "
              f"eixo {'+'.join(i['eixo_hipotese']) or '—'}", file=sys.stderr)
    print("\n  pares de instrumentos que mais co-ocorrem:", file=sys.stderr)
    for c in o["co_ocorrencia_entre_instrumentos"][:8]:
        print(f"    {c['a']:11s} × {c['b']:11s} {c['obras']:4d}", file=sys.stderr)


if __name__ == "__main__":
    main()
