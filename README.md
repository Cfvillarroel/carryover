# claude-agent-setup

Monta de un tirón un entorno de agentes para **Claude Code** + **Conductor**:

- [**headroom**](https://github.com/chopratejas/headroom) — capa de compresión de
  contexto (menos tokens) + memoria compartida entre repos.
- [**ponytail**](https://github.com/DietrichGebert/ponytail) — plugin que fuerza la
  solución más simple y mínima.
- Barra de estado con **🐴 ponytail / 🧠 headroom**, slash command `/headroom` y
  aliases de terminal.

No reempaqueta esas herramientas: instala las reales (headroom por pip, ponytail por
plugin) y enlaza la config mediante symlinks a este repo.

> macOS · Apple Silicon/Intel. Requiere `brew install python@3.13` y Claude Code (`claude`) en el PATH.

---

## Instalar

```bash
git clone https://github.com/Cfvillarroel/claude-agent-setup.git ~/claude-agent-setup
bash ~/claude-agent-setup/install.sh
```

Tras instalar: abre una terminal nueva (o `source ~/.zshrc`) y reinicia Claude.

El `install.sh` es **idempotente** (re-ejecutable) y hace:

1. **headroom** en `~/.headroom/venv` (Python 3.13) + `headroom install apply --memory`
   → proxy persistente (launchd), routing de Claude y memoria compartida entre repos.
2. **plugins** `ponytail` y `headroom` en Claude Code.
3. **symlinks** de `~/.claude/statusline.sh` y `~/.claude/commands/headroom.md` a este
   repo, y fija el `statusLine` en `~/.claude/settings.json`.
4. **aliases** de headroom en `~/.zshrc`.

> ⚠️ headroom **no** instala en Python 3.14 (extensión Rust/PyO3). Por eso el venv usa 3.13.

---

## Qué deja instalado

| Archivo en el repo | Symlink / efecto | Para qué |
|--------------------|------------------|----------|
| `claude/statusline.sh` | `~/.claude/statusline.sh` | barra de estado 🐴 / 🧠 |
| `claude/commands/headroom.md` | `~/.claude/commands/headroom.md` | slash command `/headroom` |
| `zshrc.snippet` | anexado a `~/.zshrc` | aliases `hr`, `hr-mem`, … |
| `GUIA.md` | `~/.headroom/GUIA.md` | guía de uso de headroom |

Como son **symlinks**, editar el archivo en el repo se refleja en vivo.

`settings.example.toml` es un ejemplo de settings de usuario de Conductor
(`~/.conductor/settings.toml`) — opcional, cópialo y ajústalo a tu gusto.

---

## Comandos fáciles

### Aliases (terminal)

| Alias | Hace |
|-------|------|
| `hr` | CLI base de headroom |
| `hr-status` | ¿proxy arriba/sano? |
| `hr-mem` | memorias guardadas |
| `hr-stats` | resumen de memoria |
| `hr-save` | tokens ahorrados |
| `hr-on` / `hr-off` | arrancar / parar el proxy |

### Dentro de Claude (cualquier workspace)

- `/headroom` → resumen de proxy + memoria + ahorro.
- `/headroom list --scope USER` · `/headroom show <id>` → pasa args a `headroom memory`.

### Barra de estado

- **🐴** ponytail activo (con nivel si no es full, ej. `🐴 LITE`).
- **🧠** headroom activo (proxy respondiendo en `:8787`).
- Cambiar emojis: edita `PONY_EMOJI` / `HR_EMOJI` arriba de `claude/statusline.sh`.

---

## Consultar la memoria

```bash
hr memory stats                      # total y por scope
hr memory list                       # últimas memorias
hr memory list --scope USER          # solo las compartidas entre repos
hr memory show <id>                  # detalle de una
hr memory export --output mem.json   # volcar todo a JSON
```

`hr memory list` consulta el store **global** (`~/.headroom/memory.db`). La memoria
por-proyecto vive en `~/.headroom/memories/projects/<workspace>/`. Se llena con el uso.

---

## Gestionar / desinstalar headroom

```bash
hr install status            # estado del servicio
hr install start | stop | restart
hr install remove            # DESINSTALAR (quita servicio + routing)
```

⚠️ Si el proxy se cae, las sesiones de Claude **fallan** hasta `hr-on`
(o `hr install remove` para volver a tráfico directo a Anthropic).

---

## Problemas comunes

- **Claude falla / cuelga** → ¿proxy caído? `hr-status`; si no, `hr-on`.
- **No comprime en una sesión** → `echo $ANTHROPIC_BASE_URL` vacío = sesión vieja, reiníciala.
- **No aparece 🐴/🧠** → sesión vieja; reiníciala.
- **`pip install` falla** → usa Python 3.13 (no 3.14): `brew install python@3.13`.
- **No borres `~/.headroom/venv`** sin antes `hr install remove`: respalda el servicio.

---

## Actualizar

```bash
git -C ~/claude-agent-setup pull
bash ~/claude-agent-setup/install.sh   # re-aplica (idempotente)
```

---

## Créditos

Capa de instalación sobre [headroom](https://github.com/chopratejas/headroom) y
[ponytail](https://github.com/DietrichGebert/ponytail). Gracias a sus autores.

Licencia [MIT](LICENSE).
