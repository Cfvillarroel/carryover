#!/usr/bin/env bash
# Stop hook: if there were edits this session, ask once to save to headroom memory + wiki.
input=$(cat)
sid=$(printf '%s' "$input" | jq -r '.session_id // empty')
# ponytail: already continuing because of a stop hook? never re-block (avoids the extra-turn loop)
[ "$(printf '%s' "$input" | jq -r '.stop_hook_active // false')" = "true" ] && exit 0
flag="/tmp/hr-changes-${sid}.flag"
asked="/tmp/hr-asked-${sid}.flag"
[ -n "$sid" ] && [ -f "$flag" ] || exit 0   # no edits this session → nothing to ask
[ -f "$asked" ] && exit 0                    # ponytail: ask once per session; never re-nag
touch "$asked"
rm -f "$flag"
jq -nc '{decision:"block", reason:"Files were edited this session. In your FINAL message (Conductor shows only your last message, so make it self-contained): give a 1-2 line recap of what you did, THEN ask the user — briefly, in one message — (a) whether to save this change to carryover memory, and (b) whether to update this repo'\''s wiki. To save memory, EXTRACT the knowledge as JSON and run: bash ~/.claude/hooks/mem-save.sh --json '\''<json>'\'' — where json = {\"content\":\"1-line summary\",\"facts\":[\"atomic, self-contained facts\"],\"entities\":[{\"entity\":\"X\",\"type\":\"project|tech|person|concept\"}],\"relationships\":[{\"source\":\"X\",\"relationship\":\"uses\",\"destination\":\"Y\"}],\"category\":\"area\",\"tags\":[\"...\"],\"importance\":0.7}. Each fact becomes a searchable memory; include entities and relationships for the graph. If structuring is not worth it, use: bash ~/.claude/hooks/mem-save.sh \"text\". To update the wiki (optional, ~1 min, can run in the background): bash ~/.headroom/wiki-gen.sh. Ask only once; if the user already answered, simply finish."}'
