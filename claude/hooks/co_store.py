#!/usr/bin/env python3
"""carryover memory backend. Dispatches to headroom if it's installed, else to a
built-in SQLite store at ~/.carryover/memory.db. export() emits the SAME shape as
headroom's `memory export`, so recall/forget/dashboard work unchanged either way."""
import json
import os
import re
import sqlite3
import subprocess
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()
HR_BIN = HOME / ".headroom" / "venv" / "bin" / "headroom"
HR_DB = os.environ.get("HEADROOM_DB", str(HOME / ".headroom" / "memory.db"))
CO_DB = str(HOME / ".carryover" / "memory.db")
ACTIVITY = str(HOME / ".carryover" / "activity.jsonl")
GROUPS = str(HOME / ".carryover" / "groups.conf")  # repo groups: one group per line, repos space/comma-separated
LINKS = str(HOME / ".carryover" / "links.conf")    # workspace connections: one group per line, workspace names space/comma-separated
TEAMS = str(HOME / ".carryover" / "teams.json")    # named teams: {team: {workspace: role}} — roster on top of the messaging layer
MERGES = str(HOME / ".carryover" / "entity-merges.json")  # semantic entity merges: {canonical: [member names]} — hand-editable
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


MSG_CAP = 4000  # per-message delivery cap; full text always retrievable via `co-mem inbox --all`


def render_msg_lines(m, cap=MSG_CAP):
    """Markdown lines for ONE delivered inbox message. A directed cross-workspace message is a
    single, intentional payload (unlike auto-recalled memories), so we keep it whole: newlines
    preserved (indented under the 'from' header when multi-line), only capped at `cap` as a safety
    valve with a pointer to re-read the rest. Shared by the three delivery hooks so the format,
    cap and handover tag live in one place."""
    md = m.get("metadata") or {}
    b = (m.get("content") or "").strip()
    if len(b) > cap:
        b = b[:cap].rstrip() + "… (truncated — run `co-mem inbox --all` for the full message)"
    tag = " ⚡HANDOVER" if md.get("handover") else ""
    frm = md.get("from", "?")
    if "\n" in b:
        return [f"- **from {frm}:**{tag}"] + ["  " + ln for ln in b.split("\n")]
    return [f"- **from {frm}:**{tag} {b}"]


def inbox(who=None, consume=False, history=False):
    """Messages for workspace `who` (default whoami) + '@all' broadcasts, newest first.
    'Consumed' == superseded, so recall's superseded-drop filters delivered ones for free.
    consume=True marks them delivered in the same call.
    history=True lists ALSO the already-delivered (superseded) messages — read-only, never
    consumes — so `co-mem inbox --all` can re-read what auto-delivery already consumed."""
    boxes = {"@" + i for i in identities(who)} | {"@all"}
    if history:  # include delivered/superseded: bypass recall's superseded-drop, read from export()
        msgs = [m for m in export()
                if (m.get("metadata") or {}).get("kind") == "msg"
                and (m.get("metadata") or {}).get("repo", "") in boxes]
    else:
        msgs = [m for m in recall(query=None, repos=boxes, k=200)
                if (m.get("metadata") or {}).get("kind") == "msg"]
    msgs.sort(key=lambda m: m.get("created_at") or "", reverse=True)
    if consume and not history:  # history mode is read-only
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


# --- teams: a named roster (workspace → role) on top of the messaging layer -------------------------
def _load_teams():
    try:
        with open(TEAMS) as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _save_teams(t):
    p = Path(TEAMS)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(t, indent=2, ensure_ascii=False), encoding="utf-8")


def teams():
    """All teams: {team: {workspace: role}}."""
    return _load_teams()


def team_members(team, role=None):
    """Workspace names in a team, optionally filtered by role."""
    m = _load_teams().get((team or "").strip().lower(), {})
    role = (role or "").strip().lower()
    return [w for w, r in m.items() if not role or (r or "").lower() == role]


def team_add(team, ws, role="member"):
    """Add/update one member. Creates the team if new. Returns the team's roster (or None)."""
    team = (team or "").strip().lower()
    ws = (ws or "").lstrip("@").strip().lower()
    if not team or not ws or ws == "all":   # 'all' is the broadcast mailbox — never a team member
        return None
    t = _load_teams()
    t.setdefault(team, {})[ws] = (role or "member").strip().lower() or "member"
    _save_teams(t)
    return t[team]


