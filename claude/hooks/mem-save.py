#!/usr/bin/env python3
"""carryover structured-knowledge save worker.

Writes a memory into headroom's local store (SQLite + HNSW vectors + graph) with
structured knowledge: facts, typed entities and relationships — optimized for fast
semantic + graph queries. Also mirrors the structure into `metadata` so it shows up
in `headroom memory export` (and therefore in the co-dash dashboard).

Usage (normally called in the background by mem-save.sh):
    mem-save.py <db_path> <user_id> <payload.json>
payload.json: {content, facts[], entities[{entity,type}], relationships[{source,relationship,destination}],
               category, tags[], importance}
"""
import asyncio
import json
import os
import sys

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")

from headroom.memory.easy import Memory  # noqa: E402


def norm_entities(ents):
    out = []
    for e in ents or []:
        if isinstance(e, str):
            out.append({"entity": e, "entity_type": "concept"})
        else:
            name = e.get("entity") or e.get("name")
            if name:
                out.append({"entity": name, "entity_type": e.get("entity_type") or e.get("type") or "concept"})
    return out


async def main():
    db, uid, payload_path = sys.argv[1], sys.argv[2], sys.argv[3]
    repo = sys.argv[4] if len(sys.argv) > 4 else ""
    payload = json.load(open(payload_path))
    try:
        os.unlink(payload_path)
    except OSError:
        pass

    facts = payload.get("facts") or None
    entities = norm_entities(payload.get("entities")) or None
    rels = payload.get("relationships") or None
    content = payload.get("content") or (facts[0] if facts else "")
    if not content:
        return

    # mirror the structure into metadata so `memory export` (and the dashboard) can read it
    md = {"source": "mem-save", "repo": payload.get("repo") or repo or "general"}
    if payload.get("category"):
        md["category"] = payload["category"]
    if payload.get("tags"):
        md["tags"] = payload["tags"]
    if facts:
        md["facts"] = facts
    if entities:
        md["entities"] = entities
    if rels:
        md["relationships"] = rels

    m = Memory(backend="local", db_path=db)
    mid = await m.save(
        content=content,
        user_id=uid,
        importance=float(payload.get("importance", 0.7)),
        facts=facts,
        entities=entities,
        relationships=rels,
        metadata=md,
    )
    await m.close()
    print(mid)


if __name__ == "__main__":
    asyncio.run(main())
