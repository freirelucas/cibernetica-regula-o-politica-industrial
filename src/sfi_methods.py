#!/usr/bin/env python3
"""Métodos de ciência das redes do círculo do Santa Fe Institute (stdlib puro).

Implementa, sem dependências externas, dois métodos canônicos de Aaron Clauset
(SFI) diretamente aplicáveis à rede de cocitação e à distribuição de citações:

  • powerlaw_fit  — ajuste de lei de potência a dados empíricos discretos pelo
    método de Clauset, Shalizi & Newman (SIAM Review, 2009): expoente α por
    máxima verossimilhança e x_min por minimização da estatística de
    Kolmogorov–Smirnov. Responde se a atenção do campo é de cauda pesada.
  • cnm_communities — detecção de comunidades por maximização gulosa de
    modularidade (Clauset, Newman & Moore, Phys. Rev. E, 2004), ponderada.

Referências:
  CLAUSET, A.; SHALIZI, C. R.; NEWMAN, M. E. J. Power-law distributions in
    empirical data. SIAM Review, v. 51, n. 4, p. 661–703, 2009.
  CLAUSET, A.; NEWMAN, M. E. J.; MOORE, C. Finding community structure in very
    large networks. Physical Review E, v. 70, 066111, 2004.
  Código de referência: https://aaronclauset.github.io/powerlaws/
"""
import math


def _zeta(s, q, terms=2000):
    """Zeta de Hurwitz ζ(s, q) = Σ_{k≥0} (k+q)^{-s}, soma direta + cauda integral.
    Para s>1 e q≥1 a série decai como k^{-s}; poucos milhares de termos + a correção
    de cauda (∫ de terms..∞) bastam."""
    total = 0.0
    for k in range(terms):
        total += (k + q) ** (-s)
    if s > 1:
        total += (terms + q) ** (1 - s) / (s - 1)
    return total


def powerlaw_fit(data, xmin_candidates=None):
    """Ajusta uma lei de potência discreta p(x) ∝ x^{-α} para x ≥ x_min.

    Devolve {alpha, xmin, ks, n_tail, n} — α por MLE (Clauset et al., eq. 3.7) e
    x_min escolhido por menor distância KS entre a CDF empírica e a ajustada. A KS é
    avaliada só nos valores observados (não em todo inteiro), o que a torna viável
    mesmo com contagens de citação na casa das dezenas de milhar.
    """
    import bisect
    xs = sorted(int(x) for x in data if x and x > 0)
    if len(xs) < 10:
        return {}
    uniq = sorted(set(xs))
    cands = xmin_candidates or uniq[:40]          # x_min costuma ser pequeno
    best = None
    for xmin in cands:
        lo = bisect.bisect_left(xs, xmin)
        tail = xs[lo:]
        n = len(tail)
        if n < 10:
            continue
        s = sum(math.log(x / (xmin - 0.5)) for x in tail)   # MLE (Clauset et al., eq. 3.7)
        if s <= 0:
            continue
        alpha = 1.0 + n / s
        norm = _zeta(alpha, xmin)
        D = 0.0
        for v in uniq:                              # KS só nos valores observados do tail
            if v < xmin:
                continue
            emp = (n - bisect.bisect_left(tail, v)) / n      # P_emp(X >= v)
            th = _zeta(alpha, v) / norm                       # P_th(X >= v)
            D = max(D, abs(emp - th))
        if best is None or D < best["ks"]:
            best = {"alpha": round(alpha, 3), "xmin": xmin, "ks": round(D, 4), "n_tail": n, "n": len(xs)}
    return best or {}


