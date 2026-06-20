---
description: Estado de headroom — proxy, memoria y ahorro de tokens
---

Eres el operador de headroom. Ejecuta estos comandos y resume el resultado en español, claro y breve:

```bash
HR=~/.headroom/venv/bin/headroom
DB="$HOME/.headroom/memory.db"   # store real del proxy (NO el ./headroom_memory.db del cwd)
$HR install status                       # proxy: running/healthy, puerto
$HR memory stats --db-path "$DB"         # total de memorias y por scope
$HR memory list --db-path "$DB" --limit 10   # últimas memorias
$HR output-savings 2>/dev/null || true   # tokens ahorrados (si hay datos)
```

Luego reporta:
- Si el proxy está **arriba y sano** (o caído → sugiere `hr-on`).
- Cuántas **memorias** hay (scope USER = compartidas entre repos).
- El **ahorro de tokens** si está disponible.

Si el usuario pasó argumentos en `$ARGUMENTS`, interprétalos como un subcomando de
`headroom memory` (ej. `show <id>`, `list --scope USER`, `--since 7d`) y ejecútalo
**añadiendo siempre** `--db-path "$HOME/.headroom/memory.db"` en vez del resumen por defecto.
