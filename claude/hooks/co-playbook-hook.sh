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
# optional `mode:` in YAML frontmatter → a behavioral directive prepended to the playbook. A hook can
# only inject context, not flip the harness, so "plan" is an instruction, not real plan-mode.
MODES = {
    "plan": "▶ MODE: PLAN — do NOT edit files or run mutating commands this turn; investigate and produce a plan/spec only.",
    "interrogate": "▶ MODE: INTERROGATE — ask ONE question at a time (offer a recommended answer), resolve each decision branch before the next, and do not implement yet.",
}
def parse_pb(text):
    mode, body = "", text.strip()
    if body.startswith("---"):
        lines = body.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":           # candidate closing fence
                found = False
                for ln in lines[1:i]:
                    k, sep, v = ln.partition(":")
                    if sep and k.strip().lower() == "mode":
                        mode, found = v.strip().lower(), True
                if found:                           # only a real frontmatter block (has mode:) is stripped;
                    body = "\n".join(lines[i + 1:]).strip()  # a body that merely opens with '---' is kept intact
                break
    return mode, body
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
                mode, body = parse_pb(open(p, encoding="utf-8").read())
            except Exception:
                break
            hdr = f"## ▶ Playbook: !{n}\n"
            if mode in MODES:
                hdr += MODES[mode] + "\n"
            out.append(f"{hdr}The user invoked the `!{n}` playbook. Follow this procedure for this task:\n\n{body}")
            break
if not out:
    sys.exit(0)
print("\n\n---\n\n".join(out))
PY
)
[ -n "$ctx" ] || exit 0
jq -nc --arg c "$ctx" '{hookSpecificOutput:{hookEventName:"UserPromptSubmit", additionalContext:$c}}'
