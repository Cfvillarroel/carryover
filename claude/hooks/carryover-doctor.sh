#!/usr/bin/env bash
# carryover doctor — health check (and optional --fix) of the whole setup. Run: carryover doctor [--fix]
HR="$HOME/.headroom/venv/bin/headroom"
DB="${HEADROOM_DB:-$HOME/.headroom/memory.db}"
SRC="${CARRYOVER_SRC:-$HOME/carryover}"
uid=$(id -u)
FIX=0; [ "$1" = "--fix" ] && FIX=1
ok(){    printf "  ✅ %s\n" "$1"; }
bad(){   printf "  ❌ %s\n" "$1"; }
warn(){  printf "  ⚠️  %s\n" "$1"; }
fixed(){ printf "     → %s\n" "$1"; }

[ "$FIX" = 1 ] && echo "💼 carryover doctor --fix" || echo "💼 carryover doctor"

[ -x "$HR" ] && ok "headroom installed ($($HR --version 2>/dev/null))" || bad "headroom missing — run install.sh"

# proxy
if curl -fsS http://127.0.0.1:8787/readyz >/dev/null 2>&1; then ok "proxy up (127.0.0.1:8787)"
else
  bad "proxy DOWN → hr-on"
  if [ "$FIX" = 1 ] && [ -x "$HR" ]; then
    nohup "$HR" proxy --port 8787 --memory >/dev/null 2>&1 &
    sleep 2
    curl -fsS http://127.0.0.1:8787/readyz >/dev/null 2>&1 && fixed "proxy started" || fixed "could not start — run install.sh in a real Terminal"
  fi
fi

# launchd / reboot persistence — check the plist FILE (not just a transient launchctl load)
PLIST=$(ls "$HOME"/Library/LaunchAgents/*headroom*.plist 2>/dev/null | head -1)
if [ -n "$PLIST" ] && grep -q "RunAtLoad" "$PLIST" 2>/dev/null; then
  LABEL=$(basename "$PLIST" .plist)
  if launchctl print "gui/$uid/$LABEL" >/dev/null 2>&1; then ok "launchd service loaded — survives reboot ($LABEL)"
  else
    warn "launchd plist present but not loaded → carryover persist"
    if [ "$FIX" = 1 ]; then
      launchctl bootstrap "gui/$uid" "$PLIST" 2>/dev/null
      launchctl kickstart -k "gui/$uid/$LABEL" 2>/dev/null && fixed "service bootstrapped" || fixed "bootstrap failed — must run from a real Terminal (GUI session)"
    fi
  fi
else
  warn "no launchd plist with RunAtLoad → run in YOUR terminal: $HR install apply --memory"
fi

# routing
if grep -q '"ANTHROPIC_BASE_URL"' "$HOME/.claude/settings.json" 2>/dev/null; then ok "Claude routing ON (settings.json)"
else warn "Claude routing OFF (carryover off?) → carryover on"; fi
if [ -f "$HOME/.carryover/.bypass" ]; then
  warn "global bypass flag set (routing off) → carryover on"
  [ "$FIX" = 1 ] && { rm -f "$HOME/.carryover/.bypass"; bash "$HOME/.claude/hooks/carryover-toggle.sh" on >/dev/null 2>&1; fixed "routing on"; }
else ok "no bypass flag"; fi

# installed files
MISSING=0
for f in statusline.sh commands/headroom.md commands/recall.md hooks/mem-save.sh hooks/carryover-recall.sh hooks/carryover-toggle.sh; do
  if [ -e "$HOME/.claude/$f" ]; then ok "~/.claude/$f"; else warn "~/.claude/$f missing"; MISSING=1; fi
done
for f in carryover-dash.py install-wiki.sh recall.sh; do
  [ -e "$HOME/.carryover/$f" ] && ok "~/.carryover/$f" || { warn "~/.carryover/$f missing"; MISSING=1; }
done
grep -q ">>> headroom aliases >>>" "$HOME/.zshrc" 2>/dev/null && ok "aliases in ~/.zshrc" || { warn "aliases missing in ~/.zshrc"; MISSING=1; }
if [ "$MISSING" = 1 ] && [ "$FIX" = 1 ] && [ -f "$SRC/install.sh" ]; then
  bash "$SRC/install.sh" --files-only >/dev/null 2>&1 && fixed "re-ran install.sh --files-only"
fi

# knowledge store
if [ -x "$HR" ]; then
  n=$("$HR" memory stats --db-path "$DB" 2>/dev/null | grep -oE 'Total Memories: [0-9]+' | grep -oE '[0-9]+')
  ok "knowledge store: ${n:-0} memories"
fi
[ "$FIX" = 1 ] && echo "done. (--fix applied where possible)" || echo "done."