def team_remove(team, ws=None):
    """Remove one member, or the whole team if ws is None. Returns the remaining roster."""
    team = (team or "").strip().lower()
    t = _load_teams()
    if team not in t:
        return None
    if ws:
        t[team].pop((ws or "").lstrip("@").strip().lower(), None)
        if not t[team]:
            del t[team]
    else:
        del t[team]
    _save_teams(t)
    return t.get(team, {})


def team_set(team, members):
    """Replace a team's whole roster with {workspace: role}; empty members deletes the team."""
    team = (team or "").strip().lower()
    if not team or not isinstance(members, dict):
        return False
    clean = {}
    for w, r in members.items():
        w = (w or "").lstrip("@").strip().lower()
        if w and w != "all":            # 'all' is the broadcast mailbox — never a team member
            clean[w] = (str(r) or "member").strip().lower() or "member"
    t = _load_teams()
    if clean:
        t[team] = clean
    else:
        t.pop(team, None)
    _save_teams(t)
    return True


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


# --- Obsidian vault: materialize export() as .md so the wiki + knowledge open together -----------
# The wiki is already .md; this renders the SQLite knowledge as notes + entity stubs so Obsidian's
# native graph view reproduces carryover's knowledge graph (no plugins). Two-way: content + importance
# of a memory note round-trip back via edit(); facts/entities/relationships are derived (read-only).

def _slug(name, taken=None):
    """Filesystem-safe, deduped slug for a note filename. The entity note's H1 keeps the exact name,
    so `[[Name]]` resolves regardless of the slug."""
    s = re.sub(r"[^\w.-]+", "-", (name or "").strip().lower()).strip("-")[:120] or "unnamed"
    if taken is not None:
        base, i = s, 2
        while s in taken:
            s = f"{base}-{i}"; i += 1
        taken.add(s)
    return s


def _tag(s):
    """Inline #tag form — Obsidian tags can't hold spaces or most punctuation."""
    return "#" + re.sub(r"[^\w/-]+", "-", str(s).strip()).strip("-")


def _yaml_val(v):
    """Value for our own flat frontmatter (str/number/flat string-list). We generate AND parse this,
    so it needn't cover general YAML."""
    if isinstance(v, list):
        return "[" + ", ".join(_yaml_val(x) for x in v) + "]"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return str(v)
    return '"' + str(v).replace("\\", "\\\\").replace('"', '\\"') + '"'


def _frontmatter(d):
    lines = ["---"]
    for k, v in d.items():
        if v is None or v == "" or v == []:
            continue
        lines.append(f"{k}: {_yaml_val(v)}")
    lines.append("---")
    return "\n".join(lines)


def _parse_frontmatter(text):
    """(dict, body) from a leading --- block. Parses only the flat scalars we write (id, importance…);
    body is everything after the closing ---."""
    d, body = {}, text
    if text.startswith("---"):
        lines = text.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                for ln in lines[1:i]:
                    k, sep, v = ln.partition(":")
                    if sep:
                        d[k.strip()] = v.strip().strip('"')
                body = "\n".join(lines[i + 1:])
                break
    return d, body


def _content_before_sections(body):
    """The human-editable region of a memory note = text after the frontmatter up to the first
    '## ' heading or a trailing inline-#tags line (Facts/Entities/Relationships/tags are generated).
    # ponytail: memory contents are 1-liners, so a literal '## ' inside content is a non-issue."""
    out = []
    for ln in body.split("\n"):
        s = ln.strip()
        if s.startswith("## "):
            break
        if s and all(t.startswith("#") for t in s.split()):  # inline #tags line → not content
            break
        out.append(ln)
    return "\n".join(out).strip()


def _ent_key(name):
    """Canonical key for merging entity name variants: case/separators (HarrySchool == harry-school ==
    'Harry School') and a trailing file extension (carryover-doctor == carryover-doctor.sh)."""
    s = re.sub(r"\.(sh|py|ts|tsx|js|jsx|mjs|json|md|txt|ya?ml|sql|css|scss|html|toml|cfg|ini)$",
               "", (name or "").strip().lower())
    return re.sub(r"[^a-z0-9]+", "", s)


def _is_noise_entity(display):
    """Drop pure-number / single-char 'entities' (e.g. '3000') — they only fragment the graph."""
    s = (display or "").strip()
    return len(s) < 2 or re.fullmatch(r"[\d\W]+", s) is not None


