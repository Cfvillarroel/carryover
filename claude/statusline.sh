#!/usr/bin/env bash
# ponytail: statusline propio (no editar el del plugin, se sobrescribe al actualizar).
# Muestra 🐴 si ponytail está activo y 🗜️ si el proxy de headroom responde.
# Para cambiar los emojis, edita estas dos líneas:
PONY_EMOJI="🐴"
HR_EMOJI="🧠"

cat >/dev/null 2>&1   # drena el JSON de sesión que Claude pasa por stdin

out=""

# --- ponytail: lee su flag de estado ---
flag="$HOME/.claude/.ponytail-active"
if [ -f "$flag" ]; then
    mode=$(head -n1 "$flag" | tr -d '[:space:]')
    if [ -z "$mode" ] || [ "$mode" = "full" ]; then
        out="$PONY_EMOJI"
    else
        out="$PONY_EMOJI $(printf '%s' "$mode" | tr '[:lower:]' '[:upper:]')"
    fi
fi

# --- headroom: ¿proxy escuchando en 8787? (TCP puro, sin spawnear procesos) ---
if (exec 3<>/dev/tcp/127.0.0.1/8787) 2>/dev/null; then
    exec 3>&- 3<&-
    out="${out:+$out }$HR_EMOJI"
fi

[ -n "$out" ] && printf '%s' "$out"
