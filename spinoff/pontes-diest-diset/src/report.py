"""Etapa 5 — relatório legível (RELATORIO.md) a partir de data/results.json."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import ROOT, load_json  # noqa: E402

OUT = os.path.join(ROOT, "RELATORIO.md")


def cell(v):
    """None → travessão: o relatório não deve exibir 'None' para campo ausente."""
    if v is None:
        return "—"
    if isinstance(v, list):
        return ", ".join(map(str, v)).replace("|", "/")
    return str(v).replace("|", "/")


def table(rows, cols, heads=None):
    heads = heads or cols
    out = ["| " + " | ".join(heads) + " |", "|" + "---|" * len(cols)]
    for r in rows:
        out.append("| " + " | ".join(cell(r.get(c, "")) for c in cols) + " |")
    return "\n".join(out)


def main():
    R = load_json("results.json")
    c, st = R["counts"], R["structural"]
    L = []
    L.append("# Pontes epistêmicas DIEST × DISET (Ipea) — relatório gerado\n")
    L.append(f"> Gerado por `src/report.py` a partir de `data/results.json` (janela ≥ {R['params']['start']}). "
             "Fonte: Repositório do Conhecimento do Ipea + diretório \"Quem faz pesquisa no Ipea\". "
             "Diretoria **atribuída pela produção** (ver METODO.md §2) — leia a coluna *confiança*.\n")
    L.append("## 1. Números de base\n")
    L.append(f"- Obras na janela: **{c['items_window']}**; autores distintos no corpus inteiro: {c['authors_total']}.")
    L.append(f"- Membros atribuídos — DIEST: **{c['members']['DIEST']}**, DISET: **{c['members']['DISET']}** "
             f"(servidores ativos: {c['active_staff']['DIEST']} / {c['active_staff']['DISET']}).")
    L.append(f"- Obras de cada lado (rótulo editorial ou ≥1 membro): DIEST {c['items_by_side']['DIEST']}, "
             f"DISET {c['items_by_side']['DISET']}.")
    L.append(f"- Hiperarestas com ≥3 assinaturas: **{c['share_size_ge3']:.0%}** — é isso que justifica (ou não) "
             "o hipergrafo em vez do grafo de pares.\n")

    v = R.get("validation") or {}
    L.append("## 2. Validação da lista de membros com as chefias\n")
    n_focus = v.get("n_membros_focus", 0)
    if v.get("status") == "pendente" or not v.get("n_decididos"):
        L.append("**Pendente** — nenhuma pessoa foi confirmada pelas chefias da DIEST ou da DISET "
                 f"até agora. Toda a lista abaixo ({n_focus} membros) é **inferida pela produção**, "
                 "com a circularidade parcial descrita em `METODO.md §5`: as obras definem a "
                 "diretoria das pessoas e as pessoas definem quais obras são mistas. Enquanto isso "
                 "não for validado, a precisão da atribuição é **desconhecida** e os números "
                 "estruturais (§5) herdam essa incerteza.")
        L.append("Instrumento pronto: `data/membership_validation.csv` "
                 "(gerado por `python src/membership.py --export`; instruções em "
                 "`docs/VALIDACAO_MEMBROS.md`). As respostas entram em "
                 "`data/membership_overrides.json` e passam a vencer a inferência.\n")
    else:
        L.append(f"- Decididos pelas chefias: **{v['n_decididos']}** de {n_focus} membros "
                 f"(+{v.get('n_desconhecido', 0)} marcados *desconhecido*).")
        L.append(f"- **Precisão da inferência: {v['precisao']:.1%}** "
                 f"({v['n_confirmados']}/{v['n_decididos']} confirmados).")
        if v.get("por_confianca"):
            L.append("- Por estrato de confiança: " + "; ".join(
                f"{k} {s['confirmados']}/{s['n']}"
                + (f" ({s['precisao']:.0%})" if s["precisao"] is not None else "")
                for k, s in sorted(v["por_confianca"].items())) + ".")
        if v.get("corrigidos"):
            L.append(f"- Corrigidos pelas chefias ({len(v['corrigidos'])}): " + "; ".join(
                f"{x['name']} {x['inferida']}→{x['correta']}" for x in v["corrigidos"][:20]) + ".")
        if v.get("fora"):
            L.append(f"- Não são membros, apesar da produção ({len(v['fora'])}): "
                     + "; ".join(x["name"] for x in v["fora"][:20]) + ".")
        L.append("")

    for d in ("DIEST", "DISET"):
        L.append(f"## 3.{1 if d == 'DIEST' else 2} Autores ativos — {d}\n")
        rows = [r for r in R["people"][d] if r["active"]][:40]
        L.append(table(rows, ["name", "source", "confidence", "validation", "n_items", "n_tagged",
                              "last_year", "top_terms"],
                       ["autor", "fonte", "confiança", "validação", "obras", "rotuladas",
                        "última", "termos dominantes"]))
        L.append("")

    if R.get("unassigned_with_signal"):
        L.append("**No diretório, sem diretoria atribuída, mas com produção DIEST/DISET** (validar com as chefias):\n")
        L.append(", ".join(f"{x['name']} {x['dir_weights']}" for x in R["unassigned_with_signal"][:15]) + "\n")
    L.append("*Fonte:* diretório = perfil no portal; cargo = perfil de Pessoa no repositório; produção = "
             "≥3 obras rotuladas e publicação nos últimos 3 anos (servidores fora do diretório, bolsistas).\n")
    L.append("## 4. Produção característica (log-odds com prior informativo; z>2 ≈ distintivo)\n")
    for d in ("DIEST", "DISET"):
        L.append(f"**{d}:** " + "; ".join(f"{x['term']} (z={x['z']}, n={x['n']})"
                                          for x in R["characteristic"][d][:20]) + "\n")
    L.append("**Terreno comum de alto volume (|z|<1,5 e ≥5 obras de cada lado):** "
             + "; ".join(f"{x['term']} ({x['n_DIEST']}/{x['n_DISET']})" for x in R["shared_high_volume_terms"][:20]) + "\n")

    L.append("## 5. Ligação estrutural (hipergrafo de coautoria)\n")
    L.append(f"- Hiperarestas com algum membro DIEST/DISET: {st['focus_hyperedges']}; **mistas (DIEST+DISET): "
             f"{st['mixed_hyperedges']}** vs. nulo de permutação de rótulos {st['null_mean']} ± {st['null_sd']} "
             f"(z = {st['z']}, P[nulo ≤ obs] = {st['p_le_obs']}).")
    L.append(f"- Pares cruzados distintos: {st['cross_pairs']}; destes, **{st['cross_pairs_only_via_size_ge4']}** "
             "só existem via obras com ≥4 assinaturas (laço \"de coletânea\", fraco).")
    L.append("- Grafo-linha s (hiperarestas ligadas se partilham ≥ s autores): " + "; ".join(
        f"s={s}: {v['bridging_components']} componente(s) que juntam obras de maioria DIEST e DISET "
        f"(maior: {v['largest_bridging_size']} obras)" for s, v in st["s_line"].items()) + ".")
    L.append("- Obras mistas por ano: " + ", ".join(f"{y}: {n}" for y, n in st["mixed_by_year"].items()) + "\n")
    L.append("**Pares cruzados mais fortes (peso de Newman Σ1/(|e|−1)):**\n")
    L.append(table(st["strongest_cross_pairs"], ["DIEST", "DISET", "newman_w"]))
    L.append("\n**Obras mistas recentes:**\n")
    for x in st["mixed_examples"][:12]:
        L.append(f"- {x['year']} — [{x['title']}]({x['uri']}) — {', '.join(x['authors'])}")
    L.append("\n## 6. Corretores (coassinam com os dois lados)\n")
    L.append(table(R["brokers"][:20], ["name", "diretoria", "active", "n_coaut_DIEST", "n_coaut_DISET", "score"],
                   ["autor", "diretoria", "ativo", "coaut. DIEST", "coaut. DISET", "√(d·s)"]))
    if R["trajectory_bridges"]:
        L.append("\n**Pontes por trajetória** (≥20% da produção rotulada em cada diretoria):\n")
        L.append(table(R["trajectory_bridges"], ["name", "diretoria", "share_DIEST", "share_DISET", "active"]))

    L.append("\n## 7. Zonas de convergência e hiperarestas potenciais\n")
    for i, z in enumerate(R["zones"], 1):
        L.append(f"### Z{i}. {z['label']}  (escore {z['score']})")
        L.append(f"- Termos: {', '.join(z['terms'][:10])}")
        L.append(f"- DIEST: {', '.join(z['DIEST'])}  ·  DISET: {', '.join(z['DISET'])}")
        L.append(f"- Obras mistas já existentes na zona: {z['mixed_items_existing']}"
                 + (f" (ex.: {z['examples'][0]['title']}, {z['examples'][0]['year']})" if z["examples"] else ""))
        L.append(f"- **Hiperaresta potencial (equipe):** {', '.join(z['potential_hyperedge'])}"
                 + (f" — corretor: {z['broker']}" if z["broker"] else " — sem corretor comum (ponte a construir)"))
        L.append("")

    L.append("## 8. Colaboradores potenciais (pares DIEST×DISET ainda sem coautoria)\n")
    L.append(table(R["potential_collaborators"][:30],
                   ["DIEST", "DISET", "cosine", "n_common", "shared_terms", "common_coauthors"],
                   ["DIEST", "DISET", "cos", "coaut. comuns", "termos partilhados", "intermediários"]))
    L.append("\n## 9. Termos de convergência (usuários dos dois lados, equilíbrio × volume)\n")
    L.append(table(R["convergence_terms"][:30], ["term", "n_DIEST", "n_DISET", "score"]))
    L.append("\n---\n*Ressalvas: METODO.md §5. Nenhum número aqui foi digitado à mão.*\n")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(L))
    print(f"→ {OUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
