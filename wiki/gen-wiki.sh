#!/usr/bin/env bash
# Generates/updates a LOCAL wiki in GitHub Wiki format from the repo's changes,
# using Claude headless (claude -p → uses your auth and goes through headroom).
# Usage:   bash gen-wiki.sh [GIT_RANGE]      (e.g. origin/master..HEAD; empty = HEAD~20..HEAD)
# Env:   WIKI_DIR=<output folder>  (default: <repo>/wiki)
#        WIKI_PUBLISH=1            (additionally, push to the GitHub wiki <repo>.wiki.git)
set -euo pipefail

command -v claude >/dev/null || { echo "wiki: 'claude' missing from PATH"; exit 0; }
REPO_ROOT="$(git rev-parse --show-toplevel)"
WIKI_DIR="${WIKI_DIR:-$REPO_ROOT/wiki}"
RANGE="${1:-HEAD~20..HEAD}"
git -C "$REPO_ROOT" rev-parse "$RANGE" >/dev/null 2>&1 || RANGE="HEAD"
mkdir -p "$WIKI_DIR"

# --- context (bounded; headroom compresses anyway) ---
LOG="$(git -C "$REPO_ROOT" log --no-merges --pretty='- %s (%h)' "$RANGE" 2>/dev/null | head -100)"
DIFFSTAT="$(git -C "$REPO_ROOT" diff --stat "$RANGE" 2>/dev/null | tail -80)"
TREE="$(git -C "$REPO_ROOT" ls-files 2>/dev/null | head -400)"
HOME_PREV="$([ -f "$WIKI_DIR/Home.md" ] && cat "$WIKI_DIR/Home.md" || echo '(no previous wiki)')"
MEM=""
HR="$HOME/.headroom/venv/bin/headroom"
if [ -x "$HR" ]; then
  TMPM="$(mktemp)"; "$HR" memory export --output "$TMPM" 2>/dev/null || true
  MEM="$(head -c 8000 "$TMPM" 2>/dev/null || true)"; rm -f "$TMPM"
fi

# --- prompt → Claude headless ---
OUT="$(claude -p 2>/dev/null <<EOF
You are a technical writer. Generate/update a repository's wiki in
GitHub Wiki format (standalone Markdown pages). Language: write in the same
language as the repository's README and commit messages; if unclear, default to English.

Return ONLY files, each preceded by an EXACT marker line:
=== FILE: <name>.md ===

Pages to generate:
- Home.md            overview: what it is, what it's for, how it's used.
- Architecture.md    components and how they fit together; AT LEAST one \`\`\`mermaid diagram.
- Flows.md           main flows (request/build/deploy/data) with \`\`\`mermaid.
- _Sidebar.md        navigation with wiki-links: [[Home]] [[Architecture]] [[Flows]] [[Changelog]].
- Changelog-Entry.md ONLY 3-8 bullets summarizing the changes in this push.

Rules: diagrams in \`\`\`mermaid blocks. Don't invent files that don't exist.
If there was a previous wiki, keep consistency when updating.

== File tree ==
$TREE

== Commits ($RANGE) ==
$LOG

== Diff stat ==
$DIFFSTAT

== headroom memory (context, may be empty) ==
$MEM

== Previous Home.md ==
$HOME_PREV
EOF
)"
[ -n "$OUT" ] || { echo "wiki: claude returned no content"; exit 0; }

# --- split output into files (whitelist by name, no paths) ---
printf '%s\n' "$OUT" | awk -v dir="$WIKI_DIR" '
  /^=== FILE: .+ ===$/ {
    if (f) { close(f); f="" }
    name=$0; sub(/^=== FILE: /,"",name); sub(/ ===$/,"",name)
    if (name ~ /[\/]/ || name ~ /\.\./ || name !~ /\.md$/) next
    f=dir "/" name; printf "" > f; next
  }
  f { print >> f }
'

# --- cumulative changelog (prepend with date) ---
if [ -f "$WIKI_DIR/Changelog-Entry.md" ]; then
  { echo "## $(date '+%Y-%m-%d %H:%M')"; cat "$WIKI_DIR/Changelog-Entry.md"; echo;
    [ -f "$WIKI_DIR/Changelog.md" ] && cat "$WIKI_DIR/Changelog.md"; } > "$WIKI_DIR/.cl.tmp"
  mv "$WIKI_DIR/.cl.tmp" "$WIKI_DIR/Changelog.md"
  rm -f "$WIKI_DIR/Changelog-Entry.md"
fi

echo "wiki: $WIKI_DIR → $(ls "$WIKI_DIR" 2>/dev/null | tr '\n' ' ')"

# --- optional publish to the GitHub wiki ---
if [ "${WIKI_PUBLISH:-0}" = "1" ]; then
  ORIGIN="$(git -C "$REPO_ROOT" remote get-url origin 2>/dev/null || true)"
  [ -n "$ORIGIN" ] || { echo "wiki: no origin remote, not publishing"; exit 0; }
  WIKI_URL="${ORIGIN%.git}.wiki.git"
  TMP="$(mktemp -d)"
  if git clone -q "$WIKI_URL" "$TMP" 2>/dev/null; then
    cp "$WIKI_DIR"/*.md "$TMP"/ 2>/dev/null || true
    git -C "$TMP" add -A
    git -C "$TMP" -c user.name="wiki-bot" -c user.email="wiki@local" commit -q -m "Update wiki ($(date '+%F %T'))" 2>/dev/null || true
    if git -C "$TMP" push -q 2>/dev/null; then echo "wiki: published to $WIKI_URL"
    else echo "wiki: could not publish (is the wiki enabled on GitHub?)"; fi
  else
    echo "wiki: could not clone $WIKI_URL — enable the wiki and create its first page once."
  fi
  rm -rf "$TMP"
fi
