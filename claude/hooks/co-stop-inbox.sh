#!/usr/bin/env bash
# Stop hook: when the agent finishes a turn, deliver any QUEUED cross-workspace messages so it
# processes them right then — without interrupting mid-task (this fires after the turn ends).
# Anti-loop: never re-block when already continuing from a stop hook (stop_hook_active), so two
# connected workspaces can't ping-pong forever — at most one extra turn per real turn.
input=$(cat)
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0
cwd=$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$cwd" ] || cwd="$PWD"
# resolve this script's real dir (follow symlinks) so co_store.py is importable next to it
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
HOOKDIR="$(cd -P "$(dirname "$src")" && pwd)"
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0
reason=$(HOOKDIR="$HOOKDIR" WS="${CONDUCTOR_WORKSPACE_NAME:-$(basename "$cwd")}" "$PY" - <<'PY' 2>/dev/null
import os, sys
sys.path.insert(0, os.environ["HOOKDIR"])
import co_store
ws = os.environ.get("WS", "")
msgs = co_store.inbox(who=ws, consume=True) if ws else []
if not msgs:
    sys.exit(0)
lines = ["📬 New messages from other Conductor workspaces arrived (delivered now that your turn finished):"]
for m in msgs:
    md = m.get("metadata") or {}
    b = " ".join((m.get("content") or "").split())
    if len(b) > 400:
        b = b[:400].rstrip() + "…"
    lines.append(f"- from {md.get('from','?')}: {b}")
lines.append("Surface these to the user and act on them if they need action (you may reply with co-send/co-say). "
             "Then finish normally — do not keep looping.")
co_store.log_activity("inbox", n=len(msgs))
print("\n".join(lines))
PY
)
[ -n "$reason" ] || exit 0
jq -nc --arg r "$reason" '{decision:"block", reason:$r}'
