"""Dados da página A nota: a bibliografia do texto para discussão, situada no espaço das tradições."""

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
