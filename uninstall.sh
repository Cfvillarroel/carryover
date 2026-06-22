#!/usr/bin/env bash
# Uninstall carryover's Claude-side wiring. headroom (proxy + memory) and the ponytail
# plugin are left intact — remove those separately. Run: carryover uninstall  (or: bash uninstall.sh)
set -uo pipefail
SETUP_DIR="$(cd "$(dirname "$0")" && pwd)"
CLA="$HOME/.claude"
echo "==> Removing carryover (Claude config). headroom proxy/memory are left intact."

# 1) symlinks under ~/.claude (statusline, the carryover hooks, the commands carryover installed)
rm -f "$CLA/statusline.sh"
rm -f "$CLA/hooks/headroom-mem-prompt.sh" "$CLA/hooks/mem-save.sh" \
      "$CLA/hooks/carryover-toggle.sh" "$CLA/hooks/carryover-recall.sh" "$CLA/hooks/carryover-doctor.sh"
for c in "$SETUP_DIR"/claude/commands/*.md; do rm -f "$CLA/commands/$(basename "$c")"; done

# 2) carryover's own dir (symlinks + data: dashboard, wiki scripts, recall/forget, .bypass, wikis.list, logs)
rm -rf "$HOME/.carryover"

# 3) ~/.zshrc aliases block
python3 - "$HOME/.zshrc" <<'PY'
import re, sys, pathlib
z = pathlib.Path(sys.argv[1])
if z.exists():
    t = z.read_text()
    t = re.sub(r"\n*[^\n]*>>> headroom aliases >>>[^\n]*\n.*?\n[^\n]*<<< headroom aliases <<<[^\n]*\n?", "\n", t, flags=re.S)
    z.write_text(t)
    print("  removed aliases block from ~/.zshrc")
PY

# 4) settings.json: drop statusLine + carryover's hooks (leave headroom routing for 'hr install remove')
python3 - "$CLA/settings.json" <<'PY'
import json, os, sys
p = sys.argv[1]
if not os.path.exists(p):
    sys.exit(0)
d = json.load(open(p))
if "statusline.sh" in (d.get("statusLine") or {}).get("command", ""):
    d.pop("statusLine", None)
h = d.get("hooks") or {}
MARKERS = ("hr-changes-", "headroom-mem-prompt.sh", "carryover-recall.sh")
for ev in list(h):
    h[ev] = [e for e in h[ev]
             if not any(any(m in hh.get("command", "") for m in MARKERS) for hh in e.get("hooks", []))]
    if not h[ev]:
        h.pop(ev, None)
if h:
    d["hooks"] = h
else:
    d.pop("hooks", None)
json.dump(d, open(p, "w"), indent=2, ensure_ascii=False)
print("  cleaned ~/.claude/settings.json (statusLine + carryover hooks)")
PY

echo "Done. carryover removed."
echo "Still installed (remove separately if you want):"
echo "  • headroom proxy + memory:  ~/.headroom/venv/bin/headroom install remove"
echo "  • ponytail plugin:          claude plugin uninstall ponytail@ponytail"
echo "Open a new terminal so the aliases drop."
