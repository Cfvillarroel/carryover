---
description: Connect this workspace with another (two-way) for messaging
---

Link this Conductor workspace with another so they can exchange messages without retyping names.
`$ARGUMENTS` = the other workspace's name.

Run via Bash:

```bash
python3 "$HOME/.carryover/co-mem" connect <workspace>
```

It prints the resulting peers — confirm the link to the user. If no arguments were given, run
`python3 "$HOME/.carryover/co-mem" connections` instead to show the current connections.
