#!/usr/bin/env bash
# ponytail: custom statusline (don't edit the plugin's, it gets overwritten on update).
# Shows 🐴 if ponytail is active and 🗜️ if the headroom proxy responds.
# To change the emojis, edit these two lines:
PONY_EMOJI="🐴"
HR_EMOJI="🧠"

cat >/dev/null 2>&1   # drains the session JSON that Claude passes via stdin

out=""

# --- ponytail: read its status flag ---
flag="$HOME/.claude/.ponytail-active"
if [ -f "$flag" ]; then
    mode=$(head -n1 "$flag" | tr -d '[:space:]')
    if [ -z "$mode" ] || [ "$mode" = "full" ]; then
        out="$PONY_EMOJI"
    else
        out="$PONY_EMOJI $(printf '%s' "$mode" | tr '[:lower:]' '[:upper:]')"
    fi
fi

# --- headroom: is the proxy listening on 8787? (pure TCP, no spawning processes) ---
if (exec 3<>/dev/tcp/127.0.0.1/8787) 2>/dev/null; then
    exec 3>&- 3<&-
    out="${out:+$out }$HR_EMOJI"
fi

[ -n "$out" ] && printf '%s' "$out"
