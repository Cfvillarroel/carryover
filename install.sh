#!/usr/bin/env bash
# Installs my setup (headroom + ponytail + Claude config) on this machine.
# Idempotent: it can be re-run. Usage: bash <repo>/install.sh
# Optional env: HEADROOM_PORT / HEADROOM_PROFILE to run it isolated (testing).
set -euo pipefail

SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"   # .../.conductor/setup
HR_DIR="$HOME/.headroom"          # headroom's own dir (venv + memory DBs) — we never move this
CO_DIR="$HOME/.carryover"         # carryover's own dir (dashboard, wiki scripts, recall, flags)
mkdir -p "$CO_DIR"
MODE="${1:-full}"; [ "$MODE" = "--files-only" ] && MODE=files   # files = only symlinks/settings/zshrc (used by 'carryover update')

if [ "$MODE" = full ]; then
echo "==> 1/4 headroom (venv Python 3.13)"
if ! command -v python3.13 >/dev/null; then
  echo "    Missing python3.13 → install with: brew install python@3.13"; exit 1
fi
[ -d "$HR_DIR/venv" ] || python3.13 -m venv "$HR_DIR/venv"
"$HR_DIR/venv/bin/pip" install -q --upgrade pip
"$HR_DIR/venv/bin/pip" install -q "headroom-ai[all]"   # 3.14 doesn't compile; that's why 3.13
if "$HR_DIR/venv/bin/headroom" install status >/dev/null 2>&1; then
  echo "    deployment already present and healthy — skipping apply (idempotent)"
else
  "$HR_DIR/venv/bin/headroom" install apply --memory \
    ${HEADROOM_PROFILE:+--profile "$HEADROOM_PROFILE"} ${HEADROOM_PORT:+--port "$HEADROOM_PORT"} \
    || echo "    ⚠️  'headroom install apply' failed (commonly launchctl from a non-interactive shell). Re-run it once in YOUR terminal to enable the persistent service — the rest of the install continues."
fi

echo "==> 2/4 Claude plugins (ponytail + headroom)"
claude plugin marketplace add DietrichGebert/ponytail 2>/dev/null || true
claude plugin marketplace add chopratejas/headroom    2>/dev/null || true
claude plugin install ponytail@ponytail                2>/dev/null || true
claude plugin install headroom@headroom-marketplace    2>/dev/null || true
fi   # end MODE=full; --files-only skips headroom venv + plugins above

echo "==> 3/4 ~/.claude config (symlinks to the repo)"
mkdir -p "$HOME/.claude/commands"
ln -sf "$SETUP_DIR/claude/statusline.sh"        "$HOME/.claude/statusline.sh"
for c in "$SETUP_DIR"/claude/commands/*.md; do ln -sf "$c" "$HOME/.claude/commands/$(basename "$c")"; done
ln -sf "$SETUP_DIR/GUIA.md"                      "$CO_DIR/GUIA.md"
ln -sf "$SETUP_DIR/dash/carryover-dash.py"       "$CO_DIR/carryover-dash.py"   # 'co-dash' alias target
ln -sf "$SETUP_DIR/wiki/install-wiki.sh"         "$CO_DIR/install-wiki.sh"     # 'wiki-enable' alias target
ln -sf "$SETUP_DIR/claude/hooks/recall.sh"       "$CO_DIR/recall.sh"           # 'hr-recall' alias target
ln -sf "$SETUP_DIR/claude/hooks/wiki-gen.sh"     "$CO_DIR/wiki-gen.sh"         # 'wiki-gen' alias target
ln -sf "$SETUP_DIR/zshrc.snippet"                "$CO_DIR/carryover.zsh"       # sourced by ~/.zshrc; 'carryover update' re-sources this
# migrate the old layout (carryover artifacts used to live in ~/.headroom): move data files, drop stale symlinks
for f in .bypass wikis.list; do
  if [ -f "$HR_DIR/$f" ] && [ ! -e "$CO_DIR/$f" ]; then mv "$HR_DIR/$f" "$CO_DIR/$f"; fi
done
rm -f "$HR_DIR"/carryover-dash.py "$HR_DIR"/install-wiki.sh "$HR_DIR"/recall.sh "$HR_DIR"/wiki-gen.sh "$HR_DIR"/GUIA.md "$HR_DIR"/carryover.zsh
# statusLine in settings.json: set the key without clobbering the rest (hooks/env/plugins)
python3 - "$HOME/.claude/settings.json" "$HOME/.claude/statusline.sh" <<'PY'
import json, os, sys
path, sl = sys.argv[1], sys.argv[2]
d = json.load(open(path)) if os.path.exists(path) else {}
d["statusLine"] = {"type": "command", "command": f'bash "{sl}"'}
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY

# "save to memory at the end" hook: symlink the script + idempotent merge of hooks
mkdir -p "$HOME/.claude/hooks"
ln -sf "$SETUP_DIR/claude/hooks/headroom-mem-prompt.sh" "$HOME/.claude/hooks/headroom-mem-prompt.sh"
ln -sf "$SETUP_DIR/claude/hooks/mem-save.sh" "$HOME/.claude/hooks/mem-save.sh"
ln -sf "$SETUP_DIR/claude/hooks/carryover-toggle.sh" "$HOME/.claude/hooks/carryover-toggle.sh"
ln -sf "$SETUP_DIR/claude/hooks/carryover-recall.sh" "$HOME/.claude/hooks/carryover-recall.sh"
ln -sf "$SETUP_DIR/claude/hooks/carryover-doctor.sh" "$HOME/.claude/hooks/carryover-doctor.sh"
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
ss = h.setdefault("SessionStart", [])
recall = os.path.expanduser("~/.claude/hooks/carryover-recall.sh")
if not has(ss, "carryover-recall.sh"):
    ss.append({"matcher": "startup|resume", "hooks": [{"type": "command", "command": f"bash {recall}"}]})
json.dump(d, open(path, "w"), indent=2, ensure_ascii=False)
PY

echo "==> 4/4 ~/.zshrc sources the carryover aliases"
# Static one-liner: ~/.zshrc just sources ~/.carryover/carryover.zsh (a symlink to
# the repo snippet). All future changes land via 'git pull' — no ~/.zshrc rewrite,
# and 'carryover update' re-sources just that file for an instant reload.
python3 - "$HOME/.zshrc" <<'PY'
import re, sys, pathlib
zshrc = pathlib.Path(sys.argv[1])
block = ('# >>> headroom aliases >>>\n'
         '[ -r "$HOME/.carryover/carryover.zsh" ] && source "$HOME/.carryover/carryover.zsh"\n'
         '# <<< headroom aliases <<<')
text = zshrc.read_text() if zshrc.exists() else ""
pat = re.compile(r"\n*[^\n]*>>> headroom aliases >>>[^\n]*\n.*?\n[^\n]*<<< headroom aliases <<<[^\n]*\n?", re.S)
text = pat.sub(lambda m: "\n\n" + block + "\n", text) if pat.search(text) else (text.rstrip("\n") + "\n\n" + block + "\n")
zshrc.write_text(text)
print("  ~/.zshrc now sources ~/.carryover/carryover.zsh")
PY

echo
echo "Done. Open a new terminal (or 'source ~/.zshrc') and restart Claude."
echo "Verify:  ~/.headroom/venv/bin/headroom install status"
