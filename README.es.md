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

<strong><a href="README.md">English</a> · Español · <a href="#instalar">Instalar</a></strong>

</div>

---

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

- 🧠 **Memoria persistente y compartida** entre herramientas, repos y sesiones — un store
  local que es tuyo, con **recall semántico** (por significado) con scope a cada repo o a un
  grupo de repos relacionados.
- 🕸 **Conocimiento estructurado** — facts + entidades tipadas + relaciones (un grafo
  consultable), indexado por el repo del que viene.
- 🔁 **Auto‑recall** — al iniciar una sesión en un repo, se inyecta como contexto lo que
  carryover sabe de ese repo (~0.5s, ~500 tokens, comprimido). Más `/recall` / `co-recall` a demanda
  (solo el repo actual; `--all` para todos los repos).
- 📊 **Dashboard local** (`co-dash`) — explora, busca, filtra y **gestiona** (borra/limpia)
  tu conocimiento, un grafo de relaciones, y tus wikis.
- 📄 **Wiki automática** — un LLM escribe docs + diagramas mermaid (visión general, arquitectura,
  flujos + un catálogo de **Features**) y los actualiza de forma **incremental** (preserva las
  páginas existentes, añade solo lo que cambió) al hacer push a master/main.
- 💾 **Pregunta de "guardar lo importante"** al final · 🩺 **`carryover doctor`** ·
  toggle de routing **on/off** · `carryover wrap <tool>` para Cursor/Codex/…
- Barra de estado **🐴/🧠**, slash commands, aliases de terminal.

Un instalador idempotente, **100% local**, **standalone por defecto** — con integraciones
opcionales de headroom (store compartido + compresión de tokens) y ponytail — para que tu
contexto te siga en vez de reiniciarse.

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

- Los **comandos de terminal** (`co-dash`, `mem-save`, `co-recall`, `carryover …`) funcionan en
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
- **Por repo / un conjunto:** la **wiki** — corre `co-wiki-enable` en cada repo que quieras
  (uno, varios o todos). Instala un hook `pre-push` solo ahí.
- La memoria es global pero **con scope por repo**: recall devuelve por defecto las memorias
  del repo actual. Agrupa repos relacionados (ej. el front + back de un producto) para que
  compartan recall, listándolos en una línea de `~/.carryover/groups.conf` (separados por espacio/coma).

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
| `co-recall [--all] <consulta>` | recordar conocimiento **por significado** (semántico con headroom, keyword si no) — el grupo de este repo; `--all` para todos (alias: `hr-recall`) |
| `co-forget <consulta>` | borrar memorias por keyword, con confirmación (alias: `hr-forget`) |
| `co-supersede <viejo> <nuevo>` | marcar una memoria vieja como reemplazada para que recall la omita |
| `co-send <ws> <msg>` | dejar una nota a otro workspace de Conductor (`all` = broadcast) |
| `co-inbox [--peek]` | leer las notas dirigidas a este workspace (leerlas las consume; `--peek` no) |
| `co-wiki-enable` | activar la auto-wiki en el repo actual, genera la primera (alias: `wiki-enable`) |
| `co-wiki-gen` | actualizar la wiki del repo actual a demanda, incrementalmente (alias: `wiki-gen`) |
| `co-wiki-prune` | podar entradas muertas del registro de wikis (alias: `wiki-prune`) |
| `co-dash` | dashboard local (overview, conocimiento + wikis) |
| `co-backup` / `co-restore <file>` | respaldar / restaurar todas las memorias (llevarlas a otra máquina) |
| `co-mcp` | correr el MCP server de carryover (usar la memoria desde Cursor, Claude Desktop, cualquier cliente MCP) |
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
repo* como contexto — así el conocimiento vuelve solo, no solo se guarda. Cada recall
(automático al iniciar sesión o con `/recall`) se cuenta por memoria, así `co-dash` muestra
qué memorias se reutilizan de verdad (la insignia ♻).

Dentro de Claude (cualquier workspace): `/headroom`, `/carryover` (on/off/status), `/recall [--all] <consulta>`, `/wiki-enable`.
Barra de estado: **🐴** ponytail activo, **🧠** headroom activo.

