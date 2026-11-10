#!/usr/bin/env python3
"""Gera os protótipos de desenho (design/prototipos/*.html) a partir dos modelos (design/modelos/*.html).

Por que existe: protótipo com número inventado ensina o construtor a inventar número. Aqui todo
valor vem dos derivados versionados, e o marcador usado no modelo É o caminho do dado:

    {{num.rede.n}}            inteiro, com ponto de milhar
    {{num.silos.Q|3}}         decimal com 3 casas e vírgula
    {{num.blocos.pct_inter_canonico|1}}
    {{bloco:obras_no_nucleo}} trecho de HTML montado por este script
    {{svg:solidos}}           o bloco de símbolos de design/solidos.svg

Na construção, o mesmo caminho vale: `num` é espaco.dados(...)["num"], `nota` é o que
dados_nota() devolve (a portar para src/nota.py — ver design/PLANO.md, etapa 3).

Uso:  python design/ferramentas/gera_prototipos.py        (só biblioteca padrão)
"""
import html
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.abspath(os.path.join(AQUI, "..", ".."))
sys.path.insert(0, os.path.join(RAIZ, "src"))
import build_site  # noqa: E402
import data_io  # noqa: E402
import espaco  # noqa: E402

MODELOS = os.path.join(RAIZ, "design", "modelos")
SAIDA = os.path.join(RAIZ, "design", "prototipos")
EIXO = ["cib", "reg", "pi", "cplx"]                       # mesma ordem de espaco.AX
NOME = ["Cibernética", "Regulação", "Política industrial", "Complexidade"]
SOLIDO = ["icosa", "cubo", "tetra", "octa"]
N_VIZINHAS = 4                                            # quantas "leia ao lado" por obra


def br(x, casas=None):
    """Número à brasileira: ponto de milhar, vírgula decimal."""
    if x is None:
        return "—"
    if casas is None and isinstance(x, float) and x != int(x):
        casas = 1
    if casas is None:
        return f"{int(x):,}".replace(",", ".")
    return f"{x:,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def esc(s):
    return html.escape(str(s), quote=True)


# ───────────────────────── dados da página "A nota" ─────────────────────────

def dados_nota(cena):
    """Contrato de dados da página A nota. Entrada: o dicionário de espaco.dados().

    Para cada obra da bibliografia que está no núcleo cocitado:
      - junta os registros duplicados da mesma obra (a rede tem edições repetidas) e soma o
        peso de cocitação por vizinha — sem contar os próprios registros da obra;
      - `viz`: as N_VIZINHAS obras mais cocitadas com ela (peso = nº de trabalhos que citam as
        duas), com a marca `outra` quando a vizinha é de outra tradição;
      - `triades`: em quantas tríades da agenda algum registro da obra entra.
    Nada é estimado: tudo sai de cena["nos"], cena["arestas"], cena["triades"] e cena["nota"].
    """
    nos, ar, nota = cena["nos"], cena["arestas"], cena["nota"]
    viz = {}
    for e in range(0, len(ar), 3):
        s, t, w = ar[e], ar[e + 1], ar[e + 2]
        viz.setdefault(s, {})[t] = w
        viz.setdefault(t, {})[s] = w
    obras, fora, atos = [], [], []
    for r in nota["refs"]:
        if r["t"] == "ato":
            atos.append({"ref": r["r"]})
            continue
        if not r["n"]:
            fora.append({"ref": r["r"], "doi": r["doi"], "obs": r["obs"]})
            continue
        regs = r["n"]
        princ = max(regs, key=lambda i: nos[i]["c"])           # registro mais citado representa a obra
        soma = {}
        for i in regs:
            for j, w in viz.get(i, {}).items():
                if j not in regs:
                    soma[j] = soma.get(j, 0) + w
        k = [sum(nos[i]["k"][a] for i in regs) for a in range(4)] if len(regs) > 1 else list(nos[princ]["k"])
        eixo = nos[princ]["a"]
        topo = sorted(soma.items(), key=lambda jw: (-jw[1], nos[jw[0]]["l"]))[:N_VIZINHAS]
        obras.append({
            "ref": r["r"], "doi": r["doi"], "obs": r["obs"], "ids": [nos[i]["i"] for i in regs],
            "id": nos[princ]["i"], "eixo": eixo, "observado": bool(nos[princ]["o"]), "empate": bool(nos[princ].get("e")),
            "k": k, "n_viz": len(soma),
            "aponta": (k.index(max(k)) if nos[princ]["o"] and sum(k) and k[eixo] < max(k) else -1),
            "viz": [{"id": nos[j]["i"], "rotulo": nos[j]["l"], "eixo": nos[j]["a"], "observado": bool(nos[j]["o"]),
                     "peso": w, "outra": nos[j]["a"] != eixo, "na_nota": bool(nos[j]["t"])} for j, w in topo],
            "triades": sum(1 for t in cena["triades"] if set(t["m"]) & set(regs)),
        })
    obras.sort(key=lambda o: (o["eixo"], not o["observado"], o["ref"]))
    da_nota = set(nota["nos"])
    tri = [t for t in cena["triades"] if da_nota & set(t["m"])]
    return {
        "titulo": nota["titulo"], "autores": nota["autores"],
        "versao": nota["versao"][:1].upper() + nota["versao"][1:],
        "n_refs": nota["n_refs"], "n_obras": nota["n_obras"], "n_atos": nota["n_atos"],
        "n_no_nucleo": len(obras), "n_fora": len(fora),
        "n_observado": nota["n_rotulo_observado"], "n_inferido": nota["n_rotulo_inferido"], "k": nota["k"],
        "n_triades": len(tri), "n_triades_sem_inferencia": sum(t["n"] for t in tri),
        "n_com_doi_fora": sum(1 for f in fora if f["doi"]),
        "por_eixo": [sum(1 for o in obras if o["eixo"] == a) for a in range(4)],
        "obras": obras, "fora": fora, "atos": atos,
    }


