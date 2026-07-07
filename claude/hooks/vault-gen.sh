#!/usr/bin/env bash
# Build/refresh the unified Obsidian vault: knowledge notes + entity graph + every registered repo's
# wiki, in one folder you open in Obsidian. The wiki is already .md; this materializes the SQLite
# knowledge as notes so Obsidian's graph view shows the whole knowledge graph (no plugins).
# Two-way: edits to a memory note's first paragraph or `importance` are pushed back to the store
# BEFORE regenerating, so your edits are never clobbered.
#
# Usage:  vault-gen [clean|remove|prune|merge] [DIR] [--no-import] [--describe] [--yes]
#   (no subcommand) : build/refresh the vault      (DIR defaults to ~/Documents/carryover-vault)
#   clean           : save edits, wipe everything generated, rebuild fresh (also refreshes config)
#   remove          : delete the vault folder and unregister it from Obsidian (asks unless --yes)
#   prune           : just prune orphaned generated notes (fast; no wiki/register/LLM)
#   merge           : LLM pass that groups synonymous entities into a hand-editable map, then rebuild
#   --describe      : also run an LLM pass (claude -p) to write 1-line blurbs for the top entities
set -uo pipefail
VAULT="$HOME/Documents/carryover-vault"   # visible folder (next to your other Obsidian vaults); override with an arg
NOIMPORT=""; DESCRIBE=""; CMD=""; YES=""
for arg in "$@"; do
  case "$arg" in
    clean|remove|prune|merge) CMD="$arg" ;;
    --no-import) NOIMPORT=1 ;;
    --describe)  DESCRIBE=1 ;;
    --yes|-y)    YES=1 ;;
    -*) ;;                         # ignore other flags
    *)  VAULT="$arg" ;;
  esac
done

PY="$HOME/.headroom/venv/bin/python"; [ -x "$PY" ] || PY="$(command -v python3)"
COMEM="${COMEM:-$HOME/.carryover/co-mem}"; [ -f "$COMEM" ] || COMEM="$(dirname "$0")/co-mem"

write_graph_json() {  # colour by folder + hide tag/attachment nodes so the graph isn't duplicated
  cat > "$VAULT/.obsidian/graph.json" <<'JSON'
{"showTags":false,"showAttachments":false,"colorGroups":[
  {"query":"path:knowledge/","color":{"a":1,"rgb":6000111}},
  {"query":"path:entities/","color":{"a":1,"rgb":14722136}},
  {"query":"path:wikis/","color":{"a":1,"rgb":10190558}},
  {"query":"path:indexes/","color":{"a":1,"rgb":9211020}}
]}
JSON
}
write_base() {  # Bases table over the knowledge notes (needs Obsidian 1.9+)
  cat > "$VAULT/knowledge.base" <<'YAML'
filters:
  and:
    - file.inFolder("knowledge")
views:
  - type: table
    name: Knowledge
    order: [file.name, repo, importance, access_count, created_at]
    sort:
      - property: importance
        direction: DESC
YAML
}

# --- remove: delete the vault and unregister it from Obsidian ---------------------------------
if [ "$CMD" = remove ]; then
  if [ -z "$YES" ]; then
    printf "Remove the vault at %s and unregister it from Obsidian? [y/N] " "$VAULT"
    read -r ans; case "$ans" in y|Y|yes|YES|s|S|si|SI) ;; *) echo "aborted"; exit 0 ;; esac
  fi
  OBS_CFG="$HOME/Library/Application Support/obsidian/obsidian.json"
  [ -f "$OBS_CFG" ] && "$PY" - "$OBS_CFG" "$VAULT" <<'PY' || true
import json, os, sys, shutil
cfg, vault = sys.argv[1], os.path.realpath(os.path.expanduser(sys.argv[2]))
try:
    d = json.load(open(cfg))
except Exception:
    d = {}
v = d.get("vaults", {})
gone = [k for k, x in v.items() if os.path.realpath(x.get("path", "")) == vault]
if gone:
    shutil.copy(cfg, cfg + ".carryover-bak")
    for k in gone:
        del v[k]
    json.dump(d, open(cfg, "w"), indent=2)
    print("   Unregistered from Obsidian.")
PY
  rm -rf "$VAULT"
  echo "💼 vault removed: $VAULT"
  exit 0
fi

# --- prune: just prune orphaned generated notes (fast) ----------------------------------------
if [ "$CMD" = prune ]; then
  [ -d "$VAULT/knowledge" ] || { echo "vault-gen: no vault at $VAULT"; exit 1; }
  [ -z "$NOIMPORT" ] && "$PY" "$COMEM" vault-import "$VAULT" --apply >/dev/null 2>&1 || true
  out="$("$PY" "$COMEM" vault "$VAULT")" || { echo "vault-gen: export failed"; exit 1; }
  echo "💼 vault pruned → $VAULT"
  echo "   $out"
  exit 0
fi

# --- clean: force-refresh config + hub notes, then rebuild ------------------------------------
# knowledge/ and entities/ are rebuilt in place by the normal flow below (edits and LLM entity
# descriptions preserved, stale notes pruned), so clean only wipes the derived config + hubs.
if [ "$CMD" = clean ]; then
  rm -f "$VAULT/.obsidian/graph.json" "$VAULT/knowledge.base" "$VAULT/Home.md"
  rm -rf "$VAULT/indexes"
