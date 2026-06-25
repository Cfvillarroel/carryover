#!/usr/bin/env bash
# Stop hook: when the agent finishes a turn,
#   (1) deliver any QUEUED cross-workspace messages so it processes them right then — without
#       interrupting mid-task (this fires after the turn ends), and
#   (2) if the turn referenced a CONNECTED workspace, nudge a task handoff.
# Anti-loop: never re-block when already continuing from a stop hook (stop_hook_active), so two
# connected workspaces can't ping-pong forever — at most one extra turn per real turn.
input=$(cat)
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0
read_field() { printf '%s' "$input" | python3 -c "import json,sys
try: print(json.load(sys.stdin).get('$1',''))
except Exception: print('')" 2>/dev/null; }
cwd=$(read_field cwd); [ -n "$cwd" ] || cwd="$PWD"
tpath=$(read_field transcript_path)
# resolve this script's real dir (follow symlinks) so co_store.py is importable next to it
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
HOOKDIR="$(cd -P "$(dirname "$src")" && pwd)"
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || exit 0
reason=$(HOOKDIR="$HOOKDIR" WS="${CONDUCTOR_WORKSPACE_NAME:-$(basename "$cwd")}" TRANSCRIPT="$tpath" "$PY" - <<'PY' 2>/dev/null
import os, re, sys, json
sys.path.insert(0, os.environ["HOOKDIR"])
import co_store
ws = os.environ.get("WS", "")
lines = []

# (1) deliver queued incoming messages
msgs = co_store.inbox(who=ws, consume=True) if ws else []
if msgs:
    lines.append("📬 New messages from other Conductor workspaces arrived (delivered now that your turn finished):")
    for m in msgs:
        md = m.get("metadata") or {}
        b = " ".join((m.get("content") or "").split())
        if len(b) > 400:
            b = b[:400].rstrip() + "…"
        tag = " ⚡HANDOVER" if md.get("handover") else ""
        lines.append(f"- from {md.get('from','?')}:{tag} {b}")
    if any((m.get("metadata") or {}).get("handover") for m in msgs):
        lines.append("A ⚡HANDOVER is a task to execute NOW (not just surface to the user). Do it this turn.")
    else:
        lines.append("Surface these to the user and act on them if they need action (you may reply with co-send/co-say).")
    co_store.log_activity("inbox", n=len(msgs))

# (2) handoff nudge: did this turn mention a CONNECTED workspace?
prs = co_store.peers(ws) if ws else set()
tpath = os.environ.get("TRANSCRIPT", "")
text = ""
if prs and tpath:
    try:
        with open(tpath) as f:
            tail = f.readlines()[-40:]               # roughly the last turn
        for ln in tail:
            try:
                o = json.loads(ln)
            except Exception:
                continue
            msg = o.get("message") or {}
            for blk in (msg.get("content") or []):
                if isinstance(blk, dict) and blk.get("type") == "text":
                    text += " " + (blk.get("text") or "")
    except Exception:
        text = ""
hit = [p for p in sorted(prs)
       if text and re.search(r'(?<![\w-])' + re.escape(p) + r'(?![\w-])', text, re.I)]
if hit:
    if lines:
        lines.append("")
    lines.append("↪️ This turn referenced connected workspace(s): " + ", ".join(hit) + ". "
                 "If something here is their task, hand it off: write a short summary (what's done, "
                 "what's left, key files/decisions) and send it with co-send <ws> \"<summary>\". "
                 "If it isn't a handoff, just ignore this and finish.")

if not lines:
    sys.exit(0)
print("\n".join(lines))
PY
)
[ -n "$reason" ] || exit 0
jq -nc --arg r "$reason" '{decision:"block", reason:$r}'
