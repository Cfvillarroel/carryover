#!/usr/bin/env bash
# Stop hook: if there were edits this session, ask to save to headroom memory.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
flag="/tmp/hr-changes-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0
rm -f "$flag"
jq -nc '{decision:"block", reason:"There were file edits this session. Before finishing, ask the user (text, brief) whether to save this change to carryover memory. If yes, EXTRACT the knowledge as JSON and save it via Bash: bash ~/.claude/hooks/mem-save.sh --json '\''<json>'\'' — where json = {\"content\":\"1-line summary\",\"facts\":[\"atomic, self-contained facts\"],\"entities\":[{\"entity\":\"X\",\"type\":\"project|tech|person|concept\"}],\"relationships\":[{\"source\":\"X\",\"relationship\":\"uses\",\"destination\":\"Y\"}],\"category\":\"area\",\"tags\":[\"...\"],\"importance\":0.7}. Each fact becomes a searchable memory; include entities and relationships for the graph. If structuring is not worth it, use: bash ~/.claude/hooks/mem-save.sh \"text\". If you already asked this turn, simply finish."}'
