"""Auditoria dos pressupostos do método (só stdlib).

Parte 1 — inventário. Cada pressuposto embutido no código aparece aqui com:
  `id`          rótulo curto usado no laudo (AUDITORIA.md)
  `arquivo`     onde está
  `ancora`      trecho literal do código que o implementa — **verificado**: se o código
                mudar e a âncora desaparecer, `python src/audit.py --inventario` falha.
                Isso evita o inventário virar prosa desatualizada.
  `assume`      o que o pressuposto afirma sobre o mundo (não sobre o código)
  `falsifica`   o teste que o derrubaria
  `risco`       alto / medio / baixo — quanto da conclusão depende dele

Uso:
    python src/audit.py --inventario     → data/audit_assumptions.json
"""
import itertools
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, ROOT, load_json, norm, save_json  # noqa: E402

SRC = os.path.join(ROOT, "src")

ASSUMPTIONS = [
    # ── rótulo da obra ──
    dict(id="A1-rotulo-editorial", arquivo="common.py",
         ancora='SIGNAL_FIELDS = ("publisher", "contrib_other", "serie", "title_alt", "doi"',
         assume="A unidade que editou a obra é a unidade que a produziu, e os campos "
                "editoriais do DSpace registram isso de forma confiável.",
         falsifica="Amostra de obras com rótulo conferida contra a filiação declarada dos "
                   "autores no texto: se a editora discordar da filiação em parcela "
                   "relevante, o rótulo mede circuito editorial, não autoria.",
         risco="alto"),
    dict(id="A2-titulo-nao-rotula", arquivo="common.py",
         ancora='# sem dc.title: "políticas setoriais" aparece em títulos comuns',
         assume="Um texto *sobre* a Diest não é um texto *da* Diest — decisão correta e "
                "conservadora; o custo é perder obras cuja única pista está no título.",
         falsifica="Contar obras sem rótulo cujo título traz nome de diretoria: se forem "
                   "muitas, a cobertura do rótulo é pior do que parece.",
         risco="baixo"),
    dict(id="A3-seis-diretorias", arquivo="common.py", ancora='"DINTE": [r"\\bdinte\\b"',
         assume="As seis diretorias de pesquisa esgotam o espaço de lotação relevante; "
                "assessorias, presidência e unidades de apoio não produzem obra assinada "
                "que distorça o contraste.",
         falsifica="Verificar se há obras de unidades fora das seis com volume comparável.",
         risco="medio"),
    # ── pessoa → diretoria ──
    dict(id="A4-meia-vida-4a", arquivo="attribute.py", ancora="HALF_LIFE = 4.0",
         assume="A lotação recente importa mais, e 4 anos é a escala em que a migração "
                "entre diretorias se dilui. O número não vem de nenhuma medida.",
         falsifica="Varredura HALF_LIFE ∈ {3,4,6}: se a lista de membros ou o z mudarem "
                   "muito, o número arbitrário está carregando a conclusão.",
         risco="medio"),
    dict(id="A5-min-share", arquivo="attribute.py", ancora="MIN_SHARE = 0.5",
         assume="Metade do peso na diretoria dominante basta para dizer que a pessoa é "
                "dela. Com seis diretorias no contraste, 50% é exigente; mas é um limiar "
                "escolhido, não estimado.",
         falsifica="Varredura MIN_SHARE ∈ {0,4; 0,5; 0,6} e estabilidade dos top-10.",
         risco="medio"),
    dict(id="A6-min-tagged-2", arquivo="attribute.py", ancora="MIN_TAGGED = 2",
         assume="Duas obras rotuladas são evidência suficiente de lotação.",
         falsifica="Quantas pessoas são atribuídas com exatamente 2 obras, e o que muda "
                   "ao exigir 3. Na planilha, 149 de 280 são de confiança moderada.",
         risco="alto"),
    dict(id="A7-cargo-prevalece", arquivo="attribute.py", ancora='jobs[aid]["diretoria"], "explicita"',
         assume="O cargo no perfil de Pessoa do repositório é atual. Perfil de repositório "
                "raramente é atualizado quando alguém muda de diretoria.",
         falsifica="Comparar as 21 pessoas de confiança explícita com a resposta das "
                   "chefias: é o estrato que deveria ter precisão ~100%.",
         risco="medio"),
    dict(id="A8-ativo-3-anos", arquivo="attribute.py", ancora="max(ys) >= NOW_YEAR - 3",
         assume="Publicar nos últimos 3 anos equivale a estar ativo no Ipea hoje. Confunde "
                "vínculo com publicação: quem saiu em 2024 segue 'ativo'.",
         falsifica="Cruzar com o diretório do portal: quantos 'ativos por produção' não "
                   "estão no diretório e já saíram.",
         risco="medio"),
    dict(id="A9-ativo-analise", arquivo="analysis.py",
         ancora='authors[a]["staff"] or authors[a]["n_tagged"] >= 3',
         assume="Segundo critério de ativo, diferente do de attribute.py, aplicado só na "
                "análise. Dois conceitos de 'ativo' coexistem no projeto (65/56 contra "
                "166 linhas 'atribuido+ativo' na planilha).",
         falsifica="Explicitar os dois conjuntos e checar se o relatório usa o rótulo certo "
                   "em cada seção.",
         risco="medio"),
    # ── identidade ──
    dict(id="A10-identidade-frouxa", arquivo="common.py", ancora="def loose_key(",
         assume="(sobrenome, 1º prenome) identifica unicamente alguém dentro do quadro do Ipea.",
         falsifica="Procurar colisões de loose_key no quadro e entre quadro e externos.",
         risco="medio"),
    dict(id="A11-externo-por-assinatura", arquivo="attribute.py", ancora='return "ext:" + "|".join(k)',
         assume="Fora do quadro, cada assinatura normalizada é uma pessoa. Parte a mesma "
                "pessoa em duas quando ela assina de formas diferentes — viés declarado "
                "como conservador para pontes, mas não medido.",
         falsifica="Agrupar ext: por loose_key e ver quantas pessoas se fundiriam, e se "
                   "alguma fusão criaria ponte DIEST×DISET nova.",
         risco="medio"),
    dict(id="A12-peso-dividido", arquivo="attribute.py", ancora='a["w"][d] += w / len(dirs)',
         assume="Obra com duas diretorias no rótulo divide o peso igualmente. Obra "
                "co-editada pesa menos para cada lado do que obra exclusiva.",
         falsifica="Comparar com peso cheio para cada diretoria e ver mudança na atribuição.",
         risco="baixo"),
    # ── o achado central ──
    dict(id="A13-mista-pelas-pessoas", arquivo="analysis.py", ancora="def is_mixed(e, lab):",
         assume="Obra mista é obra com assinante das duas diretorias — onde a diretoria da "
                "pessoa veio das obras. É a circularidade do METODO §5, e ela é "
                "**anti-conservadora na direção do silo**: coautores frequentes tendem a "
                "receber o mesmo rótulo porque partilham as mesmas obras rotuladas.",
         falsifica="Rodar a atribuição sobre dados sintéticos SEM silo e ver quanto de z "
                   "negativo o método fabrica sozinho. Teste decisivo da auditoria.",
         risco="alto"),
    dict(id="A14-focus-edges", arquivo="analysis.py",
         ancora="focus_edges = [(it, e) for it, e in edges if any(dir_of.get(a) in FOCUS for a in e)]",
         assume="O denominador certo são as obras com ao menos um membro DIEST ou DISET. "
                "Inclui 1 autor só, que nunca pode ser mista — infla o denominador do "
                "nulo com obras estruturalmente inelegíveis.",
         falsifica="Recontar com denominador elegível (|e|≥2) e ver o efeito em μ e z.",
         risco="alto"),
    dict(id="A15-nulo-permutacao", arquivo="analysis.py", ancora="rng.shuffle(labels)",
         assume="Trocar os rótulos de diretoria entre os 261 membros, mantendo o "
                "hipergrafo, produz o mundo contrafactual 'a diretoria não influencia com "
                "quem se escreve'. Ignora grau do autor, tamanho da obra e o fato de "
                "boletim e nota técnica serem intra-diretoria por construção editorial.",
         falsifica="Comparar com nulo estratificado, nulo de configuração de hipergrafo "
                   "(grau e tamanho preservados) e nulo restrito às obras elegíveis.",
         risco="alto"),
    dict(id="A16-janela-2010", arquivo="analysis.py", ancora='ap.add_argument("--start", type=int, default=2010)',
         assume="2010 é o começo útil da série. 16 anos numa janela única trata como "
                "simultâneas reorganizações administrativas sucessivas (a DISET só passa a "
                "ter 'Regulação' no nome depois).",
         falsifica="Repetir por quinquênio e ver se o silo é estável ou tem tendência.",
         risco="alto"),
    # ── estimadores derivados ──
    dict(id="A17-newman", arquivo="analysis.py", ancora='pair_w[(a, b)] += 1.0 / (len(e) - 1)',
         assume="1/(|e|−1) desconta coletânea. É a convenção de Newman (2001) para "
                "coautoria projetada.",
         falsifica="Comparar ranking de pares com peso 1 e com 1/(|e|−1).",
         risco="baixo"),
    dict(id="A18-coletanea-ge4", arquivo="analysis.py", ancora="big_only = sum(1 for v in pair_min.values() if v >= 4)",
         assume="4 ou mais assinaturas = coletânea, não colaboração direta. Limiar escolhido.",
         falsifica="Curva de 27/45 ao variar o limiar entre 3 e 6.",
         risco="medio"),
    dict(id="A19-s-line", arquivo="analysis.py", ancora="def s_line_components(edges, s):",
         assume="Componente do grafo-linha s mede 'equipe recorrente'; e a diretoria "
                "dominante da obra é a maioria simples dos assinantes rotulados.",
         falsifica="Ver quantas obras ficam com dominante None (empate) e o efeito no "
                   "número de componentes que juntam os dois lados.",
         risco="medio"),
    dict(id="A20-corretor-media-geometrica", arquivo="analysis.py", ancora='"score": round(math.sqrt(nd * ns), 2)',
         assume="√(nD·nS) mede intermediação. Não é medida de intermediação: ignora se os "
                "vizinhos já se conhecem entre si, que é o que define o corretor (Burt).",
         falsifica="Recalcular por intermediação de fato e por constraint de Burt e "
                   "comparar o ranking dos seis nomes do relatório.",
         risco="alto"),
    dict(id="A21-trajetoria-20pc", arquivo="analysis.py", ancora='w.get(D, 0) / tot >= 0.2 and w.get(S, 0) / tot >= 0.2',
         assume="20% do peso em cada lado indica migração de diretoria. Não distingue "
                "migração de colaboração sustentada nem de erro de identidade.",
         falsifica="Ver a série temporal de cada caso: migração tem quebra datada.",
         risco="medio"),
    # ── vocabulário e zonas ──
    dict(id="A22-log-odds-prior", arquivo="analysis.py", ancora="alpha0 = alpha0 or max(100.0, 0.01 * n0)",
         assume="α₀ = 1% do corpus implementa o prior informativo de Monroe, Colaresi & "
                "Quinn (2008); o prior é o Ipea inteiro na janela.",
         falsifica="Conferir a fórmula da variância contra o artigo e a sensibilidade a α₀.",
         risco="medio"),
    dict(id="A23-perfil-exclusivo", arquivo="analysis.py", ancora="if len(sides) == 1:  # contraste limpo",
         assume="Só obra exclusiva de um lado define o perfil característico — limpo, mas "
                "exclui por construção justamente as obras de convergência.",
         falsifica="Comparar os termos característicos com e sem as obras mistas.",
         risco="baixo"),
    dict(id="A24-termos", arquivo="analysis.py", ancora="if 2 < len(t) < 90:",
         assume="VCIpea, palavra-chave e classificação são comparáveis entre si e "
                "somáveis; sinonímia de palavra-chave livre não distorce as zonas.",
         falsifica="Medir quanto das zonas vem de VCIpea (controlado) e quanto de "
                   "palavra-chave livre; checar pares de sinônimos óbvios separados.",
         risco="alto"),
    dict(id="A25-areas-peso-2", arquivo="analysis.py", ancora='aprof[a][k] += 2',
         assume="A área declarada no portal vale duas obras. Número sem justificativa.",
         falsifica="Variar o peso em {0,1,2,5} e ver efeito nos pares potenciais.",
         risco="medio"),
    dict(id="A26-zona-2x2", arquivo="analysis.py", ancora="if nd >= 2 and ns >= 2:",
         assume="Dois ativos de cada lado usando o mesmo termo caracteriza zona de "
                "convergência. Em 65×56 ativos, dois de cada lado é um piso muito baixo.",
         falsifica="Exigir 3 e 4 de cada lado; ver quais zonas sobrevivem, sobretudo a de "
                   "AIR/governança regulatória, que é a mais citada do relatório.",
         risco="alto"),
    dict(id="A27-escore-zona", arquivo="analysis.py", ancora="bal * math.log(1 + nd + ns)",
         assume="Equilíbrio × log(volume) ordena a importância de uma zona. Escore ad hoc, "
                "sem unidade e sem incerteza — mas o relatório ordena as zonas por ele.",
         falsifica="Reordenar por volume puro e por equilíbrio puro e comparar o top-5.",
         risco="medio"),
    dict(id="A28-jaccard-03", arquivo="analysis.py", ancora="if len(u1 & u2) / len(u1 | u2) >= 0.3:",
         assume="Jaccard de usuários ≥0,3 junta dois termos na mesma zona. Union-find é "
                "transitivo: encadeia A–B–C mesmo com A e C sem sobreposição alguma.",
         falsifica="Variar o limiar e medir a maior zona; comparar com agrupamento não "
                   "transitivo (clique ou modularidade).",
         risco="alto"),
    # ── sugestões ──
    dict(id="A29-par-potencial", arquivo="analysis.py", ancora="score = c * (1 + 0.25 * min(len(cm), 4))",
         assume="Similaridade de vocabulário mais coautor comum prediz colaboração "
                "possível. Nunca foi validado: não se sabe se prevê coautoria futura.",
         falsifica="Validação temporal (item 7 da fila): treinar com ≤2021 e medir "
                   "precisão@k nas obras mistas de 2022–2026 contra linha de base aleatória.",
         risco="alto"),
    dict(id="A30-equipe-2-2-1", arquivo="analysis.py", ancora="team = topD[:2] + topS[:2]",
         assume="Equipe viável é 2+2 mais um corretor. Forma plausível para nota técnica "
                "conjunta; é escolha de desenho, não resultado de dado.",
         falsifica="Comparar com a composição real das 45 obras mistas existentes.",
         risco="medio"),
    dict(id="A31-items-by-side", arquivo="analysis.py",
         ancora='sides = {d for d in FOCUS if d in it["dirs"] or any(dir_of.get(a) == d for a in it["authors"])}',
         assume="'Obra da diretoria' é rótulo editorial OU ter membro dela. Mistura duas "
                "definições na mesma contagem (items_by_side) e no perfil de produção.",
         falsifica="Separar as duas definições e reportar as duas contagens.",
         risco="medio"),
]


