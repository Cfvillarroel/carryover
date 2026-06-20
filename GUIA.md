# Headroom — Quick guide

Context compression layer for LLMs. Compresses what Claude reads/writes
before it reaches the API → fewer tokens, same responses. Memory shared
across repos. Installed durably on 2026-06-19.

Repo: https://github.com/chopratejas/headroom

---

## What got installed

- **Service** `com.headroom.default` (launchd, starts on its own when the Mac reboots).
  Proxy at `http://127.0.0.1:8787`.
- **Claude routed at the user scope** in `~/.claude/settings.json`
  (`env.ANTHROPIC_BASE_URL` + hooks). Applies to **all** Conductor workspaces.
- **Memory:** global `~/.headroom/memory.db` (USER scope = shared across repos)
  + per-project in `~/.headroom/memories/projects/<workspace>/`.
- **CLI:** `~/.headroom/venv/bin/headroom` (service) and `~/.pipx/venvs/headroom-ai/bin/headroom` (hooks). Both 0.26.0, Python 3.13.
- Claude Code plugin `headroom@headroom-marketplace` enabled.

Tip: alias so you don't have to type the path:
```bash
echo 'alias hr=~/.headroom/venv/bin/headroom' >> ~/.zshrc && source ~/.zshrc
```

---

## Using it in any workspace

**There's nothing to install per-repo.** Routing is global. Just:

- Open a **new** Claude session in the workspace → it already goes through headroom.
- Already-open sessions: close and reopen them (`ANTHROPIC_BASE_URL` is read at startup).

---

## Easy commands

**Aliases** (in `~/.zshrc`, open a new terminal or `source ~/.zshrc`):

| Alias | Does |
|-------|------|
| `hr` | base headroom CLI |
| `hr-status` | is the proxy up/healthy? |
| `hr-mem` | saved memories |
| `hr-stats` | memory summary |
| `hr-save` | tokens saved |
| `hr-on` / `hr-off` | start / stop the proxy |

**Inside Claude** (any workspace): type `/headroom` → summary of proxy,
memory and savings. Also `/headroom list --scope USER`, `/headroom show <id>`, etc.

---

## Verify

```bash
hr install status                 # Status: running · Healthy: yes
curl -fsS http://127.0.0.1:8787/readyz   # {"status":"healthy",...}
echo $ANTHROPIC_BASE_URL          # inside a Claude session → http://127.0.0.1:8787
hr memory stats                   # accumulated memory (alias already points to the proxy store)
hr memory list --scope USER       # memories shared across repos
```

> ⚠️ Important: by default the `headroom memory` CLI uses `./headroom_memory.db` from the
> current directory, NOT the proxy store. That's why the `hr-mem`/`hr-stats` aliases
> add `--db-path "$HOME/.headroom/memory.db"`. To save a memory to that store by hand:
> `mem-save "whatever you want to remember"`.

---

## Manage

```bash
hr install start | stop | restart   # control the service
hr install status                   # status
hr install remove                   # UNINSTALL everything (removes routing + service)
```

⚠️ If the proxy goes down, Claude sessions **fail** until `hr install start`
(or `hr install remove` to go back to direct traffic).

---

## Common problems

- **Claude fails / hangs** → proxy down? `hr install status`; if not, `hr install start`.
- **Not compressing in a session** → empty `echo $ANTHROPIC_BASE_URL` = old session, restart it.
- **Get back to normal fast** → `hr install remove` (Claude goes back to talking directly to Anthropic).
- **Don't reinstall with 3.14** → the Rust extension won't compile; the venv uses Python 3.13.
- **Don't delete `~/.headroom/venv`** without `hr install remove` first: it backs the service.
