---
description: Read cross-workspace messages left for this workspace
---

Show the messages other Conductor workspaces have left for this one. Run via Bash:

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" inbox --peek
```

That lists pending messages **without consuming them** (each item has a `from` and `content`).
Present them clearly. If the user wants to mark them as read (so they don't show again), run the
same command **without** `--peek`.
