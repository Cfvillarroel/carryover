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
tm = co_store.teams()
tpath = os.environ.get("TRANSCRIPT", "")
text = ""
if (prs or tm) and tpath:
    try:
        with open(tpath) as f:
            rows = f.readlines()[-200:]              # window to find the last assistant turn (NOT `lines` — that's the output accumulator)
        for ln in rows:                              # only THIS turn's assistant text — not prior turns,
            try:                                     # user messages, or our own injected nudge (no re-seeding)
                o = json.loads(ln)
            except Exception:
                continue
            msg = o.get("message") or {}
            if (msg.get("role") or o.get("type")) != "assistant":
                continue
            parts = [blk.get("text") or "" for blk in (msg.get("content") or [])
                     if isinstance(blk, dict) and blk.get("type") == "text"]
            if parts:
                text = " ".join(parts)               # keep overwriting → ends as the LAST assistant message
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

# (3) team dispatch nudge: did this turn mention a TEAM name AND a delegation cue?
# (cue required so a passing mention — e.g. explaining teams — doesn't nudge; EN + ES stems)
DELEG = re.compile(r'(assign|dispatch|delegat|hand[ -]?(off|over)|fan[ -]?out|split|divide|distribut|'
                   r'kick[ -]?off|per[ -]?role|asign|repart|deleg|despach|distribu|encarg|arranqu|'
                   r'que cada|por rol)', re.I)
thit = ([t for t in tm if re.search(r'(?<![\w-])' + re.escape(t) + r'(?![\w-])', text, re.I)]
        if text and DELEG.search(text) else [])
if thit:
    if lines:
        lines.append("")
    for t in sorted(thit):
        roster = ", ".join(f"{w}={r}" for w, r in (tm.get(t) or {}).items())
        lines.append(f"👥 This turn referenced team '{t}' ({roster}). If you're delegating, decompose the "
                     f"goal and dispatch per role: co-team assign {t} @<role> \"<task>\" (or co-team send "
                     f"for a passive note). assign notifies each member to execute on arrival. "
                     f"If it isn't a dispatch, ignore this.")

if not lines:
    sys.exit(0)
print("\n".join(lines))
PY
)
[ -n "$reason" ] || exit 0
jq -nc --arg r "$reason" '{decision:"block", reason:$r}'
