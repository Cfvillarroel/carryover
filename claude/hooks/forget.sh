#!/usr/bin/env bash
# Forget (delete) memories matching a keyword query, with confirmation. Usage: forget.sh <query...>
# Works on either backend (headroom or the built-in store) via co-mem.
set -uo pipefail
q="$*"
[ -n "$q" ] || { echo "usage: hr-forget <query>"; exit 1; }
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
COMEM="$(cd -P "$(dirname "$src")" && pwd)/co-mem"
tmp="$(mktemp).json"
python3 "$COMEM" export "$tmp" 2>/dev/null || { echo "carryover: no memory store"; exit 0; }
# matches printed to the terminal (stderr); their ids captured (stdout)
ids="$(Q="$q" python3 - "$tmp" <<'PY'
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
    # shellcheck disable=SC2086  — ids are UUIDs (no spaces); pass them all to one delete
    python3 "$COMEM" delete $ids >/dev/null 2>&1
    echo "hr-forget: deleted $n";;
  *) echo "cancelled";;
esac
