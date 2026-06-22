#!/usr/bin/env bash
# GLOBAL toggle for headroom routing in Claude Code, surgical and reversible.
# The proxy keeps running; this only changes whether Claude goes through it (ON) or direct (OFF).
# off: removes env.ANTHROPIC_BASE_URL from settings.json + adds a guard to headroom's
#      SessionStart hook (so it doesn't re-inject it) + creates the bypass flag for shells.
# on:  reverts (removes guard, restores env, deletes flag).
set -euo pipefail
SETTINGS="$HOME/.claude/settings.json"
FLAG="$HOME/.carryover/.bypass"
PORT="${HEADROOM_PORT:-8787}"
GUARD='[ -f "$HOME/.carryover/.bypass" ] || '

# colors + 💼 only on a real terminal (and unless NO_COLOR); empty otherwise → clean pipes/logs
if [ -t 1 ] && [ -z "${NO_COLOR:-}" ]; then
  R=$'\e[0m'; O=$'\e[1;38;5;173m'; G=$'\e[32m'; Y=$'\e[33m'; D=$'\e[2m'; TAG="${O}💼 carryover${R}"
else
  R=; O=; G=; Y=; D=; TAG="carryover"
fi

case "${1:-status}" in
  off)
    touch "$FLAG"
    python3 - "$SETTINGS" "$GUARD" <<'PY'
import json, os, sys
path, guard = sys.argv[1], sys.argv[2]
if not os.path.exists(path): sys.exit(0)
d = json.load(open(path))
d.get("env", {}).pop("ANTHROPIC_BASE_URL", None)
for e in d.get("hooks", {}).get("SessionStart", []):
    for h in e.get("hooks", []):
        c = h.get("command", "")
        if "init hook ensure" in c and not c.startswith(guard):
            h["command"] = guard + c
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY
    echo "$TAG ${Y}OFF${R}${D} — Claude goes direct to Anthropic in new sessions (proxy stays alive)${R}";;
  on)
    rm -f "$FLAG"
    python3 - "$SETTINGS" "$GUARD" "$PORT" <<'PY'
import json, os, sys
path, guard, port = sys.argv[1], sys.argv[2], sys.argv[3]
if not os.path.exists(path): sys.exit(0)
d = json.load(open(path))
d.setdefault("env", {})["ANTHROPIC_BASE_URL"] = f"http://127.0.0.1:{port}"
for e in d.get("hooks", {}).get("SessionStart", []):
    for h in e.get("hooks", []):
        if h.get("command", "").startswith(guard):
            h["command"] = h["command"][len(guard):]
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY
    echo "$TAG ${G}ON${R}${D} — Claude routes through headroom in new sessions${R}";;
  status)
    if [ -f "$FLAG" ]; then echo "$TAG ${Y}OFF${R}${D} (bypass active)${R}"; else echo "$TAG ${G}ON${R}"; fi
    grep -q '"ANTHROPIC_BASE_URL"' "$SETTINGS" 2>/dev/null && echo "  ${D}routing in settings.json ✓${R}" || echo "  ${D}no routing in settings.json${R}"
    "$HOME/.headroom/venv/bin/headroom" install status 2>/dev/null | grep -iE "Status|Healthy" | sed 's/^/  proxy: /' || true;;
  *) echo "usage: carryover-toggle.sh on|off|status"; exit 1;;
esac
