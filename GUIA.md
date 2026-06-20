# Headroom — Guía rápida

Capa de compresión de contexto para LLMs. Comprime lo que Claude lee/escribe
antes de llegar a la API → menos tokens, mismas respuestas. Memoria compartida
entre repos. Instalado durablemente el 2026-06-19.

Repo: https://github.com/chopratejas/headroom

---

## Qué quedó instalado

- **Servicio** `com.headroom.default` (launchd, arranca solo al reiniciar el Mac).
  Proxy en `http://127.0.0.1:8787`.
- **Claude enrutado a scope usuario** en `~/.claude/settings.json`
  (`env.ANTHROPIC_BASE_URL` + hooks). Aplica a **todos** los workspaces de Conductor.
- **Memoria:** global `~/.headroom/memory.db` (scope USER = compartida entre repos)
  + per-proyecto en `~/.headroom/memories/projects/<workspace>/`.
- **CLI:** `~/.headroom/venv/bin/headroom` (servicio) y `~/.pipx/venvs/headroom-ai/bin/headroom` (hooks). Ambos 0.26.0, Python 3.13.
- Plugin Claude Code `headroom@headroom-marketplace` habilitado.

Tip: alias para no escribir la ruta:
```bash
echo 'alias hr=~/.headroom/venv/bin/headroom' >> ~/.zshrc && source ~/.zshrc
```

---

## Usarlo en cualquier workspace

**No hay que instalar nada por-repo.** El routing es global. Solo:

- Abre una sesión **nueva** de Claude en el workspace → ya pasa por headroom.
- Sesiones ya abiertas: ciérralas y reábrelas (el `ANTHROPIC_BASE_URL` se lee al arrancar).

---

## Comandos fáciles

**Aliases** (en `~/.zshrc`, abre una terminal nueva o `source ~/.zshrc`):

| Alias | Hace |
|-------|------|
| `hr` | CLI base de headroom |
| `hr-status` | ¿proxy arriba/sano? |
| `hr-mem` | memorias guardadas |
| `hr-stats` | resumen de memoria |
| `hr-save` | tokens ahorrados |
| `hr-on` / `hr-off` | arrancar / parar el proxy |

**Dentro de Claude** (cualquier workspace): escribe `/headroom` → resumen de proxy,
memoria y ahorro. También `/headroom list --scope USER`, `/headroom show <id>`, etc.

---

## Verificar

```bash
hr install status                 # Status: running · Healthy: yes
curl -fsS http://127.0.0.1:8787/readyz   # {"status":"healthy",...}
echo $ANTHROPIC_BASE_URL          # dentro de una sesión Claude → http://127.0.0.1:8787
hr memory stats                   # memoria acumulada (alias ya apunta al store del proxy)
hr memory list --scope USER       # memorias compartidas entre repos
```

> ⚠️ Importante: el CLI `headroom memory` por defecto usa `./headroom_memory.db` del
> directorio actual, NO el store del proxy. Por eso los aliases `hr-mem`/`hr-stats`
> añaden `--db-path "$HOME/.headroom/memory.db"`. Para guardar a mano una memoria en
> ese store: `mem-save "lo que quieras recordar"`.

---

## Gestionar

```bash
hr install start | stop | restart   # control del servicio
hr install status                   # estado
hr install remove                   # DESINSTALAR todo (quita routing + servicio)
```

⚠️ Si el proxy se cae, las sesiones de Claude **fallan** hasta `hr install start`
(o `hr install remove` para volver a tráfico directo).

---

## Problemas comunes

- **Claude falla / cuelga** → ¿proxy caído? `hr install status`; si no, `hr install start`.
- **No comprime en una sesión** → `echo $ANTHROPIC_BASE_URL` vacío = sesión vieja, reiníciala.
- **Volver a la normalidad rápido** → `hr install remove` (Claude vuelve a ir directo a Anthropic).
- **No reinstalar con 3.14** → la extensión Rust no compila; el venv usa Python 3.13.
- **No borrar `~/.headroom/venv`** sin antes `hr install remove`: respalda el servicio.