def _resolved_entities(m, resolver):
    """(entities, relationships) for a memory, each name mapped to its canonical display via
    `resolver` (None → dropped as noise). Endpoints of a relationship both feed the entity list."""
    md = m.get("metadata") or {}
    raw = [e.get("entity") if isinstance(e, dict) else e for e in (md.get("entities") or [])]
    raw += list(m.get("entity_refs") or [])
    ents = []
    for n in raw:
        d = resolver.get(n, n)
        if d and d not in ents:
            ents.append(d)
    rels = []
    for r in (md.get("relationships") or []):
        s = resolver.get(r.get("source"), r.get("source"))
        t = resolver.get(r.get("destination"), r.get("destination"))
        if s and t:
            rels.append((s, r.get("relationship", "→"), t))
            for d in (s, t):
                if d not in ents:
                    ents.append(d)
    return ents, rels


def _first_line(m):
    """First non-empty line of the content — the human-readable 1-liner used for filename + alias."""
    return ((m.get("content") or "").strip().splitlines() or [""])[0].strip()


def _memory_md(m, resolver):
    md = m.get("metadata") or {}
    tags = [t for t in (md.get("tags") or []) if t]
    repo = md.get("repo", "general")
    ents, rels = _resolved_entities(m, resolver)
    fm = {"id": m.get("id", ""), "source": "carryover", "repo": repo,
          "category": md.get("category", ""), "importance": round(float(m.get("importance") or 0.5), 3),
          "access_count": int(m.get("access_count") or 0), "created_at": m.get("created_at", ""),
          "tags": tags, "entities": [f"[[{e}]]" for e in ents]}  # links as a property → Bases + graph
    first = _first_line(m)
    if first:
        fm["aliases"] = [first]  # switcher / [[ ]] search by the full 1-liner, not the truncated filename
    body = [_frontmatter(fm), "", (m.get("content") or "").strip()]
    facts = [f for f in (md.get("facts") or []) if f]
    if facts:
        body += ["", "## Facts"] + [f"- {f}" for f in facts]
    if ents:
        body += ["", "## Entities", " · ".join(f"[[{e}]]" for e in ents)]
    if rels:
        body += ["", "## Relationships"]
        body += [f"- [[{s}]] — {v} → [[{t}]]" for s, v, t in rels]
    if tags:
        body += ["", " ".join(_tag(t) for t in tags)]   # graph colours by folder (graph.json), not repo tags
    return "\n".join(body) + "\n"


def _existing_entity_desc(path):
    """Pull the human/LLM description out of an entity note (the text after the '> type' line) so a
    regenerate preserves it. Returns '' if none."""
    try:
        _, b = _parse_frontmatter(Path(path).read_text(encoding="utf-8"))
    except Exception:
        return ""
    lines, out, seen = b.split("\n"), [], False
    for ln in lines:
        if seen:
            out.append(ln)
        elif ln.lstrip().startswith(">"):
            seen = True
    return "\n".join(out).strip()


def _entity_md(name, etype="", aliases=None, desc="", links=0):
    fm = {"source": "carryover", "entity_type": etype or "unknown", "links": links}
    if aliases:
        fm["aliases"] = aliases
    head = f"> {etype or 'entity'}" + (f" · {links} links" if links else "")
    body = [_frontmatter(fm), "", f"# {name}", "", head]
    if desc:
        body += ["", desc.strip()]
    return "\n".join(body) + "\n"


def _home_md(counts, repo_rows, top_ents):
    body = [_frontmatter({"source": "carryover"}), "", "# carryover knowledge", "",
            f"> {counts['memories']} memories · {counts['entities']} entities · {len(repo_rows)} repos",
            "", "## Repos"]
    body += [f"- [[repo-{_slug(r)}|{r}]] — {n} memories" for r, n in repo_rows]
    body += ["", "## Most-connected entities"]
    body += [f"- [[{name}]] — {c}" for name, c in top_ents]
    return "\n".join(body) + "\n"


