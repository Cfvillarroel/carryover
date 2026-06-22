#!/usr/bin/env bash
# Sandbox test: install.sh --files-only -> assert -> uninstall.sh -> assert, in a throwaway HOME.
# Exercises the env-modifying logic (symlinks, ~/.zshrc block, settings.json) without venv/network.
set -uo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
SB="$(mktemp -d)"
fail(){ echo "FAIL: $1"; rm -rf "$SB"; exit 1; }
mkdir -p "$SB/.claude"; : > "$SB/.zshrc"; echo '{}' > "$SB/.claude/settings.json"

echo "== install (--files-only) into HOME=$SB =="
HOME="$SB" bash "$REPO/install.sh" --files-only >/dev/null 2>&1 || fail "install --files-only errored"
[ -L "$SB/.claude/hooks/mem-save.sh" ]            || fail "hook symlink missing"
[ -L "$SB/.carryover/carryover-dash.py" ]         || fail "carryover symlink missing"
grep -q ">>> headroom aliases >>>" "$SB/.zshrc"   || fail "zshrc block missing"
grep -Fq 'source "$HOME/.carryover/carryover.zsh"' "$SB/.zshrc" || fail "zshrc doesn't source carryover.zsh"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert 'statusLine' in d; assert 'hooks' in d" "$SB/.claude/settings.json" || fail "settings.json missing statusLine/hooks"
# idempotent: re-run must not duplicate the zshrc block
HOME="$SB" bash "$REPO/install.sh" --files-only >/dev/null 2>&1 || fail "re-install errored"
[ "$(grep -c '>>> headroom aliases >>>' "$SB/.zshrc")" = "1" ] || fail "zshrc block duplicated on re-run"
echo "  install OK (symlinks, zshrc block, settings.json, idempotent)"

echo "== uninstall =="
HOME="$SB" bash "$REPO/uninstall.sh" >/dev/null 2>&1 || fail "uninstall errored"
[ -e "$SB/.claude/hooks/mem-save.sh" ] && fail "hook symlink not removed"
[ -e "$SB/.carryover" ] && fail "~/.carryover not removed"
grep -q ">>> headroom aliases >>>" "$SB/.zshrc" && fail "zshrc block not removed"
python3 -c "import json,sys; d=json.load(open(sys.argv[1])); assert 'statusLine' not in d" "$SB/.claude/settings.json" || fail "statusLine not removed from settings.json"
echo "  uninstall OK (symlinks, ~/.carryover, zshrc block, settings.json cleaned)"

rm -rf "$SB"
echo "sandbox-test: all passed"
