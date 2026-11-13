#!/usr/bin/env python3
"""Aceite de uma ordem de construção: um comando, um veredito.

    python scripts/aceite.py --lista          # o quadro: o que está feito, o que está liberado
    python scripts/aceite.py N1 --iniciar     # confere as dependências e marca o ponto de partida
    python scripts/aceite.py N1               # confere tudo e diz APROVADA ou REPROVADA

O que é conferido (definido em design/ordens/quadro.json):
  1. arquivos   — só mudou o que a ordem pode mudar; docs/ só entra em commit de ordem de integração;
  2. construção — python src/build_site.py termina sem erro;
  3. canônico   — docs/dados/ igual ao do git (a rede de coautoria é a do Leiden);
  4. testes     — suíte inteira sem falha; nenhum teste pulado, salvo os das ordens ainda não feitas;
                  os testes da própria ordem têm de PASSAR (pulado não vale);
  5. driver     — STATUS: OK;
  6. estrutura  — nenhuma tela com erro, rolagem lateral, aba cortada ou número vazio;
  7. telas      — as telas da ordem saem limpas da conferência completa (inclusive alvo de toque).
Sai com código 0 só se tudo passar. Não edite este arquivo nem o quadro para passar.
"""
import fnmatch
import json
import os
import subprocess
import sys
import xml.etree.ElementTree as ET

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
QUADRO = os.path.join(RAIZ, "design", "ordens", "quadro.json")
PAGINAS = ["docs/index.html", "docs/nota.html", "docs/espaco.html", "docs/explorador.html", "docs/triagem.html"]


def roda(*cmd, **kw):
    return subprocess.run(list(cmd), cwd=RAIZ, capture_output=True, text=True, **kw)


def git(*a):
    return roda("git", *a).stdout.strip()


def provada(ordem):
    for p in ordem["prova"]:
        if "arquivo" in p and not os.path.exists(os.path.join(RAIZ, p["arquivo"])):
            return False
        if "contem" in p:
            caminho = os.path.join(RAIZ, p["contem"][0])
            if not os.path.exists(caminho) or p["contem"][1] not in open(caminho, encoding="utf-8").read():
                return False
    return True


def marca(oid):
    return os.path.join(git("rev-parse", "--absolute-git-dir"), f"ordem-{oid}-partida")


def lista(ordens):
    feitas = {o["id"] for o in ordens if provada(o)}
    print(f"{'ordem':6} {'onda':11} {'situação':12} título")
    for o in ordens:
        sit = "feita" if o["id"] in feitas else ("liberada" if all(d in feitas for d in o["depende"]) else "aguarda " + ",".join(d for d in o["depende"] if d not in feitas))
        print(f"{o['id']:6} {o['onda']:11} {sit:12} {o['titulo']}")
    return 0


def mudancas(base):
    commitados = [f for f in git("diff", "--name-only", base, "HEAD").splitlines() if f]
    soltos = []
    for linha in roda("git", "status", "--porcelain").stdout.splitlines():
        soltos.append(linha[3:].split(" -> ")[-1].strip('"'))
    return [f for f in commitados if not alheio(f)], [f for f in soltos if not alheio(f)]


def alheio(caminho):
    """Cópias isoladas de outros executores moram em .claude/worktrees/: não são mudança desta ordem."""
    return caminho.startswith(".claude/worktrees/")


