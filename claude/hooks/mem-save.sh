#!/usr/bin/env bash
# Save KNOWLEDGE to headroom's local store (SQLite + vectors + graph), structured for fast query.
#
#   Plain:       mem-save "text to remember" [importance 0-1]
#                echo "text" | mem-save
#   Structured:  mem-save --json '<json>'      (or:  echo '<json>' | mem-save --json )
#     json: {"content":"…","facts":["…"],"entities":[{"entity":"X","type":"project"}],
#            "relationships":[{"source":"X","relationship":"uses","destination":"Y"}],
#            "category":"…","tags":["…"],"importance":0.7}
#
# The actual save runs in the BACKGROUND (loading the embedding model takes a few seconds),
# so this returns immediately. Logs to ~/.carryover/mem-save.log.
set -euo pipefail
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"  # headroom venv, else system python3 (built-in store)
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
UID_="${HEADROOM_USER_ID:-$(whoami)}"
[ -n "$PY" ] || { echo "mem-save: python3 not found"; exit 1; }

tmp="$(mktemp).json"
if [ "${1:-}" = "--json" ]; then
  if [ -n "${2:-}" ]; then printf '%s' "$2" > "$tmp"; else cat > "$tmp"; fi
else
  content="${1:-$(cat)}"; imp="${2:-0.7}"
  [ -n "$content" ] || { echo "mem-save: empty content"; exit 1; }
  CONTENT="$content" IMP="$imp" "$PY" -c \
    'import json,os; print(json.dumps({"content":os.environ["CONTENT"],"facts":[os.environ["CONTENT"]],"importance":float(os.environ["IMP"])}))' \
    > "$tmp"
fi

# locate mem-save.py next to this script (follow symlink so it works via ~/.claude/hooks/)
src="${BASH_SOURCE[0]:-$0}"
while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
WORKER="$(cd -P "$(dirname "$src")" && pwd)/mem-save.py"

# detect the repo this knowledge came from (for indexing in the dashboard); "general" if none
REPO="$(git remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')"
[ -n "$REPO" ] || REPO="general"

mkdir -p "$HOME/.carryover"
nohup "$PY" "$WORKER" "$DB" "$UID_" "$tmp" "$REPO" >>"$HOME/.carryover/mem-save.log" 2>&1 &
echo "💾 mem-save: queued to knowledge store (repo: $REPO, background)"
