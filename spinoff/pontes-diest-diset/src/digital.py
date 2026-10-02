"""Caso de uso — o campo da transformação digital no corpus do Ipea (só stdlib).

Por que um módulo próprio: o campo digital **não aparece** entre as 12 zonas de
convergência do RELATORIO.md, e a razão é metodológica, não substantiva. No corpus, 176
termos de indexação casam com um padrão digital; o mais frequente tem 66 ocorrências e
"transformação digital" tem 12, com 447 das 582 ocorrências em **palavra-chave livre**
contra 135 em VCIpea controlado. Nenhum termo isolado alcança o piso de "2 ativos de cada
diretoria" que `analysis.py` exige para constituir zona (pressuposto A26), e o agrupamento
por Jaccard de usuários (A28) não reúne sinônimos que não partilham usuários. Resultado: um
campo de centenas de obras fica invisível por fragmentação de vocabulário.

Este módulo delimita o campo pelo dado, em três etapas:

1. **Sementes** — termos do vocabulário **controlado** (VCIpea) que são digitais por
   definição. Lista curta e auditável; é o único ponto em que entra julgamento meu.
2. **Expansão por co-ocorrência** — todo termo que co-ocorre com as sementes dentro da
   mesma obra, medido pelo **índice de equivalência** de Callon (e = c²/(c_i·c_j), a
   medida corrente em análise de co-palavra) com teste hipergeométrico de significância.
   É a etapa que encontra o que eu não anteciparia: "governo eletrônico", "indústria 4.0",
   "teletrabalho", "comércio eletrônico" não contêm a palavra "digital".
3. **Congelamento** — `data/digital_lexicon.json` guarda cada termo com origem (semente,
   expandido ou padrão), campo (controlado/livre), obras, primeiro e último ano, e também
   os candidatos **rejeitados**, com o motivo. Sem isso o léxico seria uma lista de autor.

Duas definições de subcorpus, carregadas em paralelo por todo o resto da análise:
  **estrita** — o termo aparece nos campos de indexação (VCIpea, palavra-chave, classificação);
  **ampla**   — também vale menção no título ou no resumo.
A escolha muda o tamanho do campo (303 contra 583 obras desde 2010), então nenhuma
afirmação deste caso vale sem dizer em qual recorte ela foi medida.

Uso:
    python src/digital.py --lexico       → data/digital_lexicon.json
"""
import collections
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analysis import split_terms  # noqa: E402
from common import load_items, norm, save_json, year_of  # noqa: E402

# ── 1. sementes: digitais por definição, preferindo vocabulário controlado ──
SEED_PATTERNS = [
    r"^transformacao digital$", r"^digitalizacao$", r"^digitalisation$",
    r"^tecnologia da informacao$", r"^tecnologias? da informacao e comunicacao",
    r"^tic(s)?$", r"^internet$", r"^inteligencia artificial$",
    r"^governo (digital|eletronico)$", r"^plataformas? digitais?$",
    r"^economia digital$", r"^tecnologia digital$", r"^inclusao digital$",
    r"^telecomunicacoes$", r"^banda larga$", r"^industria 4\.0$",
    r"^big data$", r"^dados abertos$", r"^automacao$", r"^software$",
]
# termos que, se entrarem, tornam o campo tudo: aparecem em fração grande do corpus
MAX_DOC_SHARE = 0.03
MIN_WORKS = 3          # termo com 1 ou 2 obras não sustenta zona nem mapa
MIN_LIFT = 3.0         # c observado sobre c esperado se termo e campo fossem independentes
MIN_CO = 3             # co-ocorrências absolutas: 2 obras não sustentam inclusão
MIN_PUREZA_LB = 0.25   # limite inferior de Wilson (95%) da pureza, e não a pureza bruta:
                       # 2 obras de 3 dão pureza 0,67 e não significam nada
MAX_P = 0.01           # cauda superior hipergeométrica
MIN_LEN_TEXTO = 5      # termo curto ("tic", "ia") só casa em campo de indexação, nunca em texto

# Termos semanticamente digitais que a regra rejeita por contagem baixa. NÃO entram no
# léxico: servem ao teste de sensibilidade (o campo muda se eles entrarem?).
SENSIBILIDADE_PATTERNS = [r"teletrabalho", r"desinformacao", r"gestao da informacao",
                          r"governanca digital", r"seguranca cibernetica", r"blockchain",
                          r"comercio eletronico", r"industria de software", r"aplicativos?$",
                          r"midias sociais", r"redes sociais", r"protecao de dados"]

