#!/usr/bin/env python3
"""carryover MCP server — exposes carryover's shared memory to ANY MCP client (Cursor,
Claude Desktop, Windsurf, …), not just Claude Code. Two tools: `recall` and `remember`.

stdlib only, no deps. Speaks MCP over stdio (newline-delimited JSON-RPC 2.0). Run it with
headroom's venv python for SEMANTIC recall, or plain python3 for keyword recall:

    ~/.headroom/venv/bin/python ~/.carryover/co-mcp.py     # semantic (headroom present)
    python3 ~/.carryover/co-mcp.py                          # keyword (built-in store)

Register in an MCP client, e.g. Cursor/Claude Desktop mcpServers config:
    {"carryover": {"command": "<that python>", "args": ["<path>/co-mcp.py"]}}
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.realpath(__file__)))
import co_store  # noqa: E402

TOOLS = [
    {"name": "recall",
     "description": "Recall stored knowledge by meaning (semantic when headroom is present, "
                    "else keyword). Optionally scope to a repo and its group.",
     "inputSchema": {"type": "object", "properties": {
         "query": {"type": "string", "description": "what to recall"},
         "repo": {"type": "string", "description": "limit to this repo and its group; omit for all repos"},
         "limit": {"type": "integer", "description": "max results (default 10)"}},
         "required": ["query"]}},
    {"name": "remember",
     "description": "Save a fact to carryover's shared memory so it carries across tools, repos and sessions.",
     "inputSchema": {"type": "object", "properties": {
         "content": {"type": "string", "description": "the fact to remember"},
         "repo": {"type": "string", "description": "repo this knowledge belongs to (default: general/shared)"},
         "importance": {"type": "number", "description": "0..1 (default 0.7)"}},
         "required": ["content"]}},
]


def _uid():
    return os.environ.get("HEADROOM_USER_ID") or os.environ.get("USER") or "default"


def _recall(args):
    repo = args.get("repo")
    repos = co_store.group_for(repo) if repo else None
    res = co_store.recall(query=args.get("query"), repos=repos, k=int(args.get("limit", 10) or 10))
    co_store.touch([m.get("id") for m in res if m.get("id")])  # surfaced = used
    out = []
    for m in res:
        md = m.get("metadata") or {}
        out.append(f"[{md.get('repo', 'general')}] {(m.get('content') or '').strip()}")
    return "\n".join(out) or "(nothing found)"


def _remember(args):
    import asyncio
    md = {"source": "mcp", "repo": args.get("repo") or "general"}
    mid = asyncio.run(co_store.save(content=args["content"], uid=_uid(),
                                    importance=float(args.get("importance", 0.7) or 0.7), metadata=md))
    return f"remembered ({mid})"


HANDLERS = {"recall": _recall, "remember": _remember}


def _send(obj):
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def _reply(rid, result=None, error=None):
    msg = {"jsonrpc": "2.0", "id": rid}
    msg["error" if error else "result"] = error or result
    _send(msg)


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        method, rid = req.get("method"), req.get("id")
        if method == "initialize":
            _reply(rid, {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}},
                         "serverInfo": {"name": "carryover", "version": "1.0.0"}})
        elif method == "tools/list":
            _reply(rid, {"tools": TOOLS})
        elif method == "tools/call":
            p = req.get("params") or {}
            name, args = p.get("name"), (p.get("arguments") or {})
            try:
                text = HANDLERS[name](args)
                _reply(rid, {"content": [{"type": "text", "text": text}]})
            except Exception as e:
                _reply(rid, {"content": [{"type": "text", "text": f"error: {e}"}], "isError": True})
        elif method == "notifications/initialized" or rid is None:
            pass  # notification: no response
        else:
            _reply(rid, error={"code": -32601, "message": f"method not found: {method}"})


if __name__ == "__main__":
    main()
