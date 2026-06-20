#!/usr/bin/env bash
# Enables the "wiki" capability in a project repo: copies the generator and the pre-push hook.
# Usage:  bash install-wiki.sh [/path/to/repo]   (default: current repo)
set -euo pipefail
SRC="$(cd "$(dirname "$0")" && pwd)"
TARGET="${1:-$(git rev-parse --show-toplevel 2>/dev/null || true)}"
[ -n "$TARGET" ] && git -C "$TARGET" rev-parse --git-dir >/dev/null 2>&1 \
  || { echo "Not a git repo: '${TARGET:-<empty>}'"; exit 1; }

mkdir -p "$TARGET/wiki"
cp "$SRC/gen-wiki.sh" "$TARGET/wiki/gen-wiki.sh"; chmod +x "$TARGET/wiki/gen-wiki.sh"
HOOK="$(git -C "$TARGET" rev-parse --git-path hooks)/pre-push"
cp "$SRC/pre-push" "$HOOK"; chmod +x "$HOOK"
grep -qxF "wiki/.gen.log" "$TARGET/.gitignore" 2>/dev/null || echo "wiki/.gen.log" >> "$TARGET/.gitignore"

# register this repo so the carryover dashboard (co-dash) can find its wiki
reg="$HOME/.headroom/wikis.list"; mkdir -p "$HOME/.headroom"
abs="$(cd "$TARGET" && pwd)"
grep -qxF "$abs" "$reg" 2>/dev/null || echo "$abs" >> "$reg"

echo "Wiki enabled in $TARGET"
echo "  → regenerates when pushing to master/main, in $TARGET/wiki/ (GitHub Wiki format)"
echo "  → publish to the GitHub wiki: set WIKI_PUBLISH=1 before the push, or run wiki/gen-wiki.sh manually"
