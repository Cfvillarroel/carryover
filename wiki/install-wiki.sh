#!/usr/bin/env bash
# Enables the "wiki" capability in a project repo: copies the generator and the pre-push hook.
# Usage:  bash install-wiki.sh [/path/to/repo]   (default: current repo)
set -euo pipefail
# resolve this script's REAL directory, following symlinks, so gen-wiki.sh / pre-push are
# found even when invoked via ~/.headroom/install-wiki.sh (the wiki-enable alias target).
src="${BASH_SOURCE[0]:-$0}"
while [ -L "$src" ]; do
  dir="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"
  [ "${src#/}" = "$src" ] && src="$dir/$src"
done
SRC="$(cd -P "$(dirname "$src")" && pwd)"
TARGET="${1:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
[ -n "$TARGET" ] && git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 \
  || { echo "Not a git repo: '${TARGET:-<empty>}'"; exit 1; }

mkdir -p "$TARGET/wiki"
cp "$SRC/gen-wiki.sh" "$TARGET/wiki/gen-wiki.sh"; chmod +x "$TARGET/wiki/gen-wiki.sh"
HOOK_DIR="$(git -C "$TARGET" rev-parse --absolute-git-dir)/hooks"
mkdir -p "$HOOK_DIR"
cp "$SRC/pre-push" "$HOOK_DIR/pre-push"; chmod +x "$HOOK_DIR/pre-push"
# keep the generated wiki strictly local — never committed with the code repo.
# (to version it instead, remove this line; to publish it, use WIKI_PUBLISH=1 → GitHub wiki)
grep -qxF "wiki/" "$TARGET/.gitignore" 2>/dev/null || echo "wiki/" >> "$TARGET/.gitignore"

# register this repo so the carryover dashboard (co-dash) can find its wiki
reg="$HOME/.headroom/wikis.list"; mkdir -p "$HOME/.headroom"
abs="$(cd "$TARGET" && pwd)"
grep -qxF "$abs" "$reg" 2>/dev/null || echo "$abs" >> "$reg"

echo "Wiki enabled in $TARGET"
if [ "${WIKI_NO_GEN:-0}" = "1" ]; then
  echo "  → setup only (run wiki-gen to generate)"
else
  echo "  → generating the FIRST wiki now, in the background (~1 min) → $TARGET/wiki/"
  nohup bash "$TARGET/wiki/gen-wiki.sh" >>"$TARGET/wiki/.gen.log" 2>&1 &
fi
echo "  → updates on push to master/main, or run 'wiki-gen' anytime · publish with WIKI_PUBLISH=1"
