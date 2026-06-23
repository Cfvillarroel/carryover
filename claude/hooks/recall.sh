#!/usr/bin/env bash
# Recall knowledge. Semantic when headroom is present (uses its embedder); keyword otherwise.
# Scoped to the current repo's group by default; --all searches every repo.
# Usage: recall.sh [--all] <query...>
set -uo pipefail
all=0; case "${1:-}" in --all|-a) all=1; shift;; esac
q="$*"
[ -n "$q" ] || { echo "usage: recall [--all] <query>"; exit 1; }
# resolve this script's real dir (follow symlinks) so co_store.py is importable next to it
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
HOOKDIR="$(cd -P "$(dirname "$src")" && pwd)"
# headroom's venv python enables SEMANTIC recall (its embedder); else system python3 → keyword
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3 || true)"
[ -n "$PY" ] || { echo "carryover: python3 not found"; exit 1; }
# scope to the current repo (and its group); --all clears it
repo=$(git remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')
[ "$all" = "1" ] && repo=""
HOOKDIR="$HOOKDIR" Q="$q" REPO="$repo" "$PY" - <<'PY'
import os, sys
sys.path.insert(0, os.environ["HOOKDIR"])
import co_store
q = os.environ["Q"]
repo = os.environ.get("REPO", "")
repos = co_store.group_for(repo) if repo else None  # repo's group, or None = every repo
res = co_store.recall(query=q, repos=repos, k=10)
if not res:
    print(f"(nothing found for: {q}" + (f" in {repo}" if repo else "") + ")"
          + ("  — try: recall --all" if repo else ""))
    sys.exit(0)
print(f"{len(res)} match(es)" + (f" in {repo}" if repo else "") + ":\n")
for m in res:
    md = m.get("metadata") or {}
    print(f"  [{md.get('repo','general')}] {(m.get('content') or '').strip()}")
    for f in (md.get("facts") or []):
        if f != m.get("content"):
            print(f"      • {f}")
co_store.touch([m.get("id") for m in res if m.get("id")])  # surfaced = used
PY
