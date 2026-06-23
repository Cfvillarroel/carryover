<div align="center">

<h2>💼</h2>

<pre>
 ██████╗ █████╗ ██████╗ ██████╗ ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██████╗
██╔════╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║     ███████║██████╔╝██████╔╝ ╚████╔╝ ██║   ██║██║   ██║█████╗  ██████╔╝
██║     ██╔══██║██╔══██╗██╔══██╗  ╚██╔╝  ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╗██║  ██║██║  ██║██║  ██║   ██║   ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
</pre>

<strong>Pack your context once — carry it across every AI tool.</strong><br/>
<sub><em>like a carry-on for your AI's brain 💼</em></sub>

<sub>shared persistent memory · 60–95% fewer tokens · leaner agent · auto-wiki · save-to-memory<br/>
Claude Code · Cursor · Windsurf · Conductor — one install · 100% local</sub>

<p>
<a href="https://github.com/Cfvillarroel/carryover/actions/workflows/ci.yml"><img src="https://github.com/Cfvillarroel/carryover/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
<a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License: MIT"></a>
<img src="https://img.shields.io/badge/platform-macOS-black.svg" alt="Platform: macOS">
<img src="https://img.shields.io/badge/local--first-yes-success.svg" alt="local-first">
<a href="https://github.com/chopratejas/headroom"><img src="https://img.shields.io/badge/works%20with-headroom-orange.svg" alt="works with headroom"></a>
<a href="https://github.com/Cfvillarroel/carryover/stargazers"><img src="https://img.shields.io/github/stars/Cfvillarroel/carryover?style=social" alt="GitHub stars"></a>
</p>

<strong>English · <a href="README.es.md">Español</a> · <a href="#install">Install</a></strong>

</div>

---

## The problem

You don't work in a single AI tool anymore — Claude Code one day, Cursor or Windsurf
the next, Conductor for parallel work. But **context doesn't travel with you**: every
tool, project and session starts from zero, so you re‑explain the same codebase over and
over. On top of that each agent **burns tokens** on bloated context, **forgets**
everything between sessions, and tends to **over‑engineer** — and the few things worth
remembering never get captured. Wiring up the fix by hand is fiddly and has to be redone
on every machine.

## The fix

A local layer that makes your context **carry over** across tools, projects and sessions:

- 🧠 **Persistent, shared memory** across tools, repos and sessions — a local store you own,
  with **semantic recall** (by meaning) scoped to each repo or a group of related repos.
- 🕸 **Structured knowledge** — saved as facts + typed entities + relationships (a queryable
  graph), indexed by the repo it came from.
- 🔁 **Auto‑recall** — when you start a session in a repo, what carryover knows about it is
  injected as context (~0.5s, ~500 tokens, compressed). Plus `/recall` / `co-recall` on demand
  (current repo by default; `--all` for every repo).
- 📊 **Local dashboard** (`co-dash`) — browse, search, filter and **manage** (delete/clear)
  your knowledge, a relationship graph, and your project wikis.
- 📄 **Auto‑wiki** — an LLM writes docs + mermaid diagrams (overview, architecture, flows + a
  **Features** catalog) and updates them **incrementally** (preserves existing pages, adds only
  what changed) on push to master/main.
- 💾 **Save‑what‑mattered prompt** at session end · 🩺 **`carryover doctor`** health check ·
  routing **on/off** toggle · `carryover wrap <tool>` for Cursor/Codex/…
- Status bar **🐴/🧠**, slash commands, terminal aliases.

One idempotent install, **100% local**, **standalone by default** — with optional headroom
(shared store + token compression) and ponytail integrations — so your context follows you
instead of resetting.

## Works with

The shared memory + compression work with any agent that routes through the local proxy:

| Tool | Compression + shared memory | Claude extras (🐴/🧠, `/headroom`, save‑to‑memory) |
|------|:---------------------------:|:---:|
| Claude Code | ✅ auto (installer) | ✅ |
| Conductor | ✅ auto (runs Claude Code) | ✅ |
| Cursor | ✅ `headroom wrap cursor` (paste config) | — |
| Windsurf / Devin | ✅ OpenAI‑compatible → base URL `http://127.0.0.1:8787/v1` | — |
| Codex / Copilot / Aider / Cline / Continue / Goose | ✅ `headroom wrap <tool>` | — |