def verify(strict=True):
    """Confere que cada âncora existe no arquivo indicado. Inventário que não acompanha o
    código é pior do que nenhum, então aqui a divergência é erro."""
    problems = []
    cache = {}
    for a in ASSUMPTIONS:
        path = os.path.join(SRC, a["arquivo"])
        if path not in cache:
            with open(path, encoding="utf-8") as f:
                cache[path] = f.read()
        if a["ancora"] not in cache[path]:
            problems.append(f"{a['id']}: âncora não encontrada em {a['arquivo']}: {a['ancora'][:60]!r}")
    if problems and strict:
        raise AssertionError("inventário desatualizado:\n" + "\n".join(problems))
    return problems


def inventory(save=True):
    verify()
    out = {"n": len(ASSUMPTIONS),
           "por_risco": {r: sum(1 for a in ASSUMPTIONS if a["risco"] == r)
                         for r in ("alto", "medio", "baixo")},
           "assumptions": ASSUMPTIONS}
    if save:
        save_json("audit_assumptions.json", out)
    return out


def zone_gate(min_side=2, jacc=0.3, generic=0.25, merge=None, start=2010):
    """Reproduz o portão que `analysis.py` usa para constituir zona de convergência.

    Serve para responder por que o campo digital não vira zona. `merge` é uma lista de
    termos a fundir num único termo sintético — a operação que a sinonímia (A24) impede
    o pipeline de fazer sozinho.
    """
    import collections

    from analysis import item_terms
    authors = load_json("authors.json")
    items = [i for i in load_json("items_tagged.json") if i["year"] and i["year"] >= start]
    dir_of = {a: v["diretoria"] for a, v in authors.items() if v["diretoria"]}
    members = {d: {a for a, x in dir_of.items() if x == d} for d in FOCUS}
    active = {d: {a for a in members[d] if authors[a]["active"]
                  and (authors[a]["staff"] or authors[a]["n_tagged"] >= 3)} for d in FOCUS}
    act = active[FOCUS[0]] | active[FOCUS[1]]
    mset = set(merge or [])
    MERGED = "__campo_digital__"
    aprof = {a: collections.Counter() for a in act}
    for it in items:
        tc = item_terms(it, with_classes=False)
        if mset:
            hit = sum(v for t, v in tc.items() if t in mset)
            if hit:
                tc = collections.Counter({t: v for t, v in tc.items() if t not in mset})
                tc[MERGED] = hit
        for a in it["authors"]:
            if a in aprof:
                aprof[a].update(tc)
    for a in act:
        for ar in authors[a]["areas"]:
            aprof[a][norm(ar)] += 2
    users = collections.defaultdict(set)
    for a, c in aprof.items():
        for t in c:
            users[t].add(a)
    n_act = len(act) or 1
    conv = []
    for t, u in users.items():
        if len(u) > generic * n_act:
            continue
        nd = sum(1 for a in u if a in active[FOCUS[0]])
        ns = sum(1 for a in u if a in active[FOCUS[1]])
        if nd >= min_side and ns >= min_side:
            bal = 2 * min(nd, ns) / (nd + ns)
            conv.append((t, nd, ns, bal * math.log(1 + nd + ns)))
    conv.sort(key=lambda x: -x[3])
    conv = conv[:60]
    parent = {t: t for t, *_ in conv}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x
    for (t1, *_), (t2, *_) in itertools.combinations(conv, 2):
        u1, u2 = users[t1], users[t2]
        if len(u1 & u2) / len(u1 | u2) >= jacc:
            parent[find(t1)] = find(t2)
    groups = collections.defaultdict(list)
    for t, nd, ns, sc in conv:
        groups[find(t)].append((t, nd, ns, sc))
    gl = sorted(groups.values(), key=lambda g: -sum(x[3] for x in g))
    return {"n_ativos": n_act, "n_termos_convergentes": len(conv), "n_zonas": len(gl),
            "maior_zona": len(gl[0]) if gl else 0,
            "zonas": [{"termos": [x[0] for x in g], "score": round(sum(x[3] for x in g), 2)}
                      for g in gl],
            "users": users, "active": active, "conv": conv}