def cnm_communities(node_ids, links, weight="peso"):
    """Comunidades por modularidade gulosa (Clauset–Newman–Moore, 2004), ponderada.

    node_ids: iterável de ids; links: lista de dicts com source/target/<weight>.
    Devolve (comm, Q, k): mapa id->comunidade, modularidade final e nº de comunidades.
    """
    nodes = list(node_ids)
    idx = {n: i for i, n in enumerate(nodes)}
    m2 = 0.0
    adj = {i: {} for i in range(len(nodes))}
    for l in links:
        a, b = idx.get(l["source"]), idx.get(l["target"])
        if a is None or b is None or a == b:
            continue
        w = l.get(weight, 1)
        adj[a][b] = adj[a].get(b, 0) + w
        adj[b][a] = adj[b].get(a, 0) + w
        m2 += 2 * w
    if m2 == 0:
        return {n: i for i, n in enumerate(nodes)}, 0.0, len(nodes)
    # e_ij = fração do peso entre comunidades i,j; a_i = fração das pontas em i
    comm = {i: i for i in range(len(nodes))}
    e = {i: {j: w / m2 for j, w in adj[i].items()} for i in range(len(nodes))}
    a = {i: sum(e[i].values()) for i in range(len(nodes))}
    members = {i: {i} for i in range(len(nodes))}
    Q = sum(e[i].get(i, 0) for i in e) - sum(v * v for v in a.values())

    def dq(i, j):
        return 2 * (e[i].get(j, 0) - a[i] * a[j])

    alive = set(range(len(nodes)))
    while len(alive) > 1:
        best, bij = 0.0, None
        for i in alive:
            for j in e[i]:
                if j > i and j in alive:
                    d = dq(i, j)
                    if d > best:
                        best, bij = d, (i, j)
        if bij is None:                      # nenhuma fusão aumenta Q
            break
        i, j = bij                            # funde j em i
        Q += best
        neigh = set(e[i]) | set(e[j])
        for k in neigh:
            if k in (i, j):
                continue
            e[i][k] = e[i].get(k, 0) + e[j].get(k, 0)
            e[k][i] = e[i][k]
            if j in e[k]:
                del e[k][j]
        e[i][i] = e[i].get(i, 0) + e[j].get(j, 0) + 2 * e[i].get(j, 0)
        e[i].pop(j, None)
        a[i] += a[j]
        members[i] |= members[j]
        alive.discard(j)
        for d in (e, a, members):
            pass
    # rotula
    out, c = {}, 0
    for i in alive:
        for mem in members[i]:
            out[nodes[mem]] = c
        c += 1
    return out, round(Q, 3), c


def participation_z(node_ids, links, comm, weight="peso"):
    """Cartografia de papéis de Guimerà & Amaral (Nature, 2005), ponderada.

    Devolve (P, z): coeficiente de participação P_i = 1 − Σ_s (k_is/k_i)² — alto quando
    as ligações do nó se espalham por muitas comunidades (CONECTOR entre comunidades,
    independente do grau) — e o grau intramódulo padronizado z (hub vs não-hub). Usa as
    comunidades `comm` (mapa id->comunidade, idealmente as detectadas pelo CNM).
    """
    from collections import defaultdict
    deg = defaultdict(float)
    kc = defaultdict(lambda: defaultdict(float))
    for l in links:
        s, t, w = l["source"], l["target"], l.get(weight, 1)
        deg[s] += w; deg[t] += w
        kc[s][comm.get(t)] += w
        kc[t][comm.get(s)] += w
    P, kin = {}, {}
    for n in node_ids:
        d = deg.get(n, 0)
        P[n] = (1 - sum((v / d) ** 2 for v in kc[n].values())) if d else 0.0
        kin[n] = kc[n].get(comm.get(n), 0)
    z = {}
    for c in set(comm.get(n) for n in node_ids):
        mem = [n for n in node_ids if comm.get(n) == c]
        vals = [kin[n] for n in mem]
        mu = sum(vals) / len(vals) if vals else 0.0
        sd = (sum((v - mu) ** 2 for v in vals) / len(vals)) ** 0.5 if vals else 0.0
        for n in mem:
            z[n] = (kin[n] - mu) / sd if sd > 0 else 0.0
    return P, z


def ga_role(P, z):  # papéis de Guimerà-Amaral (limiares do artigo)
    if z >= 2.5:
        return "hub conector" if P > 0.30 else "hub provincial"
    if P > 0.62:
        return "conector"
    if P > 0.05:
        return "periférico"
    return "ultraperiférico"


if __name__ == "__main__":
    import json
    import os
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    net = json.load(open(os.path.join(root, "data", "network.json"), encoding="utf-8"))
    cited = [n.get("cited_by", 0) for n in net["nodes"]]
    print("lei de potência (citações dos nós):", powerlaw_fit(cited))
    comm, Q, k = cnm_communities([n["id"] for n in net["nodes"]], net["links"])
    print(f"CNM: {k} comunidades, Q = {Q}")
