---
description: Hand a task OVER to another workspace — it gets a notification and is told to execute on arrival
---

Like `/handoff`, but an *active* transfer: the target workspace is pinged (macOS desktop
notification) and, when its inbox is delivered, the agent is told to **execute the task now**, not
just read it.

`$ARGUMENTS` = the target workspace name (optionally followed by a note about what to hand over).

Write a concise handover summary **yourself**, from this session's context. Include:
- what was done,
- the current state,
- what you're asking the other workspace to do,
- key files, decisions, or gotchas they'll need to continue.

Then send it via Bash (resolve the headroom venv python so the write works):

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" handover <workspace> "<your handover summary>"
```

Substitute `<workspace>` and your summary, escaping it safely. Confirm to the user what you handed
over and to whom. Address the target by its **city codename** or **project name** (stable); a renamed
title may not resolve. If no workspace was given, ask which one (or run
`python3 "$HOME/.carryover/co-mem" connections` to see connected ones).

Note: the target won't run on its own while idle — the notification tells the user to open it; the
agent picks up and executes the handover on its next turn (via the inbox hook).