## Mensajes entre workspaces

¿Corres varios workspaces de Conductor a la vez? Comparten un único store de memoria, así que
pueden dejarse notas entre sí — "mergeé X, rebasea", "build roto, no hagas pull". Cada workspace
responde a varios nombres: su **codename** (la carpeta del worktree, p.ej. `paris`, `sarajevo`) —
la **dirección estable y duradera**; su **nombre de workspace** (la etiqueta que muestra Conductor,
que reescribe al nombre del branch/tarea cuando interactúas con él la primera vez); y su **nombre de
proyecto** (el encabezado bajo el que vive, p.ej. `proyectate-back`). Manda al **nombre de proyecto**
para llegar a cualquier workspace de ese proyecto — ideal para un par frontend↔backend entre repos —
o al **codename** para uno específico. Todos son globales, no atados a un repo. Direcciona por
**codename o nombre de proyecto** (ambos estables ante renombrados); un título que Conductor ya
renombró puede no resolver.

- `co-send <nombre> <mensaje>` — dejar una nota a otro workspace o proyecto entero. `all` hace broadcast.
- `co-inbox` — leer las notas dirigidas a **este** workspace (más los broadcasts). Leerlas las
  consume para que no se repitan; `co-inbox --peek` lee sin consumir.
- `co-connect <nombre>` — vincular dos workspaces/proyectos en ambos sentidos (persistente). Luego
  `co-say <mensaje>` envía a **todos** los conectados sin reteclear nombres; `co-connections` los
  lista y `co-disconnect <nombre>` desconecta. Útil para un par frontend/backend entre repos.
- `/handoff <nombre>` (en el chat) — traspasar una tarea: el agente escribe un resumen (qué se hizo,
  qué falta, archivos clave) y lo manda a ese workspace/proyecto. También se sugiere solo cuando un
  turno menciona un workspace conectado.
- `/handover <nombre>` (en el chat; en shell `co-handover`) — como `/handoff`, pero una **transferencia
  activa**: el destino además recibe una notificación de escritorio y, cuando se le entrega el inbox,
  se le dice al agente que **ejecute la tarea ahora**, no que solo la lea. Conductor no puede despertar
  un workspace inactivo, así que la notificación es tu señal para abrirlo; ahí la tarea corre en su
  primer turno.
- **Entrega automática:** las notas pendientes se inyectan en el contexto del workspace cuando su
  sesión **arranca**, **antes de cada uno de tus turnos** (`UserPromptSubmit`), y **cuando el agente
  termina un turno** (`Stop`) — así una nota que llega mientras trabaja se recoge en cuanto queda
  libre, sin interrumpirlo a media tarea. Se entrega una sola vez y se marca leída. La entrega por
  `Stop` tiene un freno anti-bucle (`stop_hook_active`) para que dos workspaces conectados no entren
  en ping-pong. (Sigue siendo pull: un agente totalmente inactivo —que ya te devolvió el control—
  la recibe en su siguiente turno.)

Solo pull, por diseño: a un agente *en marcha* no se le interrumpe — las notas llegan cuando su
sesión vuelve a arrancar, o cuando ejecutas `co-inbox`. Los mensajes viven en su propio buzón
`@<workspace>`, así que nunca aparecen en el recall normal ni ensucian el conocimiento de un repo.

**Cada workspace lo tiene automáticamente.** Los comandos, los hooks de entrega y el buzón compartido
se instalan una vez a nivel de usuario (con `install.sh`, o con el plugin de Claude), así que cualquier
workspace nuevo de Conductor — incluido un worktree recién creado — puede enviar y recibir sin
configuración por workspace; su dirección sale del entorno de Conductor. La única excepción es
`co-connect`/`co-say`: un workspace nuevo no tiene enlaces hasta que lo conectas una vez (los dirigidos
`co-send`/`/handoff`/`/handover` no necesitan ninguno).

**Pruébalo** — dos workspaces del mismo proyecto, `paris` y `surabaya`:

