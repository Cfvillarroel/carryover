#!/usr/bin/env bash
# Stop hook: si hubo ediciones esta sesión, pide guardar en memoria de headroom.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
flag="/tmp/hr-changes-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0
rm -f "$flag"
jq -nc '{decision:"block", reason:"Hubo ediciones de archivos esta sesión. Antes de terminar, pregunta al usuario (texto, breve) si quiere guardar este cambio en la memoria de headroom. Si dice que sí: si tienes la tool memory_save úsala; si no, ejecútalo por Bash: bash ~/.claude/hooks/mem-save.sh \"<resumen del cambio>\". Si ya lo preguntaste en este turno, simplemente termina."}'
