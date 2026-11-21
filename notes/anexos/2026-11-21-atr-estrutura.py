#!/usr/bin/env python3
"""Conferência estática do pacote da skill analise-tematica-reflexiva (labiia-lab). Só leitura.

Acompanha a nota notes/2026-11-21-skill-atr-auditoria-e-sugestoes.md e o script de reprodução
ao lado. Mede o que não depende de executar a skill: frontmatter e tamanho do SKILL.md,
referências internas, estrutura dos cenários, catálogo de códigos, versão declarada,
termos residuais, superfície que a regra E10 não alcança, complexidade aproximada dos
scripts e o que o enunciado do teste de aptidão revela do gabarito.

Uso: python3 -I -B notes/anexos/2026-11-21-atr-estrutura.py /caminho/do/clone
"""
from __future__ import annotations

import ast
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

R = Path(sys.argv[1]).resolve()
mds = sorted(p for p in R.rglob("*.md") if ".git" not in p.parts)
texto = {p: p.read_text(encoding="utf-8") for p in mds}
rel = lambda p: p.relative_to(R).as_posix()


def titulo(t):
    print("\n=== " + t)


titulo("1. SKILL.md: frontmatter e tamanho")
skill = texto[R / "SKILL.md"]
fm = skill.split("---", 2)[1]
nome = re.search(r"^name:\s*(.+)$", fm, re.M).group(1).strip()
desc = re.search(r"^description:\s*(.+)$", fm, re.M).group(1).strip()
corpo = skill.split("---", 2)[2]
print(f"name={nome!r} (pasta do repositório: {R.name!r}) | description: {len(desc)} caracteres, {len(desc.split())} palavras")
print(f"corpo: {len(corpo.splitlines())} linhas, {len(corpo.split())} palavras | termos em português na description:",
      [t for t in ("análise", "temática", "entrevista", "codifica", "grupo focal") if t in desc.lower()] or "nenhum")
print("menção a versão no SKILL.md:", re.findall(r".{0,30}(?:vers[aã]o|\b2\.0\.0\b).{0,30}", skill, re.I)[:3] or "nenhuma")

titulo("2. Referências internas (caminhos entre crases e links relativos)")
padrao = re.compile(r"`((?:referencias|templates|scripts|testes)/[\w./-]+\.(?:md|py|txt|jsonl?))`")
link = re.compile(r"\]\(([^)#\s]+)\)")
faltam, total = [], 0
for p, t in texto.items():
    for alvo in padrao.findall(t):
        total += 1
        if not (R / alvo).exists():
            faltam.append((rel(p), alvo))
    for alvo in link.findall(t):
        if alvo.startswith(("http://", "https://", "mailto:")):
            continue
        total += 1
        if not ((p.parent / alvo).exists() or (R / alvo).exists()):
            faltam.append((rel(p), alvo))
print(f"{total} referências conferidas; quebradas: {faltam or 'nenhuma'}")

titulo("3. Arquivos de referencias/, templates/ e scripts/ não citados no SKILL.md")
for pasta in ("referencias", "templates", "scripts"):
    for p in sorted((R / pasta).rglob("*")):
        if p.is_file() and rel(p) not in skill and p.name not in skill:
            print("   não citado:", rel(p))
print("   (fim da lista)")

titulo("4. Cenários comportamentais: estrutura dos 28 arquivos")
assinaturas = defaultdict(list)
for p in sorted((R / "testes").glob("cenario-*.md"), key=lambda q: int(re.search(r"cenario-(\d+)", q.name).group(1))):
    cab = tuple(re.sub(r"\s+", " ", h).strip().lower() for h in re.findall(r"^#{2,3}\s+(.+)$", texto[p], re.M))
    assinaturas[cab].append(int(re.search(r"cenario-(\d+)", p.name).group(1)))