def _log_comb(n, k):
    if k < 0 or k > n:
        return float("-inf")
    return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)


def _wilson_lower(k, n, z=1.96):
    """Limite inferior do intervalo de Wilson para proporção — penaliza n pequeno."""
    if n == 0:
        return 0.0
    ph = k / n
    d = 1 + z * z / n
    centro = ph + z * z / (2 * n)
    raio = z * math.sqrt(ph * (1 - ph) / n + z * z / (4 * n * n))
    return max(0.0, (centro - raio) / d)


def _hyper_sf(k, K, n, N):
    """P[X ≥ k] hipergeométrica: K sucessos em N, amostra n.

    Em espaço logarítmico: com N ≈ 16,5 mil os coeficientes binomiais estouram o float.
    """
    if N < n or k > min(K, n):
        return 1.0 if k <= 0 else 0.0
    den = _log_comb(N, n)
    tot = 0.0
    for i in range(max(k, 0), min(K, n) + 1):
        lp = _log_comb(K, i) + _log_comb(N - K, n - i) - den
        if lp > -745:  # abaixo disso exp() é zero em dupla precisão
            tot += math.exp(lp)
    return min(1.0, tot)


def corpus_terms():
    """Para cada obra: termos de indexação normalizados, ano, campo de origem de cada termo."""
    docs, origin = [], collections.defaultdict(collections.Counter)
    display = {}
    for it in load_items():
        ts = set()
        for f in ("vcipea", "keywords", "classification"):
            for t in split_terms(it.get(f, [])):
                k = norm(t)
                if not k:
                    continue
                ts.add(k)
                origin[k][f] += 1
                display.setdefault(k, t)
        docs.append({"uuid": it["uuid"], "year": year_of(it), "terms": ts,
                     "title": (it.get("title") or [""])[0],
                     "abstract": ((it.get("abstract") or [""])[0])[:2000]})
    return docs, origin, display


def build_lexicon(save=True):
    docs, origin, display = corpus_terms()
    N = len(docs)
    df = collections.Counter()
    for d in docs:
        df.update(d["terms"])

    seeds = sorted(t for t in df if any(re.search(p, t) for p in SEED_PATTERNS))
    seed_docs = {i for i, d in enumerate(docs) if d["terms"] & set(seeds)}

    # co-ocorrência com o conjunto de sementes + índice de equivalência de Callon
    cand = []
    for t, n_t in df.items():
        if t in seeds or n_t < MIN_WORKS or n_t > MAX_DOC_SHARE * N:
            continue
        ti = {i for i, d in enumerate(docs) if t in d["terms"]}
        c = len(ti & seed_docs)
        if c == 0:
            continue
        esperado = n_t * len(seed_docs) / N
        lift = c / esperado if esperado else 0.0
        pureza = c / n_t
        pureza_lb = _wilson_lower(c, n_t)
        p = _hyper_sf(c, len(seed_docs), n_t, N)
        cand.append({"term": t, "display": display.get(t, t), "n_works": n_t,
                     "co_seed": c, "esperado": round(esperado, 2), "lift": round(lift, 1),
                     "pureza": round(pureza, 2), "pureza_lb": round(pureza_lb, 3), "p": p,
                     "campo": "controlado" if origin[t]["vcipea"] >= origin[t]["keywords"] else "livre"})

    def motivo(c):
        if c["co_seed"] < MIN_CO:
            return "co_ocorrencia_insuficiente"
        if c["lift"] < MIN_LIFT:
            return "associacao_fraca"
        if c["pureza_lb"] < MIN_PUREZA_LB:
            return "termo_usado_sobretudo_fora_do_campo"
        if c["p"] > MAX_P:
            return "nao_significativo"
        return None
    accepted = [c for c in cand if motivo(c) is None]
    rejected = [dict(c, motivo=motivo(c)) for c in cand if motivo(c) is not None]
    accepted.sort(key=lambda c: (-c["lift"], -c["n_works"]))
    rejected.sort(key=lambda c: -c["co_seed"])

    terms = sorted(set(seeds) | {c["term"] for c in accepted})
    # metadados por termo do léxico final
    lex = []
    for t in terms:
        ys = [d["year"] for d in docs if t in d["terms"] and d["year"]]
        lex.append({"term": t, "display": display.get(t, t),
                    "origem": "semente" if t in seeds else "expandido",
                    "campo": "controlado" if origin[t]["vcipea"] >= origin[t]["keywords"] else "livre",
                    "n_works": df[t], "vcipea": origin[t]["vcipea"], "keywords": origin[t]["keywords"],
                    "classification": origin[t]["classification"],
                    "primeiro_ano": min(ys) if ys else None, "ultimo_ano": max(ys) if ys else None})
    lex.sort(key=lambda x: -x["n_works"])

    out = {
        "parametros": {"MIN_WORKS": MIN_WORKS, "MIN_LIFT": MIN_LIFT, "MIN_CO": MIN_CO, "MIN_PUREZA_LB": MIN_PUREZA_LB,
                       "MAX_P": MAX_P, "MAX_DOC_SHARE": MAX_DOC_SHARE,
                       "MIN_LEN_TEXTO": MIN_LEN_TEXTO, "n_corpus": N,
                       "n_obras_semente": len(seed_docs)},
        "n_sementes": len(seeds), "n_expandidos": len(accepted), "n_lexico": len(lex),
        "n_candidatos_rejeitados": len(rejected),
        "sementes": seeds,
        "lexico": lex,
        "expandidos": accepted,
        "rejeitados": rejected[:80],
        "fragmentacao": fragmentation(lex),
        "sensibilidade_rejeitados": [c for c in rejected
                                     if any(re.search(pp, c["term"]) for pp in SENSIBILIDADE_PATTERNS)],
    }
    if save:
        save_json("digital_lexicon.json", out)
    return out, docs


