"""Avaliação do achado estrutural: cinco nulos e um teste de fabricação (só stdlib).

O número mais citado do projeto é z ≈ −15: 45 obras mistas DIEST+DISET contra ≈391
esperadas. Ele sai de **um** nulo — permutação de rótulos de diretoria sobre o hipergrafo
fixo (pressuposto A15) — que tem três fragilidades conhecidas:

  (i)   o denominador inclui obras de autor único, que **nunca** podem ser mistas (A14);
  (ii)  ignora o grau dos autores: quem publica muito entra em mais obras e tem mais
        chance de estar numa mista, e os dois lados podem diferir em grau;
  (iii) boletim e nota técnica são intra-diretoria **por construção editorial**, e é
        justamente o sinal editorial que define a diretoria das pessoas (A13, circularidade).

Nulos implementados:
  A  permutacao          o atual: embaralha rótulos entre os 261 membros
  B  elegiveis           idem, mas só sobre hiperarestas com |e| ≥ 2
  C  grau_estratificado  embaralha rótulos **dentro** de decis de grau do autor
  D  sem_rotulo          só obras SEM sinal editorial de diretoria — as únicas em que o
                         rótulo da pessoa não foi derivado da própria obra. É o nulo que
                         escapa da circularidade.
  E  configuracao        modelo de configuração de hipergrafo: preserva grau do autor e
                         tamanho da hiperaresta, embaralha a incidência por troca dupla
                         (MCMC), e conta mistas com os rótulos REAIS.

Teste de fabricação (o decisivo): permuta o rótulo editorial **entre as obras**,
preservando a distribuição de rótulos e toda a estrutura de coautoria, e então roda a
regra de atribuição de `attribute.py` sobre esse mundo sintético. Nesse mundo não existe
silo: o rótulo é independente de quem escreve com quem. Se mesmo assim o z sair
fortemente negativo, a conclusão do relatório é artefato da regra de atribuição.

Uso:
    python src/nulls.py --todos [--perm 1000] [--fab 40]
"""
import argparse
import collections
import json
import math
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import FOCUS, NOW_YEAR, load_json, save_json  # noqa: E402

D, S = FOCUS
ALL_DIRS = ("DIEST", "DISET", "DISOC", "DIRUR", "DIMAC", "DINTE")
HALF_LIFE = 4.0
MIN_SHARE = 0.5
MIN_TAGGED = 2


def load(start=2010):
    authors = load_json("authors.json")
    items = [i for i in load_json("items_tagged.json")
             if i["year"] and i["year"] >= start and i["authors"]]
    dir_of = {a: v["diretoria"] for a, v in authors.items() if v["diretoria"]}
    return authors, items, dir_of


def mixed_count(edges, lab):
    n = 0
    for e in edges:
        ds = {lab.get(a) for a in e}
        if D in ds and S in ds:
            n += 1
    return n


def zstat(obs, null):
    mu = sum(null) / len(null)
    sd = math.sqrt(sum((x - mu) ** 2 for x in null) / max(1, len(null) - 1)) or 1.0
    return {"obs": obs, "mu": round(mu, 1), "sd": round(sd, 1),
            "z": round((obs - mu) / sd, 2),
            "p_le_obs": round(sum(1 for x in null if x <= obs) / len(null), 4)}


def perm_null(edges, dir_of, perm, rng, strata=None):
    """Permuta rótulos entre os membros do foco. `strata` restringe a troca a cada bloco."""
    pool = [a for a in dir_of if dir_of[a] in FOCUS]
    blocks = collections.defaultdict(list)
    for a in pool:
        blocks[(strata or {}).get(a, 0)].append(a)
    out = []
    for _ in range(perm):
        lab = {}
        for _k, members in blocks.items():
            labs = [dir_of[a] for a in members]
            rng.shuffle(labs)
            lab.update(zip(members, labs))
        out.append(mixed_count(edges, lab))
    return out


