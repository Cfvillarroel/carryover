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
GROUPS = str(HOME / ".carryover" / "groups.conf")  # repo groups: one group per line, repos space/comma-separated
LINKS = str(HOME / ".carryover" / "links.conf")    # workspace connections: one group per line, workspace names space/comma-separated
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


def touch(ids):
    """Bump access_count (+ last_accessed where the column exists) for recalled memories.
    Fail-safe: any error returns 0 and never breaks a recall. headroom has no CLI for this,
    so we UPDATE its db directly.
    # ponytail: direct UPDATE on headroom's db; switch to a CLI if headroom ever adds one."""
    ids = [i for i in ids if i]
    if not ids:
        return 0
    hr = _headroom()
    db = HR_DB if hr else CO_DB
    qs = ",".join("?" * len(ids))
    try:
        if not hr:
            Path(CO_DB).parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(db, timeout=5)
        c.execute("PRAGMA busy_timeout=3000")  # proxy may be reading headroom's db
        now = datetime.now(timezone.utc).isoformat()
        cols = {r[1] for r in c.execute("PRAGMA table_info(memories)")}
        if "last_accessed" in cols:
            c.execute(f"UPDATE memories SET access_count=COALESCE(access_count,0)+1, last_accessed=? WHERE id IN ({qs})",
                      [now, *ids])
        else:
            c.execute(f"UPDATE memories SET access_count=COALESCE(access_count,0)+1 WHERE id IN ({qs})", ids)
        n = c.total_changes
        c.commit()
        c.close()
        return n
    except Exception:
        return 0


def search(query, uid=None, k=20):
    """Semantic search via headroom's embedder (HNSW + graph). Returns [{id,content,metadata,score}]
    or None when there's no semantic backend (builtin store) — callers fall back to keyword."""
    if not _headroom():
        return None
    try:
        import asyncio
        import warnings
        warnings.filterwarnings("ignore")  # hush the embedder's FutureWarning/HF notices
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
        from headroom.memory.easy import Memory  # noqa: E402
        uid = uid or os.environ.get("HEADROOM_USER_ID") or Path.home().name

        async def _run():
            m = Memory(backend="local", db_path=HR_DB)
            res = await m.search(query=query, user_id=uid, top_k=k)
            await m.close()
            return res
        return [{"id": r.id, "content": r.content, "metadata": r.metadata or {},
                 "score": float(getattr(r, "score", 0.0) or 0.0)} for r in asyncio.run(_run())]
    except Exception:
        return None


def is_superseded(m):
    """A memory replaced by a newer one (headroom column or builtin metadata) — skip in recall."""
    return bool(m.get("superseded_by") or (m.get("metadata") or {}).get("superseded_by"))


def rank_score(m, now=None):
    """Recall rank when there's no semantic query: importance × recency-decay × reuse-boost.
    Recency half-life ~60d (floored so old-but-important memories don't vanish)."""
    import math
    imp = float(m.get("importance") or 0.5)
    ac = int(m.get("access_count") or 0)
    rec = 1.0
    ts = m.get("last_accessed") or m.get("created_at") or ""
    try:
        t = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        now = now or datetime.now(timezone.utc)
        age_days = max(0.0, (now - t).total_seconds() / 86400)
        rec = 0.5 ** (age_days / 60.0)
    except Exception:
        pass
    return imp * (0.4 + 0.6 * rec) * (1.0 + math.log1p(ac))


def group_for(repo):
    """Set of repos that share recall with `repo` (its group), or {repo} if ungrouped.
    groups.conf: one group per line, repo names separated by spaces/commas; # starts a comment."""
    repos = {repo} if repo else set()
    try:
        for ln in open(GROUPS):
            ln = ln.split("#", 1)[0].strip()
            if ln and repo in (members := set(ln.replace(",", " ").split())):
                repos |= members
    except Exception:
        pass
    return repos