# ───────────────────────── contraste das fichas de cor ─────────────────────────

def _luminancia(hexa):
    h = hexa.lstrip("#")
    canais = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    r, g, b = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in canais]
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a, b):
    """Razão de contraste WCAG entre duas cores #rrggbb."""
    la, lb = sorted((_luminancia(a), _luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def fichas_de_cor(css):
    """Lê as fichas --sd-* em hexadecimal de sistema.css."""
    return dict(re.findall(r"--sd-([a-z-]+):\s*(#[0-9a-fA-F]{6})\b", css))


# ───────────────────────── trechos de HTML ─────────────────────────

def solido(eixo, observado=True, extra=""):
    if eixo < 0:
        return ""
    return (f'<svg class="sd-sol {extra} sd-eixo-{EIXO[eixo]} {"sd-cheio" if observado else "sd-vazado"}" '
            f'aria-hidden="true"><use href="#sd-sol-{SOLIDO[eixo]}"/></svg>')


def selo(eixo, observado, empate=False):
    origem = "rótulo observado" if observado else ("rótulo inferido, com empate" if empate else "rótulo inferido")
    return (f'<span class="sd-selo sd-eixo-{EIXO[eixo]}">{solido(eixo, observado)}{NOME[eixo]} '
            f'<small>{origem}</small></span>')


def mistura(k):
    tot = sum(k) or 1
    partes = "".join(f'<span class="sd-eixo-{EIXO[a]}" style="--p:{100 * k[a] / tot:.1f}"></span>' for a in range(4) if k[a])
    texto = "; ".join(f"{NOME[a].lower()} {k[a]}" for a in range(4) if k[a])
    chave = "".join(f'<span><b>{k[a]}</b> {NOME[a].lower()}</span>' for a in range(4) if k[a])
    return (f'<div class="sd-mistura" role="img" aria-label="Vizinhas de rótulo observado: {texto}">{partes}</div>'
            f'<div class="sd-mistura-chave">{chave}</div>')


def item_obra(o):
    def marcas(v):
        m = (["outra tradição"] if v["outra"] else []) + (["também na nota"] if v["na_nota"] else [])
        return f' <small class="sd-legenda">{", ".join(m)}</small>' if m else ""
    viz = "".join(
        f'<li>{solido(v["eixo"], v["observado"])}<span>{esc(v["rotulo"])}{marcas(v)}</span>'
        f'<span class="sd-num">{v["peso"]} trabalhos</span></li>' for v in o["viz"])
    acoes = [f'<a href="../../docs/espaco.html#lente=nota&amp;obra={o["id"]}">Ver no espaço 3D</a>']
    if o["doi"]:
        acoes.append(f'<a href="https://doi.org/{esc(o["doi"])}" target="_blank" rel="noopener">Abrir pelo DOI (nova aba)</a>')
    acoes.append(f'<a href="https://openalex.org/{o["id"]}" target="_blank" rel="noopener">Registro no OpenAlex (nova aba)</a>')
    extra = []
    if o["triades"]:
        extra.append(f'entra em {o["triades"]} {"tríade" if o["triades"] == 1 else "tríades"} a construir')
    if o["obs"]:
        extra.append(esc(o["obs"]))
    if o["aponta"] >= 0:
        extra.append(f'o vocabulário diz {NOME[o["eixo"]].lower()}, a vizinhança aponta {NOME[o["aponta"]].lower()}')
    return (
        f'<li class="sd-obra" data-eixo="{EIXO[o["eixo"]]}" data-origem="{"observado" if o["observado"] else "inferido"}">'
        f'{solido(o["eixo"], o["observado"], "sd-g")}'
        f'<p class="sd-obra-ref">{esc(o["ref"])}</p>'
        f'<p class="sd-obra-meta">{selo(o["eixo"], o["observado"], o["empate"])}'
        + (f'<span>{"; ".join(extra)}</span>' if extra else "") + '</p>'
        f'<div><p class="sd-sobre">Com quem é cocitada: {br(sum(o["k"]))} vizinhas de rótulo observado</p>{mistura(o["k"])}</div>'
        f'<div><p class="sd-sobre">Leia ao lado: as mais cocitadas com ela</p><ul class="sd-vizinhas">{viz}</ul>'
        f'<p class="sd-obra-acoes">{"".join(acoes)}</p></div></li>')


def cartao_triagem():
    """Um cartão da triagem com valores reais: a primeira obra da síntese que é alvo de agenda."""
    pagina = open(os.path.join(RAIZ, "docs", "triagem.html"), encoding="utf-8").read()
    obras = json.loads(re.search(r"const RAYYAN_WORKS=(\[.*?\]);\n", pagina, re.S).group(1))
    w = next(x for x in obras if (x.get("solidez") or {}).get("estrutural") is not None)
    mapa = {"Cibernética": 0, "Regulação econômica": 1, "Política industrial": 2, "Economia da complexidade": 3}
    selos = "".join(f'<span class="sd-selo sd-eixo-{EIXO[mapa[a]]}">{solido(mapa[a])}{NOME[mapa[a]]}</span>' for a in w["axes"] if a in mapa)
    s = w["solidez"]
    medidas = "".join(f"<div><dt>{rot}</dt><dd>{br(float(v), 2)}</dd></div>" for rot, v in (
        ("Integração (ΔKf)", s["estrutural"]), ("Latente", s["latente"]), ("Semântico", s["semantico"]), ("Prioridade", w["prioridade"])) if v is not None)
    return (f'<article class="sd-cartao"><h3 class="sd-cartao-t">{esc(w["title"])}</h3>'
            f'<p class="sd-obra-meta">{selos}<span>{esc(", ".join(w["roles"]))}</span></p>'
            f'<dl class="sd-medidas">{medidas}</dl>'
            '<div class="sd-cartao-acoes"><button type="button" class="sd-botao sd-primario">Incluir</button>'
            '<button type="button" class="sd-botao">Talvez</button><button type="button" class="sd-botao">Excluir</button></div></article>')


def item_fora(f):
    elo = f' <a href="https://doi.org/{esc(f["doi"])}" target="_blank" rel="noopener">DOI (nova aba)</a>' if f["doi"] else ""
    obs = f' <span class="sd-legenda">{esc(f["obs"])}</span>' if f["obs"] else ""
    return f'<li>{esc(f["ref"])}{elo}{obs}</li>'


# ───────────────────────── montagem ─────────────────────────

def busca(ctx, caminho):
    o = ctx
    for k in caminho.split("."):
        o = o[int(k)] if isinstance(o, list) else o[k]
    return o


def monta(modelo, ctx, blocos):
    def troca(m):
        corpo = m.group(1).strip()
        if corpo.startswith("bloco:"):
            return blocos[corpo[6:]]
        if corpo == "svg:solidos":
            return blocos["solidos"]
        caminho, _, casas = corpo.partition("|")
        v = busca(ctx, caminho)
        return esc(v) if isinstance(v, str) else br(v, int(casas) if casas else None)
    return re.sub(r"\{\{([^{}]+)\}\}", troca, modelo)


def main():
    cena = espaco.dados(build_site.explorer_network())
    if not cena["nota"]:
        sys.exit("data/td_referencias.json ausente: sem a nota não há protótipo da página A nota.")
    R = data_io.load_data("scisci_results.json", required=True)
    nota = dados_nota(cena)
    cores = fichas_de_cor(open(os.path.join(RAIZ, "design", "sistema.css"), encoding="utf-8").read())
    ctx = {"num": cena["num"], "nota": nota, "corpus": {"n": R["corpus_size"], "sementes": R["n_seeds"]},
           "cor": cores,
           "contraste": {k.replace("-", "_"): min(contraste(v, cores["papel"]), contraste(v, cores["superficie"]))
                         for k, v in cores.items() if k.endswith("-texto") or k in ("apagado", "tinta", "nota", "alerta")}}
    blocos = {
        "solidos": open(os.path.join(RAIZ, "design", "solidos.svg"), encoding="utf-8").read(),
        "obras_no_nucleo": "\n".join(item_obra(o) for o in nota["obras"]),
        "obras_fora": "\n".join(item_fora(f) for f in nota["fora"]),
        "atos": "\n".join(f"<li>{esc(a['ref'])}</li>" for a in nota["atos"]),
        "autores": esc(", ".join(nota["autores"])),
        "chips_eixo": "".join(
            f'<button type="button" class="sd-chip" data-eixo="{EIXO[a]}" aria-pressed="true"'
            + (" disabled" if not nota["por_eixo"][a] else "")
            + f'>{solido(a)}{NOME[a]} <span class="sd-num">{nota["por_eixo"][a]}</span></button>' for a in range(4)),
        "heroi_json": json.dumps(espaco.heroi(cena), separators=(",", ":")),
        "cartao_triagem": cartao_triagem(),
        "obra_exemplo": item_obra(nota["obras"][0]),
        "chips_rede": "".join(
            f'<button type="button" class="sd-chip" aria-pressed="true">{solido(a)}{NOME[a]} '
            f'<span class="sd-num">{sum(1 for n in cena["nos"] if n["a"] == a and n["o"])} + '
            f'{sum(1 for n in cena["nos"] if n["a"] == a and not n["o"])}</span></button>' for a in range(4)),
        "cores": "".join(
            f'<div class="g-cor"><span style="background:{v}"></span><code>--sd-{k}</code><small>{v}'
            + (f', contraste {br(min(contraste(v, cores["papel"]), contraste(v, cores["superficie"])), 1)}:1' if (k.endswith("-texto") or k in ("apagado", "tinta", "nota", "alerta")) else "")
            + '</small></div>' for k, v in cores.items()),
    }
    os.makedirs(SAIDA, exist_ok=True)
    for nome in sorted(os.listdir(MODELOS)):
        if not nome.endswith(".html"):
            continue
        saida = monta(open(os.path.join(MODELOS, nome), encoding="utf-8").read(), ctx, blocos)
        resto = re.findall(r"\{\{[^{}]+\}\}", saida)
        assert not resto, f"{nome}: marcador sem valor {resto[:3]}"
        with open(os.path.join(SAIDA, nome), "w", encoding="utf-8") as f:
            f.write(saida)
        print(f"protótipo: design/prototipos/{nome} ({len(saida) // 1024} KB)")


if __name__ == "__main__":
    main()
