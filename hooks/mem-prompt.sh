#!/usr/bin/env bash
# Stop hook (plugin): if files changed this session, ask whether to save to headroom memory.
# Arg $1 = plugin root (CLAUDE_PLUGIN_ROOT), used to locate mem-save.sh.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
flag="/tmp/hr-changes-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0
rm -f "$flag"
root="${1:-${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}}"
jq -nc --arg s "$root/hooks/mem-save.sh" '{decision:"block", reason:("Files were edited this session. Before finishing, briefly ask the user whether to save this change to headroom memory. If yes: use the memory_save tool if you have it; otherwise run via Bash: bash \"" + $s + "\" \"<change summary>\". If you already asked this turn, just finish.")}'