def recall(query=None, repos=None, k=10, uid=None, semantic=True):
    """Unified recall used by recall.sh, the auto-recall hook and the MCP server.
    - repos: iterable of repo names to scope to (None = every repo).
    - query + semantic + headroom → semantic search; else keyword over export().
    - no query → decay-ranked browse (importance × recency × reuse).
    Always drops superseded memories and scopes by repo. Returns a list of memory dicts."""
    scope = set(repos) if repos else None

    def in_scope(m):
        return scope is None or (m.get("metadata") or {}).get("repo", "general") in scope

    if query and semantic:
        sem = search(query, uid=uid, k=max(k * 3, 30))  # over-fetch, then filter/scope
        if sem:
            return [m for m in sem if not is_superseded(m) and in_scope(m)][:k]

    data = [m for m in export() if not is_superseded(m) and in_scope(m)]
    if query:
        words = query.lower().split()

        def hay(m):
            md = m.get("metadata") or {}
            ents = [e.get("entity", "") if isinstance(e, dict) else e
                    for e in (md.get("entities") or m.get("entity_refs") or [])]
            parts = [m.get("content", "")] + (md.get("facts") or []) + ents + (md.get("tags") or [])
            return " ".join(str(p) for p in parts).lower()
        data = [m for m in data if all(w in hay(m) for w in words)]
    data.sort(key=rank_score, reverse=True)
    return data[:k]


def supersede(old_id, new_id):
    """Mark old_id as replaced by new_id so recall skips the stale one. Fail-safe."""
    if not old_id or not new_id:
        return False
    hr = _headroom()
    db = HR_DB if hr else CO_DB
    try:
        if not hr:
            Path(CO_DB).parent.mkdir(parents=True, exist_ok=True)
        c = sqlite3.connect(db, timeout=5)
        c.execute("PRAGMA busy_timeout=3000")
        cols = {r[1] for r in c.execute("PRAGMA table_info(memories)")}
        if "superseded_by" in cols:
            c.execute("UPDATE memories SET superseded_by=? WHERE id=?", (new_id, old_id))
        else:  # builtin: stash it in metadata json
            row = c.execute("SELECT metadata FROM memories WHERE id=?", (old_id,)).fetchone()
            if not row:
                c.close()
                return False
            md = json.loads(row[0] or "{}")
            md["superseded_by"] = new_id
            c.execute("UPDATE memories SET metadata=? WHERE id=?",
                      (json.dumps(md, ensure_ascii=False), old_id))
        ok = c.total_changes > 0
        c.commit()
        c.close()
        return ok
    except Exception:
        return False


def whoami():
    """Workspace identity. Prefer Conductor's own CONDUCTOR_WORKSPACE_NAME — it's the name shown
    in the app, stable regardless of the git branch and resolvable from any subdir. Fall back to
    the cwd basename for plain terminals outside Conductor."""
    return os.environ.get("CONDUCTOR_WORKSPACE_NAME") or Path.cwd().name


def project():
    """Conductor project name = the folder ABOVE the workspace (~/conductor/workspaces/<project>/
    <workspace>) — what you see as the heading in the app. Lets you address a whole project
    (e.g. 'proyectate-back') instead of the internal workspace/city name. '' outside Conductor."""
    p = os.environ.get("CONDUCTOR_WORKSPACE_PATH") or os.getcwd()
    return os.path.basename(os.path.dirname(p)).lower() if "/conductor/workspaces/" in p else ""


def codename():
    """Stable workspace address = the worktree FOLDER name (e.g. 'jerusalem'). Conductor rewrites
    CONDUCTOR_WORKSPACE_NAME to the branch/task title after the first interaction, but never renames
    the folder — so this is the durable name to address a workspace by, surviving renames."""
    p = os.environ.get("CONDUCTOR_WORKSPACE_PATH") or os.getcwd()
    return os.path.basename(p).lower()


def identities(who=None):
    """Every name this workspace answers to as a recipient: its workspace name, its stable codename,
    AND its project name. So `co-send <project>` reaches any workspace of that project and
    `co-send <workspace>` (city codename) a specific one even after Conductor renames it."""
    ids = {(who or whoami()).lstrip("@").lower()}
    if who is None:                       # for THIS workspace we also answer to our stable codename
        ids.add(codename())
    p = project()
    if p:
        ids.add(p)
    return ids


async def send_msg(to, body, frm=None, importance=0.0, handover=False):
    """Drop a message into mailbox '@<to>' as a normal memory. `to` is a workspace name or
    'all' (broadcast). Reuses save() (headroom/builtin dual). Returns the new memory id.
    Lives in mailbox '@<to>' so normal recall (scoped to real repos) never sees it.
    handover=True marks it as a task to execute on arrival (see /handover)."""
    to = to.lstrip("@").lower()
    md = {"kind": "msg", "repo": "@" + to, "to": to,
          "from": (frm or project() or whoami()), "source": "co-send"}
    if handover:
        md["handover"] = True
    uid = os.environ.get("HEADROOM_USER_ID") or Path.home().name
    return await save(content=body, uid=uid, importance=float(importance), metadata=md)


