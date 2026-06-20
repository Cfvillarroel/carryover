#!/usr/bin/env bash
# Saves a memory to the REAL store of the headroom proxy (~/.headroom/memory.db).
# Reliable fallback when the memory_save tool is not available.
# Usage:  mem-save.sh "text to remember" [importance 0-1]
#         echo "text" | mem-save.sh
set -euo pipefail
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
PY="$HOME/.headroom/venv/bin/python"
HR="$HOME/.headroom/venv/bin/headroom"
[ -x "$HR" ] || { echo "mem-save: headroom not installed"; exit 1; }
content="${1:-$(cat)}"
imp="${2:-0.7}"
[ -n "$content" ] || { echo "mem-save: empty content"; exit 1; }

tmp="$(mktemp).json"
HEADROOM_USER_ID="${HEADROOM_USER_ID:-$(whoami)}" "$PY" - "$tmp" "$content" "$imp" <<'PY'
import json, sys, uuid, os
from datetime import datetime, timezone
now = datetime.now(timezone.utc).isoformat()
json.dump([{
    "id": str(uuid.uuid4()),
    "content": sys.argv[2],
    "user_id": os.environ.get("HEADROOM_USER_ID", "user"),
    "created_at": now, "valid_from": now,
    "importance": float(sys.argv[3]),
    "metadata": {"source": "mem-save"},
}], open(sys.argv[1], "w"))
PY
"$HR" memory import "$tmp" --db-path "$DB" --force >/dev/null && echo "mem-save: saved to $DB"
rm -f "$tmp"
