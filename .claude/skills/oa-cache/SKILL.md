---
name: oa-cache
description: Versiona e mantém em dia o cache do raw das consultas OpenAlex (data/oa_cache/) — reprodutibilidade offline do funil. Use ao rodar crawls, ao perguntar se as consultas estão guardadas no repo, ao inspecionar/limpar o cache, ou ao (re)instalar o hook que o mantém versionado.
---

# /oa-cache — raw das consultas OpenAlex versionado no repo

Estado-alvo ("goal"): **o raw de toda consulta ao OpenAlex fica guardado em
`data/oa_cache/` e versionado no GitHub** — o funil reconstrói offline, crawls
não re-batem na API e depurar deixa de ser doloroso (nada de "quebrou cedo").

## O que é

Cada resposta bem-sucedida do OpenAlex é gravada como um JSON, com nome =
`sha1(url)` em pastas-balde de 2 caracteres (`data/oa_cache/ab/abcd….json`). A
chave é a **URL** (independe da credencial mailto/api_key). Quem grava:

- `src/oa.py` — `get(url)` dos scripts locais (minirun, split_eecs2, author_snowball, cross_brasil…).
- o `oa_get` do notebook (`OUT/oa_cache/` no Colab).

Só sucesso entra no cache; um 429 esgotado devolve `{}` e **não** o envenena.

## Manter em dia (caminho principal — automático)

O **hook de `pre-commit`** estagia `data/oa_cache/` (e regenera o CHANGELOG) a
cada commit, então toda consulta nova entra no repo sozinha. Reinstale após um
clone (não é versionado):

```bash
cat > .git/hooks/pre-commit <<'SH'
#!/bin/sh
root="$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
if [ -f "$root/.claude/skills/changelog/changelog.py" ]; then
  python3 "$root/.claude/skills/changelog/changelog.py" >/dev/null 2>&1 && git add "$root/CHANGELOG.md" 2>/dev/null
fi
[ -d "$root/data/oa_cache" ] && git add "$root/data/oa_cache" 2>/dev/null
exit 0
SH
chmod +x .git/hooks/pre-commit
```

## Inspecionar

```bash
du -sh data/oa_cache && find data/oa_cache -name '*.json' | wc -l   # tamanho e nº de respostas
```

## Forçar refresh de uma consulta (raro)

O cache nunca expira por design (respostas do OpenAlex são estáveis para fins de
reprodução). Para re-buscar uma URL, apague o arquivo dela ou rode com
`oa.get(url, use_cache=False)` (no notebook, `oa_get(..., use_cache=False)`).

## Gotchas

- **Cresce com o corpus.** Hoje ~2 MB / dezenas de respostas; um funil completo
  (817 obras + citantes + refs no Colab) pode chegar a dezenas de MB. É o preço
  da reprodutibilidade offline — aceitável para um repo de pesquisa. Se incomodar,
  versione só o cache das fases caras (enrichment/cocitação) e mantenha o resto local.
- **Não comitar `{}`/erros:** o `get()` já evita (só grava sucesso).
- Verificado nesta sessão: `data/oa_cache/` versionado, hook estagiando, 2ª
  chamada à mesma URL retorna do cache em ~0,00 s.
