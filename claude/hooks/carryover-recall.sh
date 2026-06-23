#!/usr/bin/env bash
# SessionStart hook: inject "what I know about THIS repo" as context, so knowledge carries
# over into a new session. Backend-agnostic (co-mem → headroom or built-in). Fail-safe —
# any problem just exits 0 with no output. Logs each injection for the dashboard's context metrics.
set -uo pipefail
input=$(cat 2>/dev/null || true)
# locate co-mem next to this script (follow symlink so it works via ~/.carryover/ or the plugin)
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d="$(cd -P "$(dirname "$src")" && pwd)"; src="$(readlink "$src")"; [ "${src#/}" = "$src" ] && src="$d/$src"; done
COMEM="$(cd -P "$(dirname "$src")" && pwd)/co-mem"
[ -f "$COMEM" ] && command -v python3 >/dev/null 2>&1 || exit 0

# repo of the session's cwd (fall back to current dir)
cwd=$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("cwd",""))
except Exception: print("")' 2>/dev/null)
[ -n "$cwd" ] || cwd="$PWD"
repo=$(git -C "$cwd" remote get-url origin 2>/dev/null | sed -E 's#/+$##; s#.*/##; s#\.git$##')

tmp="$(mktemp).json"; pidf="$(mktemp)"
python3 "$COMEM" export "$tmp" 2>/dev/null || { rm -f "$tmp" "$pidf"; exit 0; }

ctx=$(REPO="$repo" IDS="$pidf" python3 - "$tmp" <<'PY' 2>/dev/null
import datetime, json, os, sys
repo = os.environ.get("REPO", "")
try:
    mems = json.load(open(sys.argv[1]))
except Exception:
    sys.exit(0)
def md(m): return m.get("metadata") or {}
this_repo = [m for m in mems if repo and md(m).get("repo") == repo]
general = [m for m in mems if md(m).get("repo", "general") == "general"]
this_repo.sort(key=lambda m: m.get("importance", 0), reverse=True)
general.sort(key=lambda m: m.get("importance", 0), reverse=True)
picked = this_repo[:12] + general[:4]
if not picked:
    sys.exit(0)
try:  # ids of carried memories → bump their access_count (auto-recall counts as use)
    with open(os.environ["IDS"], "w") as fh:
        fh.write("\n".join(str(m.get("id")) for m in picked if m.get("id")))
except Exception:
    pass
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
print(out)
PY
)
# bump access_count for the memories we carried into context (fail-safe)
pids="$(tr '\n' ' ' < "$pidf" 2>/dev/null)"
[ -n "${pids// }" ] && python3 "$COMEM" touch $pids >/dev/null 2>&1 || true
rm -f "$tmp" "$pidf"
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"SessionStart", additionalContext:$c}}'
