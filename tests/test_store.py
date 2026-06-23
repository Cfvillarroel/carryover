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

# --- recall / scope / supersede / groups / import (cross-tool memory features) ---
m2 = asyncio.run(cs.save(content="old: uses MySQL", uid="default", importance=0.8,
                         metadata={"source": "mem-save", "repo": "other-repo"}))
m3 = asyncio.run(cs.save(content="new: uses Postgres", uid="default", importance=0.8,
                         metadata={"source": "mem-save", "repo": "other-repo"}))
assert cs.search("anything") is None  # builtin has no embedder → recall falls back to keyword
r = cs.recall(query=None, repos={"other-repo"})  # scope filter
assert {x["metadata"]["repo"] for x in r} == {"other-repo"} and len(r) == 2
assert cs.supersede(m2, m3) is True  # hide the stale one
r = cs.recall(query=None, repos={"other-repo"})
assert [x["id"] for x in r] == [m3], "superseded memory must be dropped from recall"
open(os.path.join(os.environ["HOME"], ".carryover", "groups.conf"), "w").write("carryover other-repo\n")
assert cs.group_for("carryover") == {"carryover", "other-repo"}  # grouped repos share recall
assert cs.rank_score({"importance": 0.9, "access_count": 3}) > cs.rank_score({"importance": 0.4, "access_count": 0})
exp = tempfile.mktemp(suffix=".json")
__import__("json").dump(cs.export(), open(exp, "w"))
assert cs.import_(exp) == 0  # all ids already present → dedup, no dupes
assert cs.delete([m2, m3]) == 2

assert cs.delete([mid]) == 1
assert cs.stats() == 0

print("test_store: all passed")
