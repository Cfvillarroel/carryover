---
description: headroom routing — show status, or turn it on/off
---

Manage carryover routing (whether Claude goes through the headroom proxy).

Run and report the status:

```bash
bash ~/.claude/hooks/carryover-toggle.sh status
```

If the user asked to change it (on/off in their arguments), run instead
`bash ~/.claude/hooks/carryover-toggle.sh on` (or `off`) and confirm. Turning it off
makes new sessions go straight to Anthropic (the proxy keeps running, so turning it back
on is instant). Per-terminal: `carryover off --session` / `on --session`.
