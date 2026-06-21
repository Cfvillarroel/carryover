#!/usr/bin/env bash
# Genera/actualiza una wiki LOCAL en formato GitHub Wiki desde los cambios del repo,
# usando Claude headless (claude -p → usa tu auth y pasa por headroom).
# Uso:   bash gen-wiki.sh [RANGO_GIT]      (ej. origin/master..HEAD; vacío = HEAD~20..HEAD)
# Env:   WIKI_DIR=<carpeta salida>  (def: <repo>/wiki)
#        WIKI_PUBLISH=1             (además, push al wiki de GitHub <repo>.wiki.git)
set -euo pipefail

command -v claude >/dev/null || { echo "wiki: falta 'claude' en PATH"; exit 0; }
REPO_ROOT="$(git rev-parse --show-toplevel)"
WIKI_DIR="${WIKI_DIR:-$REPO_ROOT/wiki}"
RANGE="${1:-HEAD~20..HEAD}"
git -C "$REPO_ROOT" rev-parse "$RANGE" >/dev/null 2>&1 || RANGE="HEAD"
mkdir -p "$WIKI_DIR"

# --- contexto (acotado; headroom comprime de todas formas) ---
LOG="$(git -C "$REPO_ROOT" log --no-merges --pretty='- %s (%h)' "$RANGE" 2>/dev/null | head -100)"
DIFFSTAT="$(git -C "$REPO_ROOT" diff --stat "$RANGE" 2>/dev/null | tail -80)"
TREE="$(git -C "$REPO_ROOT" ls-files 2>/dev/null | head -400)"
HOME_PREV="$([ -f "$WIKI_DIR/Home.md" ] && cat "$WIKI_DIR/Home.md" || echo '(sin wiki previa)')"
MEM=""
HR="$HOME/.headroom/venv/bin/headroom"
if [ -x "$HR" ]; then
  TMPM="$(mktemp)"; "$HR" memory export --output "$TMPM" 2>/dev/null || true
  MEM="$(head -c 8000 "$TMPM" 2>/dev/null || true)"; rm -f "$TMPM"
fi

# --- prompt → Claude headless ---
OUT="$(claude -p 2>/dev/null <<EOF
Eres documentalista técnico. Genera/actualiza la wiki de un repositorio en
formato GitHub Wiki (páginas Markdown sueltas). Idioma: español.

Devuelve SOLO archivos, cada uno precedido por una línea marcador EXACTA:
=== FILE: <nombre>.md ===

Páginas a generar:
- Home.md            visión general: qué es, para qué, cómo se usa.
- Architecture.md    componentes y cómo encajan; AL MENOS un diagrama \`\`\`mermaid.
- Flows.md           flujos principales (request/build/deploy/datos) con \`\`\`mermaid.
- _Sidebar.md        navegación con wiki-links: [[Home]] [[Architecture]] [[Flows]] [[Changelog]].
- Changelog-Entry.md SOLO 3-8 bullets resumiendo los cambios de este push.

Reglas: diagramas en bloques \`\`\`mermaid. No inventes archivos que no existan.
Si había wiki previa, mantén coherencia al actualizar.

== Árbol de archivos ==
$TREE

== Commits ($RANGE) ==
$LOG

== Diff stat ==
$DIFFSTAT

== Memoria headroom (contexto, puede ir vacía) ==
$MEM

== Home.md previa ==
$HOME_PREV
EOF
)"
[ -n "$OUT" ] || { echo "wiki: claude no devolvió contenido"; exit 0; }

# --- trocear salida en archivos (whitelist por nombre, sin rutas) ---
printf '%s\n' "$OUT" | awk -v dir="$WIKI_DIR" '
  /^=== FILE: .+ ===$/ {
    if (f) { close(f); f="" }
    name=$0; sub(/^=== FILE: /,"",name); sub(/ ===$/,"",name)
    if (name ~ /[\/]/ || name ~ /\.\./ || name !~ /\.md$/) next
    f=dir "/" name; printf "" > f; next
  }
  f { print >> f }
'

# --- changelog acumulativo (prepend con fecha) ---
if [ -f "$WIKI_DIR/Changelog-Entry.md" ]; then
  { echo "## $(date '+%Y-%m-%d %H:%M')"; cat "$WIKI_DIR/Changelog-Entry.md"; echo;
    [ -f "$WIKI_DIR/Changelog.md" ] && cat "$WIKI_DIR/Changelog.md"; } > "$WIKI_DIR/.cl.tmp"
  mv "$WIKI_DIR/.cl.tmp" "$WIKI_DIR/Changelog.md"
  rm -f "$WIKI_DIR/Changelog-Entry.md"
fi

echo "wiki: $WIKI_DIR → $(ls "$WIKI_DIR" 2>/dev/null | tr '\n' ' ')"

# --- publicar opcional al wiki de GitHub ---
if [ "${WIKI_PUBLISH:-0}" = "1" ]; then
  ORIGIN="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)"
  [ -n "$ORIGIN" ] || { echo "wiki: sin remoto origin, no publico"; exit 0; }
  WIKI_URL="${ORIGIN%.git}.wiki.git"
  TMP="$(mktemp -d)"
  if git clone -q "$WIKI_URL" "$TMP" 2>/dev/null; then
    cp "$WIKI_DIR"/*.md "$TMP"/ 2>/dev/null || true
    git -C "$TMP" add -A
    git -C "$TMP" -c user.name="wiki-bot" -c user.email="wiki@local" commit -q -m "Update wiki ($(date '+%F %T'))" 2>/dev/null || true
    if git -C "$TMP" push -q 2>/dev/null; then echo "wiki: publicada en $WIKI_URL"
    else echo "wiki: no se pudo publicar (¿wiki habilitada en GitHub?)"; fi
  else
    echo "wiki: no pude clonar $WIKI_URL — habilita la wiki y crea su primera página una vez."
  fi
  rm -rf "$TMP"
fi
