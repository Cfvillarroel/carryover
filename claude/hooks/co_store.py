#!/usr/bin/env python3
"""carryover memory backend. Dispatches to headroom if it's installed, else to a
built-in SQLite store at ~/.carryover/memory.db. export() emits the SAME shape as
headroom's `memory export`, so recall/forget/dashboard work unchanged either way."""
import json
import os
import sqlite3
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HR_BIN = HOME / ".headroom" / "venv" / "bin" / "headroom"
HR_DB = os.environ.get("HEADROOM_DB", str(HOME / ".headroom" / "memory.db"))
CO_DB = str(HOME / ".carryover" / "memory.db")
ACTIVITY = str(HOME / ".carryover" / "activity.jsonl")
SAVINGS = HOME / ".headroom" / "proxy_savings.json"


def _headroom():
    return str(HR_BIN) if HR_BIN.exists() else None


def backend():
    """('headroom'|'builtin', db_path) — which store is active."""
    return ("headroom", HR_DB) if _headroom() else ("builtin", CO_DB)


def _conn():
    Path(CO_DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(CO_DB)
    c.execute("""CREATE TABLE IF NOT EXISTS memories(
        id TEXT PRIMARY KEY, content TEXT NOT NULL, created_at TEXT,
        importance REAL DEFAULT 0.7, access_count INTEGER DEFAULT 0, metadata TEXT)""")
    return c


def export():
    """List of memories in headroom's export shape, from whichever backend is active."""
    hr = _headroom()
    if hr:
        tmp = tempfile.mktemp(suffix=".json")
        try:
            subprocess.run([hr, "memory", "export", "--output", tmp, "--db-path", HR_DB],
                           capture_output=True, timeout=25)
            return json.load(open(tmp))
        except Exception:
            return []
        finally:
            if os.path.exists(tmp):
                os.unlink(tmp)
    c = _conn()
    rows = c.execute("SELECT id,content,created_at,importance,access_count,metadata FROM memories").fetchall()
    c.close()
    return [{"id": r[0], "content": r[1], "created_at": r[2], "importance": r[3],
             "access_count": r[4], "entity_refs": [], "metadata": json.loads(r[5] or "{}")} for r in rows]


async def save(content, uid, importance=0.7, facts=None, entities=None, relationships=None, metadata=None):
    metadata = metadata or {}
    hr = _headroom()
    if hr:
        from headroom.memory.easy import Memory  # only when headroom is the backend (needs its venv)
        m = Memory(backend="local", db_path=HR_DB)
        mid = await m.save(content=content, user_id=uid, importance=float(importance),
                           facts=facts, entities=entities, relationships=relationships, metadata=metadata)
        await m.close()
        return mid
    mid = str(uuid.uuid4())
    c = _conn()
    c.execute("INSERT INTO memories(id,content,created_at,importance,access_count,metadata) VALUES(?,?,?,?,0,?)",
              (mid, content, datetime.now(timezone.utc).isoformat(), float(importance),
               json.dumps(metadata, ensure_ascii=False)))
    c.commit()
    c.close()
    return mid


def delete(ids):
    ids = [i for i in ids if i]
    if not ids:
        return 0
    hr = _headroom()
    if hr:
        n = 0
        for i in ids:
            try:
                r = subprocess.run([hr, "memory", "delete", i, "--db-path", HR_DB, "--force"],
                                   capture_output=True, timeout=15)
                n += (r.returncode == 0)
            except Exception:
                pass
        return n
    c = _conn()
    c.executemany("DELETE FROM memories WHERE id=?", [(i,) for i in ids])
    n = c.total_changes
    c.commit()
    c.close()
    return n


def edit(mid, content=None, importance=None):
    if not mid:
        return False
    hr = _headroom()
    if hr:
        cmd = [hr, "memory", "edit", mid, "--db-path", HR_DB]
        if content not in (None, ""):
            cmd += ["--content", content]
        if importance not in (None, ""):
            cmd += ["--importance", str(importance)]
        try:
            return subprocess.run(cmd, capture_output=True, timeout=15).returncode == 0
        except Exception:
            return False
    sets, args = [], []
    if content not in (None, ""):
        sets.append("content=?"); args.append(content)
    if importance not in (None, ""):
        sets.append("importance=?"); args.append(float(importance))
    if not sets:
        return False
    args.append(mid)
    c = _conn()
    c.execute(f"UPDATE memories SET {','.join(sets)} WHERE id=?", args)
    ok = c.total_changes > 0
    c.commit()
    c.close()
    return ok


def stats():
    hr = _headroom()
    if hr:
        try:
            import re
            r = subprocess.run([hr, "memory", "stats", "--db-path", HR_DB],
                               capture_output=True, text=True, timeout=15)
            m = re.search(r"Total Memories:\s*(\d+)", r.stdout)
            return int(m.group(1)) if m else 0
        except Exception:
            return 0
    c = _conn()
    n = c.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
    c.close()
    return n


def log_activity(event, repo="general", n=0, **extra):
    """Append one context-management event to ~/.carryover/activity.jsonl (fail-safe)."""
    try:
        import datetime
        Path(ACTIVITY).parent.mkdir(parents=True, exist_ok=True)
        rec = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(),
               "event": event, "repo": repo or "general", "n": n}
        rec.update(extra)
        with open(ACTIVITY, "a") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def load_activity(limit=5000):
    try:
        with open(ACTIVITY) as f:
            return [json.loads(ln) for ln in f.read().splitlines()[-limit:] if ln.strip()]
    except Exception:
        return []


def load_savings():
    """headroom proxy savings (lifetime + session), or None if headroom isn't installed."""
    if not SAVINGS.exists():
        return None
    try:
        d = json.loads(SAVINGS.read_text())
        return {"lifetime": d.get("lifetime") or {}, "session": d.get("display_session") or {}}
    except Exception:
        return None