def zone_diagnosis(save=True):
    """Por que o campo digital não aparece entre as zonas do RELATORIO.md."""
    lex = load_json("digital_lexicon.json")
    dterms = [x["term"] for x in lex["lexico"]]
    base = zone_gate()
    users, active = base["users"], base["active"]
    # 1. cada termo digital, isolado, contra o piso de 2 ativos de cada lado
    per_term = []
    for t in dterms:
        u = users.get(t, set())
        nd = sum(1 for a in u if a in active[FOCUS[0]])
        ns = sum(1 for a in u if a in active[FOCUS[1]])
        per_term.append({"termo": t, "usuarios_ativos": len(u), "DIEST": nd, "DISET": ns,
                         "passa_piso_2": nd >= 2 and ns >= 2})
    per_term.sort(key=lambda r: (-min(r["DIEST"], r["DISET"]), -r["usuarios_ativos"]))
    passam = [r for r in per_term if r["passa_piso_2"]]
    # 2. Fundindo o léxico num termo só — a operação que a sinonímia (A24) impede o
    #    pipeline de fazer. Sem teto de genericidade, para separar os três mecanismos
    #    de exclusão: piso de 2+2, teto de 25% dos ativos e corte do top-60.
    MG = "__campo_digital__"
    merged = zone_gate(merge=dterms, generic=1.0)
    users_m, act_m = merged["users"], merged["active"]
    full = []
    for t, u in users_m.items():
        d_ = sum(1 for a in u if a in act_m[FOCUS[0]])
        s_ = sum(1 for a in u if a in act_m[FOCUS[1]])
        if d_ >= 2 and s_ >= 2:
            full.append((t, d_, s_, (2 * min(d_, s_) / (d_ + s_)) * math.log(1 + d_ + s_)))
    full.sort(key=lambda x: -x[3])
    rank = next((i + 1 for i, x in enumerate(full) if x[0] == MG), None)
    mu = next((x for x in full if x[0] == MG), None)
    u_m = users_m.get(MG, set())
    fundido = {
        "usuarios_ativos": len(u_m),
        "share_dos_ativos": round(len(u_m) / merged["n_ativos"], 3),
        "DIEST": mu[1] if mu else 0, "DISET": mu[2] if mu else 0,
        "equilibrio": round(2 * min(mu[1], mu[2]) / (mu[1] + mu[2]), 3) if mu else None,
        "score": round(mu[3], 3) if mu else None,
        "posicao_entre_convergentes": rank, "n_convergentes_total": len(full),
        "score_do_60o": round(full[59][3], 3) if len(full) >= 60 else None,
        "passa_piso_2x2": bool(mu),
        "passa_teto_genericidade": len(u_m) <= 0.25 * merged["n_ativos"],
        "entra_no_top60": bool(rank and rank <= 60),
    }
    # 3. sensibilidade do piso e do Jaccard
    sens = []
    for ms in (2, 3, 4):
        for jc in (0.2, 0.3, 0.4):
            g = zone_gate(min_side=ms, jacc=jc)
            sens.append({"piso": ms, "jaccard": jc, "n_termos": g["n_termos_convergentes"],
                         "n_zonas": g["n_zonas"], "maior_zona": g["maior_zona"]})
    out = {
        "base": {"n_ativos": base["n_ativos"], "n_termos_convergentes": base["n_termos_convergentes"],
                 "n_zonas": base["n_zonas"], "maior_zona": base["maior_zona"]},
        "termos_digitais_no_portao": per_term[:20],
        "n_termos_digitais_que_passam": len(passam),
        "termos_que_passam": passam,
        "fundido": fundido,
        "sensibilidade_piso_jaccard": sens,
    }
    if save:
        save_json("audit_zone_diagnosis.json", out)
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--inventario" in argv:
        out = inventory()
        print(f"{out['n']} pressupostos: {out['por_risco']}", file=sys.stderr)
        print(" ".join(a["id"] for a in ASSUMPTIONS if a["risco"] == "alto"), file=sys.stderr)
    elif "--zonas" in argv:
        o = zone_diagnosis()
        b = o["base"]
        print(f"base: {b['n_ativos']} ativos · {b['n_termos_convergentes']} termos convergentes · "
              f"{b['n_zonas']} zonas (maior com {b['maior_zona']} termos)", file=sys.stderr)
        print(f"termos digitais que passam o piso de 2+2: {o['n_termos_digitais_que_passam']} "
              f"de {len(load_json('digital_lexicon.json')['lexico'])}", file=sys.stderr)
        f = o["fundido"]
        print(f"fundido num termo só: {f['usuarios_ativos']} ativos ({f['share_dos_ativos']:.1%}), "
              f"DIEST {f['DIEST']} / DISET {f['DISET']}, equilíbrio {f['equilibrio']}, "
              f"escore {f['score']} → posição {f['posicao_entre_convergentes']} de "
              f"{f['n_convergentes_total']} (60º = {f['score_do_60o']})", file=sys.stderr)
        print(f"  piso 2+2: {'passa' if f['passa_piso_2x2'] else 'nao passa'} · "
              f"teto 25%: {'passa' if f['passa_teto_genericidade'] else 'nao passa'} · "
              f"top-60: {'entra' if f['entra_no_top60'] else 'NAO ENTRA'}", file=sys.stderr)
    else:
        print(__doc__, file=sys.stderr)


if __name__ == "__main__":
    main()
