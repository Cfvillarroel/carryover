#!/usr/bin/env bash
# SessionStart hook: inject "what I know about THIS repo" as context, so knowledge
# carries over into a new session automatically. Fast (no embedder): reads the export
# and filters by repo. Fail-safe — any problem just exits 0 with no output.
set -uo pipefail
input=$(cat 2>/dev/null || true)
HR="$HOME/.headroom/venv/bin/headroom"
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
PY="$HOME/.headroom/venv/bin/python"
[ -x "$HR" ] && [ -x "$PY" ] || exit 0

# repo of the session's cwd (fall back to current dir)
cwd=$(printf '%s' "$input" | "$PY" -c 'import json,sys;
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$cwd" ] || cwd="$PWD"
repo=$(git -C "$cwd" remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')

tmp="$(mktemp).json"
"$HR" memory export --output "$tmp" --db-path "$DB" >/dev/null 2>&1 || { rm -f "$tmp"; exit 0; }

ctx=$(REPO="$repo" "$PY" - "$tmp" <<'PY' 2>/dev/null
import json, os, sys
repo = os.environ.get("REPO", "")
try:
    mems = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
def md(m): return m.get("metadata") or {}
# this repo's memories first, then a few general ones; by importance, capped
this_repo = [m for m in mems if repo and md(m).get("repo") == repo]
general = [m for m in mems if md(m).get("repo", "general") == "general"]
this_repo.sort(key=lambda m: m.get("importance", 0), reverse=True)
general.sort(key=lambda m: m.get("importance", 0), reverse=True)
picked = this_repo[:12] + general[:4]
if not picked:
    sys.exit(0)
lines = ["# carryover — what you already know" + (f" about {repo}" if repo else "")]
for m in picked:
    c = (m.get("content") or "").strip()
    if c:
        tag = "" if md(m).get("repo", "general") == repo else " (general)"
        lines.append(f"- {c}{tag}")
print("\n".join(lines))
PY
)
rm -f "$tmp"
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"SessionStart", additionalContext:$c}}'
