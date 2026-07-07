#!/usr/bin/env python3
"""End-to-end test of the Obsidian-vault export/import: pure-logic self-check, entity-variant
merge (incl. file extensions), noise drop, hub notes, orphan prune, and the content/importance
round-trip. Uses the builtin SQLite backend (HOME→temp, no headroom, no network)."""
import asyncio
import importlib.util
import os
import pathlib
import re
import tempfile

os.environ["HOME"] = tempfile.mkdtemp()  # no ~/.headroom here → builtin backend
os.environ.pop("HEADROOM_DB", None)

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("co_store", ROOT / "claude/hooks/co_store.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

cs._demo()  # pure-logic self-check: memory_md round-trip, key merge, noise, resolver, quoted prune
assert cs.backend()[0] == "builtin"

# two entity name variants that MUST merge (separators + file extension), plus a pure-number noise entity
asyncio.run(cs.save(content="carryover-doctor runs the health checks", uid="default", importance=0.8,
    metadata={"repo": "carryover", "category": "ops",
              "entities": [{"entity": "carryover-doctor", "entity_type": "tech"}]}))
asyncio.run(cs.save(content="the doctor script lives in hooks", uid="default", importance=0.7,
    metadata={"repo": "carryover", "category": "ops",
              "entities": [{"entity": "carryover-doctor.sh"}],
              "relationships": [{"source": "carryover-doctor.sh", "relationship": "is", "destination": "3000"}]}))
asyncio.run(cs.save(content="unrelated note", uid="default", importance=0.5,
    metadata={"repo": "other", "entities": [{"entity": "3000"}]}))

V = tempfile.mkdtemp()
r = cs.export_vault(V)
assert r["memories"] == 3, r
vp = pathlib.Path(V)

# carryover-doctor and carryover-doctor.sh merged into ONE entity note; "3000" dropped as noise
ents = sorted(p.name for p in (vp / "entities").glob("*.md"))
assert len(ents) == 1, ents
merged = (vp / "entities" / ents[0]).read_text()
assert "aliases:" in merged and "carryover-doctor" in merged, merged
assert not (vp / "entities" / "3000.md").exists(), "pure-number entity must be dropped"

# hub notes + one knowledge note per memory
assert (vp / "Home.md").exists() and (vp / "indexes" / "repo-carryover.md").exists()
assert len(list((vp / "knowledge").glob("*.md"))) == 3

# round-trip: edit a knowledge note's first paragraph → import detects it and applies it to the store
note = sorted((vp / "knowledge").glob("*.md"))[0]
t = note.read_text()
mid = re.search(r'^id: "?([^"\n]+)', t, re.M).group(1)
head, _, rest = t.partition("\n---\n")
lines = rest.split("\n")
for i, ln in enumerate(lines):
    if ln.strip():
        lines[i] = "EDITED IN OBSIDIAN"
        break
note.write_text(head + "\n---\n" + "\n".join(lines))
dry = cs.import_vault(V)
assert any(c["id"] == mid and c["content"] == "EDITED IN OBSIDIAN" for c in dry["changed"]), dry
assert cs.import_vault(V, apply=True)["applied"] == 1
assert {m["id"]: m for m in cs.export()}[mid]["content"] == "EDITED IN OBSIDIAN"

# prune: an orphan carrying our QUOTED marker is removed; a user's own note is kept
(vp / "entities" / "orphan.md").write_text('---\nsource: "carryover"\n---\nstale\n')
(vp / "entities" / "mine.md").write_text("# my own note\n")
cs.export_vault(V)
assert not (vp / "entities" / "orphan.md").exists(), "orphan must be pruned"
assert (vp / "entities" / "mine.md").exists(), "user note must be kept"

print("test_vault: all passed")
