#!/usr/bin/env python3
"""Round-trip test of the built-in SQLite backend. Forces the builtin path by pointing
HOME at a temp dir with no ~/.headroom, and checks the export matches headroom's shape."""
import asyncio
import importlib.util
import os
import pathlib
import tempfile

os.environ["HOME"] = tempfile.mkdtemp()  # no ~/.headroom here → builtin backend
os.environ.pop("HEADROOM_DB", None)

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("co_store", ROOT / "claude/hooks/co_store.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)

assert cs.backend()[0] == "builtin", "should pick builtin without headroom"
assert cs.stats() == 0

mid = asyncio.run(cs.save(
    content="Carryover works standalone", uid="default", importance=0.8,
    facts=["standalone fact"], entities=[{"entity": "carryover", "entity_type": "project"}],
    metadata={"source": "mem-save", "repo": "carryover", "facts": ["standalone fact"], "tags": ["t1"]},
))
assert mid and cs.stats() == 1

data = cs.export()
assert len(data) == 1
m = data[0]
for k in ("id", "content", "created_at", "importance", "access_count", "entity_refs", "metadata"):
    assert k in m, f"export missing headroom-shape key: {k}"
assert m["metadata"]["repo"] == "carryover"
assert m["metadata"]["facts"] == ["standalone fact"]

assert cs.edit(mid, content="edited content", importance=0.9) is True
assert cs.export()[0]["content"] == "edited content"

assert m["access_count"] == 0  # nothing recalled yet
assert cs.touch([mid]) == 1
assert cs.export()[0]["access_count"] == 1
assert cs.touch([mid]) == 1
assert cs.export()[0]["access_count"] == 2
assert cs.touch([]) == 0  # empty is a no-op

assert cs.delete([mid]) == 1
assert cs.stats() == 0

print("test_store: all passed")
