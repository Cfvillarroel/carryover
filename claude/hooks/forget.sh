#!/usr/bin/env bash
# Forget (delete) memories matching a keyword query, with confirmation. Usage: forget.sh <query...>
set -uo pipefail
HR="$HOME/.headroom/venv/bin/headroom"
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
PY="$HOME/.headroom/venv/bin/python"
q="$*"
[ -n "$q" ] || { echo "usage: hr-forget <query>"; exit 1; }
[ -x "$HR" ] || { echo "carryover: headroom not installed"; exit 1; }
tmp="$(mktemp).json"
"$HR" memory export --output "$tmp" --db-path "$DB" >/dev/null 2>&1 || { echo "carryover: no memory store"; exit 0; }
# matches printed to the terminal (stderr); their ids captured (stdout)
ids="$(Q="$q" "$PY" - "$tmp" <<'PY'
import json, os, sys
q = os.environ["Q"].lower()
try: mems = json.load(open(sys.argv[1]))
except Exception: sys.exit(0)
def md(m): return m.get("metadata") or {}
def hay(m):
    ents = [e.get("entity", "") if isinstance(e, dict) else e for e in (md(m).get("entities") or m.get("entity_refs") or [])]
    return " ".join(str(p) for p in [m.get("content", "")] + (md(m).get("facts") or []) + ents + (md(m).get("tags") or [])).lower()
hits = [m for m in mems if all(w in hay(m) for w in q.split())]
hits.sort(key=lambda m: m.get("importance", 0), reverse=True)
for m in hits[:25]:
    sys.stderr.write(f"  {m.get('id','')[:8]}  [{md(m).get('repo','general')}] {m.get('content','').strip()[:88]}\n")
    print(m.get("id", ""))
PY
)"
rm -f "$tmp"
n=$(printf '%s\n' "$ids" | grep -c .)
[ "$n" -gt 0 ] || { echo "(nothing found for: $q)"; exit 0; }
printf "Delete the %s shown memory(ies)? [y/N] " "$n"
read -r ans
case "$ans" in
  y|Y|yes|s|S|si)
    printf '%s\n' "$ids" | while read -r id; do [ -n "$id" ] && "$HR" memory delete "$id" --db-path "$DB" --force >/dev/null 2>&1; done
    echo "hr-forget: deleted $n";;
  *) echo "cancelled";;
esac
