#!/usr/bin/env bash
# Recall knowledge by keyword (fast, no embedder). Usage: recall.sh <query...>
# Works on either backend (headroom or the built-in store) via co-mem.
set -uo pipefail
q="$*"
[ -n "$q" ] || { echo "usage: recall <query>"; exit 1; }
# locate co-mem next to this script (follow symlink so it works via ~/.carryover/ or the plugin)
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
COMEM="$(cd -P "$(dirname "$src")" && pwd)/co-mem"
tmp="$(mktemp).json"
python3 "$COMEM" export "$tmp" 2>/dev/null || { echo "carryover: no memory store"; exit 0; }
Q="$q" python3 - "$tmp" <<'PY'
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