def _repo_index_md(repo, mems, top_ents, note_stem):
    by_cat = defaultdict(list)
    for m in mems:
        by_cat[(m.get("metadata") or {}).get("category") or "general"].append(m)
    body = [_frontmatter({"source": "carryover", "repo": repo}), "", f"# {repo}", "",
            f"> {len(mems)} memories"]
    for cat in sorted(by_cat):
        body += ["", f"## {cat}"]
        for m in by_cat[cat]:
            label = ((m.get("content") or "").strip().split("\n")[0][:80] or m.get("id", "")).replace("[", "").replace("]", "")
            stem = note_stem.get(m.get("id")) or m.get("id", "")  # link the real filename, not the UUID (else broken link → Obsidian ghost note)
            body.append(f"- [[{stem}|{label}]]")
    if top_ents:
        body += ["", "## Top entities"] + [f"- [[{name}]] — {c}" for name, c in top_ents]
    return "\n".join(body) + "\n"


def _prune(folder, keep):
    """Delete generated *.md in `folder` not in `keep` — only files carrying our own
    `source: carryover` marker, so a user's stray note is never removed."""
    n = 0
    for p in Path(folder).glob("*.md"):
        if p.name in keep:
            continue
        try:
            head = p.read_text(encoding="utf-8")[:200].replace('"', '')  # frontmatter quotes the value
            if "source: carryover" in head:
                p.unlink(); n += 1
        except Exception:
            pass
    return n


def _load_merges():
    """alias(lower) -> canonical display, from the hand-editable semantic-merge map
    (~/.carryover/entity-merges.json, shape {canonical: [members]}). Empty/absent → no merges."""
    out = {}
    try:
        for canonical, members in json.loads(Path(MERGES).read_text()).items():
            for m in list(members) + [canonical]:
                out[str(m).strip().lower()] = canonical
    except Exception:
        pass
    return out


def _syntactic_entities(mems):
    """Group raw entity names by _ent_key (case / separators / file extension), pick a display per
    group, drop noise. Returns (syn, gtype): syn maps every raw name to its display (or None if
    noise); gtype maps a display to its entity type. This is the merge layer that needs no LLM."""
    raw_count, raw_type = defaultdict(int), {}

    def see(name, etype=""):
        if name:
            raw_count[name] += 1
            if etype and not raw_type.get(name):
                raw_type[name] = etype

    for m in mems:
        md = m.get("metadata") or {}
        for e in (md.get("entities") or []):
            see(e.get("entity"), e.get("entity_type") or e.get("type", "")) if isinstance(e, dict) else see(e)
        for e in (m.get("entity_refs") or []):
            see(e)
        for r in (md.get("relationships") or []):
            see(r.get("source")); see(r.get("destination"))

    groups = {}
    for name, c in raw_count.items():
        k = _ent_key(name)
        if not k:
            continue
        g = groups.setdefault(k, {"variants": defaultdict(int), "type": ""})
        g["variants"][name] += c
        g["type"] = g["type"] or raw_type.get(name, "")

    syn, gtype = {}, {}
    for g in groups.values():
        display = max(g["variants"], key=lambda n: (g["variants"][n], len(n)))
        if _is_noise_entity(display):
            for n in g["variants"]:
                syn[n] = None
            continue
        for n in g["variants"]:
            syn[n] = display
        gtype[display] = g["type"] or "unknown"
    return syn, gtype


