#!/usr/bin/env bash
# SessionStart hook: inject "what I know about THIS repo (and its group)" as context, so
# knowledge carries into a new session. Backend-agnostic; decay-ranked, drops superseded.
# Fail-safe — any problem just exits 0 with no output. Logs each injection for the dashboard.
set -uo pipefail
input=$(cat 2>/dev/null || true)
# resolve this script's real dir (follow symlinks) so co_store.py is importable next to it
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
HOOKDIR="$(cd -P "$(dirname "$src")" && pwd)"
command -v python3 >/dev/null 2>&1 || exit 0
command -v jq >/dev/null 2>&1 || exit 0

# repo of the session's cwd (fall back to current dir)
cwd=$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$cwd" ] || cwd="$PWD"
repo=$(git -C "$cwd" remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')

ctx=$(HOOKDIR="$HOOKDIR" REPO="$repo" python3 - <<'PY' 2>/dev/null
import datetime, json, os, sys
sys.path.insert(0, os.environ["HOOKDIR"])
import co_store
repo = os.environ.get("REPO", "")
# this repo's group (decay-ranked, superseded dropped) + a few shared "general" memories
this = co_store.recall(query=None, repos=co_store.group_for(repo), k=12) if repo else []
gen = co_store.recall(query=None, repos={"general"}, k=4)
seen, picked = set(), []
for m in this + gen:
    i = m.get("id")
    if i and i not in seen:
        seen.add(i)
        picked.append(m)
if not picked:
    sys.exit(0)
def md(m): return m.get("metadata") or {}
lines = ["# carryover — what you already know" + (f" about {repo}" if repo else "")]
for m in picked:
    c = " ".join((m.get("content") or "").split())
    if len(c) > 180:
        c = c[:180].rstrip() + "…"
    if c:
        tag = "" if md(m).get("repo", "general") == repo else " (general)"
        lines.append(f"- {c}{tag}")
out = "\n".join(lines)
try:  # instrument: record what context we carried, for the dashboard
    log = os.path.expanduser("~/.carryover/activity.jsonl")
    os.makedirs(os.path.dirname(log), exist_ok=True)
    with open(log, "a") as f:
        f.write(json.dumps({"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                            "event": "recall", "repo": repo or "general", "n": len(picked), "chars": len(out)}) + "\n")
except Exception:
    pass
co_store.touch([m.get("id") for m in picked if m.get("id")])  # auto-recall counts as use
print(out)
PY
)
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"SessionStart", additionalContext:$c}}'
