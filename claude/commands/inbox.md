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

Note: the auto-delivery hooks (session start / end of turn) already **consume** incoming messages
as they surface them into context — so `--peek` will often be empty even right after a message
arrived. To **re-read** a message that was already delivered (e.g. it got truncated in context, or
context was compacted), run with `--all`, which also lists already-delivered messages and never
consumes:

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" inbox --all
```