def export_vault(out_dir, repos=None):
    """Render export() as an Obsidian vault. Memories → knowledge/<id>.md, entities → entities/<slug>.md
    (variants merged via aliases so the graph is connected, not fragmented), plus Home.md and per-repo
    index notes. `[[Entity]]` links reproduce the knowledge graph in Obsidian's graph view. Existing
    entity descriptions (from --describe) are preserved across runs. Backend-agnostic, idempotent.
    Returns {'memories', 'entities', 'pruned'}."""
    out = Path(out_dir).expanduser()
    kdir, edir, idir = out / "knowledge", out / "entities", out / "indexes"
    for d in (kdir, edir, idir):
        d.mkdir(parents=True, exist_ok=True)
    scope = set(repos) if repos else None

    def in_scope(m):
        return scope is None or (m.get("metadata") or {}).get("repo", "general") in scope

    mems = [m for m in export() if not is_superseded(m) and in_scope(m)
            and (m.get("metadata") or {}).get("kind") != "msg"]  # skip cross-workspace mailbox msgs

    # --- pass 1: canonicalize entities. Two layers: syntactic (case/sep/extension merge, always on)
    # then semantic (the hand-editable LLM merge map, off unless you ran `co-vault merge`). ----------
    syn, gtype = _syntactic_entities(mems)
    merges = _load_merges()
    resolver, canon = {}, {}  # raw name -> canonical|None ; canonical -> {type, aliases}
    for raw, disp in syn.items():
        if disp is None:
            resolver[raw] = None
            continue
        canonical = merges.get(disp.lower(), disp)   # semantic layer folds the syntactic display in
        resolver[raw] = canonical
        e = canon.setdefault(canonical, {"type": "", "aliases": set()})
        if not e["type"]:
            e["type"] = gtype.get(canonical) or gtype.get(disp) or "unknown"
        for a in (raw, disp):
            if a != canonical:
                e["aliases"].add(a)

    # --- pass 2: write memory notes + tally per-entity link counts + per-repo buckets --------------
    ent_links = defaultdict(int)
    by_repo = defaultdict(list)
    keep_k, taken_k, note_stem = set(), set(), {}
    for m in mems:
        ents, _ = _resolved_entities(m, resolver)
        for d in ents:
            ent_links[d] += 1
        by_repo[(m.get("metadata") or {}).get("repo", "general")].append(m)
        # name by content (a 1-liner) like entity/repo notes, not the opaque UUID; _slug dedupes.
        first = _first_line(m)
        title = first if len(first) <= 64 else first[:64].rsplit(" ", 1)[0]  # cut on a word boundary
        fn = _slug(title or m.get("id") or uuid.uuid4().hex, taken_k) + ".md"
        (kdir / fn).write_text(_memory_md(m, resolver), encoding="utf-8")
        keep_k.add(fn)
        note_stem[m.get("id")] = fn[:-3]  # index links must reference this filename, not the UUID

    # --- entity notes (preserve any existing description) -----------------------------------------
    keep_e, taken = set(), set()
    for canonical, meta in canon.items():
        fn = _slug(canonical, taken) + ".md"
        desc = _existing_entity_desc(edir / fn)
        (edir / fn).write_text(_entity_md(canonical, meta["type"], sorted(meta["aliases"]), desc,
                                          ent_links.get(canonical, 0)), encoding="utf-8")
        keep_e.add(fn)

    # --- hub notes: Home + one index per repo -----------------------------------------------------
    top = lambda names, n: sorted(((d, ent_links[d]) for d in names), key=lambda x: -x[1])[:n]
    repo_rows = sorted(((r, len(ms)) for r, ms in by_repo.items()), key=lambda x: -x[1])
    keep_i = set()
    for repo, ms in by_repo.items():
        seen = {d for m in ms for d in _resolved_entities(m, resolver)[0]}
        fn = f"repo-{_slug(repo)}.md"
        (idir / fn).write_text(_repo_index_md(repo, ms, top(seen, 10), note_stem), encoding="utf-8")
        keep_i.add(fn)
    (out / "Home.md").write_text(
        _home_md({"memories": len(mems), "entities": len(canon)}, repo_rows, top(ent_links, 20)),
        encoding="utf-8")

    pruned = _prune(kdir, keep_k) + _prune(edir, keep_e) + _prune(idir, keep_i)
    return {"memories": len(mems), "entities": len(canon), "pruned": pruned}


def _num(v):
    try:
        return round(float(v), 3)
    except Exception:
        return None


def import_vault(vault_dir, apply=False):
    """The way back: read edits from knowledge/*.md and push content + importance to the store via
    edit() (only those two round-trip safely). Deleting a note never deletes a memory; duplicate ids
    are skipped. apply=False → dry-run. Returns {'changed', 'applied', 'skipped'}."""
    kdir = Path(vault_dir).expanduser() / "knowledge"
    by_id = {m.get("id"): m for m in export() if m.get("id")}
    seen, dup = {}, set()
    for p in sorted(kdir.glob("*.md")):
        try:
            fm, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if fm.get("source") != "carryover" or not fm.get("id"):
            continue
        mid = fm["id"]
        if mid in seen:
            dup.add(mid)
        seen.setdefault(mid, []).append((fm, body))

    changed, skipped = [], []
    for mid, notes in seen.items():
        if mid in dup:
            skipped.append({"id": mid, "why": "duplicate id in vault"}); continue
        if mid not in by_id:
            skipped.append({"id": mid, "why": "not in store"}); continue
        fm, body = notes[0]
        new_content = _content_before_sections(body)
        cur = (by_id[mid].get("content") or "").strip()
        cdiff = bool(new_content) and new_content != cur
        idiff = fm.get("importance") not in (None, "") and _num(fm["importance"]) != _num(by_id[mid].get("importance"))
        if cdiff or idiff:
            changed.append({"id": mid, "content": new_content if cdiff else None,
                            "importance": fm["importance"] if idiff else None})

    applied = 0
    if apply:
        for ch in changed:
            if edit(ch["id"], ch.get("content"), ch.get("importance")):
                applied += 1
    return {"changed": changed, "applied": applied, "skipped": skipped}


