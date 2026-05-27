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

Verificar sem escrever (ex.: num hook ou na CI) — sai com código ≠ 0 se estiver
desatualizado:

```bash
python .claude/skills/changelog/changelog.py --check
```

## Manter em dia "a cada novo commit"

Regenerar é uma ação; "a cada commit" é um comportamento automático. Duas formas:

1. **Na rotina de commit do agente** (o que fazemos aqui): após cada `git commit`,
   rode o driver e inclua o `CHANGELOG.md` no commit seguinte (ou faça
   `git commit --amend` se ainda não empurrou). Funciona enquanto o agente é quem
   comita.
2. **Hook de `post-commit`** (sem agente) — escreve a versão mecânica a cada commit:

   ```bash
   printf '#!/bin/sh\npython "$(git rev-parse --show-toplevel)/.claude/skills/changelog/changelog.py"\ngit add CHANGELOG.md\n' \
     > .git/hooks/post-commit && chmod +x .git/hooks/post-commit
   ```

   (O hook regenera e estagia; o conteúdo entra no **próximo** commit. Hooks em
   `.git/hooks/` não são versionados — reinstale por clone.)

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