def fragmentation(lex):
    """Mede a fragmentação que torna o campo invisível para o pipeline atual."""
    n = sum(x["n_works"] for x in lex)
    livre = sum(x["n_works"] for x in lex if x["campo"] == "livre")
    # famílias de quase-sinônimos por prefixo de 10 caracteres do termo normalizado
    fam = collections.defaultdict(list)
    for x in lex:
        fam[x["term"][:10]].append(x["term"])
    multi = {k: v for k, v in fam.items() if len(v) > 1}
    return {
        "ocorrencias_totais": n,
        "share_palavra_chave_livre": round(livre / n, 3) if n else None,
        "maior_termo": lex[0]["display"] if lex else None,
        "obras_do_maior_termo": lex[0]["n_works"] if lex else None,
        "n_termos": len(lex),
        "termos_com_menos_de_10_obras": sum(1 for x in lex if x["n_works"] < 10),
        "familias_de_quase_sinonimos": len(multi),
        "exemplos_de_familia": {k: v for k, v in list(multi.items())[:8]},
    }


def subcorpus(docs, lex_terms, mode="estrito"):
    """Obras do campo. `estrito` = termo de indexação; `amplo` = também título/resumo."""
    tset = set(lex_terms)
    # fronteira de palavra e comprimento mínimo: sem isso "tic" casa dentro de "política",
    # "prática" e "estatística", e o recorte amplo passa de 583 para 11 mil obras.
    longos = [t for t in tset if len(t) >= MIN_LEN_TEXTO]
    pat = re.compile(r"\b(?:" + "|".join(re.escape(t) for t in
                                         sorted(longos, key=len, reverse=True)) + r")\b")
    out = []
    for d in docs:
        hit = sorted(d["terms"] & tset)
        if not hit and mode == "amplo":
            blob = norm(d["title"] + " " + d["abstract"])
            if pat.search(blob):
                hit = ["<texto>"]
        if hit:
            out.append({"uuid": d["uuid"], "year": d["year"], "terms": hit})
    return out


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if "--lexico" in argv:
        out, docs = build_lexicon()
        f = out["fragmentacao"]
        print(f"léxico: {out['n_lexico']} termos ({out['n_sementes']} sementes + "
              f"{out['n_expandidos']} expandidos), {out['n_candidatos_rejeitados']} rejeitados",
              file=sys.stderr)
        print(f"fragmentação: maior termo = {f['maior_termo']!r} com {f['obras_do_maior_termo']} obras; "
              f"{f['termos_com_menos_de_10_obras']}/{f['n_termos']} termos com <10 obras; "
              f"{f['share_palavra_chave_livre']:.0%} das ocorrências em palavra-chave livre",
              file=sys.stderr)
        for mode in ("estrito", "amplo"):
            sub = subcorpus(docs, [x["term"] for x in out["lexico"]], mode)
            w = [s for s in sub if s["year"] and s["year"] >= 2010]
            print(f"subcorpus {mode}: {len(sub)} obras ({len(w)} desde 2010)", file=sys.stderr)
    else:
        print(__doc__, file=sys.stderr)


if __name__ == "__main__":
    main()
