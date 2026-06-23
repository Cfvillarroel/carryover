# carryover — Guía rápida

Lleva tu contexto entre herramientas de IA: memoria que se recuerda entre sesiones, wiki
automática por repo, recall y un dashboard local. **Funciona solo**, con un store local propio.
Opcionalmente se integra con **headroom** (proxy de compresión + memoria compartida entre
herramientas) y con **ponytail** (plugin lazy-dev). 100% local.

> Carpetas:
> - **carryover** (`~/.carryover/`) — lo propio: backend de memoria, dashboard, wiki, recall, flags.
> - **headroom** (`~/.headroom/`) — opcional: el motor proxy + store compartido. Si está, carryover lo usa; si no, usa el suyo.

---

## Instalar

```bash
git clone https://github.com/Cfvillarroel/carryover && bash carryover/install.sh
```

Eso instala **solo carryover** (store propio). Para sumar el proxy/memoria compartida o el
plugin: `--with-headroom`, `--with-ponytail`, o `--full`. Con headroom, córrelo en una
**Terminal real** (el servicio launchd solo se monta desde una sesión GUI). Abre una terminal
nueva (o `source ~/.zshrc`) y reinicia Claude.

---

## Comandos

Escribe **`carryover`** (sin nada) y verás el estado + la lista completa, en 3 secciones:
comandos de shell, slash-commands de carryover en Claude, y ponytail. Los más usados:

| Comando | Hace |
|---------|------|
| `carryover on` / `off` | activar / desactivar el routing por el proxy (`--session` = solo esta shell) |
| `carryover status` | ¿routing activo? estado del proxy |
| `carryover doctor [--fix]` | chequeo de salud de todo (y lo repara con `--fix`) |
| `carryover persist` | que el proxy sobreviva al reboot (monta el servicio launchd) |
| `carryover update` | traer lo último + re-sincronizar esta máquina (se auto-recarga) |
| `carryover version` | versión instalada + si hay updates |
| `carryover wrap <tool>` | enrutar otra herramienta (Cursor, Codex…) por el proxy |
| `carryover uninstall` | quitar carryover (deja headroom y ponytail) |
| `co-dash` | dashboard local (memorias + wikis) |
| `hr-dash` | dashboard de ahorro/uso de headroom |
| `wiki-enable` / `wiki-gen` / `wiki-prune` | activar / regenerar / podar la wiki del repo |
| `hr-recall <q>` / `hr-forget <q>` / `hr-prune` | recordar / borrar / purgar conocimiento |
| `mem-save "texto"` | guardar una memoria a mano |

En Claude (en el chat): `/carryover`, `/recall <q>`, `/wiki-enable`, `/headroom`.

---

## Cómo funciona

- **Memoria que viaja:** al iniciar una sesión, carryover inyecta lo que ya sabe del repo;
  al terminar, te ofrece guardar lo que importó (con dedup para no acumular duplicados).
- **Wiki automática:** `wiki-enable` en un repo genera y registra su wiki (Home, Architecture,
  Flows con mermaid, Changelog); se ve en `co-dash`.
- **Dashboard local** (`co-dash`, `localhost:8788`): busca, filtra, edita ✏️ y borra memorias;
  navega las wikis. Para los números de ahorro de tokens usa `hr-dash` (dashboard de headroom).

---

## Verificar

```bash
carryover doctor          # chequea proxy, launchd (reboot), routing, symlinks, store
carryover status          # ¿routing activo? proxy running/healthy
hr-recall <palabra>       # buscar en el conocimiento
```

---

## Problemas comunes

- **Comandos nuevos no aparecen** tras `carryover update` → tu terminal tenía la función vieja
  en memoria: `source ~/.zshrc` (o abre una pestaña nueva). A partir de ahí se auto-recarga.
- **Claude falla / cuelga** → proxy caído: `carryover doctor --fix` (o `carryover off` para ir directo).
- **El proxy no sobrevive al reboot** → `carryover persist` desde una Terminal real.
- **No reinstalar con Python 3.14** → la extensión no compila; el venv usa 3.13.
- **No borres `~/.headroom/venv`** sin `hr install remove` antes: respalda el servicio.

---

## Quitar

```bash
carryover uninstall                         # quita carryover (symlinks, aliases, hooks)
~/.headroom/venv/bin/headroom install remove # quita headroom (proxy + memoria)
claude plugin uninstall ponytail@ponytail    # quita ponytail
```
