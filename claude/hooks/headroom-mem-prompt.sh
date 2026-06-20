#!/usr/bin/env bash
# Stop hook: if there were edits this session, ask to save to headroom memory.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
flag="/tmp/hr-changes-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0
rm -f "$flag"
jq -nc '{decision:"block", reason:"There were file edits this session. Before finishing, ask the user (text, brief) whether they want to save this change to headroom memory. If they say yes: if you have the memory_save tool, use it; if not, run it via Bash: bash ~/.claude/hooks/mem-save.sh \"<summary of the change>\". If you already asked this turn, simply finish."}'
