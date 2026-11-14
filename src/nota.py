"""Dados da página A nota: a bibliografia do texto para discussão, situada no espaço das tradições."""
from marcadores import br, esc, monta

EIXO = ["cib", "reg", "pi", "cplx"]                       # mesma ordem de espaco.AX
NOME = ["Cibernética", "Regulação", "Política industrial", "Complexidade"]
SOLIDO = ["icosa", "cubo", "tetra", "octa"]
N_VIZINHAS = 4                                            # quantas "leia ao lado" por obra


def dados(cena):
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
    acoes = [f'<a href="espaco.html#lente=nota&amp;obra={o["id"]}">Ver no espaço 3D</a>']
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


def item_fora(f):
    elo = f' <a href="https://doi.org/{esc(f["doi"])}" target="_blank" rel="noopener">DOI (nova aba)</a>' if f["doi"] else ""
    obs = f' <span class="sd-legenda">{esc(f["obs"])}</span>' if f["obs"] else ""
    return f'<li>{esc(f["ref"])}{elo}{obs}</li>'


def pagina(modelo, ctx):
    """Monta docs/nota.html: resolve os marcadores do modelo com o contexto e os blocos desta tela."""
    n = ctx["nota"]
    blocos = {
        "obras_no_nucleo": "\n".join(item_obra(o) for o in n["obras"]),
        "obras_fora": "\n".join(item_fora(f) for f in n["fora"]),
        "atos": "\n".join(f"<li>{esc(a['ref'])}</li>" for a in n["atos"]),
        "autores": esc(", ".join(n["autores"])),
        "chips_eixo": "".join(
            f'<button type="button" class="sd-chip" data-eixo="{EIXO[a]}" aria-pressed="true"'
            + (" disabled" if not n["por_eixo"][a] else "")
            + f'>{solido(a)}{NOME[a]} <span class="sd-num">{n["por_eixo"][a]}</span></button>' for a in range(4)),
    }
    return monta(modelo, ctx, blocos)