def notify(to, body):
    """Best-effort macOS desktop ping so a handover to an IDLE workspace gets noticed (Conductor has
    no API to wake a sleeping workspace). No-op off macOS / if osascript is missing."""
    title = "📬 handover → " + to
    text = " ".join((body or "").split())[:120]
    # AppleScript string literal: escape \ and " only, keep UTF-8 literal (json.dumps would emit
    # \uXXXX escapes that osascript rejects as unknown tokens).
    esc = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'
    try:
        subprocess.run(["osascript", "-e",
                        "display notification %s with title %s" % (esc(text), esc(title))],
                       timeout=5, check=False)
    except Exception:
        pass


def inbox(who=None, consume=False):
    """Pending (non-consumed) messages for workspace `who` (default whoami) + '@all'
    broadcasts, newest first. 'Consumed' == superseded, so recall's superseded-drop filters
    delivered ones for free. consume=True marks them delivered in the same call."""
    boxes = {"@" + i for i in identities(who)} | {"@all"}
    msgs = [m for m in recall(query=None, repos=boxes, k=200)
            if (m.get("metadata") or {}).get("kind") == "msg"]
    msgs.sort(key=lambda m: m.get("created_at") or "", reverse=True)
    if consume:
        for m in msgs:
            if m.get("id"):
                supersede(m["id"], m["id"])  # self-supersede == 'consumed', no successor needed
    return msgs


def _read_links():
    """Connection groups from ~/.carryover/links.conf — one group per line, workspace names
    space/comma separated, '#' starts a comment. Same shape as groups.conf."""
    out = []
    try:
        for ln in open(LINKS):
            ln = ln.split("#", 1)[0].strip()
            m = set(ln.replace(",", " ").split())
            if m:
                out.append(m)
    except Exception:
        pass
    return out


def _write_links(groups):
    os.makedirs(os.path.dirname(LINKS), exist_ok=True)
    with open(LINKS, "w") as f:
        for g in groups:
            if len(g) >= 2:                       # a connection needs at least two workspaces
                f.write(" ".join(sorted(g)) + "\n")


def peers(who=None):
    """Workspaces connected to this one (its co-say recipients). Matches on either the workspace
    name or the project name, so a connection works whichever you used to make it."""
    ids = identities(who)
    out = set()
    for g in _read_links():
        if g & ids:
            out |= g
    return out - ids


def connect(ws, me=None):
    """Connect this workspace (whoami) with `ws`, two-way and persistent. Merges any groups the
    two already belong to. Returns me's resulting peer set."""
    me = (me or codename()).lstrip("@").lower()
    ws = ws.lstrip("@").lower()
    if not ws or ws == me:
        return peers(me)
    merged, rest = {me, ws}, []
    for g in _read_links():
        if g & merged:
            merged |= g
        else:
            rest.append(g)
    rest.append(merged)
    _write_links(rest)
    return merged - {me}


def disconnect(ws, me=None):
    """Remove `ws` from this workspace's connection group (drops the line if fewer than two remain).
    Matches this workspace by either its workspace name or project name."""
    ids = identities(me)
    ws = ws.lstrip("@").lower()
    out = []
    for g in _read_links():
        if (g & ids) and ws in g:
            g = g - {ws}
        if len(g) >= 2:
            out.append(g)
    _write_links(out)
    return peers(me)


def import_(path):
    """Import memories from a JSON export (cross-machine portability). headroom → its CLI;
    builtin → insert rows we don't already have (dedup by id). Returns imported count (or -1)."""
    hr = _headroom()
    if hr:
        try:
            import subprocess
            r = subprocess.run([hr, "memory", "import", path, "--db-path", HR_DB],
                               capture_output=True, text=True, timeout=120)
            return -1 if r.returncode == 0 else 0
        except Exception:
            return 0
    try:
        data = json.load(open(path))
    except Exception:
        return 0
    try:
        c = _conn()
        have = {r[0] for r in c.execute("SELECT id FROM memories")}
        n = 0
        for m in data:
            mid = m.get("id") or str(uuid.uuid4())
            if mid in have:
                continue
            c.execute("INSERT OR IGNORE INTO memories(id,content,created_at,importance,access_count,metadata) "
                      "VALUES(?,?,?,?,?,?)",
                      (mid, m.get("content", ""), m.get("created_at"), float(m.get("importance", 0.7) or 0.7),
                       int(m.get("access_count", 0) or 0), json.dumps(m.get("metadata") or {}, ensure_ascii=False)))
            n += 1
        c.commit()
        c.close()
        return n
    except Exception:
        return 0


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