```sh
# en el workspace 'paris' — dejar notas a otro workspace
$ co-send surabaya "el endpoint /v2 ya está mergeado, rebasea"
$ co-send all       "build roto en master, no hagáis pull"

# en el workspace 'surabaya' — leerlas
$ co-inbox --peek                 # mirar sin consumir
📬 from paris: el endpoint /v2 ya está mergeado, rebasea
📬 from paris: build roto en master, no hagáis pull
$ co-inbox                        # leer + consumir (no se repiten)
📬 from paris: el endpoint /v2 ya está mergeado, rebasea
📬 from paris: build roto en master, no hagáis pull
$ co-inbox
(no messages)
```

O simplemente **arranca una sesión nueva** en `surabaya` — las notas pendientes aparecen en su
contexto inicial automáticamente:

```
## 📬 messages for this workspace
- **from paris:** el endpoint /v2 ya está mergeado, rebasea
- **from paris:** build roto en master, no hagáis pull
```

### Conectar workspaces (p.ej. frontend ↔ backend, incluso entre repos)

Vincula dos workspaces una vez, y luego habla sin reteclear nombres largos:

```sh
# en el workspace de frontend
co-connect proyectate-back-main      # 🔗 vínculo bidireccional, persistente
co-say "el contrato de /users cambió: email ahora es obligatorio"   # → a todos los conectados
co-connections                       # 🔗 connected to: proyectate-back-main
```

El workspace de backend lo recibe como cualquier otra nota (al arrancar, en su próximo turno, o con
`co-inbox`). `co-disconnect proyectate-back-main` desconecta.

(Los comandos nuevos llegan con `carryover update`; hasta entonces un workspace puede usarlos desde
su checkout: `python3 claude/hooks/co-mem send <ws> "<msg>"`.)

## Playbooks (`!macros`)

Procedimientos reusables que disparás escribiendo `!nombre` en cualquier prompt de Claude — como los
playbooks de Devin. Un playbook es un archivo markdown en `~/.carryover/playbooks/`; cuando tu prompt
contiene `!grill`, un hook `UserPromptSubmit` inyecta ese archivo y el agente sigue el procedimiento.

```
!grill agregar login con Google al checkout
```

- **Correr:** escribí `!<nombre>` en cualquier parte de un prompt.
- **Listar:** `/playbooks` (en el chat) o `co-playbooks` (shell).
- **Gestionar:** la pestaña **📓 Playbooks** del dashboard (`co-dash`) — crear, editar, borrar — o soltá
  un `.md` en `~/.carryover/playbooks/`. Las ediciones del dashboard sobreviven a `carryover update`.
- **Modo (opcional):** una línea `mode:` en el frontmatter del playbook — `plan` (investigar, no
  implementar) o `interrogate` (una pregunta a la vez) — antepone esa directiva al correr el macro.

Viene con `grill` (un playbook de interrogación de planes). Los playbooks se encadenan — `!grill`
puede derivar a `!feature`, `!bugfix`, … cuando los agregues.

## Paneles / dashboards (local)

Dos dashboards web locales — nada sale de tu máquina:

- **`co-dash`** → el dashboard propio de carryover en `http://127.0.0.1:8788` — explora tu
  **conocimiento** (facts, entidades tipadas, tags, con búsqueda + filtros), con una
  **insignia de reúso** (♻ N = veces recordada en contexto) en cada memoria, **agrupado por
  el repo** del que viene (o *general*), un **grafo de relaciones** auto-generado, y tus
  **wikis** (Markdown + mermaid). También es **gestor**: borra una memoria o limpia un repo
  entero con un clic. Lee/escribe tu DB en vivo; Ctrl-C para parar. (Capturas en la versión inglesa.)
- **`hr-dash`** → el dashboard de **ahorro** de headroom en `http://127.0.0.1:8787/dashboard`
  — tokens ahorrados, compresión, cache.

(Las wikis aparecen en `co-dash` después de correr `co-wiki-enable` en un repo y pushear a master/main.)

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

