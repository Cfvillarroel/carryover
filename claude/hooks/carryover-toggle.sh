#!/usr/bin/env bash
# Toggle GLOBAL del routing de headroom para Claude Code, quirúrgico y reversible.
# El proxy sigue corriendo; solo cambia si Claude pasa por él (ON) o va directo (OFF).
# off: quita env.ANTHROPIC_BASE_URL de settings.json + pone un guard al hook SessionStart
#      de headroom (para que no la re-inyecte) + crea el flag de bypass para las shells.
# on:  revierte (quita guard, restaura env, borra flag).
set -euo pipefail
SETTINGS="$HOME/.claude/settings.json"
FLAG="$HOME/.headroom/.bypass"
PORT="${HEADROOM_PORT:-8787}"
GUARD='[ -f "$HOME/.headroom/.bypass" ] || '

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
    echo "carryover: OFF — Claude irá directo a Anthropic en sesiones nuevas (el proxy sigue vivo)";;
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
    echo "carryover: ON — Claude enruta por headroom en sesiones nuevas";;
  status)
    [ -f "$FLAG" ] && echo "global: OFF (bypass)" || echo "global: ON"
    grep -q '"ANTHROPIC_BASE_URL"' "$SETTINGS" 2>/dev/null && echo "settings.json: routing presente" || echo "settings.json: sin routing"
    "$HOME/.headroom/venv/bin/headroom" install status 2>/dev/null | grep -iE "Status|Healthy" | sed 's/^/proxy: /' || true;;
  *) echo "uso: carryover-toggle.sh on|off|status"; exit 1;;
esac