### Set it up in each tool (the cross-tool part)

The memory and compression are shared through the local proxy — each tool just needs to be
pointed at it **once**. (The proxy must be running: check with `carryover doctor` or `hr-status`.)

- **Claude Code / Conductor** — automatic. `install.sh` already wired the routing; nothing to do.
- **Cursor** — run `carryover wrap cursor` (delegates to `headroom wrap cursor`). It prints the
  exact config to paste into Cursor's model settings (points its API base at the proxy). From
  then on, Cursor's AI shares the same memory + compression as Claude.
- **Windsurf / Devin** — in its AI/model settings, set a custom **OpenAI base URL** to
  `http://127.0.0.1:8787/v1`. (`carryover wrap windsurf` prints this reminder.)
- **Codex / Aider / Cline / Continue / Goose / Copilot** — `carryover wrap <tool>`.
- **Any other OpenAI/Anthropic-compatible tool** — point its base URL at the proxy:
  `http://127.0.0.1:8787` (Anthropic-style) or `http://127.0.0.1:8787/v1` (OpenAI-style).

Two things to keep in mind:

- **Terminal commands** (`co-dash`, `mem-save`, `co-recall`, `carryover …`) work in **any**
  tool's integrated terminal — they live in your shell (`~/.zshrc`), not in a specific app.
- **Slash commands** (`/headroom`, `/recall`, `/carryover`, `/wiki-enable`) and the 🐴/🧠 status
  bar are **Claude Code only**. Other tools get the shared memory + compression, not the slash UI.
- A tool is **not** auto-detected — it shares everything only after you point it at the proxy once.

## Install

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

That installs **carryover standalone** — memory, recall, wikis and the dashboard, backed by a
built-in local store (`~/.carryover/memory.db`). Open a new terminal (or `source ~/.zshrc`) and
restart Claude. Requirements: macOS · Python 3 · Claude Code (`claude`) on PATH.

**Optional integrations** (opt-in):
```bash
bash ~/carryover/install.sh --with-headroom   # + headroom: compression proxy + shared memory backend
bash ~/carryover/install.sh --with-ponytail   # + ponytail: a lazy-dev Claude plugin
bash ~/carryover/install.sh --full            # carryover + headroom + ponytail
```
- **headroom** upgrades carryover's memory to a *shared* store across tools and adds the
  compression proxy (routing for Claude / Cursor / Codex…). When installed, carryover uses it
  automatically; otherwise it uses the built-in store. Needs `brew install python@3.13`
  (headroom's Rust/PyO3 extension doesn't build on 3.14).
- **ponytail** is an independent third-party plugin — purely optional.

The installer is **idempotent**: it symlinks the hooks, dashboard, status bar and `/headroom`
command, and adds aliases to `~/.zshrc`.

