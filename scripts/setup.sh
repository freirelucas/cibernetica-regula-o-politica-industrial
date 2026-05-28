#!/bin/sh
# Configuração one-shot por checkout:
#   - hook de pre-commit autoinstalável (auto-estagia o cache do OpenAlex e o CHANGELOG)
# Uso: sh scripts/setup.sh
set -e
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "erro: rode dentro do repo git"; exit 1; }
cd "$root"
git config core.hooksPath .githooks
chmod +x .githooks/* 2>/dev/null || true
echo "ok: core.hooksPath -> .githooks (pre-commit auto-estagia data/oa_cache/ e CHANGELOG.md)"