for cab, ids in sorted(assinaturas.items(), key=lambda kv: -len(kv[1])):
    print(f"   {len(ids):2d} cenário(s) {ids if len(ids) <= 12 else str(ids[:12]) + '…'}: {list(cab)}")
exigidos = ("objetivo", "prompt", "falha", "comportamento", "critério")
for p in sorted((R / "testes").glob("cenario-*.md")):
    baixo = texto[p].lower()
    falta = [e for e in exigidos if e not in baixo]
    if falta:
        print("   sem o elemento obrigatório", falta, "->", p.name)
print("   registros de execução dos cenários no repositório:",
      [rel(p) for p in R.rglob("*") if p.is_file() and ".git" not in p.parts and re.search(r"resultado|forward|baseline|regress", p.name, re.I)] or "nenhum")

titulo("5. Referências com mais de 100 linhas sem sumário")
print("  ", [f"{rel(p)} ({len(t.splitlines())} linhas)" for p, t in texto.items()
             if p.parent.name == "referencias" and len(t.splitlines()) > 100 and "## Sumário" not in t] or "nenhuma")

titulo("6. Códigos de erro/alerta: usados no script e onde estão documentados")
fonte_aud = (R / "scripts" / "auditar_analise.py").read_text(encoding="utf-8")
usados = sorted(set(re.findall(r'"([EA]\d\d)"', fonte_aud)))
doc = {c: [rel(p) for p, t in texto.items() if re.search(rf"\b{c}\b", t) and p.parent.name != "testes"] for c in usados}
print("   usados:", " ".join(usados))
print("   lacunas na numeração:", [f"E{n:02d}" for n in range(1, 14) if f"E{n:02d}" not in usados],
      [f"A{n:02d}" for n in range(1, 18) if f"A{n:02d}" not in usados])
print("   códigos explicados em algum .md fora de testes/:", {c: v for c, v in doc.items() if v} or "nenhum")

titulo("7. Versão declarada, por arquivo")
for p in sorted(R.rglob("*")):
    if p.is_file() and ".git" not in p.parts and p.suffix in (".md", ".cff", ".py", ".txt"):
        n = len(re.findall(r"\b2\.0\.0\b", p.read_text(encoding="utf-8")))
        if n:
            print(f"   {rel(p)}: {n}")

titulo("8. Termos residuais e inconsistências de nomenclatura")
for termo in (r"advogad[oa] do diabo", r"auditor de evidências", r"corpus-sombra", r"\b4\s?[-–a]\s?8\b", r"Byrne \(2021\)", r"BYRNE.*2022", r"devil"):
    achados = [(rel(p), i) for p, t in texto.items() for i, l in enumerate(t.splitlines(), 1) if re.search(termo, l, re.I)]
    print(f"   /{termo}/ -> {achados[:8] or 'nenhum'}")

titulo("9. Frequência da palavra 'todo' (\\btodo\\b, sem diferenciar caixa) nos textos da própria skill")
re_todo = re.compile(r"\btodo\b", re.I)
por_pasta = Counter()
exemplos = []
for p, t in texto.items():
    for i, l in enumerate(t.splitlines(), 1):
        if re_todo.search(l):
            por_pasta[p.parent.name if p.parent != R else "(raiz)"] += 1
            if len(exemplos) < 6:
                exemplos.append(f"{rel(p)}:{i}: {l.strip()[:90]}")
print("   linhas com a palavra, por pasta:", dict(por_pasta))
for e in exemplos[:6]:
    print("     ", e)
micro = (R / "scripts" / "aptidao" / "microcorpus.txt").read_text(encoding="utf-8")
print("   no microcorpus de aptidão:", len(re_todo.findall(micro)), "| nas falas de teste (FALA_1..3):",
      len(re_todo.findall((R / "testes" / "test_auditar_analise.py").read_text(encoding="utf-8").split("def base")[0])))

