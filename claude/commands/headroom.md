---
description: Headroom status — proxy, memory, and token savings
---

You are the headroom operator. Run these commands and summarize the result clearly and briefly:

```bash
HR=~/.headroom/venv/bin/headroom
DB="$HOME/.headroom/memory.db"   # the proxy's real store (NOT the ./headroom_memory.db in cwd)
$HR install status                       # proxy: running/healthy, port
$HR memory stats --db-path "$DB"         # total memories and by scope
$HR memory list --db-path "$DB" --limit 10   # latest memories
$HR output-savings 2>/dev/null || true   # tokens saved (if data is available)
```

Then report:
- Whether the proxy is **up and healthy** (or down → suggest `hr-on`).
- How many **memories** there are (USER scope = shared across repos).
- The **token savings** if available.

If the user passed arguments in `$ARGUMENTS`, interpret them as a subcommand of
`headroom memory` (e.g. `show <id>`, `list --scope USER`, `--since 7d`) and run it
**always adding** `--db-path "$HOME/.headroom/memory.db"` instead of the default summary.
