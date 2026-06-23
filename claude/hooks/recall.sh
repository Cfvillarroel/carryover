#!/usr/bin/env bash
# Recall knowledge by keyword (fast, no embedder). Usage: recall.sh [--all] <query...>
# Scope: by default only THIS repo's memories; --all (-a) searches every repo.
# Works on either backend (headroom or the built-in store) via co-mem.
set -uo pipefail
all=0
case "${1:-}" in --all|-a) all=1; shift;; esac
q="$*"
[ -n "$q" ] || { echo "usage: recall [--all] <query>"; exit 1; }
# locate co-mem next to this script (follow symlink so it works via ~/.carryover/ or the plugin)
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
COMEM="$(cd -P "$(dirname "$src")" && pwd)/co-mem"
# repo of the current dir; recall is scoped to it unless --all (or not in a git repo)
repo=$(git remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')
[ "$all" = "1" ] && repo=""
tmp="$(mktemp).json"; ids="$(mktemp)"
python3 "$COMEM" export "$tmp" 2>/dev/null || { echo "carryover: no memory store"; rm -f "$tmp" "$ids"; exit 0; }
Q="$q" REPO="$repo" IDS="$ids" python3 - "$tmp" <<'PY'
import json, os, sys
q = os.environ["Q"].lower()
repo = os.environ.get("REPO", "")
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
if repo:  # strict: only this repo's memories (use --all to search every repo)
    hits = [m for m in hits if md(m).get("repo") == repo]
hits.sort(key=lambda m: m.get("importance", 0), reverse=True)
scope = f" in {repo}" if repo else ""
if not hits:
    print(f"(nothing found for: {os.environ['Q']}{scope})" + ("  — try: recall --all" if repo else ""))
    sys.exit(0)
print(f"{len(hits)} match(es){scope}:\n")
shown = hits[:10]
for m in shown:
    print(f"  [{md(m).get('repo','general')}] {m.get('content','').strip()}")
    for f in (md(m).get("facts") or []):
        if f != m.get("content"):
            print(f"      • {f}")
with open(os.environ["IDS"], "w") as fh:  # ids of shown matches → bump their access_count
    fh.write("\n".join(str(m.get("id")) for m in shown if m.get("id")))
PY
# bump access_count for what we surfaced (fail-safe)
read_ids="$(tr '\n' ' ' < "$ids" 2>/dev/null)"
[ -n "${read_ids// }" ] && python3 "$COMEM" touch $read_ids >/dev/null 2>&1 || true
rm -f "$tmp" "$ids"
