<div align="center">
<pre>
 ██████╗ █████╗ ██████╗ ██████╗ ██╗   ██╗ ██████╗ ██╗   ██╗███████╗██████╗
██╔════╝██╔══██╗██╔══██╗██╔══██╗╚██╗ ██╔╝██╔═══██╗██║   ██║██╔════╝██╔══██╗
██║     ███████║██████╔╝██████╔╝ ╚████╔╝ ██║   ██║██║   ██║█████╗  ██████╔╝
██║     ██╔══██║██╔══██╗██╔══██╗  ╚██╔╝  ██║   ██║╚██╗ ██╔╝██╔══╝  ██╔══██╗
╚██████╗██║  ██║██║  ██║██║  ██║   ██║   ╚██████╔╝ ╚████╔╝ ███████╗██║  ██║
 ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝    ╚═════╝   ╚═══╝  ╚══════╝╚═╝  ╚═╝
</pre>

💼 <strong>Your context, carried across AI coding tools.</strong>

<sub>shared persistent memory · 60–95% fewer tokens · leaner agent · auto-wiki · save-to-memory<br/>
Claude Code · Cursor · Windsurf · Conductor — one install · 100% local</sub>

<p>
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
- Status bar **🐴/🧠**, `/headroom` command, terminal aliases.
- **Auto‑wiki** on push to master/main (an LLM writes docs + mermaid diagrams).
- **Save‑what‑mattered prompt** at the end of each session.

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

## Install

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

Requirements: macOS · `brew install python@3.13` · Claude Code (`claude`) on PATH.
Then open a new terminal (or `source ~/.zshrc`) and restart Claude.

The installer is **idempotent** and:
1. installs headroom in `~/.headroom/venv` (Python 3.13) + `headroom install apply --memory`
   → persistent proxy (launchd), Claude routing, shared memory;
2. installs the `ponytail` and `headroom` Claude plugins;
3. symlinks the status bar, `/headroom` command and hooks, sets `statusLine`;
4. adds aliases to `~/.zshrc`.

> ⚠️ headroom doesn't build on Python 3.14 (Rust/PyO3 extension) — the venv uses 3.13.

## Scope: global vs per‑repo

- **Global (once per Mac):** headroom proxy + memory + Claude config. Global **by
  design** — that's what makes context shared across all repos and tools.
- **Per repo / a set of repos:** the **wiki** capability — run `wiki-enable` in each repo
  you want (one, several or all). It installs a `pre-push` hook there only.
- Memory is global but internally scoped: `USER` = shared across repos, `project` = per
  workspace.

## Easy commands

| Alias | Does |
|-------|------|
| `hr` | headroom CLI |
| `hr-status` | proxy up / healthy? |
| `hr-mem` | stored memories |
| `hr-stats` | memory summary |
| `hr-save` | tokens saved |
| `mem-save "text"` | save a memory by hand |
| `hr-on` / `hr-off` | start / stop the proxy |

Inside Claude (any workspace): `/headroom` → proxy + memory + savings summary.
Status bar: **🐴** ponytail active, **🧠** headroom active.

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

Regenerates a project wiki **on push to master/main** using headless Claude (`claude -p`)
to read the diff and draw mermaid diagrams. Local by default; publishing to the GitHub
wiki is optional.

```bash
cd /path/to/your/repo && wiki-enable     # installs a pre-push hook + wiki/gen-wiki.sh
bash wiki/gen-wiki.sh                     # regenerate by hand
WIKI_PUBLISH=1 bash wiki/gen-wiki.sh      # also push to the GitHub wiki
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
- Barra de estado **🐴/🧠**, comando `/headroom`, aliases de terminal.
- **Wiki automática** al hacer push a master/main (un LLM escribe docs + diagramas mermaid).
- **Pregunta de "guardar lo importante"** al final de cada sesión.

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

## Instalar

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

Requisitos: macOS · `brew install python@3.13` · Claude Code (`claude`) en el PATH.
Luego abre una terminal nueva (o `source ~/.zshrc`) y reinicia Claude.

El instalador es **idempotente** y:
1. instala headroom en `~/.headroom/venv` (Python 3.13) + `headroom install apply --memory`
   → proxy persistente (launchd), routing de Claude, memoria compartida;
2. instala los plugins `ponytail` y `headroom` en Claude;
3. symlinkea la barra de estado, el comando `/headroom` y los hooks, fija el `statusLine`;
4. añade los aliases a `~/.zshrc`.

> ⚠️ headroom no compila en Python 3.14 (extensión Rust/PyO3) — el venv usa 3.13.

## Alcance: global vs por‑repo

- **Global (una vez por Mac):** proxy + memoria + config de Claude. Global **por diseño** —
  es lo que hace que el contexto sea compartido entre todos los repos y herramientas.
- **Por repo / un conjunto:** la **wiki** — corre `wiki-enable` en cada repo que quieras
  (uno, varios o todos). Instala un hook `pre-push` solo ahí.
- La memoria es global pero con scope interno: `USER` = compartida entre repos, `project` =
  por workspace.

## Comandos fáciles

| Alias | Hace |
|-------|------|
| `hr` | CLI de headroom |
| `hr-status` | ¿proxy arriba/sano? |
| `hr-mem` | memorias guardadas |
| `hr-stats` | resumen de memoria |
| `hr-save` | tokens ahorrados |
| `mem-save "texto"` | guardar una memoria a mano |
| `hr-on` / `hr-off` | arrancar / parar el proxy |

Dentro de Claude (cualquier workspace): `/headroom` → resumen de proxy + memoria + ahorro.
Barra de estado: **🐴** ponytail activo, **🧠** headroom activo.

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

Regenera una wiki del proyecto **al hacer push a master/main** usando Claude headless
(`claude -p`) para leer el diff y dibujar diagramas mermaid. Local por defecto; publicar al
wiki de GitHub es opcional.

```bash
cd /ruta/a/tu/repo && wiki-enable        # instala un hook pre-push + wiki/gen-wiki.sh
bash wiki/gen-wiki.sh                     # regenerar a mano
WIKI_PUBLISH=1 bash wiki/gen-wiki.sh      # además publicar al wiki de GitHub
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