def _parse_list(s):
    """Parse a frontmatter list value we wrote (e.g. '["a", "b"]') back to a Python list."""
    try:
        v = json.loads(s) if s and s.strip().startswith("[") else []
        return v if isinstance(v, list) else []
    except Exception:
        return []


def describe_entities(vault_dir, limit=60, min_links=3, claude_cmd=None):
    """One `claude -p` call writes a 1-line description for the most-connected entities, grounded in
    the memories that mention them. Only touches target entity notes; export_vault preserves the text
    on later runs. Opt-in (it costs an LLM call). Returns {'described': n} or {'error': ...}."""
    root = Path(vault_dir).expanduser()
    edir, kdir = root / "entities", root / "knowledge"
    if not edir.is_dir():
        return {"error": "no vault at " + str(root)}
    ev = defaultdict(list)  # entity display -> [memory contents that mention it]
    for p in kdir.glob("*.md"):
        try:
            _, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        content = _content_before_sections(body)
        for name in set(re.findall(r"\[\[([^\]|]+)\]\]", body)):
            if content:
                ev[name].append(content)

    targets = []  # (links, name, path, type, aliases)
    for p in edir.glob("*.md"):
        try:
            fm, body = _parse_frontmatter(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if fm.get("source") != "carryover":
            continue
        links = int(fm.get("links") or 0)
        if links < min_links:
            continue
        name = next((ln[2:].strip() for ln in body.split("\n") if ln.startswith("# ")), p.stem)
        targets.append((links, name, p, fm.get("entity_type", ""), _parse_list(fm.get("aliases"))))
    targets.sort(key=lambda x: -x[0])
    targets = targets[:limit]
    if not targets:
        return {"described": 0}

    blocks = [f"### {name}\n{' | '.join(ev.get(name, [])[:6])[:600]}" for _, name, _, _, _ in targets]
    prompt = ("For each entity below, write ONE concise sentence (max ~20 words) describing what it "
              "is, based only on the evidence. Output exactly one line per entity as:\n"
              "ENTITY<TAB>description\n(a literal tab between the exact entity name and the sentence; "
              "no bullets, no extra text.)\n\n" + "\n\n".join(blocks))
    try:
        out = subprocess.run(claude_cmd or ["claude", "-p"], input=prompt,
                             capture_output=True, text=True, timeout=240).stdout
    except Exception as e:
        return {"error": str(e)}

    desc = {}
    for ln in out.splitlines():
        if "\t" in ln:
            k, v = ln.split("\t", 1)
            desc[k.strip()] = v.strip()
    n = 0
    for links, name, p, etype, aliases in targets:
        d = desc.get(name)
        if d:
            p.write_text(_entity_md(name, etype, aliases, d, links), encoding="utf-8")
            n += 1
    return {"described": n, "targets": len(targets)}


def merge_entities(claude_cmd=None):
    """Opt-in semantic merge: ask `claude -p` to group entity names that mean the SAME thing
    (synonyms/abbreviations) — beyond the syntactic case/extension merge — and persist the result to
    ~/.carryover/entity-merges.json ({canonical: [members]}). The map is applied deterministically by
    export_vault on every run and is hand-editable, so a bad merge is one line to fix. Conservative by
    design (won't merge merely-related names). Returns {'groups': {...}} or {'error': ...}."""
    mems = [m for m in export() if not is_superseded(m) and (m.get("metadata") or {}).get("kind") != "msg"]
    syn, _ = _syntactic_entities(mems)
    links = defaultdict(int)
    for m in mems:
        md = m.get("metadata") or {}
        raws = [e.get("entity") if isinstance(e, dict) else e for e in (md.get("entities") or [])]
        raws += list(m.get("entity_refs") or [])
        for r in (md.get("relationships") or []):
            raws += [r.get("source"), r.get("destination")]
        seen = set()
        for rn in raws:
            d = syn.get(rn)
            if d and d not in seen:
                seen.add(d); links[d] += 1
    names = sorted(links, key=lambda d: -links[d])
    if len(names) < 2:
        return {"error": "not enough entities to merge"}

    listing = "\n".join(f"{d} ({links[d]})" for d in names)
    prompt = (
        "Below are entity names from a knowledge graph, with how many notes link each. Group ONLY "
        "names that refer to the SAME real thing (synonyms, abbreviations, the same file/module/tool/"
        "person under different names). BE CONSERVATIVE: do NOT merge names that are merely related or "
        "part of the same system — e.g. 'headroom-memory' and 'headroom-graph' are DIFFERENT and must "
        "stay separate. Most names belong to no group. Output ONLY groups with 2+ members, one per "
        "line, as:\nCANONICAL<TAB>member|member|...\nCANONICAL is the clearest, most complete name "
        "(usually one of the members). Use a literal tab. No other text.\n\n" + listing)
    try:
        out = subprocess.run(claude_cmd or ["claude", "-p"], input=prompt,
                             capture_output=True, text=True, timeout=240).stdout
    except Exception as e:
        return {"error": str(e)}

    valid = set(names)
    groups = {}
    for ln in out.splitlines():
        if "\t" not in ln:
            continue
        canonical, rest = ln.split("\t", 1)
        canonical = canonical.strip()
        members = sorted({x.strip() for x in rest.split("|")
                          if x.strip() and x.strip() != canonical and x.strip() in valid})
        if canonical and members:
            groups[canonical] = members
    Path(MERGES).write_text(json.dumps(groups, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"groups": groups, "count": len(groups), "merged": sum(len(v) for v in groups.values())}


def _demo():
    """Self-check: round-trip a fake memory through _memory_md → parse content back; slug dedups."""
    m = {"id": "abc-123", "content": "hello world", "importance": 0.8, "access_count": 2,
         "created_at": "2026-01-01T00:00:00",
         "metadata": {"repo": "carryover", "tags": ["a", "b c"], "facts": ["f1"],
                      "entities": [{"entity": "X", "entity_type": "tech"}],
                      "relationships": [{"source": "X", "relationship": "uses", "destination": "Y"}]}}
    md = _memory_md(m, {})
    fm, body = _parse_frontmatter(md)
    assert fm["id"] == "abc-123" and fm["source"] == "carryover", fm
    assert _content_before_sections(body) == "hello world", repr(_content_before_sections(body))
    assert "[[X]]" in md and "[[Y]]" in md and "#b-c" in md and "#repo/" not in md, md
    # a memory with tags but no sections must not swallow the #tags line into content
    m2 = {"id": "z", "content": "just this", "metadata": {"tags": ["t1"]}}
    _, b2 = _parse_frontmatter(_memory_md(m2, {}))
    assert _content_before_sections(b2) == "just this", repr(_content_before_sections(b2))
    taken = set()
    assert _slug("Ada Lovelace", taken) == "ada-lovelace"
    assert _slug("Ada Lovelace", taken) == "ada-lovelace-2"  # dedup
    # entity hygiene: variants share a canonical key; pure numbers are noise
    assert _ent_key("HarrySchool") == _ent_key("harry-school") == _ent_key("Harry School")
    assert _ent_key("carryover-doctor") == _ent_key("carryover-doctor.sh")  # extension merge
    assert _is_noise_entity("3000") and _is_noise_entity("x") and not _is_noise_entity("co-dash")
    # resolver rewrites a memory's links to the canonical display and drops noise
    r = {"X": "Xavier", "N": None}
    md3 = _memory_md({"id": "q", "content": "c", "metadata": {"entities": [{"entity": "X"}, {"entity": "N"}]}}, r)
    assert "[[Xavier]]" in md3 and "[[N]]" not in md3, md3
    # prune must recognise the QUOTED frontmatter we actually write (regression: it looked for unquoted)
    d = Path(tempfile.mkdtemp())
    (d / "gen.md").write_text(_entity_md("Gen", "tech"), encoding="utf-8")   # source: "carryover"
    (d / "mine.md").write_text("# my own note\n", encoding="utf-8")
    assert _prune(d, set()) == 1, "prune should drop the generated note only"
    assert not (d / "gen.md").exists() and (d / "mine.md").exists()
    print("co_store vault self-check: OK")


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


if __name__ == "__main__":
    _demo()  # python co_store.py → run the vault self-check