fi

# --- merge: LLM groups synonymous entities into ~/.carryover/entity-merges.json, then rebuild -----
if [ "$CMD" = merge ]; then
  if command -v claude >/dev/null; then
    echo "   merging synonymous entities via claude -p… (~30-60s)"
    "$PY" "$COMEM" vault-merge 2>/dev/null | "$PY" -c 'import json,sys
try: d=json.load(sys.stdin)
except Exception: d={}
g=d.get("groups") or {}
if g:
    print("   merged %d name(s) into %d group(s) — review/edit ~/.carryover/entity-merges.json:" % (d.get("merged",0), d.get("count",0)))
    for c,ms in g.items(): print("     %s  ←  %s" % (c, ", ".join(ms)))
else:
    print("   no merges proposed" + ((" ("+d["error"]+")") if d.get("error") else ""))'
  else
    echo "   merge needs 'claude' in PATH; skipped."
  fi
fi

mkdir -p "$VAULT"/knowledge "$VAULT"/entities "$VAULT"/wikis "$VAULT"/.obsidian
# minimal Obsidian config so the vault opens cleanly — written only if absent (never clobber it)
[ -f "$VAULT/.obsidian/app.json" ] || printf '{"newFileLocation":"root","attachmentFolderPath":"/"}\n' > "$VAULT/.obsidian/app.json"
[ -f "$VAULT/README.md" ] || printf '# carryover vault\n\nGenerated by carryover. `knowledge/`, `entities/`, `indexes/` and `Home.md` are regenerated from the memory store on every `co-vault`; edit a memory note'\''s first paragraph or `importance` and it syncs back on the next run. Everything else (facts, entities, relationships, tags) is derived and read-only. `wikis/` are symlinks to each repo'\''s wiki.\n' > "$VAULT/README.md"
[ -f "$VAULT/.obsidian/graph.json" ] || write_graph_json
[ -f "$VAULT/knowledge.base" ] || write_base

# 1) import edits back FIRST — protects local edits before the overwrite
[ -z "$NOIMPORT" ] && "$PY" "$COMEM" vault-import "$VAULT" --apply >/dev/null 2>&1 || true
# 2) regenerate knowledge + entities from the store
"$PY" "$COMEM" vault "$VAULT" >/dev/null || { echo "vault-gen: export failed"; exit 1; }
# 2b) optional: LLM blurbs for the top entities (opt-in, ~1 claude -p call)
if [ -n "$DESCRIBE" ]; then
  if command -v claude >/dev/null; then
    echo "   describing top entities via claude -p… (~30-60s)"
    "$PY" "$COMEM" vault-describe "$VAULT" >/dev/null || echo "   (entity descriptions skipped)"
  else
    echo "   --describe needs 'claude' in PATH; skipped."
  fi
fi

# 3) refresh wiki symlinks from the registry (one per repo; last worktree wins on name collision)
reg="$HOME/.carryover/wikis.list"
if [ -f "$reg" ]; then
  while IFS= read -r d; do
    [ -n "$d" ] || continue
    if [ -d "$d/wiki" ]; then root="$d"
    elif [ "$(basename "$d")" = "wiki" ] && [ -d "$d" ]; then root="$(dirname "$d")"
    else continue; fi
    # real repo name (git remote), else the folder name  # ponytail: basename is fine for a label
    label="$(git -C "$root" remote get-url origin 2>/dev/null | sed -E 's#/$##; s#.*/##; s#\.git$##')"
    [ -n "$label" ] || label="$(basename "$root")"
    ln -sfn "$root/wiki" "$VAULT/wikis/$label"
  done < "$reg"
fi
# drop dead symlinks (repo/worktree gone)
find "$VAULT/wikis" -maxdepth 1 -type l ! -exec test -e {} \; -delete 2>/dev/null || true

# 4) register the vault with Obsidian so it shows up in the vault switcher (macOS) — idempotent
OBS_CFG="$HOME/Library/Application Support/obsidian/obsidian.json"
[ -f "$OBS_CFG" ] && "$PY" - "$OBS_CFG" "$VAULT" <<'PY' || true
import json, os, sys, secrets, time, shutil
cfg, vault = sys.argv[1], os.path.realpath(os.path.expanduser(sys.argv[2]))
try:
    d = json.load(open(cfg))
except Exception:
    d = {}
vaults = d.setdefault("vaults", {})
if not any(os.path.realpath(v.get("path", "")) == vault for v in vaults.values()):
    shutil.copy(cfg, cfg + ".carryover-bak")          # back up before touching another app's config
    vaults[secrets.token_hex(8)] = {"path": vault, "ts": int(time.time() * 1000)}
    json.dump(d, open(cfg, "w"), indent=2)
    print("   Registered with Obsidian — pick it from the vault switcher (restart Obsidian if open).")
PY

n="$("$PY" "$COMEM" stats 2>/dev/null || echo '?')"
echo "💼 vault: ${n} memories + wikis → $VAULT"
echo "   Open in Obsidian:  co-vault-open   (or pick 'vault' in Obsidian's vault switcher)"
