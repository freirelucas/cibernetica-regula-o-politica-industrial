---
name: changelog
description: Gera ou atualiza o CHANGELOG.md desta branch a partir do git, com uma entrada por commit de trabalho agrupada por tema. Use quando pedirem para criar/atualizar/regenerar o changelog, o "registro de mudanças", ou manter o CHANGELOG em dia após novos commits.
---

# /changelog — registro de mudanças por tema

Estado-alvo ("goal"): **`CHANGELOG.md` existe e tem uma entrada para cada commit
de trabalho (feat/fix) desta branch desde o início, agrupada por tema, e é
atualizado a cada novo commit.**

O CHANGELOG é **gerado**, não editado à mão — assim a regra "uma entrada por
commit, por tema" nunca sai do lugar. O driver é
`.claude/skills/changelog/changelog.py` (só biblioteca padrão + `git`).

## Atualizar / regenerar (caminho principal)

```bash
python .claude/skills/changelog/changelog.py
```

Lê `git log --no-merges` (pula merges e o upload inicial), classifica cada
commit num tema pela 1ª palavra-chave que casa no assunto e reescreve
`CHANGELOG.md` (mais recente primeiro dentro de cada tema). Idempotente: rode de
novo após cada commit para manter em dia.

Conferir drift sem escrever (sai com código ≠ 0 se o arquivo divergir do
regenerado) — útil manualmente; sob o hook de `pre-commit` fica naturalmente um
commit atrás (a auto-referência), então não use como gate estrito de CI:

```bash
python .claude/skills/changelog/changelog.py --check
```

## Manter em dia "a cada novo commit"

Regenerar é uma ação; "a cada commit" é um comportamento automático. Duas formas:

1. **Na rotina de commit do agente** (o que fazemos aqui): após cada `git commit`,
   rode o driver e inclua o `CHANGELOG.md` no commit seguinte (ou faça
   `git commit --amend` se ainda não empurrou). Funciona enquanto o agente é quem
   comita.
2. **Hook de `pre-commit`** (recomendado — automático, sem agente, árvore limpa):

   ```bash
   cat > .git/hooks/pre-commit <<'SH'
   #!/bin/sh
   root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
   if [ -f "$root/.claude/skills/changelog/changelog.py" ]; then
     python3 "$root/.claude/skills/changelog/changelog.py" >/dev/null 2>&1 && git add "$root/CHANGELOG.md" 2>/dev/null
   fi
   [ -d "$root/data/oa_cache" ] && git add "$root/data/oa_cache" 2>/dev/null   # ver skill /oa-cache
   exit 0
   SH
   chmod +x .git/hooks/pre-commit
   ```
   (O mesmo hook também versiona o cache de consultas OpenAlex — ver `/oa-cache`.)

   Regenera e **estagia o CHANGELOG dentro do próprio commit** (a árvore fica
   limpa, sem nada pendente depois). Nunca bloqueia o commit (todos os ramos
   saem com `exit 0`). A entrada do commit que está sendo feito só aparece no
   commit seguinte — auto-referência inevitável de um changelog que se versiona.
   Hooks em `.git/hooks/` **não são versionados**: reinstale após cada clone
   (este bloco é o instalador).

## Temas

Ordem fixa, 1ª regra que casa vence (ver `THEMES` no driver): Integridade de
dados · Triagem/Rayyan · Explorador e visualizações · Análise (cienciometria) ·
Funil/dados/reprodutibilidade · Conteúdo acadêmico e autoria · Site/Pages ·
Infraestrutura/testes/ferramentas · Outros.

## Gotchas

- **Classificação por palavra-chave**, não por rótulo de commit: um commit que
  toca dois temas cai no primeiro que casar (ex.: "explorador … triagem" cai em
  Triagem por causa de "triagem"). Para recolocar, ajuste a ordem/palavras em
  `THEMES` — é transparente de propósito.
- **`Outros` deve ficar vazio.** Se aparecer, falta palavra-chave para aquele
  assunto: acrescente em `THEMES` e regenere.
- Sem prefixo convencional (`feat:`/`fix:`) no repo: o driver inclui **todos** os
  commits não-merge (menos o upload inicial). Se o projeto adotar Conventional
  Commits, filtre por prefixo em `commits()`.
- Verificado nesta sessão: 78 commits, 8 temas preenchidos, `Outros` vazio,
  `--check` retorna "em dia".