def degree_strata(edges, dir_of, nbins=10):
    deg = collections.Counter()
    for e in edges:
        for a in e:
            deg[a] += 1
    pool = sorted((a for a in dir_of if dir_of[a] in FOCUS), key=lambda a: deg[a])
    strata = {}
    for i, a in enumerate(pool):
        strata[a] = min(nbins - 1, i * nbins // max(1, len(pool)))
    return strata


def config_null(edges, dir_of, perm, rng, swaps_per_edge=10):
    """Modelo de configuração: troca dupla de incidências preservando grau e tamanho."""
    inc = [list(e) for e in edges]
    pos = []           # (indice da aresta, posicao do autor dentro dela)
    for i, e in enumerate(inc):
        for j in range(len(e)):
            pos.append((i, j))
    n_swaps = int(swaps_per_edge * len(inc))
    out = []
    for _ in range(perm):
        for _s in range(n_swaps):
            (i1, j1), (i2, j2) = rng.choice(pos), rng.choice(pos)
            if i1 == i2:
                continue
            a1, a2 = inc[i1][j1], inc[i2][j2]
            if a1 == a2 or a2 in inc[i1] or a1 in inc[i2]:
                continue
            inc[i1][j1], inc[i2][j2] = a2, a1
        out.append(mixed_count([set(e) for e in inc], dir_of))
    return out


# ───────────────────── teste de fabricação ─────────────────────

def attribute_from_labels(items, item_dirs):
    """Reaplica a regra de attribute.py: peso por recência, dominante ≥50% e ≥2 rotuladas."""
    w = collections.defaultdict(collections.Counter)
    tagged = collections.Counter()
    for it in items:
        dirs = item_dirs.get(it["uuid"], [])
        if not dirs:
            continue
        ww = 0.5 ** (max(0, NOW_YEAR - (it["year"] or 1990)) / HALF_LIFE)
        for a in it["authors"]:
            tagged[a] += 1
            for d in dirs:
                w[a][d] += ww / len(dirs)
    out = {}
    for a, c in w.items():
        tot = sum(c.values())
        top, topw = c.most_common(1)[0]
        if tot and topw / tot >= MIN_SHARE and tagged[a] >= MIN_TAGGED:
            out[a] = top
    return out


def fabrication_test(items, n_rep, perm, rng):
    """Permuta o rótulo editorial ENTRE as obras e roda a atribuição nesse mundo sem silo."""
    labelled = [(it["uuid"], it["dirs"]) for it in items if it["dirs"]]
    labels = [d for _u, d in labelled]
    uuids = [u for u, _d in labelled]
    edges_all = [set(it["authors"]) for it in items]
    res = []
    for _ in range(n_rep):
        rng.shuffle(labels)
        fake = dict(zip(uuids, labels))
        dir_f = attribute_from_labels(items, fake)
        focus = {a: d for a, d in dir_f.items() if d in FOCUS}
        if sum(1 for d in focus.values() if d == D) < 5 or \
           sum(1 for d in focus.values() if d == S) < 5:
            continue
        edges = [e for e in edges_all if any(focus.get(a) in FOCUS for a in e)]
        obs = mixed_count(edges, focus)
        null = perm_null(edges, focus, perm, rng)
        st = zstat(obs, null)
        st["n_membros"] = {d: sum(1 for x in focus.values() if x == d) for d in FOCUS}
        res.append(st)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--todos", action="store_true")
    ap.add_argument("--perm", type=int, default=1000)
    ap.add_argument("--fab", type=int, default=40)
    ap.add_argument("--fabperm", type=int, default=200)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args(argv)
    if not args.todos:
        print(__doc__, file=sys.stderr)
        return
    rng = random.Random(args.seed)
    authors, items, dir_of = load()

    edges_all = [(it, set(it["authors"])) for it in items]
    focus = [(it, e) for it, e in edges_all if any(dir_of.get(a) in FOCUS for a in e)]
    out = {"n_obras": len(items), "n_focus": len(focus), "perm": args.perm, "nulos": {}}

    # A — o nulo atual
    E = [e for _it, e in focus]
    out["nulos"]["A_permutacao"] = zstat(mixed_count(E, dir_of), perm_null(E, dir_of, args.perm, rng))
    # B — só obras elegíveis (|e| ≥ 2)
    Eb = [e for e in E if len(e) >= 2]
    out["nulos"]["B_elegiveis"] = dict(zstat(mixed_count(Eb, dir_of),
                                             perm_null(Eb, dir_of, args.perm, rng)),
                                       n_arestas=len(Eb), n_autor_unico=len(E) - len(Eb))
    # C — permutação dentro de decis de grau
    st = degree_strata(E, dir_of)
    out["nulos"]["C_grau_estratificado"] = zstat(mixed_count(E, dir_of),
                                                 perm_null(E, dir_of, args.perm, rng, strata=st))
    # D — só obras SEM rótulo editorial (sem circularidade)
    Ed = [e for it, e in focus if not it["dirs"] and len(e) >= 2]
    out["nulos"]["D_sem_rotulo"] = dict(zstat(mixed_count(Ed, dir_of),
                                              perm_null(Ed, dir_of, args.perm, rng)),
                                        n_arestas=len(Ed))
    Ec = [e for it, e in focus if it["dirs"] and len(e) >= 2]
    out["nulos"]["D2_com_rotulo"] = dict(zstat(mixed_count(Ec, dir_of),
                                               perm_null(Ec, dir_of, args.perm, rng)),
                                         n_arestas=len(Ec))
    # E — modelo de configuração (preserva grau e tamanho)
    nperm_cfg = max(50, args.perm // 10)
    out["nulos"]["E_configuracao"] = dict(
        zstat(mixed_count(Eb, dir_of), config_null(Eb, dir_of, nperm_cfg, rng)),
        perm=nperm_cfg)
    # F — fabricação
    fab = fabrication_test(items, args.fab, args.fabperm, rng)
    zs = sorted(x["z"] for x in fab)
    out["fabricacao"] = {
        "n_replicas": len(fab),
        "z_mediano": zs[len(zs) // 2] if zs else None,
        "z_min": zs[0] if zs else None, "z_max": zs[-1] if zs else None,
        "obs_mediano": sorted(x["obs"] for x in fab)[len(fab) // 2] if fab else None,
        "mu_mediano": sorted(x["mu"] for x in fab)[len(fab) // 2] if fab else None,
        "replicas": fab,
    }
    save_json("audit_nulls.json", out)
    for k, v in out["nulos"].items():
        print(f"  {k:22s} obs={v['obs']:4d}  nulo={v['mu']:7.1f}±{v['sd']:5.1f}  z={v['z']:7.2f}",
              file=sys.stderr)
    f = out["fabricacao"]
    print(f"  fabricação ({f['n_replicas']} réplicas, mundo SEM silo): z mediano {f['z_mediano']}, "
          f"faixa [{f['z_min']}, {f['z_max']}], mistas medianas {f['obs_mediano']} "
          f"contra nulo {f['mu_mediano']}", file=sys.stderr)


if __name__ == "__main__":
    main()
