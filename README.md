# 💼 carryover

> One command to set up a **leaner, cheaper, memory-equipped** Claude Code + Conductor environment on macOS.
> Un comando para montar un entorno Claude Code + Conductor **más barato, ligero y con memoria**, en macOS.

**Languages / Idiomas:** [English](#english) · [Español](#español)

---

## Why this exists · Por qué existe

**The problem (EN).** You don't work in a single AI tool anymore — Claude Code one day,
Cursor or Windsurf the next, Conductor for parallel work. But **context doesn't travel
with you**: every tool, project and session starts from zero, so you re‑explain the same
codebase over and over. On top of that each agent **burns tokens** on bloated context,
**forgets** everything between sessions, and tends to **over‑engineer** — and the few
things worth remembering never get captured. Wiring up the fix by hand is fiddly and
has to be redone on every machine.

**The fix — carryover (EN).** A local layer that makes your context **carry over** across
tools, projects and sessions: one **shared, persistent memory** every agent routes
through; **60–95% less context** (fit more, pay less); a **leaner** agent; **auto‑docs**
(a wiki) on every push; and a **save‑what‑mattered prompt** at the end of each session.
One idempotent install, the **real upstream tools** (no forks), **global by design** — so
your context follows you instead of resetting.

**El problema (ES).** Ya no trabajas en una sola herramienta de IA — hoy Claude Code,
mañana Cursor o Windsurf, Conductor para trabajo en paralelo. Pero **el contexto no
viaja contigo**: cada herramienta, proyecto y sesión empieza de cero, así que
re‑explicas el mismo código una y otra vez. Encima cada agente **quema tokens** con
contexto inflado, **olvida** todo entre sesiones y tiende a **sobre‑diseñar** — y lo poco
que vale la pena recordar nunca se captura. Y dejar el arreglo listo a mano es engorroso
y hay que repetirlo en cada Mac.

**La solución — carryover (ES).** Una capa local que hace que tu contexto **se traspase**
(*carry over*) entre herramientas, proyectos y sesiones: una **memoria compartida y
persistente** por la que pasan todos los agentes; **60–95% menos contexto** (cabe más,
pagas menos); un agente más **ligero**; **docs automáticas** (una wiki) en cada push; y
una **pregunta de "guardar lo importante"** al final de cada sesión. Un instalador
idempotente, las **herramientas reales** (sin forks), **global por diseño** — para que tu
contexto te siga en vez de reiniciarse.

What you get / Qué incluye:

- 🧠 [**headroom**](https://github.com/chopratejas/headroom) — context compression proxy + cross‑repo memory.
- 🐴 [**ponytail**](https://github.com/DietrichGebert/ponytail) — plugin that forces the simplest solution.
- Status bar **🐴/🧠**, `/headroom` command, terminal aliases.
- **Auto‑wiki** on push to master/main (LLM writes docs + mermaid diagrams).
- **End‑of‑session prompt** to save what you learned to memory.

---

## Works with · Funciona con

The shared memory + token compression work with **any agent that routes through the
local headroom proxy** — so context follows you from tool to tool instead of starting
over. La memoria compartida y la compresión funcionan con cualquier agente que pase por
el proxy local de headroom.

| Tool | Compression + shared memory | Claude extras (🐴/🧠, `/headroom`, save‑to‑memory) |
|------|:---------------------------:|:---:|
| Claude Code | ✅ auto (installer) | ✅ |
| Conductor | ✅ auto (corre Claude Code) | ✅ |
| Cursor | ✅ `headroom wrap cursor` (pega la config) | — |
| Windsurf / Devin | ✅ OpenAI‑compatible → base URL `http://127.0.0.1:8787/v1` | — |
| Codex / Copilot / Aider / Cline / Continue / Goose | ✅ `headroom wrap <tool>` | — |

The 🐴/🧠 status bar, `/headroom` and the save‑to‑memory prompt are Claude Code
features; other tools still share the **same memory store**. · La barra 🐴/🧠,
`/headroom` y el guardado en memoria son de Claude Code; las demás herramientas igual
comparten el **mismo store de memoria**.

## Install scope · Alcance de instalación

- **Global (once per Mac · una vez por Mac):** headroom proxy + memory + Claude config.
  By design / a propósito — es lo que hace que el contexto sea compartido entre todos
  los repos y herramientas.
- **Per repo / a set of repos · un repo o varios:** the **wiki** capability — run
  `wiki-enable` in each repo you want (one, several or all); installs a `pre-push` hook
  only there.
- Memory is global but internally scoped · La memoria es global pero con scope interno:
  `USER` = compartida entre repos, `project` = por workspace.

## Direct install · Instalación directa

You don't need this repo — install the tools directly. No necesitas este repo, puedes
instalar las herramientas directamente:

```bash
pip install "headroom-ai[all]" && headroom install apply --memory   # proxy + memoria global
claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail
```

This repo just bundles that into one idempotent command + the wiki, status bar and
memory prompt. Este repo solo lo empaqueta en un comando idempotente + la wiki, la
barra de estado y el prompt de memoria.

---

# English

## Requirements

macOS · `brew install python@3.13` · Claude Code (`claude`) in your PATH.

## Install

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

Then open a new terminal (or `source ~/.zshrc`) and restart Claude.

The installer is **idempotent** (safe to re‑run) and:

1. Installs **headroom** in `~/.headroom/venv` (Python 3.13) and runs
   `headroom install apply --memory` → persistent proxy (launchd), Claude routing, shared memory.
2. Installs the **ponytail** and **headroom** Claude Code plugins.
3. **Symlinks** `~/.claude/statusline.sh`, `~/.claude/commands/headroom.md` and the
   memory hook to this repo, and sets the `statusLine` in `~/.claude/settings.json`.
4. Adds headroom **aliases** and a `wiki-enable` alias to `~/.zshrc`.

> ⚠️ headroom does **not** build on Python 3.14 (Rust/PyO3). Use 3.13.

## What gets installed

| File in repo | Symlink / effect | Purpose |
|---|---|---|
| `claude/statusline.sh` | `~/.claude/statusline.sh` | status bar 🐴 / 🧠 |
| `claude/commands/headroom.md` | `~/.claude/commands/headroom.md` | `/headroom` slash command |
| `claude/hooks/headroom-mem-prompt.sh` | `~/.claude/hooks/...` + Stop hook | "save to memory?" at session end |
| `zshrc.snippet` | appended to `~/.zshrc` | aliases `hr`, `hr-mem`, … |
| `GUIA.md` | `~/.headroom/GUIA.md` | headroom usage guide |

Symlinks mean editing the repo file applies live. **Not versioned** (on purpose):
the headroom venv (~1.9 GB, rebuilt by pip) and memory `.db` files (personal data).

## Easy commands

| Alias | Does |
|---|---|
| `hr` | headroom CLI |
| `hr-status` | is the proxy up/healthy? |
| `hr-mem` | stored memories |
| `hr-stats` | memory summary |
| `hr-save` | tokens saved |
| `hr-on` / `hr-off` | start / stop proxy |

Inside Claude (any workspace): `/headroom` → proxy + memory + savings summary;
`/headroom list --scope USER`, `/headroom show <id>` pass args to `headroom memory`.

Status bar: **🐴** ponytail active (with level, e.g. `🐴 LITE`), **🧠** headroom active.
Change emojis in `claude/statusline.sh` (`PONY_EMOJI` / `HR_EMOJI`).

## Auto‑wiki (local, GitHub‑Wiki format)

Generates/updates a project wiki **on push to master/main**, using headless Claude
(`claude -p`) to understand the diff and draw mermaid diagrams. Local by default;
publishing to the GitHub wiki is optional.

```bash
cd /path/to/your/project
wiki-enable                 # or: bash ~/carryover/wiki/install-wiki.sh
```

Installs a `pre-push` hook + `wiki/gen-wiki.sh`. On push it regenerates `wiki/`
(Home, Architecture, Flows with mermaid, Changelog) in the background.
Manual run: `bash wiki/gen-wiki.sh`. Publish: `WIKI_PUBLISH=1 bash wiki/gen-wiki.sh`.

## Save‑to‑memory prompt

After a session that edited files, a `Stop` hook asks whether to save what you learned
to headroom memory. Installed automatically. Memory is shared across all your repos
(`hr memory list --scope USER`).

## Manage / uninstall headroom

```bash
hr install status | start | stop | restart
hr install remove        # removes service + routing
```

⚠️ If the proxy goes down, Claude sessions fail until `hr-on` (or `hr install remove`).

## Update

```bash
git -C ~/carryover pull && bash ~/carryover/install.sh
```

---

# Español

## Requisitos

macOS · `brew install python@3.13` · Claude Code (`claude`) en el PATH.

## Instalar

```bash
git clone https://github.com/Cfvillarroel/carryover.git ~/carryover
bash ~/carryover/install.sh
```

Luego abre una terminal nueva (o `source ~/.zshrc`) y reinicia Claude.

El instalador es **idempotente** (re‑ejecutable) y:

1. Instala **headroom** en `~/.headroom/venv` (Python 3.13) y corre
   `headroom install apply --memory` → proxy persistente (launchd), routing de Claude, memoria compartida.
2. Instala los plugins **ponytail** y **headroom** de Claude Code.
3. **Symlinks** de `~/.claude/statusline.sh`, `~/.claude/commands/headroom.md` y el
   hook de memoria a este repo, y fija el `statusLine` en `~/.claude/settings.json`.
4. Añade los **aliases** de headroom y un alias `wiki-enable` a `~/.zshrc`.

> ⚠️ headroom **no** compila en Python 3.14 (Rust/PyO3). Usa 3.13.

## Qué deja instalado

| Archivo en el repo | Symlink / efecto | Para qué |
|---|---|---|
| `claude/statusline.sh` | `~/.claude/statusline.sh` | barra de estado 🐴 / 🧠 |
| `claude/commands/headroom.md` | `~/.claude/commands/headroom.md` | slash command `/headroom` |
| `claude/hooks/headroom-mem-prompt.sh` | `~/.claude/hooks/...` + hook Stop | "¿guardar en memoria?" al terminar |
| `zshrc.snippet` | anexado a `~/.zshrc` | aliases `hr`, `hr-mem`, … |
| `GUIA.md` | `~/.headroom/GUIA.md` | guía de uso de headroom |

Al ser symlinks, editar el archivo del repo se refleja en vivo. **No se versiona**
(a propósito): el venv de headroom (~1.9 GB, se reconstruye con pip) y los `.db` de memoria.

## Comandos fáciles

| Alias | Hace |
|---|---|
| `hr` | CLI de headroom |
| `hr-status` | ¿proxy arriba/sano? |
| `hr-mem` | memorias guardadas |
| `hr-stats` | resumen de memoria |
| `hr-save` | tokens ahorrados |
| `hr-on` / `hr-off` | arrancar / parar el proxy |

Dentro de Claude (cualquier workspace): `/headroom` → resumen de proxy + memoria +
ahorro; `/headroom list --scope USER`, `/headroom show <id>` pasan args a `headroom memory`.

Barra de estado: **🐴** ponytail activo (con nivel, ej. `🐴 LITE`), **🧠** headroom activo.
Cambia los emojis en `claude/statusline.sh` (`PONY_EMOJI` / `HR_EMOJI`).

## Wiki automática (local, formato GitHub Wiki)

Genera/actualiza una wiki del proyecto **al hacer push a master/main**, usando Claude
headless (`claude -p`) para entender el diff y dibujar diagramas mermaid. Local por
defecto; publicar al wiki de GitHub es opcional.

```bash
cd /ruta/a/tu/proyecto
wiki-enable                 # o: bash ~/carryover/wiki/install-wiki.sh
```

Instala un hook `pre-push` + `wiki/gen-wiki.sh`. Al pushear regenera `wiki/`
(Home, Architecture, Flows con mermaid, Changelog) en segundo plano.
A mano: `bash wiki/gen-wiki.sh`. Publicar: `WIKI_PUBLISH=1 bash wiki/gen-wiki.sh`.

## Pregunta de "guardar en memoria"

Tras una sesión con ediciones, un hook `Stop` pregunta si guardar lo aprendido en la
memoria de headroom. Se instala automáticamente. La memoria es compartida entre todos
tus repos (`hr memory list --scope USER`).

## Gestionar / desinstalar headroom

```bash
hr install status | start | stop | restart
hr install remove        # quita servicio + routing
```

⚠️ Si el proxy se cae, las sesiones de Claude fallan hasta `hr-on` (o `hr install remove`).

## Actualizar

```bash
git -C ~/carryover pull && bash ~/carryover/install.sh
```

---

## Credits · Créditos

This is only an installation/glue layer. The real work is by:

- **headroom** — [@chopratejas](https://github.com/chopratejas) · https://github.com/chopratejas/headroom
- **ponytail** — [@DietrichGebert](https://github.com/DietrichGebert) · https://github.com/DietrichGebert/ponytail

Huge thanks to their creators / Mil gracias a sus creadores. Licensed [MIT](LICENSE).