**Not on Claude Code?** With headroom the proxy is shared, so memory + compression apply to
**any** tool (Cursor, Windsurf, Codex, Aider…) — point each at the proxy (see [Works with](#works-with)).

### Install just the Claude plugin (optional)

Only want the Claude-side commands + the save-to-memory prompt, without the full installer?

```bash
claude plugin marketplace add Cfvillarroel/carryover
claude plugin install carryover@carryover
```

You still need the headroom proxy for memory/compression:
`pip install "headroom-ai[all]" && headroom install apply --memory`.

## Scope: global vs per‑repo

- **Global (once per Mac):** headroom proxy + memory + Claude config. Global **by
  design** — that's what makes context shared across all repos and tools.
- **Per repo / a set of repos:** the **wiki** capability — run `co-wiki-enable` in each repo
  you want (one, several or all). It installs a `pre-push` hook there only.
- Memory is global but **scoped by repo**: recall returns the current repo's memories by
  default. Group related repos (e.g. the front + back of one product) so they share recall by
  listing them on one line of `~/.carryover/groups.conf` (space/comma-separated).

## Easy commands

| Command | Does |
|---------|------|
| `hr` | headroom CLI |
| `hr-status` | proxy up / healthy? |
| `hr-on` / `hr-off` | start / stop the proxy |
| `hr-save` | tokens saved |
| `hr-mem` | stored memories |
| `hr-stats` | memory summary |
| `hr-prune …` | prune memories (e.g. `--older-than 30d --dry-run`) |
| `mem-save "text"` | save a memory by hand (or structured `--json`) |
| `co-recall [--all] <query>` | recall knowledge **by meaning** (semantic with headroom, keyword otherwise) — this repo's group; `--all` for every repo (alias: `hr-recall`) |
| `co-forget <query>` | delete memories by keyword, with confirm (alias: `hr-forget`) |
| `co-supersede <old> <new>` | mark an old memory as replaced by a newer one so recall skips it |
| `co-wiki-enable` | enable the auto-wiki in the current repo, generates the first one (alias: `wiki-enable`) |
| `co-wiki-gen` | update the current repo's wiki on demand, incrementally (alias: `wiki-gen`) |
| `co-wiki-prune` | drop dead entries from the wiki registry (alias: `wiki-prune`) |
| `co-dash` | local dashboard (overview, knowledge + wikis) |
| `co-backup` / `co-restore <file>` | snapshot / restore all memories (carry them to another machine) |
| `co-mcp` | run carryover's MCP server (use the memory from Cursor, Claude Desktop, any MCP client) |
| `hr-dash` | headroom's savings dashboard |
| `carryover status` | is routing on? |
| `carryover on` / `off` | turn proxy routing on / off (`--session` = this shell only) |
| `carryover doctor [--fix]` | health-check the whole setup (and auto-repair with `--fix`) |
| `carryover update` | pull the latest carryover + re-sync this machine (no manual copies) |
| `carryover version` | show installed version + whether updates are pending |
| `carryover persist` | make the proxy survive reboot (bootstrap its launchd service) |
| `carryover wrap <tool>` | route another tool (Cursor, Codex…) through the proxy |
| `carryover uninstall` | remove carryover (keeps headroom + ponytail) |

**Auto-recall:** when you start a session in a repo, carryover injects *what it already
knows about that repo* as context — so the knowledge actually comes back, not just gets stored.
Every recall (auto at session start or via `/recall`) is counted per memory, so `co-dash` shows
which memories actually get reused (the ♻ badge).

Inside Claude (any workspace): `/headroom` (proxy + memory + savings), `/carryover` (routing on/off/status), `/recall [--all] <query>`, `/wiki-enable`.
Status bar: **🐴** ponytail active, **🧠** headroom active.

## Dashboards (local)

Two local web dashboards — nothing leaves your machine:

- **`co-dash`** → carryover's own dashboard at `http://127.0.0.1:8788` — browse your
  **knowledge** (facts, typed entities, tags, with search + entity/tag filters), each memory
  showing a **reuse badge** (♻ N = times recalled into context),
  **grouped by the repo** it came from (or *general*), an auto-built **relationship
  graph**, and your project **wikis** (Markdown + mermaid). It's also a **manager**:
  delete a single memory or clear a whole repo with one click. Reads/writes your DB live; Ctrl-C to stop.
- **`hr-dash`** → headroom's **savings** dashboard at `http://127.0.0.1:8787/dashboard` —
  tokens saved, compression, cache hit rate.

<sub>(Screenshots below use fictitious data. Wikis appear in `co-dash` after you run
`co-wiki-enable` in a repo and push to master/main.)</sub>

| Knowledge | Graph | Wikis |
|---|---|---|
| ![Knowledge](assets/dash-knowledge.png) | ![Graph](assets/dash-graph.png) | ![Wikis](assets/dash-wikis.png) |

## Enable / disable routing

Routing is **ON by default** for every new session. Toggle it without uninstalling (the
proxy keeps running):

```bash
carryover off            # new sessions go straight to Anthropic (global)
carryover on             # route through headroom again (global)
carryover off --session  # only the current terminal
carryover status         # show state
```

`off` is surgical and reversible: it drops the routing env and guards headroom's
SessionStart hook so it won't re‑add it; `on` reverts.

## Memory

```bash
hr memory stats --db-path ~/.headroom/memory.db    # (the hr-* aliases already pass this)
hr memory list  --db-path ~/.headroom/memory.db --scope USER
mem-save "what you want to remember"
```

> The `headroom memory` CLI defaults to `./headroom_memory.db` in the current dir, **not**
> the proxy store — that's why the aliases pass `--db-path ~/.headroom/memory.db`.

**Recall is semantic** (by meaning, via headroom's embedder) and **scoped to the current
repo's group**; `co-recall --all` searches everything. `co-backup` / `co-restore` move the
whole store to another machine. `co-supersede <old> <new>` hides a stale memory so an updated
fact wins.

## Use the memory from other tools (MCP)

carryover's memory is also an **MCP server**, so any MCP client — Cursor, Claude Desktop,
Windsurf — can `recall` and `remember` against the same store, not just Claude Code:

```json
{ "mcpServers": {
    "carryover": { "command": "~/.headroom/venv/bin/python", "args": ["~/.carryover/co-mcp.py"] }
} }
```

No headroom? Use `python3` as the `command` (recall falls back to keyword). Tools exposed:
`recall` (semantic, repo-scoped) and `remember`. Most clients don't expand `~` — use absolute
paths.

It runs **entirely on your machine**: the client launches it as a local subprocess and talks
over stdio — no network, no port, no telemetry. Your knowledge never leaves your computer.

📖 **Full setup per client** (Claude Desktop / Cursor / Windsurf), repo scoping, examples and
troubleshooting: **[docs/MCP.md](docs/MCP.md)**.

## Auto‑wiki (local, GitHub‑Wiki format)

Generates a project wiki with headless Claude (`claude -p`) — overview, architecture, flows
and a **Features** catalog, with mermaid diagrams. It updates **incrementally**: each run
preserves existing pages and complements them with what changed, so the wiki **grows** over
time instead of being rewritten from scratch. **`co-wiki-enable` generates the first wiki
immediately** (so it's never empty), then it stays current via `co-wiki-gen` and the
end-of-session prompt. (A `pre-push` hook on master/main also folds in changes, though in
Conductor worktrees you'll mostly use `co-wiki-gen`.) Local by default; publishing to the
GitHub wiki is optional.

```bash
cd /path/to/your/repo && co-wiki-enable   # enable + generate the first wiki now (background)
co-wiki-gen                               # update the wiki incrementally on demand (no push needed)
WIKI_PUBLISH=1 co-wiki-gen                # also push to the GitHub wiki
```

<details>
<summary><b>Manage / uninstall headroom</b></summary>

```bash
hr install status | start | stop | restart
hr install remove        # remove service + routing (back to direct Anthropic)
```

⚠️ If the proxy is down, Claude sessions fail until `hr-on` (or `hr install remove`).

</details>

<details>
<summary><b>Direct install (without this repo)</b></summary>

```bash
pip install "headroom-ai[all]" && headroom install apply --memory
claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail
```

carryover is more than a bundle: on top of a one‑command idempotent install, it adds its
own layer — cross‑tool memory wiring, the 🐴/🧠 status bar, the `/headroom` command, the
save‑to‑memory system (Stop hook + `mem-save`, since headroom has no `memory add` CLI),
the **auto‑wiki** (`claude -p` → GitHub‑Wiki docs with mermaid), and the `carryover`
routing toggle.

</details>

<details>
<summary><b>Troubleshooting</b></summary>

- **Claude hangs / fails** → proxy down? `hr-status`; if so, `hr-on`.
- **No compression in a session** → `echo $ANTHROPIC_BASE_URL` empty = old session, restart it.
- **`pip install` fails** → use Python 3.13 (not 3.14): `brew install python@3.13`.
- **`headroom install apply` fails with a `launchctl` error** → run `install.sh` from your
  **real Terminal app**, not an SSH/automation/agent shell — macOS launchd (GUI domain) needs
  an interactive session. The installer keeps going regardless; just re-run apply in Terminal.
- **Don't delete `~/.headroom/venv`** before `hr install remove` — it backs the service.

</details>

---

## Credits · Créditos

carryover adds its own layer (cross‑tool memory wiring, the 🐴/🧠 status bar, `/headroom`,
the save‑to‑memory system, the auto‑wiki and the routing toggle) on top of two excellent
tools. Full credit to their creators — carryover construye encima de dos herramientas
excelentes; todo el crédito a sus creadores:

- **headroom** — [@chopratejas](https://github.com/chopratejas/headroom)
- **ponytail** — [@DietrichGebert](https://github.com/DietrichGebert/ponytail)

Licensed [MIT](LICENSE) · Licencia [MIT](LICENSE).
