#!/usr/bin/env bash
# Instala mi setup (headroom + ponytail + config de Claude) en esta máquina.
# Idempotente: se puede re-ejecutar. Uso: bash ~/.conductor/setup/install.sh
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
"$HR_DIR/venv/bin/headroom" install apply --memory      # proxy persistente + routing + memoria

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

echo "==> 4/4 aliases en ~/.zshrc"
if ! grep -qF ">>> headroom aliases >>>" "$HOME/.zshrc" 2>/dev/null; then
  cat "$SETUP_DIR/zshrc.snippet" >> "$HOME/.zshrc"
fi

echo
echo "Listo. Abre una terminal nueva (o 'source ~/.zshrc') y reinicia Claude."
echo "Verifica:  ~/.headroom/venv/bin/headroom install status"
