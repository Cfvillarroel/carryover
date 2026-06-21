#!/usr/bin/env bash
# Recall knowledge by keyword (fast, no embedder). Usage: recall.sh <query...>
set -uo pipefail
HR="$HOME/.headroom/venv/bin/headroom"
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
PY="$HOME/.headroom/venv/bin/python"
q="$*"
[ -n "$q" ] || { echo "usage: recall <query>"; exit 1; }
[ -x "$HR" ] || { echo "carryover: headroom not installed"; exit 1; }
tmp="$(mktemp).json"
"$HR" memory export --output "$tmp" --db-path "$DB" >/dev/null 2>&1 || { echo "carryover: no memory store"; exit 0; }
Q="$q" "$PY" - "$tmp" <<'PY'
import json, os, sys
q = os.environ["Q"].lower()
try:
    mems = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
def md(m): return m.get("metadata") or {}
def hay(m):
    ents = [e.get("entity", "") if isinstance(e, dict) else e for e in (md(m).get("entities") or m.get("entity_refs") or [])]
    parts = [m.get("content", "")] + (md(m).get("facts") or []) + ents + (md(m).get("tags") or [])
    return " ".join(str(p) for p in parts).lower()
words = q.split()
hits = [m for m in mems if all(w in hay(m) for w in words)]
hits.sort(key=lambda m: m.get("importance", 0), reverse=True)
if not hits:
    print(f"(nothing found for: {os.environ['Q']})"); sys.exit(0)
print(f"{len(hits)} match(es):\n")
for m in hits[:10]:
    print(f"  [{md(m).get('repo','general')}] {m.get('content','').strip()}")
    for f in (md(m).get("facts") or []):
        if f != m.get("content"):
            print(f"      • {f}")
PY
rm -f "$tmp"
