# Using carryover from any tool (MCP)

carryover's memory is an **MCP server** (`co-mcp.py`), so any MCP-compatible client — Claude
Desktop, Cursor, Windsurf, … — can read and write the **same** memory carryover uses
everywhere, not just Claude Code. Two tools are exposed:

- **`recall`** — find stored knowledge *by meaning* (semantic with headroom, keyword
  otherwise), optionally scoped to a repo.
- **`remember`** — save a fact to the shared store.

It runs **entirely on your machine**: the client launches it as a local subprocess and talks
over stdio. No network, no port, no telemetry — your knowledge never leaves your computer.

## The command to run

The server is one Python file. The interpreter you point at it decides recall quality:

| Interpreter | Recall |
|---|---|
| `~/.headroom/venv/bin/python` | **semantic** (uses headroom's embedder) |
| `python3` (system) | keyword (built-in store) |

> ⚠️ **Use absolute paths.** Most MCP clients do **not** expand `~`. Print yours and paste the
> full `/Users/you/...` values into the configs below:
> ```bash
> echo "$HOME/.headroom/venv/bin/python"   # interpreter (or: command -v python3)
> echo "$HOME/.carryover/co-mcp.py"        # the server
> ```

## Claude Desktop

Config file (macOS): `~/Library/Application Support/Claude/claude_desktop_config.json`
— or open it from **Settings → Developer → Edit Config**.

```json
{
  "mcpServers": {
    "carryover": {
      "command": "/Users/you/.headroom/venv/bin/python",
      "args": ["/Users/you/.carryover/co-mcp.py"]
    }
  }
}
```

Then fully **quit** Claude Desktop (Cmd+Q — not just close the window) and reopen it. Confirm:
the 🔨 tools icon at the bottom of a chat shows `recall` / `remember`.
Logs live in `~/Library/Logs/Claude/mcp*.log`.

## Cursor

Config file: `~/.cursor/mcp.json` (global, all projects) or `.cursor/mcp.json` (per project)
— or use **Settings → Tools & MCP → New MCP Server**. Same `mcpServers` shape as above.
Restart Cursor after saving.

> Gotcha: if the top-level `mcpServers` key is missing, Cursor ignores the whole file
> silently (no error).

## Windsurf

Config file (macOS/Linux): `~/.codeium/windsurf/mcp_config.json`. Same `mcpServers` shape.
Restart Windsurf. (Windsurf also supports `${env:VAR}` interpolation if you'd rather not
hardcode the path.)

## No headroom?

Use `python3` as the `command` (point at the system interpreter). Everything works the same —
recall just falls back to keyword instead of semantic.

## Scope: which repo does recall use?

The auto-recall hook in Claude Code knows your repo from the working directory. **The MCP
server has no working directory**, so:

- `recall` **without** a `repo` searches **every** repo.
- Pass `repo` to scope to that repo (and its group — see `groups.conf`).

You don't pass args by hand — you ask in natural language and the model fills them:

- *"recall what we know about the auth flow in the **api** repo"* → `recall(query="auth flow", repo="api")`
- *"what do you already know here?"* → `recall(query="…")` across all repos

## Examples

- **Pull context:** *"Before we start, recall what carryover knows about this project."*
- **Save a decision:** *"Remember that we moved the queue from Redis to SQS."* → `remember(...)`
- **Cross-tool:** save something in Cursor, open Claude Desktop, `recall` it — same brain.

## Verify it works

1. Restart the client after editing the config.
2. Find the tools: Claude Desktop → 🔨 icon; Cursor → Settings → Tools & MCP; Windsurf →
   Cascade's MCP panel.
3. Ask: *"Use the recall tool to find anything about carryover."* You should get memories back.

## Troubleshooting

- **Tools don't appear** → JSON error (a stray/missing comma disables everything) or a missing
  `mcpServers` root key. Validate the JSON.
- **Server won't start / "command not found"** → `~` wasn't expanded; use absolute paths.
  Check the interpreter exists: `ls /Users/you/.headroom/venv/bin/python`.
- **Recall is keyword, not semantic** → you're pointing at system `python3`, or headroom isn't
  installed. Point `command` at `~/.headroom/venv/bin/python` (absolute).
- **Empty results** → the store may be empty for that repo; try without `repo`, or open
  `co-dash` to see what's stored.
- **Claude Desktop logs:** `~/Library/Logs/Claude/mcp*.log`.

---

The `recall` / `remember` tools use the same `co_store` backend as `co-recall`, the dashboard
and the auto-recall hook — one shared, local memory.