**El recall es semántico** (por significado, vía el embedder de headroom) y **con scope al
grupo del repo actual**; `co-recall --all` busca en todo. `co-backup` / `co-restore` llevan el
store completo a otra máquina. `co-supersede <viejo> <nuevo>` oculta una memoria obsoleta para
que gane el dato actualizado.

## Usar la memoria desde otras herramientas (MCP)

La memoria de carryover es también un **servidor MCP**, así que cualquier cliente MCP —Cursor,
Claude Desktop, Windsurf— puede `recall` y `remember` sobre el mismo store, no solo Claude Code:

```json
{ "mcpServers": {
    "carryover": { "command": "~/.headroom/venv/bin/python", "args": ["~/.carryover/co-mcp.py"] }
} }
```

¿Sin headroom? Usa `python3` como `command` (el recall cae a keyword). Tools: `recall`
(semántico, con scope por repo) y `remember`. La mayoría de clientes no expanden `~` — usa
rutas absolutas.

Corre **enteramente en tu máquina**: el cliente lo lanza como un subproceso local y se
comunican por stdio — sin red, sin puerto, sin telemetría. Tu conocimiento nunca sale de tu equipo.

📖 **Guía completa por cliente** (Claude Desktop / Cursor / Windsurf), scope por repo, ejemplos
y troubleshooting: **[docs/MCP.md](docs/MCP.md)**.

## Wiki automática (local, formato GitHub Wiki)

Genera una wiki del proyecto con Claude headless (`claude -p`) — visión general,
arquitectura, flujos y un catálogo de **Features**, con diagramas mermaid. Se actualiza de
forma **incremental**: cada corrida preserva las páginas existentes y las complementa con lo
que cambió, así la wiki **crece** en vez de regenerarse desde cero. **`co-wiki-enable` genera
la primera wiki de inmediato** (así nunca queda vacía), y se mantiene al día con `co-wiki-gen`
y el prompt de fin de sesión. (Un hook `pre-push` en master/main también integra los cambios,
aunque en worktrees de Conductor usarás sobre todo `co-wiki-gen`.) Local por defecto; publicar
al wiki de GitHub es opcional.

```bash
cd /ruta/a/tu/repo && co-wiki-enable     # activa + genera la primera wiki ahora (background)
co-wiki-gen                               # actualizar la wiki incrementalmente a demanda (sin push)
WIKI_PUBLISH=1 co-wiki-gen                # además publicar al wiki de GitHub
```

<details>
<summary><b>Gestionar / desinstalar headroom</b></summary>

```bash
hr install status | start | stop | restart
hr install remove        # quita servicio + routing (vuelve a Anthropic directo)
```

⚠️ Si el proxy se cae, las sesiones de Claude fallan hasta `hr-on` (o `hr install remove`).

</details>

<details>
<summary><b>Instalación directa (sin este repo)</b></summary>

```bash
pip install "headroom-ai[all]" && headroom install apply --memory
claude plugin marketplace add DietrichGebert/ponytail && claude plugin install ponytail@ponytail
```

carryover es más que un bundle: sobre un instalador idempotente de un comando, añade su
propia capa — memoria cross‑tool, la barra 🐴/🧠, el comando `/headroom`, el sistema de
guardar‑en‑memoria (hook Stop + `mem-save`, porque headroom no tiene `memory add`), la
**wiki automática** (`claude -p` → docs formato GitHub‑Wiki con mermaid) y el toggle de
routing `carryover`.

</details>

<details>
<summary><b>Problemas comunes</b></summary>

- **Claude cuelga / falla** → ¿proxy caído? `hr-status`; si sí, `hr-on`.
- **No comprime en una sesión** → `echo $ANTHROPIC_BASE_URL` vacío = sesión vieja, reiníciala.
- **`pip install` falla** → usa Python 3.13 (no 3.14): `brew install python@3.13`.
- **`headroom install apply` falla con error de `launchctl`** → corre `install.sh` desde tu
  **Terminal real**, no desde SSH/automatización/un agente — launchd de macOS (dominio GUI)
  necesita sesión interactiva. El instalador continúa igual; re-corre apply en tu Terminal.
- **No borres `~/.headroom/venv`** antes de `hr install remove` — respalda el servicio.

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
