#!/usr/bin/env bash
# Generate/update the CURRENT repo's wiki on demand — no push to master/main needed.
# (In Conductor you work on worktree branches, so the push-to-master hook rarely fires;
#  this is the same idea as the end-of-session memory prompt, but for the wiki.)
# Usage:  wiki-gen            (current repo)
#         WIKI_PUBLISH=1 wiki-gen   (also push to the GitHub wiki)
set -uo pipefail
root="$(git -C "${1:-$PWD}" rev-parse --show-toplevel 2>/dev/null)" || { echo "wiki-gen: not a git repo"; exit 1; }
# ensure the repo is wiki-enabled (copies gen-wiki.sh + pre-push + registers it) — idempotent
WIKI_NO_GEN=1 bash "$HOME/.carryover/install-wiki.sh" "$root" >/dev/null 2>&1 || true
[ -x "$root/wiki/gen-wiki.sh" ] || { echo "wiki-gen: could not set up wiki/gen-wiki.sh in $root"; exit 1; }
echo "💼 wiki-gen: generating wiki for $(basename "$root")… (uses claude -p, ~30-60s)"
bash "$root/wiki/gen-wiki.sh"
