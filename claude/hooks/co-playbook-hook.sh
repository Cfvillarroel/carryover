#!/usr/bin/env bash
# UserPromptSubmit hook: Devin-style playbook macros. If the prompt contains a `!<name>` token and a
# matching playbook file exists, inject that playbook as context so the agent follows the procedure.
# Pure injection — never blocks; emits nothing when no macro matches. Playbooks are plain .md files in
# ~/.carryover/playbooks/ (drop a file → it's a macro). Also searches the plugin dir for plugin users.
input=$(cat)
prompt=$(printf '%s' "$input" | python3 -c 'import json,sys
try: print(json.load(sys.stdin).get("prompt",""))
except Exception: print("")' 2>/dev/null)
[ -n "$prompt" ] || exit 0
ctx=$(PROMPT="$prompt" PLUGIN_ROOT="${CLAUDE_PLUGIN_ROOT:-}" python3 - <<'PY' 2>/dev/null
import os, re, sys
prompt = os.environ.get("PROMPT", "")
dirs = [os.path.expanduser("~/.carryover/playbooks")]
pr = os.environ.get("PLUGIN_ROOT")
if pr:
    dirs.append(os.path.join(pr, "playbooks"))
# macro = !name at a word boundary; name is letters/digits/_/- (no dots or slashes → no path escape)
names = []
for m in re.finditer(r'(?<![\w/!])!([a-zA-Z][\w-]*)', prompt):
    n = m.group(1).lower()
    if n not in names:
        names.append(n)
out = []
for n in names:
    for d in dirs:
        p = os.path.join(d, n + ".md")
        if os.path.isfile(p):
            try:
                body = open(p, encoding="utf-8").read().strip()
            except Exception:
                break
            out.append(f"## ▶ Playbook: !{n}\n"
                       f"The user invoked the `!{n}` playbook. Follow this procedure for this task:\n\n{body}")
            break
if not out:
    sys.exit(0)
print("\n\n---\n\n".join(out))
PY
)
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"UserPromptSubmit", additionalContext:$c}}'
