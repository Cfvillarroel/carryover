---
description: Build/refresh a unified Obsidian vault (knowledge + all repo wikis)
---

Build or refresh the unified Obsidian vault. Run via Bash:

```bash
bash ~/.carryover/vault-gen.sh
```

Then tell the user: it wrote `~/Documents/carryover-vault` (a visible folder, and it registers the
vault with Obsidian so it shows up in the vault switcher) — open it in Obsidian to browse every
memory as a note, the entity/relationship graph in the graph view, and each registered repo's wiki,
all together. It's two-way: editing a memory note's first paragraph or its `importance` in Obsidian
syncs back to the store on the next `co-vault` (facts, entities, relationships and tags are derived
and regenerated, so they're read-only). No Obsidian plugins needed.
