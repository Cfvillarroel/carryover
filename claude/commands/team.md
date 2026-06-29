---
description: Build a team of Conductor workspaces (with roles) and dispatch tasks to it
---

Assemble and drive a **team** of Conductor workspaces. A team is a named roster mapping each member
workspace to a role (e.g. `lead`, `frontend`, `backend`, `reviewer`). `$ARGUMENTS` is free-form intent
(e.g. "make a team checkout-revamp with paris as frontend and zurich as backend, then have each start").

Use the `co-mem team` CLI via Bash (resolve the headroom venv python so writes succeed):

```bash
PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
"$PY" "$HOME/.carryover/co-mem" team list                       # show teams + rosters
"$PY" "$HOME/.carryover/co-mem" team add <team> <workspace> <role>
"$PY" "$HOME/.carryover/co-mem" team rm <team> [<workspace>]     # drop a member, or the whole team
"$PY" "$HOME/.carryover/co-mem" team send <team> [@role] "<message>"    # notify (passive)
"$PY" "$HOME/.carryover/co-mem" team assign <team> [@role] "<task>"     # handover: notify + "execute now"
```

As the lead, when dispatching real work: **decompose the goal into per-role tasks yourself**, then
`assign` each role its own slice (role-specific `assign <team> @frontend "…"`) rather than blasting the
same message to everyone. Address members by their **city codename** or **project name** (stable).

Manage teams visually in the dashboard (`co-dash` → **👥 Teams** tab). Note: `assign` notifies idle
workspaces but can't wake them — a teammate picks up its task when its workspace is next opened.
