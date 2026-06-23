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
<a href="https://github.com/chopratejas/headroom"><img src="https://img.shields.io/badge/built%20on-headroom-orange.svg" alt="built on headroom"></a>
<a href="https://github.com/DietrichGebert/ponytail"><img src="https://img.shields.io/badge/built%20on-ponytail-ff69b4.svg" alt="built on ponytail"></a>
<a href="https://github.com/Cfvillarroel/carryover/stargazers"><img src="https://img.shields.io/github/stars/Cfvillarroel/carryover?style=social" alt="GitHub stars"></a>
</p>

<strong><a href="#english">English</a> · <a href="#español">Español</a> · <a href="#install">Install</a></strong>

</div>

---

# English

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

- 🧠 **[headroom](https://github.com/chopratejas/headroom)** — context‑compression proxy
  (60–95% fewer tokens) + **shared, persistent memory** across all your repos.
- 🐴 **[ponytail](https://github.com/DietrichGebert/ponytail)** — keeps the agent from
  over‑engineering (simplest solution that works).
- 🕸 **Structured knowledge** — saved as facts + typed entities + relationships (a queryable
  graph), indexed by the repo it came from.
- 🔁 **Auto‑recall** — when you start a session in a repo, what carryover knows about it is
  injected as context (~0.5s, ~500 tokens, compressed). Plus `/recall` / `hr-recall` on demand.
- 📊 **Local dashboard** (`co-dash`) — browse, search, filter and **manage** (delete/clear)
  your knowledge, a relationship graph, and your project wikis.
- 📄 **Auto‑wiki** on push to master/main (an LLM writes docs + mermaid diagrams).
- 💾 **Save‑what‑mattered prompt** at session end · 🩺 **`carryover doctor`** health check ·
  routing **on/off** toggle · `carryover wrap <tool>` for Cursor/Codex/…
- Status bar **🐴/🧠**, slash commands, terminal aliases.

One idempotent install, the **real upstream tools** (no forks), **global by design** — so
your context follows you instead of resetting.

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

- **Terminal commands** (`co-dash`, `mem-save`, `hr-recall`, `carryover …`) work in **any**
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
- **Per repo / a set of repos:** the **wiki** capability — run `wiki-enable` in each repo
  you want (one, several or all). It installs a `pre-push` hook there only.
- Memory is global but internally scoped: `USER` = shared across repos, `project` = per
  workspace.

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
| `co-recall <query>` | recall knowledge by keyword (alias: `hr-recall`) |
| `co-forget <query>` | delete memories by keyword, with confirm (alias: `hr-forget`) |
| `co-wiki-enable` | enable the auto-wiki in the current repo, generates the first one (alias: `wiki-enable`) |
| `co-wiki-gen` | regenerate the current repo's wiki on demand (alias: `wiki-gen`) |
| `co-wiki-prune` | drop dead entries from the wiki registry (alias: `wiki-prune`) |
| `co-dash` | local dashboard (overview, knowledge + wikis) |
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

Inside Claude (any workspace): `/headroom` (proxy + memory + savings), `/carryover` (routing on/off/status), `/recall <query>`, `/wiki-enable`.
Status bar: **🐴** ponytail active, **🧠** headroom active.

## Dashboards (local)

Two local web dashboards — nothing leaves your machine:

- **`co-dash`** → carryover's own dashboard at `http://127.0.0.1:8788` — browse your
  **knowledge** (facts, typed entities, tags, with search + entity/tag filters),
  **grouped by the repo** it came from (or *general*), an auto-built **relationship
  graph**, and your project **wikis** (Markdown + mermaid). It's also a **manager**:
  delete a single memory or clear a whole repo with one click. Reads/writes your DB live; Ctrl-C to stop.
- **`hr-dash`** → headroom's **savings** dashboard at `http://127.0.0.1:8787/dashboard` —
  tokens saved, compression, cache hit rate.

<sub>(Screenshots below use fictitious data. Wikis appear in `co-dash` after you run
`wiki-enable` in a repo and push to master/main.)</sub>

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

## Auto‑wiki (local, GitHub‑Wiki format)

Generates a project wiki with headless Claude (`claude -p`) — overview, architecture and
flows with mermaid diagrams. **`wiki-enable` generates the first wiki immediately** (so it's
never empty), then it stays current via `wiki-gen` and the end-of-session prompt. (A
`pre-push` hook on master/main also refreshes it, though in Conductor worktrees you'll
mostly use `wiki-gen`.) Local by default; publishing to the GitHub wiki is optional.

```bash
cd /path/to/your/repo && wiki-enable     # enable + generate the first wiki now (background)
wiki-gen                                  # regenerate / update on demand (no push needed)
WIKI_PUBLISH=1 wiki-gen                    # also push to the GitHub wiki
```

## Manage / uninstall headroom

```bash
hr install status | start | stop | restart
hr install remove        # remove service + routing (back to direct Anthropic)
```

⚠️ If the proxy is down, Claude sessions fail until `hr-on` (or `hr install remove`).

## Direct install (without this repo)

```bash
pip install "headroom-ai[all]" && headroom install apply --memory
claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail
```

carryover is more than a bundle: on top of a one‑command idempotent install, it adds its
own layer — cross‑tool memory wiring, the 🐴/🧠 status bar, the `/headroom` command, the
save‑to‑memory system (Stop hook + `mem-save`, since headroom has no `memory add` CLI),
the **auto‑wiki** (`claude -p` → GitHub‑Wiki docs with mermaid), and the `carryover`
routing toggle.

## Troubleshooting

- **Claude hangs / fails** → proxy down? `hr-status`; if so, `hr-on`.
- **No compression in a session** → `echo $ANTHROPIC_BASE_URL` empty = old session, restart it.
- **`pip install` fails** → use Python 3.13 (not 3.14): `brew install python@3.13`.
- **`headroom install apply` fails with a `launchctl` error** → run `install.sh` from your
  **real Terminal app**, not an SSH/automation/agent shell — macOS launchd (GUI domain) needs
  an interactive session. The installer keeps going regardless; just re-run apply in Terminal.
- **Don't delete `~/.headroom/venv`** before `hr install remove` — it backs the service.

---

# Español

## El problema

Ya no trabajas en una sola herramienta de IA — hoy Claude Code, mañana Cursor o Windsurf,
Conductor para trabajo en paralelo. Pero **el contexto no viaja contigo**: cada
herramienta, proyecto y sesión empieza de cero, así que re‑explicas el mismo código una y
otra vez. Encima cada agente **quema tokens** con contexto inflado, **olvida** todo entre
sesiones y tiende a **sobre‑diseñar** — y lo poco que vale la pena recordar nunca se
captura. Y dejar el arreglo listo a mano es engorroso y hay que repetirlo en cada Mac.

## La solución

Una capa local que hace que tu contexto **se traspase** (*carry over*) entre herramientas,
proyectos y sesiones:

- 🧠 **[headroom](https://github.com/chopratejas/headroom)** — proxy de compresión de
  contexto (60–95% menos tokens) + **memoria compartida y persistente** entre todos tus repos.
- 🐴 **[ponytail](https://github.com/DietrichGebert/ponytail)** — evita que el agente
  sobre‑diseñe (la solución más simple que funciona).
- 🕸 **Conocimiento estructurado** — facts + entidades tipadas + relaciones (un grafo
  consultable), indexado por el repo del que viene.
- 🔁 **Auto‑recall** — al iniciar una sesión en un repo, se inyecta como contexto lo que
  carryover sabe de ese repo (~0.5s, ~500 tokens, comprimido). Más `/recall` / `hr-recall` a demanda.
- 📊 **Dashboard local** (`co-dash`) — explora, busca, filtra y **gestiona** (borra/limpia)
  tu conocimiento, un grafo de relaciones, y tus wikis.
- 📄 **Wiki automática** al hacer push a master/main (un LLM escribe docs + diagramas mermaid).
- 💾 **Pregunta de "guardar lo importante"** al final · 🩺 **`carryover doctor`** ·
  toggle de routing **on/off** · `carryover wrap <tool>` para Cursor/Codex/…
- Barra de estado **🐴/🧠**, slash commands, aliases de terminal.

Un instalador idempotente, las **herramientas reales** (sin forks), **global por diseño** —
para que tu contexto te siga en vez de reiniciarse.

## Funciona con

La memoria compartida + compresión funcionan con cualquier agente que pase por el proxy local:

| Herramienta | Compresión + memoria compartida | Extras de Claude (🐴/🧠, `/headroom`, guardar en memoria) |
|-------------|:-------------------------------:|:---:|
| Claude Code | ✅ auto (instalador) | ✅ |
| Conductor | ✅ auto (corre Claude Code) | ✅ |
| Cursor | ✅ `headroom wrap cursor` (pega la config) | — |
| Windsurf / Devin | ✅ OpenAI‑compatible → base URL `http://127.0.0.1:8787/v1` | — |
| Codex / Copilot / Aider / Cline / Continue / Goose | ✅ `headroom wrap <tool>` | — |

### Configurarlo en cada herramienta (la parte cross-tool)

La memoria y la compresión se comparten a través del proxy local — cada herramienta solo
necesita que la apuntes a él **una vez**. (El proxy debe estar corriendo: revísalo con
`carryover doctor` o `hr-status`.)

- **Claude Code / Conductor** — automático. El `install.sh` ya dejó el routing; nada que hacer.
- **Cursor** — corre `carryover wrap cursor` (delega en `headroom wrap cursor`). Imprime la
  config exacta para pegar en los ajustes de modelo de Cursor (apunta su API base al proxy).
  Desde ahí, la IA de Cursor comparte la misma memoria + compresión que Claude.
- **Windsurf / Devin** — en sus ajustes de IA/modelo, pon una **OpenAI base URL** personalizada:
  `http://127.0.0.1:8787/v1`. (`carryover wrap windsurf` imprime este recordatorio.)
- **Codex / Aider / Cline / Continue / Goose / Copilot** — `carryover wrap <tool>`.
- **Cualquier otra herramienta compatible con OpenAI/Anthropic** — apunta su base URL al proxy:
  `http://127.0.0.1:8787` (estilo Anthropic) o `http://127.0.0.1:8787/v1` (estilo OpenAI).

Dos cosas a tener en cuenta:

- Los **comandos de terminal** (`co-dash`, `mem-save`, `hr-recall`, `carryover …`) funcionan en
  la terminal integrada de **cualquier** herramienta — viven en tu shell (`~/.zshrc`), no en una app.
- Los **slash commands** (`/headroom`, `/recall`, `/carryover`, `/wiki-enable`) y la barra 🐴/🧠
  son **solo de Claude Code**. Las demás herramientas reciben la memoria + compresión, no el slash UI.
- Una herramienta **no** se auto-detecta — comparte todo solo después de apuntarla al proxy una vez.

## Instalar

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

Instala **carryover standalone** — memoria, recall, wikis y el dashboard, con un store local
propio (`~/.carryover/memory.db`). Abre una terminal nueva (o `source ~/.zshrc`) y reinicia
Claude. Requisitos: macOS · Python 3 · Claude Code (`claude`) en el PATH.

**Integraciones opcionales** (opt-in):
```bash
bash ~/carryover/install.sh --with-headroom   # + headroom: proxy de compresión + backend de memoria compartido
bash ~/carryover/install.sh --with-ponytail   # + ponytail: plugin lazy-dev de Claude
bash ~/carryover/install.sh --full            # carryover + headroom + ponytail
```
- **headroom** convierte la memoria en un store *compartido* entre herramientas y añade el
  proxy de compresión (routing para Claude / Cursor / Codex…). Si está instalado, carryover lo
  usa solo; si no, usa el store propio. Necesita `brew install python@3.13` (la extensión
  Rust/PyO3 de headroom no compila en 3.14).
- **ponytail** es un plugin de terceros independiente — puramente opcional.

El instalador es **idempotente**: symlinkea los hooks, el dashboard, la barra y el comando
`/headroom`, y añade los aliases a `~/.zshrc`.

**¿No usas Claude Code?** carryover no es solo para Claude. El proxy de headroom es
compartido, así que la memoria + compresión aplican a **cualquier** herramienta una vez
corriendo — Cursor, Windsurf, Codex, Aider… solo apuntas cada una al proxy (mira
[Funciona con](#funciona-con) para el one-liner por herramienta). Los extras específicos
de Claude del `install.sh` (barra de estado, `/headroom`, los plugins) son para Claude
Code / Conductor; lo demás comparte el mismo proxy + memoria.

### Instalar solo el plugin de Claude (opcional)

¿Solo quieres los comandos de Claude + el prompt de guardar-en-memoria, sin el instalador completo?

```bash
claude plugin marketplace add Cfvillarroel/carryover
claude plugin install carryover@carryover
```

Igual necesitas el proxy de headroom para memoria/compresión:
`pip install "headroom-ai[all]" && headroom install apply --memory`.

## Alcance: global vs por‑repo

- **Global (una vez por Mac):** proxy + memoria + config de Claude. Global **por diseño** —
  es lo que hace que el contexto sea compartido entre todos los repos y herramientas.
- **Por repo / un conjunto:** la **wiki** — corre `wiki-enable` en cada repo que quieras
  (uno, varios o todos). Instala un hook `pre-push` solo ahí.
- La memoria es global pero con scope interno: `USER` = compartida entre repos, `project` =
  por workspace.

## Comandos fáciles

| Comando | Hace |
|---------|------|
| `hr` | CLI de headroom |
| `hr-status` | ¿proxy arriba/sano? |
| `hr-on` / `hr-off` | arrancar / parar el proxy |
| `hr-save` | tokens ahorrados |
| `hr-mem` | memorias guardadas |
| `hr-stats` | resumen de memoria |
| `hr-prune …` | purgar memorias (ej. `--older-than 30d --dry-run`) |
| `mem-save "texto"` | guardar una memoria a mano (o estructurada `--json`) |
| `co-recall <consulta>` | recordar conocimiento por keyword (alias: `hr-recall`) |
| `co-forget <consulta>` | borrar memorias por keyword, con confirmación (alias: `hr-forget`) |
| `co-wiki-enable` | activar la auto-wiki en el repo actual, genera la primera (alias: `wiki-enable`) |
| `co-wiki-gen` | regenerar la wiki del repo actual a demanda (alias: `wiki-gen`) |
| `co-wiki-prune` | podar entradas muertas del registro de wikis (alias: `wiki-prune`) |
| `co-dash` | dashboard local (overview, conocimiento + wikis) |
| `hr-dash` | dashboard de ahorro de headroom |
| `carryover status` | ¿routing activo? |
| `carryover on` / `off` | activar / desactivar el routing por el proxy (`--session` = solo esta shell) |
| `carryover doctor [--fix]` | chequeo de salud de todo el setup (y auto-arreglo con `--fix`) |
| `carryover update` | traer lo último de carryover + re-sincronizar esta máquina (sin copias a mano) |
| `carryover version` | ver versión instalada + si hay updates pendientes |
| `carryover persist` | que el proxy sobreviva al reboot (monta su servicio launchd) |
| `carryover wrap <tool>` | enrutar otra herramienta (Cursor, Codex…) por el proxy |
| `carryover uninstall` | quitar carryover (deja headroom + ponytail) |

**Auto-recall:** al iniciar una sesión en un repo, carryover inyecta *lo que ya sabe de ese
repo* como contexto — así el conocimiento vuelve solo, no solo se guarda.

Dentro de Claude (cualquier workspace): `/headroom`, `/carryover` (on/off/status), `/recall <consulta>`, `/wiki-enable`.
Barra de estado: **🐴** ponytail activo, **🧠** headroom activo.

## Paneles / dashboards (local)

Dos dashboards web locales — nada sale de tu máquina:

- **`co-dash`** → el dashboard propio de carryover en `http://127.0.0.1:8788` — explora tu
  **conocimiento** (facts, entidades tipadas, tags, con búsqueda + filtros), **agrupado por
  el repo** del que viene (o *general*), un **grafo de relaciones** auto-generado, y tus
  **wikis** (Markdown + mermaid). También es **gestor**: borra una memoria o limpia un repo
  entero con un clic. Lee/escribe tu DB en vivo; Ctrl-C para parar. (Capturas en la versión inglesa.)
- **`hr-dash`** → el dashboard de **ahorro** de headroom en `http://127.0.0.1:8787/dashboard`
  — tokens ahorrados, compresión, cache.

(Las wikis aparecen en `co-dash` después de correr `wiki-enable` en un repo y pushear a master/main.)

## Habilitar / deshabilitar el routing

El routing está **ON por defecto** en cada sesión nueva. Conmútalo sin desinstalar (el
proxy sigue corriendo):

```bash
carryover off            # las sesiones nuevas van directo a Anthropic (global)
carryover on             # vuelve a enrutar por headroom (global)
carryover off --session  # solo la terminal actual
carryover status         # ver estado
```

`off` es quirúrgico y reversible: quita la env de routing y le pone un guard al hook
SessionStart de headroom para que no la re‑inyecte; `on` lo revierte.

## Memoria

```bash
hr memory stats --db-path ~/.headroom/memory.db    # (los alias hr-* ya lo pasan)
hr memory list  --db-path ~/.headroom/memory.db --scope USER
mem-save "lo que quieras recordar"
```

> El CLI `headroom memory` usa por defecto `./headroom_memory.db` del directorio actual,
> **no** el store del proxy — por eso los aliases pasan `--db-path ~/.headroom/memory.db`.

## Wiki automática (local, formato GitHub Wiki)

Genera una wiki del proyecto con Claude headless (`claude -p`) — visión general,
arquitectura y flujos con diagramas mermaid. **`wiki-enable` genera la primera wiki de
inmediato** (así nunca queda vacía), y se mantiene al día con `wiki-gen` y el prompt de fin
de sesión. (Un hook `pre-push` en master/main también la refresca, aunque en worktrees de
Conductor usarás sobre todo `wiki-gen`.) Local por defecto; publicar al wiki de GitHub es opcional.

```bash
cd /ruta/a/tu/repo && wiki-enable        # activa + genera la primera wiki ahora (background)
wiki-gen                                  # regenerar / actualizar a demanda (sin push)
WIKI_PUBLISH=1 wiki-gen                    # además publicar al wiki de GitHub
```

## Gestionar / desinstalar headroom

```bash
hr install status | start | stop | restart
hr install remove        # quita servicio + routing (vuelve a Anthropic directo)
```

⚠️ Si el proxy se cae, las sesiones de Claude fallan hasta `hr-on` (o `hr install remove`).

## Instalación directa (sin este repo)

```bash
pip install "headroom-ai[all]" && headroom install apply --memory
claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail
```

carryover es más que un bundle: sobre un instalador idempotente de un comando, añade su
propia capa — memoria cross‑tool, la barra 🐴/🧠, el comando `/headroom`, el sistema de
guardar‑en‑memoria (hook Stop + `mem-save`, porque headroom no tiene `memory add`), la
**wiki automática** (`claude -p` → docs formato GitHub‑Wiki con mermaid) y el toggle de
routing `carryover`.

## Problemas comunes

- **Claude cuelga / falla** → ¿proxy caído? `hr-status`; si sí, `hr-on`.
- **No comprime en una sesión** → `echo $ANTHROPIC_BASE_URL` vacío = sesión vieja, reiníciala.
- **`pip install` falla** → usa Python 3.13 (no 3.14): `brew install python@3.13`.
- **`headroom install apply` falla con error de `launchctl`** → corre `install.sh` desde tu
  **Terminal real**, no desde SSH/automatización/un agente — launchd de macOS (dominio GUI)
  necesita sesión interactiva. El instalador continúa igual; re-corre apply en tu Terminal.
- **No borres `~/.headroom/venv`** antes de `hr install remove` — respalda el servicio.

---

## Credits · Créditos

carryover adds its own layer (cross‑tool memory wiring, the 🐴/🧠 status bar, `/headroom`,
the save‑to‑memory system, the auto‑wiki and the routing toggle) on top of two excellent
tools. Full credit to their creators — carryover construye encima de dos herramientas
excelentes; todo el crédito a sus creadores:

- **headroom** — [@chopratejas](https://github.com/chopratejas/headroom)
- **ponytail** — [@DietrichGebert](https://github.com/DietrichGebert/ponytail)

Licensed [MIT](LICENSE) · Licencia [MIT](LICENSE).
