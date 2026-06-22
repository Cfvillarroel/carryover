#!/usr/bin/env bash
# carryover doctor — health check of the whole setup. Run: carryover doctor
HR="$HOME/.headroom/venv/bin/headroom"
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
ok(){   printf "  ✅ %s\n" "$1"; }
bad(){  printf "  ❌ %s\n" "$1"; }
warn(){ printf "  ⚠️  %s\n" "$1"; }

echo "💼 carryover doctor"

[ -x "$HR" ] && ok "headroom installed ($($HR --version 2>/dev/null))" || { bad "headroom missing — run install.sh"; }

if curl -fsS http://127.0.0.1:8787/readyz >/dev/null 2>&1; then ok "proxy up (127.0.0.1:8787)"
else bad "proxy DOWN → run: hr-on   (or: $HR install apply --memory)"; fi

if launchctl list 2>/dev/null | grep -qi headroom; then ok "proxy is a launchd service (survives reboot)"
else warn "proxy not registered with launchd (won't survive reboot) → run in YOUR terminal: $HR install apply --memory"; fi

if grep -q '"ANTHROPIC_BASE_URL"' "$HOME/.claude/settings.json" 2>/dev/null; then ok "Claude routing ON (settings.json)"
else warn "Claude routing OFF (carryover off?) → carryover on"; fi
[ -f "$HOME/.carryover/.bypass" ] && warn "global bypass flag set (routing off) → carryover on" || ok "no bypass flag"

for f in statusline.sh commands/headroom.md commands/recall.md hooks/mem-save.sh hooks/carryover-recall.sh hooks/carryover-toggle.sh; do
  if [ -e "$HOME/.claude/$f" ]; then ok "~/.claude/$f"; else warn "~/.claude/$f missing — re-run install.sh"; fi
done
for f in carryover-dash.py install-wiki.sh recall.sh; do
  [ -e "$HOME/.carryover/$f" ] && ok "~/.carryover/$f" || warn "~/.carryover/$f missing — re-run install.sh"
done

grep -q ">>> headroom aliases >>>" "$HOME/.zshrc" 2>/dev/null && ok "aliases in ~/.zshrc" || warn "aliases missing — open a new terminal / re-run install.sh"

if [ -x "$HR" ]; then
  n=$("$HR" memory stats --db-path "$DB" 2>/dev/null | grep -oE 'Total Memories: [0-9]+' | grep -oE '[0-9]+')
  ok "knowledge store: ${n:-0} memories"
fi
echo "done."
