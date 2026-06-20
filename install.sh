#!/usr/bin/env bash
# Instala mi setup (headroom + ponytail + config de Claude) en esta máquina.
# Idempotente: se puede re-ejecutar. Uso: bash <repo>/install.sh
# Env opcional: HEADROOM_PORT / HEADROOM_PROFILE para correrlo aislado (testing).
set -euo pipefail

SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"   # .../.conductor/setup
HR_DIR="$HOME/.headroom"

echo "==> 1/4 headroom (venv Python 3.13)"
if ! command -v python3.13 >/dev/null; then
  echo "    Falta python3.13 → instala con: brew install python@3.13"; exit 1
fi
[ -d "$HR_DIR/venv" ] || python3.13 -m venv "$HR_DIR/venv"
"$HR_DIR/venv/bin/pip" install -q --upgrade pip
"$HR_DIR/venv/bin/pip" install -q "headroom-ai[all]"   # 3.14 no compila; por eso 3.13
"$HR_DIR/venv/bin/headroom" install apply --memory \
  ${HEADROOM_PROFILE:+--profile "$HEADROOM_PROFILE"} ${HEADROOM_PORT:+--port "$HEADROOM_PORT"}   # proxy persistente + routing + memoria

echo "==> 2/4 plugins de Claude (ponytail + headroom)"
claude plugin marketplace add DietrichGebert/ponytail 2>/dev/null || true
claude plugin marketplace add chopratejas/headroom    2>/dev/null || true
claude plugin install ponytail@ponytail                2>/dev/null || true
claude plugin install headroom@headroom-marketplace    2>/dev/null || true

echo "==> 3/4 config de ~/.claude (symlinks al repo)"
mkdir -p "$HOME/.claude/commands"
ln -sf "$SETUP_DIR/claude/statusline.sh"        "$HOME/.claude/statusline.sh"
ln -sf "$SETUP_DIR/claude/commands/headroom.md" "$HOME/.claude/commands/headroom.md"
ln -sf "$SETUP_DIR/GUIA.md"                      "$HR_DIR/GUIA.md"
# statusLine en settings.json: fija la clave sin pisar lo demás (hooks/env/plugins)
python3 - "$HOME/.claude/settings.json" "$HOME/.claude/statusline.sh" <<'PY'
import json, os, sys
path, sl = sys.argv[1], sys.argv[2]
d = json.load(open(path)) if os.path.exists(path) else {}
d["statusLine"] = {"type": "command", "command": f'bash "{sl}"'}
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY

# hook "guardar en memoria al final": symlink del script + merge idempotente de hooks
mkdir -p "$HOME/.claude/hooks"
ln -sf "$SETUP_DIR/claude/hooks/headroom-mem-prompt.sh" "$HOME/.claude/hooks/headroom-mem-prompt.sh"
ln -sf "$SETUP_DIR/claude/hooks/mem-save.sh" "$HOME/.claude/hooks/mem-save.sh"
ln -sf "$SETUP_DIR/claude/hooks/carryover-toggle.sh" "$HOME/.claude/hooks/carryover-toggle.sh"
python3 - "$HOME/.claude/settings.json" "$HOME/.claude/hooks/headroom-mem-prompt.sh" <<'PY'
import json, os, sys
path, hook = sys.argv[1], sys.argv[2]
d = json.load(open(path)) if os.path.exists(path) else {}
h = d.setdefault("hooks", {})
def has(arr, needle):
    return any(needle in hh.get("command", "") for e in arr for hh in e.get("hooks", []))
post = h.setdefault("PostToolUse", [])
if not has(post, "hr-changes-"):
    post.append({"matcher": "Write|Edit|NotebookEdit", "hooks": [{"type": "command",
        "command": "sid=$(jq -r '.session_id // empty'); [ -n \"$sid\" ] && touch \"/tmp/hr-changes-$sid.flag\""}]})
stop = h.setdefault("Stop", [])
if not has(stop, "headroom-mem-prompt.sh"):
    stop.append({"hooks": [{"type": "command", "command": f"bash {hook}"}]})
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY

echo "==> 4/4 aliases en ~/.zshrc (headroom + wiki-enable)"
if ! grep -qF ">>> headroom aliases >>>" "$HOME/.zshrc" 2>/dev/null; then
  cat "$SETUP_DIR/zshrc.snippet" >> "$HOME/.zshrc"
fi
if ! grep -qF ">>> wiki-enable alias >>>" "$HOME/.zshrc" 2>/dev/null; then
  {
    echo "# >>> wiki-enable alias >>>"
    echo "alias wiki-enable=\"bash '$SETUP_DIR/wiki/install-wiki.sh'\""  # activa la wiki en el repo actual
    echo "# <<< wiki-enable alias <<<"
  } >> "$HOME/.zshrc"
fi

echo
echo "Listo. Abre una terminal nueva (o 'source ~/.zshrc') y reinicia Claude."
echo "Verifica:  ~/.headroom/venv/bin/headroom install status"
