#!/usr/bin/env bash
# Stop hook (plugin): if files changed this session, ask whether to save structured knowledge.
# Arg $1 = plugin root (CLAUDE_PLUGIN_ROOT), used to locate mem-save.sh.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
flag="/tmp/hr-changes-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0
rm -f "$flag"
root="${1:-${CLAUDE_PLUGIN_ROOT:-$HOME/.claude}}"
jq -nc --arg s "$root/hooks/mem-save.sh" '{decision:"block", reason:("Files were edited this session. Before finishing, ask the user (brief) whether to save this change to carryover memory. If yes, EXTRACT the knowledge as JSON and save it via Bash: bash \"" + $s + "\" --json '\''<json>'\'' — where json = {\"content\":\"1-line summary\",\"facts\":[\"atomic, self-contained facts\"],\"entities\":[{\"entity\":\"X\",\"type\":\"project|tech|person|concept\"}],\"relationships\":[{\"source\":\"X\",\"relationship\":\"uses\",\"destination\":\"Y\"}],\"category\":\"area\",\"tags\":[\"...\"],\"importance\":0.7}. Each fact becomes a searchable memory; include entities and relationships for the graph. If structuring is not worth it: bash \"" + $s + "\" \"text\". If you already asked this turn, just finish.")}'
