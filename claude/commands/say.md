---
description: Message all workspaces connected to this one
---

Send a message to every workspace connected to this one (set up with `/connect`). `$ARGUMENTS` =
the message.

Run via Bash (resolve the headroom venv python so the write succeeds):

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" say <message>
```

Substitute `<message>` from the arguments, escaping it safely. It reports which workspaces received
it. If this workspace isn't connected to any other, the command errors — tell the user to run
`/connect <workspace>` first.
