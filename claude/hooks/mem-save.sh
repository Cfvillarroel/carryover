#!/usr/bin/env bash
# Guarda una memoria en el store REAL del proxy de headroom (~/.headroom/memory.db).
# Fallback fiable cuando la tool memory_save no está disponible.
# Uso:  mem-save.sh "texto a recordar" [importancia 0-1]
#       echo "texto" | mem-save.sh
set -euo pipefail
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
PY="$HOME/.headroom/venv/bin/python"
HR="$HOME/.headroom/venv/bin/headroom"
[ -x "$HR" ] || { echo "mem-save: headroom no instalado"; exit 1; }
content="${1:-$(cat)}"
imp="${2:-0.7}"
[ -n "$content" ] || { echo "mem-save: contenido vacío"; exit 1; }

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
"$HR" memory import "$tmp" --db-path "$DB" --force >/dev/null && echo "mem-save: guardado en $DB"
rm -f "$tmp"