def testes():
    saida = os.path.join(git("rev-parse", "--absolute-git-dir"), "aceite-junit.xml")
    res = {}
    if os.path.exists(saida):
        os.remove(saida)
    r = roda(sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", f"--junitxml={saida}")
    if not os.path.exists(saida):                     # o pytest morreu antes de relatar: é falha, não exceção
        return {"pytest": ("falhou", "o pytest não chegou a rodar")}, [(r.stderr or r.stdout).strip()[-300:]]
    for caso in ET.parse(saida).getroot().iter("testcase"):
        nid = caso.get("classname", "").replace(".", "/") + ".py::" + caso.get("name", "")
        filhos = {f.tag: (f.get("message") or "") for f in caso}
        res[nid] = ("falhou", filhos.get("failure") or filhos.get("error")) if ("failure" in filhos or "error" in filhos) else \
                   ("pulado", filhos["skipped"]) if "skipped" in filhos else ("passou", "")
    return res, (r.stdout or "").strip().splitlines()[-1:]


def main():
    q = json.load(open(QUADRO, encoding="utf-8"))
    ordens = q["ordens"]
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if "--lista" in sys.argv or not args:
        return lista(ordens)
    por_id = {o["id"]: o for o in ordens}
    if args[0] not in por_id:
        print("ordem desconhecida:", args[0], "| existentes:", ", ".join(por_id))
        return 2
    o = por_id[args[0]]
    feitas = {x["id"] for x in ordens if provada(x)}

    if "--iniciar" in sys.argv:
        faltam = [d for d in o["depende"] if d not in feitas]
        if faltam:
            print(f"NÃO INICIE: a ordem {o['id']} depende de {', '.join(faltam)}, que ainda não está feita.")
            return 1
        sujo = [l for l in roda("git", "status", "--porcelain").stdout.splitlines()
                if not l[3:].startswith("docs/") and not alheio(l[3:])]
        if sujo:
            print("NÃO INICIE: há mudanças soltas fora de docs/. Commite ou desfaça antes:\n  " + "\n  ".join(sujo[:8]))
            return 1
        open(marca(o["id"]), "w").write(git("rev-parse", "HEAD"))
        print(f"Ordem {o['id']} iniciada em {git('rev-parse', '--short', 'HEAD')}: {o['titulo']}")
        print("Você pode mudar SÓ estes arquivos:\n  " + ("\n  ".join(o["arquivos"]) or "(nenhum arquivo de código; só docs/, por reconstrução)"))
        print("docs/: " + ("entra no commit, reconstruído" if o["docs"] else "NÃO entra no commit (quem commita docs/ é a ordem de integração)"))
        return 0

    if not os.path.exists(marca(o["id"])):
        print(f"Rode primeiro: python scripts/aceite.py {o['id']} --iniciar")
        return 2
    base = open(marca(o["id"])).read().strip()
    linhas, ok_geral = [], True

    def registra(nome, ok, detalhe=""):
        nonlocal ok_geral
        ok_geral = ok_geral and ok
        linhas.append((nome, "ok" if ok else "FALHOU", detalhe))

    # 1. arquivos
    commitados, soltos = mudancas(base)
    # o '*' de um padrão não atravessa pasta: src/*_template.html não cobre src/outra/x_template.html
    permitido = lambda f: any(fnmatch.fnmatch(f, g) and f.count("/") == g.count("/") for g in o["arquivos"])   # noqa: E731
    fora = sorted({f for f in commitados + soltos if not f.startswith("docs/") and not permitido(f)})
    docs_no_commit = sorted(f for f in commitados if f.startswith("docs/"))
    det = ""
    if fora:
        det = "fora da lista da ordem: " + ", ".join(fora[:8])
    elif docs_no_commit and not o["docs"]:
        det = "docs/ entrou num commit desta ordem (não pode): " + ", ".join(docs_no_commit[:4])
    registra("1. arquivos", not det, det)

    # 2 e 3. construção e docs canônico
    r = roda(sys.executable, os.path.join("src", "build_site.py"))
    registra("2. construção", r.returncode == 0, (r.stderr or r.stdout).strip()[-300:] if r.returncode else "")
    sujo = git("status", "--porcelain", "--", "docs/dados")
    registra("3. canônico", not sujo, "docs/dados/ divergiu: rode python scripts/preparar.py" if sujo else "")

    # 4. testes
    res, resumo = testes()
    falhas = [n for n, (s, _) in res.items() if s == "falhou"]
    tolerados = {t for x in ordens if x["id"] not in feitas and x["id"] != o["id"] for t in x["testes"]}
    pulados = [n for n, (s, _) in res.items() if s == "pulado" and n not in tolerados]
    proprios = [t for t in o["testes"] if res.get(t, ("ausente",))[0] != "passou"]
    det = []
    if falhas:
        det.append("falharam: " + ", ".join(f.split("::")[-1] for f in falhas[:6]))
    if pulados:
        det.append("pulados sem motivo aceito (falta ferramenta? rode scripts/preparar.py): " + ", ".join(p.split("::")[-1] for p in pulados[:6]))
    if proprios:
        det.append("testes da ordem que não passaram: " + ", ".join(f"{t.split('::')[-1]} ({res.get(t, ('ausente',))[0]})" for t in proprios))
    registra("4. testes", not det, "; ".join(det) or (resumo[0] if resumo else ""))

    # 5. driver
    r = roda(sys.executable, os.path.join(".claude", "skills", "run-scisci-ipea", "driver.py"))
    registra("5. driver", "STATUS: OK" in r.stdout, "" if "STATUS: OK" in r.stdout else (r.stdout or r.stderr).strip()[-300:])

    # 6. estrutura de todas as telas; 7. telas da ordem, conferência completa
    existentes = [p for p in PAGINAS if os.path.exists(os.path.join(RAIZ, p))]
    r = roda(sys.executable, os.path.join("scripts", "conferir_telas.py"), "--so-estrutura", *existentes)
    registra("6. estrutura", r.returncode == 0, "" if r.returncode == 0 else "\n".join(l for l in r.stdout.splitlines() if "PROBLEMA" in l or l.strip().startswith("-"))[:500])
    if o["paginas"]:
        r = roda(sys.executable, os.path.join("scripts", "conferir_telas.py"), *o["paginas"])
        registra("7. telas", r.returncode == 0, "" if r.returncode == 0 else "\n".join(l for l in r.stdout.splitlines() if "PROBLEMA" in l or l.strip().startswith("-"))[:700])
    else:
        linhas.append(("7. telas", "—", "esta ordem não fecha nenhuma tela inteira"))

    print(f"\nAceite da ordem {o['id']} — {o['titulo']}")
    for nome, sit, det in linhas:
        print(f"  {nome:14} {sit:7} {det}")
    print("\nVEREDITO:", "APROVADA" if ok_geral else "REPROVADA")
    if ok_geral:
        meus = sorted({f for f in soltos if permitido(f) or (o["docs"] and f.startswith("docs/"))})
        if meus:
            print("Para commitar (só estes):\n  git add " + " ".join(meus))
        if not o["docs"]:
            print("Não use 'git add -A': docs/ não entra no commit desta ordem.")
    return 0 if ok_geral else 1


if __name__ == "__main__":
    sys.exit(main())
