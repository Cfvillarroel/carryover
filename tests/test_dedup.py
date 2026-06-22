#!/usr/bin/env python3
"""Unit tests for mem-save dedup logic. The headroom import in mem-save.py is lazy,
so the pure functions (_norm/_toks/_dup) import without headroom installed."""
import importlib.util
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
spec = importlib.util.spec_from_file_location("memsave", ROOT / "claude/hooks/mem-save.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

# _norm: case / whitespace / surrounding punctuation
assert m._norm("  Hello,  World. ") == "hello,  world".replace("  ", " ")
assert m._norm("Fact one.") == m._norm("fact one")
assert m._norm(None) == ""

# _toks
assert m._toks("a b a") == {"a", "b"}

# _dup: normalized-exact match (case/punct insensitive)
seen = {m._norm("carryover on")}
tk = [m._toks("carryover on")]
assert m._dup("Carryover On.", seen, tk) is True          # same statement, different formatting
assert m._dup("carryover off", seen, tk) is False         # short + distinct → kept

# _dup: high token-overlap (Jaccard) near-dupe vs distinct refinement
ex = "the carryover update command pulls latest and re-syncs the machine state"
seen2 = {m._norm(ex)}
tk2 = [m._toks(ex)]
assert m._dup(ex + " now", seen2, tk2) is True            # ~0.9 overlap → dupe
assert m._dup("uses Python 3.13 in the headroom venv", seen2, tk2) is False  # different → kept

print("test_dedup: all passed")