titulo("10. Superfície que a regra E10 não alcança, medida nos 9 templates")
dois, vazias, marcadores, tres = 0, 0, 0, 0
for p, t in texto.items():
    if "templates" not in p.parts:
        continue
    for l in t.splitlines():
        s = l.strip()
        if not s.startswith("|") and s.count(" | ") == 1 and len(re.findall(r"[\wÀ-ÿ'-]+", s)) <= 12:
            dois += 1
        if not s.startswith("|") and s.count(" | ") >= 2 and len(re.findall(r"[\wÀ-ÿ'-]+", s)) <= 12:
            tres += 1
        if s.startswith("|") and not set(s) <= set("|-: ") and not any(c.strip() for c in s.strip("|").split("|")):
            vazias += 1
        if s.startswith("|") and set(s) <= set("| ") and len(s) > 2:
            vazias += 1
        marcadores += len(re.findall(r"\[[^\]\[]{12,}\](?!\()", s))
print(f"   linhas de alternativa com 3+ opções (detectadas): {tres} | com 2 opções (não detectadas): {dois}")
print(f"   linhas de tabela totalmente vazias (não detectadas): {vazias} | marcadores entre colchetes (detectados): {marcadores}")

titulo("11. Scripts: tamanho, complexidade aproximada e imports sem uso")
DEC = (ast.If, ast.For, ast.While, ast.IfExp, ast.ExceptHandler, ast.With, ast.comprehension)


def cc(no):
    n = 1
    for s in ast.walk(no):
        if isinstance(s, DEC):
            n += 1
        elif isinstance(s, ast.BoolOp):
            n += len(s.values) - 1
    return n


for p in sorted((R / "scripts").glob("*.py")) + sorted((R / "testes").glob("test_*.py")):
    fonte = p.read_text(encoding="utf-8")
    arv = ast.parse(fonte)
    funcs = [(cc(n), (n.end_lineno - n.lineno + 1), n.name, n.lineno) for n in ast.walk(arv) if isinstance(n, ast.FunctionDef)]
    importados = {}
    for n in ast.walk(arv):
        if isinstance(n, ast.Import):
            for a in n.names:
                importados[(a.asname or a.name).split(".")[0]] = n.lineno
        elif isinstance(n, ast.ImportFrom) and n.module != "__future__":
            for a in n.names:
                importados[a.asname or a.name] = n.lineno
    nomes = {n.id for n in ast.walk(arv) if isinstance(n, ast.Name)} | {n.value.id for n in ast.walk(arv) if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name)}
    sem_uso = sorted(f"{k} (linha {v})" for k, v in importados.items() if k not in nomes)
    maiores = ", ".join(f"{nm}:{ln} CC≈{c} ({t} linhas)" for c, t, nm, ln in sorted(funcs, reverse=True)[:4])
    print(f"   {rel(p)}: {len(fonte.splitlines())} linhas, {len(funcs)} funções | imports sem uso: {sem_uso or 'nenhum'}")
    if p.parent.name == "scripts":
        print(f"      mais complexas: {maiores}")
        print(f"      operador := (exige Python 3.8+): {':=' in fonte} | docstrings em funções: "
              f"{sum(1 for n in ast.walk(arv) if isinstance(n, ast.FunctionDef) and ast.get_docstring(n))}/{len(funcs)}")

titulo("12. Teste de aptidão: o que o enunciado e a pasta revelam do gabarito")
tarefa = texto[R / "scripts" / "aptidao" / "tarefa.md"]
print("   exemplo de formato em tarefa.md:", re.search(r'"classificacao": \{[^}]+\}', tarefa).group(0))
print("   gabarito no script:", re.search(r"GABARITO_CLASSIFICACAO = (\{[^}]+\})", fonte_aud).group(1))
print("   gabarito completo também em:", [rel(p) for p in R.rglob("*.py") if "nao_literais" in p.read_text(encoding="utf-8") and p.name != "auditar_analise.py"])
