#!/usr/bin/env python3
"""Handover + rename-proof addressing. Forces the builtin backend (HOME temp, no ~/.headroom) and
checks: (1) a workspace answers to its stable codename even after Conductor renames its title,
(2) a handover sent to that codename reaches it and is tagged, (3) a connection survives our rename."""
import asyncio
import importlib.util
import os
import pathlib
import tempfile

os.environ["HOME"] = tempfile.mkdtemp()          # no ~/.headroom → builtin backend
os.environ.pop("HEADROOM_DB", None)
# a renamed workspace: folder is 'jerusalem', but Conductor rewrote the title to the branch name
os.environ["CONDUCTOR_WORKSPACE_PATH"] = "/x/conductor/workspaces/carryover/jerusalem"
os.environ["CONDUCTOR_WORKSPACE_NAME"] = "error-en-imagen"

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("co_store", ROOT / "claude/hooks/co_store.py")
cs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cs)
assert cs.backend()[0] == "builtin", "should pick builtin without headroom"

# (1) stable codename present despite the rename
assert cs.codename() == "jerusalem"
ids = cs.identities()
assert {"jerusalem", "error-en-imagen", "carryover"} <= ids, ids

# (2) handover addressed by codename reaches the renamed workspace, tagged
mid = asyncio.run(cs.send_msg("jerusalem", "run the migration", handover=True))
assert mid
box = cs.inbox(consume=False)                    # who=None → this workspace's identities
hit = [m for m in box if m.get("id") == mid]
assert hit, "handover sent to codename must reach the renamed workspace"
assert (hit[0].get("metadata") or {}).get("handover") is True
# a plain message lacks the flag
mid2 = asyncio.run(cs.send_msg("jerusalem", "fyi only"))
plain = [m for m in cs.inbox(consume=False) if m.get("id") == mid2]
assert plain and not (plain[0].get("metadata") or {}).get("handover")

# (3) connection stored by codename → survives our own later rename
cs.connect("doha")
assert "doha" in cs.peers()
os.environ["CONDUCTOR_WORKSPACE_NAME"] = "some-other-branch-title"   # renamed again
assert "doha" in cs.peers(), "connection must survive a self-rename (stored by codename)"

print("ok")
