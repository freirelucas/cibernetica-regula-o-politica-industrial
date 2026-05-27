#!/usr/bin/env python3
"""Gera/atualiza CHANGELOG.md a partir do histórico do git, agrupado por tema.

Estado-alvo (o "goal"): o CHANGELOG existe e tem uma entrada para cada commit
de trabalho (feat/fix) desta branch desde o início, agrupada por tema, e é
recriado a cada execução — basta rodar de novo após cada commit para mantê-lo
em dia.

Determinístico: classifica cada commit num tema por palavras-chave do assunto
(primeira regra que casa vence), pulando merges e o upload inicial do pacote.

Uso:  python .claude/skills/changelog/changelog.py            # escreve CHANGELOG.md
      python .claude/skills/changelog/changelog.py --check    # falha se desatualizado
"""
import subprocess
import sys
import os

ROOT = subprocess.check_output(["git", "rev-parse", "--show-toplevel"], text=True).strip()
OUT = os.path.join(ROOT, "CHANGELOG.md")

# (título do tema, [palavras-chave em minúsculas]) — ordem importa: 1ª regra que casa vence.
THEMES = [
    ("Integridade de dados", [
        "integridade", "não resolvem", "404", "duplicad", "funde nós", "dedup"]),
    ("Triagem e exportação (Rayyan)", [
        "rayyan", "triagem", "curadoria", "recorte", "inclusão/exclusão",
        "endnote", "bibtex", "ris/csv", "downloads", "zip", "decisões"]),
    ("Explorador e visualizações", [
        "explorador", "d3", "visualiza", "clicáve", "gráfico temporal", "viz",
        "legibilidade", "silos", "disposição", "rede do núcleo", "interatividade"]),
    ("Análise (cienciometria / Science of Science)", [
        "modularidade", "força de associação", "lei de potência", "cnm", "clauset",
        "participação", "intermediação", "modelo nulo", "nmi", "comunidades",
        "snowball", "explodid", "4º eixo", "complexidade", "caminhos potenciais",
        "separação", "pontes", "ponte de lange", "testa empiricamente", "rigor"]),
    ("Funil, dados e reprodutibilidade", [
        "funil", "colab", "notebook", "célula", "openalex", "crawl", "eecs-ii",
        "doi", "autorias", "metadados", "exportáveis", "descompacta",
        "regeneração", "secret", "banho de loja", "rate-limit", "429",
        "busca automatizada", "dado baixável", "cocitação real"]),
    ("Conteúdo acadêmico e autoria", [
        "acadêmic", "brasileir", "faganello", "coautor", "autoria", "capítulo",
        "síntese", "leitura recomendada", "jargão", "tarja", "corpora", "rodrik",
        "precedente", "análise independente", "claucia"]),
    ("Site e publicação (GitHub Pages)", [
        "site", "cdn", "javascript", "responsivo", "mobile", "impressão", "pages",
        "deploy", "dicionário", "skip-link", "fallback", "ux", "desktop-first"]),
    ("Infraestrutura, testes e ferramentas", [
        "skill", "pytest", " ci ", "testes", "readme", "driver", "gerador legado",
        "objetivo"]),
]
OTHER = "Outros"
SKIP_SUBJECTS = {"Add files via upload"}


def commits():
    out = subprocess.check_output(
        ["git", "log", "--no-merges", "--reverse", "--date=short",
         "--pretty=format:%h\x1f%ad\x1f%s"], text=True)
    for line in out.splitlines():
        h, d, s = line.split("\x1f", 2)
        if s.strip() in SKIP_SUBJECTS:
            continue
        yield h, d, s.strip()


def theme_of(subject):
    low = (" " + subject + " ").lower()
    for title, kws in THEMES:
        if any(kw in low for kw in kws):
            return title
    return OTHER


def build():
    buckets = {t: [] for t, _ in THEMES}
    buckets[OTHER] = []
    n = 0
    for h, d, s in commits():
        buckets[theme_of(s)].append((h, d, s))
        n += 1
    order = [t for t, _ in THEMES] + [OTHER]
    lines = [
        "# CHANGELOG",
        "",
        f"Registro de mudanças desta branch, agrupado por tema "
        f"({n} commits de trabalho). **Gerado** por "
        "`.claude/skills/changelog/changelog.py` — para atualizar após um novo "
        "commit, rode o script (ou use a skill `/changelog`).",
        "",
    ]
    for t in order:
        items = buckets[t]
        if not items:
            continue
        lines.append(f"## {t}")
        lines.append("")
        for h, d, s in reversed(items):          # mais recente primeiro dentro do tema
            lines.append(f"- {s} · `{h}` · {d}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", n


def main():
    text, n = build()
    if "--check" in sys.argv:
        cur = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        if cur != text:
            print("CHANGELOG.md desatualizado — rode: python .claude/skills/changelog/changelog.py")
            sys.exit(1)
        print(f"CHANGELOG.md em dia ({n} commits).")
        return
    open(OUT, "w", encoding="utf-8").write(text)
    print(f"CHANGELOG.md escrito: {n} commits em {sum(1 for _ in [t for t,_ in THEMES]+[OTHER])} temas possíveis.")


if __name__ == "__main__":
    main()
