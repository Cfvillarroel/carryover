#!/usr/bin/env bash
# Activa la capacidad "wiki" en un repo de proyecto: copia el generador y el hook pre-push.
# Uso:  bash install-wiki.sh [/ruta/al/repo]   (def: repo actual)
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
[ -n "$TARGET" ] && git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 \
  || { echo "No es un repo git: '${TARGET:-<vacío>}'"; exit 1; }

mkdir -p "$TARGET/wiki"
cp "$SRC/gen-wiki.sh" "$TARGET/wiki/gen-wiki.sh"; chmod +x "$TARGET/wiki/gen-wiki.sh"
HOOK="$(git -C "$TARGET" rev-parse --git-path hooks)/pre-push"
cp "$SRC/pre-push" "$HOOK"; chmod +x "$HOOK"
grep -qxF "wiki/.gen.log" "$TARGET/.gitignore" 2>/dev/null || echo "wiki/.gen.log" >> "$TARGET/.gitignore"

echo "Wiki activada en $TARGET"
echo "  → se regenera al pushear a master/main, en $TARGET/wiki/ (formato GitHub Wiki)"
echo "  → publicar al wiki de GitHub: WIKI_PUBLISH=1 antes del push, o corre wiki/gen-wiki.sh a mano"
