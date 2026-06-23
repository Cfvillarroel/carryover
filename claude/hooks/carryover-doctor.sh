#!/usr/bin/env bash
# carryover doctor — health check (and optional --fix) of the whole setup. Run: carryover doctor [--fix]
HR="$HOME/.headroom/venv/bin/headroom"
SRC="${CARRYOVER_SRC:-$HOME/carryover}"
uid=$(id -u)
FIX=0; [ "$1" = "--fix" ] && FIX=1
ok(){    printf "  ✅ %s\n" "$1"; }
bad(){   printf "  ❌ %s\n" "$1"; }
warn(){  printf "  ⚠️  %s\n" "$1"; }
info(){  printf "  •  %s\n" "$1"; }
fixed(){ printf "     → %s\n" "$1"; }

[ "$FIX" = 1 ] && echo "💼 carryover doctor --fix" || echo "💼 carryover doctor"

# locate co-mem next to this script (follow symlink)
src="${BASH_SOURCE[0]:-$0}"; while [ -L "$src" ]; do d=$(cd -P "$(dirname "$src")" && pwd); src=$(readlink "$src"); [ "${src#/}" = "$src" ] && src="$d/$src"; done
COMEM="$(cd -P "$(dirname "$src")" && pwd)/co-mem"

# memory backend + store (works with OR without headroom)
if [ -f "$COMEM" ]; then
  be=$(python3 "$COMEM" backend 2>/dev/null | cut -f1)
  ok "memory backend: ${be:-builtin}"
  ok "knowledge store: $(python3 "$COMEM" stats 2>/dev/null || echo 0) memories"
else
  warn "co-mem missing — re-run install.sh"
fi

# routing / proxy — headroom is OPTIONAL
if [ -x "$HR" ]; then
  ok "headroom proxy installed ($($HR --version 2>/dev/null))"
  if curl -fsS http://127.0.0.1:8787/readyz >/dev/null 2>&1; then ok "proxy up (127.0.0.1:8787)"
  else
    bad "proxy DOWN → hr-on"
    if [ "$FIX" = 1 ]; then
      nohup "$HR" proxy --port 8787 --memory >/dev/null 2>&1 & sleep 2
      curl -fsS http://127.0.0.1:8787/readyz >/dev/null 2>&1 && fixed "proxy started" || fixed "could not start — run install.sh in a real Terminal"
    fi
  fi
  PLIST=$(ls "$HOME"/Library/LaunchAgents/*headroom*.plist 2>/dev/null | head -1)
  if [ -n "$PLIST" ] && grep -q "RunAtLoad" "$PLIST" 2>/dev/null; then
    LABEL=$(basename "$PLIST" .plist)
    if launchctl print "gui/$uid/$LABEL" >/dev/null 2>&1; then ok "launchd service loaded — survives reboot ($LABEL)"
    else
      warn "launchd plist present but not loaded → carryover persist"
      if [ "$FIX" = 1 ]; then
        launchctl bootstrap "gui/$uid" "$PLIST" 2>/dev/null
        launchctl kickstart -k "gui/$uid/$LABEL" 2>/dev/null && fixed "service bootstrapped" || fixed "bootstrap failed — run from a real Terminal (GUI session)"
      fi
    fi
  else
    warn "no launchd plist with RunAtLoad → run in YOUR terminal: $HR install apply --memory"
  fi
  if grep -q '"ANTHROPIC_BASE_URL"' "$HOME/.claude/settings.json" 2>/dev/null; then ok "Claude routing ON (settings.json)"
  else warn "Claude routing OFF (carryover off?) → carryover on"; fi
  if [ -f "$HOME/.carryover/.bypass" ]; then
    warn "global bypass flag set (routing off) → carryover on"
    [ "$FIX" = 1 ] && { rm -f "$HOME/.carryover/.bypass"; bash "$HOME/.claude/hooks/carryover-toggle.sh" on >/dev/null 2>&1; fixed "routing on"; }
  else ok "no bypass flag"; fi
else
  info "headroom proxy not installed — routing & compression OFF (optional; memory & wiki work fine)"
fi

# installed files
MISSING=0
for f in statusline.sh commands/headroom.md commands/recall.md hooks/mem-save.sh hooks/carryover-recall.sh hooks/carryover-toggle.sh; do
  if [ -e "$HOME/.claude/$f" ]; then ok "~/.claude/$f"; else warn "~/.claude/$f missing"; MISSING=1; fi
done
for f in carryover-dash.py install-wiki.sh recall.sh co-mem; do
  [ -e "$HOME/.carryover/$f" ] && ok "~/.carryover/$f" || { warn "~/.carryover/$f missing"; MISSING=1; }
done
grep -q ">>> headroom aliases >>>" "$HOME/.zshrc" 2>/dev/null && ok "aliases in ~/.zshrc" || { warn "aliases missing in ~/.zshrc"; MISSING=1; }
if [ "$MISSING" = 1 ] && [ "$FIX" = 1 ] && [ -f "$SRC/install.sh" ]; then
  bash "$SRC/install.sh" --files-only >/dev/null 2>&1 && fixed "re-ran install.sh --files-only"
fi

[ "$FIX" = 1 ] && echo "done. (--fix applied where possible)" || echo "done."
