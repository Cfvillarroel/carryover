#!/usr/bin/env bash
# UserPromptSubmit hook: deliver pending cross-workspace messages as context, WITHOUT interrupting.
# Pull-only — on each of your turns it surfaces notes addressed to this workspace (left via co-send),
# then marks them delivered. Lightweight on purpose: only the inbox, never the full recall, and it
# injects nothing when there are no messages.
input=$(cat)
cwd=$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$cwd" ] || cwd="$PWD"
# resolve this script'\''s real dir (follow symlinks) so co_store.py is importable next to it
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
HOOKDIR="$(cd -P "$(dirname "$src")" && pwd)"
# headroom venv python if present (writes via headroom); else system python3 (built-in store)
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0
ctx=$(HOOKDIR="$HOOKDIR" WS="${CONDUCTOR_WORKSPACE_NAME:-$(basename "$cwd")}" "$PY" - <<'PY' 2>/dev/null
import os, sys
sys.path.insert(0, os.environ["HOOKDIR"])
import co_store
ws = os.environ.get("WS", "")
msgs = co_store.inbox(who=ws, consume=True) if ws else []
if not msgs:
    sys.exit(0)
lines = ["## 📬 messages for this workspace (left by other workspaces)"]
for m in msgs:
    md = m.get("metadata") or {}
    b = " ".join((m.get("content") or "").split())
    if len(b) > 240:
        b = b[:240].rstrip() + "…"
    lines.append(f"- **from {md.get('from','?')}:** {b}")
co_store.log_activity("inbox", n=len(msgs))
print("\n".join(lines))
PY
)
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"UserPromptSubmit", additionalContext:$c}}'
