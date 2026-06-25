---
description: Send a message to another Conductor workspace
---

Leave a note for another Conductor workspace. Arguments `$ARGUMENTS`: the first word is the target
workspace name (or `all` to broadcast), the rest is the message.

Run via Bash (resolve the headroom venv python so the write succeeds):

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" send <workspace> "<message>"
```

Substitute `<workspace>` and `<message>` from the arguments, escaping the message safely. Then
confirm to the user what was sent and to whom. If no arguments were given, ask who to message and
what to say.
