#!/usr/bin/env python3
"""carryover dashboard — a local viewer + manager for your headroom KNOWLEDGE and project WIKIS.

Distinct from headroom's savings dashboard (localhost:8787/dashboard). This one shows the
knowledge stored in the DB — facts, typed entities, relationships, tags — grouped by the
repo it came from, lets you delete/clear memories, and renders your auto-generated wikis.

Usage:
    python3 carryover-dash.py [port]      # serve on localhost:PORT (default 8788) and open it
Env:
    CARRYOVER_DASH_PORT  port (default 8788)
    HEADROOM_DB          memory db (default ~/.headroom/memory.db)
"""
import http.server
import json
import os
import re
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

HOME = Path.home()
CARRYOVER = HOME / ".carryover"    # carryover's own files (memory backend, wikis.list, dash export)
PLAYBOOKS = CARRYOVER / "playbooks"  # Devin-style !macro playbooks (one .md each)
WORKSPACES = HOME / "conductor" / "workspaces"  # Conductor workspace roots: <project>/<codename>
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("CARRYOVER_DASH_PORT", "8788"))

# memory backend (co_store): installed at ~/.carryover, or repo claude/hooks when run in-tree
for _p in (Path(__file__).resolve().parent.parent / "claude" / "hooks", CARRYOVER):
    sys.path.insert(0, str(_p))
import co_store  # noqa: E402


def load_memories():
    try:
        data = co_store.export()
    except Exception:
        return []
    data.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return data


def delete_ids(ids):
    try:
        return co_store.delete([i for i in ids if i])
    except Exception:
        return 0


def edit_memory(mid, content=None, importance=None):
    try:
        return co_store.edit(mid, content, importance)
    except Exception:
        return False


def repo_name(root):
    """Real repository name (from git remote), not the Conductor worktree folder name."""
    try:
        url = subprocess.run(["git", "-C", str(root), "remote", "get-url", "origin"],
                             capture_output=True, text=True, timeout=5).stdout.strip()
        if url:
            name = url.rstrip("/").split("/")[-1]
            name = name[:-4] if name.endswith(".git") else name
            if name:
                return name
    except Exception:
        pass
    p = Path(root)
    if p.parent.parent.name == "workspaces":
        return p.parent.name
    return p.name


def wiki_dirs():
    dirs = []
    listfile = CARRYOVER / "wikis.list"
    if listfile.exists():
        for line in listfile.read_text().splitlines():
            if line.strip():
                dirs.append(Path(line.strip()).expanduser())
    if (Path.cwd() / "wiki").exists():
        dirs.append(Path.cwd())
    seen, out = set(), []
    for d in dirs:
        root = d if (d / "wiki").exists() else (d.parent if d.name == "wiki" else d)
        if str(root) not in seen and (root / "wiki").exists():
            seen.add(str(root))
            out.append(root)
    return out


def load_wikis():
    # One wiki per repo: many Conductor worktrees of the same repo each register
    # their own wiki/ dir, so group by repo and keep the most recently generated.
    by_repo = {}  # repo -> (mtime, entry)
    for root in wiki_dirs():
        mds = sorted((root / "wiki").glob("*.md"))
        pages = {}
        for md in mds:
            try:
                pages[md.name] = md.read_text()
            except Exception:
                pass
        if not pages:
            continue
        repo = repo_name(root)
        mtime = max((md.stat().st_mtime for md in mds), default=0.0)
        if repo not in by_repo or mtime > by_repo[repo][0]:
            by_repo[repo] = (mtime, {"repo": repo, "path": str(root / "wiki"), "pages": pages})
    return [entry for _, entry in sorted(by_repo.values(), key=lambda kv: -kv[0])]


PB_NAME = re.compile(r"^[a-zA-Z][\w-]*$")  # safe playbook name AND mode token: no dots/slashes/newlines


def _split_frontmatter(text):
    """(mode, body): read optional `mode:` from a leading --- frontmatter block. Only a block that
    actually contains a `mode:` key is treated as frontmatter, so a body that merely opens with '---'
    (a Markdown thematic break) is preserved intact rather than silently truncated."""
    mode, body = "", (text or "").strip()
    if body.startswith("---"):
        lines = body.split("\n")
        for i in range(1, len(lines)):
            if lines[i].strip() == "---":
                found = False
                for ln in lines[1:i]:
                    k, sep, v = ln.partition(":")
                    if sep and k.strip().lower() == "mode":
                        mode, found = v.strip().lower(), True
                if found:
                    body = "\n".join(lines[i + 1:]).strip()
                break
    return mode, body


def load_playbooks():
    """Each .md in ~/.carryover/playbooks is a `!name` macro. content = body without frontmatter.
    shipped=True (a symlink) means delete only hides it until the next `carryover update`."""
    out = []
    if PLAYBOOKS.is_dir():
        for p in sorted(PLAYBOOKS.glob("*.md")):
            try:
                mode, body = _split_frontmatter(p.read_text(encoding="utf-8"))
                out.append({"name": p.stem, "content": body, "mode": mode, "shipped": p.is_symlink()})
            except Exception:
                pass
    return out


def save_playbook(name, content, mode="", old=""):
    name = (name or "").strip().lower()
    if not PB_NAME.match(name):
        return False
    mode = (mode or "").strip().lower()
    if mode and not PB_NAME.match(mode):   # mode is a single safe token → can't inject a newline/fence
        mode = ""
    body = (content or "").strip()
    text = f"---\nmode: {mode}\n---\n\n{body}\n" if mode else body + "\n"
    PLAYBOOKS.mkdir(parents=True, exist_ok=True)
    p = PLAYBOOKS / (name + ".md")
    if p.is_symlink():            # break the shipped symlink so the user's edit survives `carryover update`
        p.unlink()
    p.write_text(text, encoding="utf-8")
    old = (old or "").strip().lower()      # rename: remove the previous file so it isn't left orphaned
    if old and old != name and PB_NAME.match(old):
        try:
            (PLAYBOOKS / (old + ".md")).unlink()
        except FileNotFoundError:
            pass
    return True


def delete_playbook(name):
    name = (name or "").strip().lower()
    if not PB_NAME.match(name):
        return False
    try:
        (PLAYBOOKS / (name + ".md")).unlink()
        return True
    except FileNotFoundError:
        return False


def list_workspaces():
    """Conductor workspaces on this machine, for the team picker: [{name: codename, project}].
    The folder name is the stable, addressable codename (Conductor's display title isn't on disk)."""
    out = []
    try:
        for proj in sorted(WORKSPACES.iterdir()):
            if proj.is_dir() and not proj.name.startswith("."):
                for ws in sorted(proj.iterdir()):
                    if ws.is_dir() and not ws.name.startswith("."):
                        out.append({"name": ws.name, "project": proj.name})
    except Exception:
        pass
    return out


def build_html():
    data = json.dumps({"memories": load_memories(), "wikis": load_wikis(), "playbooks": load_playbooks(),
                       "teams": co_store.teams(), "workspaces": list_workspaces(),
                       "activity": co_store.load_activity(), "savings": co_store.load_savings()}, ensure_ascii=False)
    return HTML.replace("/*__DATA__*/", data)


class Handler(http.server.BaseHTTPRequestHandler):
    def _json(self, obj, code=200):
        out = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(out)))
        self.end_headers()
        self.wfile.write(out)

    def do_GET(self):
        if self.path not in ("/", "/index.html"):
            self.send_response(404)
            self.end_headers()
            return
        body = build_html().encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", "0") or 0)
        try:
            data = json.loads(self.rfile.read(ln) or b"{}") if ln else {}
        except Exception:
            data = {}
        if self.path == "/api/edit":
            return self._json({"ok": edit_memory(data.get("id"), data.get("content"), data.get("importance"))})
        if self.path == "/api/playbook/save":
            return self._json({"ok": save_playbook(data.get("name"), data.get("content"), data.get("mode"), data.get("oldName"))})
        if self.path == "/api/playbook/delete":
            return self._json({"ok": delete_playbook(data.get("name"))})
        if self.path == "/api/team/save":
            ok = co_store.team_set(data.get("team"), data.get("members") or {})
            old = (data.get("oldName") or "").strip().lower()   # rename: write new first, then drop old
            if ok and old and old != (data.get("team") or "").strip().lower():
                co_store.team_remove(old)
            return self._json({"ok": ok})
        if self.path == "/api/team/delete":
            co_store.team_remove(data.get("team"))              # idempotent: absent == success
            return self._json({"ok": True})
        if self.path == "/api/delete":
            ids = [data["id"]] if data.get("id") else []
        elif self.path == "/api/clear":
            repo = data.get("repo")
            mems = load_memories()
            if repo == "__all__":
                ids = [m.get("id") for m in mems]
            else:
                ids = [m.get("id") for m in mems if (m.get("metadata") or {}).get("repo", "general") == repo]
        else:
            return self._json({"error": "not found"}, 404)
        return self._json({"deleted": delete_ids(ids)})

    def log_message(self, *a):
        pass


HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>💼 carryover — knowledge</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  window.__mermaid = mermaid; mermaid.initialize({ startOnLoad:false, theme:'neutral', suppressErrorRendering:true });
</script>
<style>
  :root{--bg:#f6efe4;--panel:#fffaf2;--ink:#3a2f25;--muted:#8a7a68;--line:#e6dac8;
    --accent:#b5651d;--accent2:#7a5230;--tan:#d9c3a3;--ok:#3f7d52;--chip:#efe2cd;--red:#b23b3b;}
  *{box-sizing:border-box}
  body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--ink)}
  header{display:flex;align-items:center;gap:14px;padding:18px 24px;border-bottom:2px solid var(--tan);background:linear-gradient(180deg,#fffaf2,#f3e8d6)}
  header .brand{font-size:26px;font-weight:800;letter-spacing:.5px}
  header .tag{color:var(--muted);font-size:13px}
  header .spacer{flex:1}
  header a.hr{font-size:13px;color:var(--accent2);text-decoration:none;border:1px solid var(--tan);padding:6px 12px;border-radius:20px;background:#fff}
  header a.hr:hover{background:var(--chip)}
  .tabs{display:flex;gap:6px;padding:14px 24px 0}
  .tab{padding:8px 18px;border:1px solid var(--line);border-bottom:none;border-radius:10px 10px 0 0;cursor:pointer;background:#f0e6d6;color:var(--muted);font-weight:600}
  .tab.active{background:var(--panel);color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset}
  main{padding:20px 24px;max-width:1320px;margin:0 auto}
  .repobar{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-bottom:12px}
  .rchip{font-size:13px;padding:4px 12px;border-radius:20px;border:1px solid var(--tan);background:#fff;cursor:pointer;color:var(--accent2)}
  .rchip b{color:var(--muted);font-weight:600}
  .rchip.on{background:var(--accent);color:#fff;border-color:var(--accent)} .rchip.on b{color:#ffe}
  .rchip.del{margin-left:auto;border-color:#e3bcbc;color:var(--red)} .rchip.del:hover{background:#fbeaea}
  .toolbar{display:flex;gap:10px;align-items:center;margin-bottom:12px;flex-wrap:wrap}
  input[type=search]{flex:1;min-width:220px;padding:10px 14px;border:1px solid var(--line);border-radius:10px;background:#fff;font-size:14px}
  .count{color:var(--muted);font-size:13px}
  .facets{margin-bottom:14px}
  .facets>summary{cursor:pointer;color:var(--muted);font-size:12px;padding:4px 0;user-select:none}
  .facets>summary:hover{color:var(--accent2)} .facets>summary b{color:var(--accent2);font-weight:600}
  .filters{display:flex;flex-wrap:wrap;gap:6px;align-items:center;margin-top:6px}
  .filters .lbl{color:var(--muted);font-size:12px;margin-right:4px}
  .fchip{font-size:12px;padding:3px 10px;border-radius:20px;border:1px solid var(--tan);background:#fff;cursor:pointer;color:var(--accent2)}
  .fchip.on{background:var(--accent);color:#fff;border-color:var(--accent)}
  .card{position:relative;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;margin-bottom:12px;box-shadow:0 1px 2px rgba(120,90,50,.05)}
  .card .meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
  .badge{font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;background:var(--chip);color:var(--accent2)}
  .badge.user{background:#dcebd8;color:var(--ok)}
  .badge.cat{background:#e7dcff;color:#5b3fb5}
  .badge.repo{background:#fde9cf;color:#9a5b14}
  .badge.reuse{background:#d8eef0;color:#15727e}
  .date{color:var(--muted);font-size:12px}
  .del-btn{border:1px solid var(--line);background:#fff;color:var(--red);cursor:pointer;border-radius:8px;font-size:12px;padding:2px 8px}
  .del-btn:hover{background:#fbeaea;border-color:#e3bcbc}
  .edit-btn{margin-left:auto;border:1px solid var(--line);background:#fff;color:var(--accent2);cursor:pointer;border-radius:8px;font-size:12px;padding:2px 8px}
  .edit-btn:hover{background:var(--chip)}
  .ovgrid{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:6px}
  .ovcard{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px;text-align:center}
  .ovnum{font-size:26px;font-weight:700;color:var(--accent)} .ovlbl{font-size:12px;color:var(--muted)}
  #overview h3{font-size:13px;color:var(--accent2);margin:20px 0 8px}
  .ovspark{display:flex;align-items:flex-end;gap:5px;height:50px}
  .ovspark .b{flex:1;background:var(--tan);border-radius:3px 3px 0 0;min-height:2px}
  .ovcols{display:grid;grid-template-columns:1fr 1fr;gap:24px}
  .ovbar{display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:13px}
  .ovbarlbl{width:130px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:var(--ink)}
  .ovbartrack{flex:1;height:10px;background:var(--chip);border-radius:6px;overflow:hidden}
  .ovbarfill{display:block;height:100%;background:var(--accent)}
  .ovbarval{width:30px;text-align:right;color:var(--muted)}
  .ovreuse{font-size:13px;margin-bottom:6px;color:var(--ink)} .ovreuse b{color:var(--accent2)}
  .ovnudge{font-size:13px;margin-bottom:7px;color:var(--ink)} .ovnudge b{color:var(--accent)}
  .ovnudge code{background:var(--chip);padding:1px 7px;border-radius:5px;font-size:12px;margin-left:4px;color:var(--accent2)}
  .impwrap{width:70px;height:6px;border-radius:4px;background:var(--line);display:inline-block;overflow:hidden}
  .imp{height:6px;border-radius:4px;background:var(--accent);display:inline-block;vertical-align:middle}
  .content{white-space:pre-wrap;word-break:break-word;font-weight:600}
  .facts{margin:8px 0 0;padding-left:18px}.facts li{margin:2px 0}
  .chips{margin-top:8px}
  .chip{display:inline-block;font-size:11px;background:#fff;border:1px solid var(--tan);color:var(--accent2);padding:1px 8px;border-radius:20px;margin:2px 4px 0 0;cursor:pointer}
  .chip.tag{background:#f0e6d6} .chip .ty{color:var(--muted);font-size:9px}
  .empty{color:var(--muted);text-align:center;padding:50px;font-style:italic}
  .wikiwrap{display:flex;gap:18px}
  .wikinav{width:240px;flex-shrink:0}
  .wikinav .repo{font-weight:700;margin:14px 0 4px;color:var(--accent2);font-size:13px}
  .wikinav a{display:block;padding:5px 10px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14px;cursor:pointer}
  .wikinav a:hover{background:var(--chip)} .wikinav a.active{background:var(--accent);color:#fff}
  .wikibody{flex:1;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px 28px;min-width:0}
  .ghint{margin:6px 0 14px;font-size:12px;color:var(--muted)}
  .ghint code{background:var(--panel);border:1px solid var(--line);border-radius:5px;padding:1px 5px}
  .wikibody h1,.wikibody h2{border-bottom:1px solid var(--line);padding-bottom:6px}
  .wikibody pre{background:#f3e8d6;padding:12px;border-radius:8px;overflow:auto}
  .wikibody code{background:#f3e8d6;padding:1px 5px;border-radius:5px}
  .wikibody table{border-collapse:collapse}.wikibody td,.wikibody th{border:1px solid var(--line);padding:6px 10px}
  .wikinav .pbadd{display:block;width:100%;margin:0 0 10px;padding:7px 10px;border:1px dashed var(--accent2);border-radius:8px;background:none;color:var(--accent2);font-weight:700;cursor:pointer}
  .pbedit{display:flex;flex-direction:column;gap:10px;max-width:820px}
  .pbrow{display:flex;gap:8px} .pbrow .pbname{flex:1}
  .pbname{padding:8px 12px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);font:600 14px ui-monospace,monospace}
  .pbmode{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);font:13px ui-monospace,monospace}
  .pbbody{min-height:420px;padding:12px 14px;border:1px solid var(--line);border-radius:8px;background:var(--panel);color:var(--ink);font:13px/1.5 ui-monospace,monospace;resize:vertical}
  .pbactions{display:flex;gap:8px;align-items:center}
  .pbbtn{padding:7px 16px;border:1px solid var(--line);border-radius:8px;background:var(--chip);color:var(--ink);font-weight:600;cursor:pointer}
  .pbbtn.save{background:var(--accent);color:#fff;border-color:var(--accent)} .pbbtn.danger{color:#b3261e}
  .pbtip{color:var(--muted);font-size:12px} .pbtip code{background:var(--chip);padding:1px 5px;border-radius:5px}
  .hide{display:none}
</style></head>
<body>
<header>
  <div class="brand">💼 carryover</div>
  <div class="tag">knowledge &amp; wikis · local</div>
  <div class="spacer"></div>
  <a class="hr" href="http://127.0.0.1:8787/dashboard" target="_blank">headroom savings ↗</a>
</header>
<div class="tabs">
  <div class="tab active" data-tab="overview">📊 Overview</div>
  <div class="tab" data-tab="mem">🧠 Knowledge</div>
  <div class="tab" data-tab="wiki">📄 Wikis</div>
  <div class="tab" data-tab="playbooks">📓 Playbooks</div>
  <div class="tab" data-tab="teams">👥 Teams</div>
</div>
<main>
  <section id="overview"><div id="overviewbody"></div></section>
  <section id="mem" class="hide">
    <div class="repobar" id="repobar"></div>
    <div class="toolbar">
      <input type="search" id="q" placeholder="Search knowledge (content, facts, entities, tags)…">
      <span class="count" id="memcount"></span>
    </div>
    <div id="filters"></div>
    <div class="ghint">🕸 Knowledge graph → run <code>co-vault</code> and open the vault in Obsidian for the interactive graph.</div>
    <div id="memlist"></div>
  </section>
  <section id="wiki" class="hide">
    <div class="wikiwrap">
      <div class="wikinav" id="wikinav"></div>
      <div class="wikibody" id="wikibody"><div class="empty">Pick a page</div></div>
    </div>
  </section>
  <section id="playbooks" class="hide">
    <div class="wikiwrap">
      <div class="wikinav" id="pbnav"></div>
      <div class="wikibody">
        <div class="pbedit">
          <div class="pbrow">
            <input id="pbname" class="pbname" placeholder="playbook-name (letters, digits, -)" autocomplete="off">
            <select id="pbmode" class="pbmode" title="behavioral mode injected with this playbook">
              <option value="">mode: default</option>
              <option value="plan">mode: plan (don't implement)</option>
              <option value="interrogate">mode: interrogate (one Q at a time)</option>
            </select>
          </div>
          <textarea id="pbbody" class="pbbody" placeholder="# Title&#10;&#10;The procedure the agent follows when you type !name in any prompt…"></textarea>
          <div class="pbactions">
            <button class="pbbtn save" onclick="savePlaybook()">Save</button>
            <button class="pbbtn" onclick="newPlaybook()">New</button>
            <button class="pbbtn danger" onclick="deletePlaybook()">Delete</button>
            <span id="pbhint" class="muted"></span>
          </div>
          <div class="pbtip">Type <code>!name</code> in any Claude prompt to run it. Files live in <code>~/.carryover/playbooks/</code>.</div>
        </div>
      </div>
    </div>
  </section>
  <section id="teams" class="hide">
    <div class="wikiwrap">
      <div class="wikinav" id="teamnav"></div>
      <div class="wikibody">
        <div class="pbedit">
          <input id="teamname" class="pbname" placeholder="team-name (e.g. checkout-revamp)" autocomplete="off">
          <div class="pbrow">
            <select id="wspick" class="pbmode" style="flex:1" title="pick an existing Conductor workspace"></select>
            <input id="wsrole" class="pbname" style="flex:0 0 180px" placeholder="role (e.g. frontend)" autocomplete="off">
            <button class="pbbtn" onclick="addMember()">+ add</button>
          </div>
          <textarea id="teamroster" class="pbbody" placeholder="one member per line:&#10;&#10;doha: lead&#10;paris: frontend&#10;zurich: backend&#10;oslo: reviewer"></textarea>
          <div class="pbactions">
            <button class="pbbtn save" onclick="saveTeam()">Save</button>
            <button class="pbbtn" onclick="newTeam()">New</button>
            <button class="pbbtn danger" onclick="deleteTeam()">Delete</button>
            <span id="teamhint" class="muted"></span>
          </div>
          <div class="pbtip">Each line is <code>workspace: role</code>. Dispatch with <code>co-team assign &lt;team&gt; [@role] "&lt;task&gt;"</code> or <code>/team</code>.</div>
        </div>
      </div>
    </div>
  </section>
</main>
<script>
const DATA = /*__DATA__*/;
const $=s=>document.querySelector(s), $$=s=>[...document.querySelectorAll(s)];
const esc=s=>(s+'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
function fmtDate(s){ if(!s) return ''; try{return new Date(s).toLocaleString();}catch(e){return s;} }
function scopeOf(m){ if(m.turn_id)return'TURN'; if(m.agent_id)return'AGENT'; if(m.session_id)return'SESSION'; return'USER'; }
function mdOf(m){ return m.metadata||{}; }
function repoOf(m){ return mdOf(m).repo||'general'; }
function entitiesOf(m){ const md=mdOf(m); if(Array.isArray(md.entities)&&md.entities.length) return md.entities.map(e=>typeof e==='string'?{entity:e}:e); return (m.entity_refs||[]).map(e=>({entity:e})); }
function tagsOf(m){ return mdOf(m).tags||[]; }

let repoFilter='__all__', active=new Set();

// --- mutations ---
async function post(path,body){ try{ const r=await fetch(path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}); return await r.json(); }catch(e){ alert('Failed: '+e); return null; } }
async function delMem(id){ if(!confirm('Delete this memory?'))return; await post('/api/delete',{id}); location.reload(); }
async function editMem(id){ const m=(DATA.memories||[]).find(x=>x.id===id); if(!m)return; const c=prompt('Edit memory content:', m.content||''); if(c===null)return; const t=c.trim(); if(!t||t===m.content)return; await post('/api/edit',{id,content:t}); location.reload(); }
async function clearRepo(repo,label){ const m=DATA.memories.filter(x=>repo==='__all__'||repoOf(x)===repo).length; if(!confirm('Delete ALL '+m+' '+label+' memories? This cannot be undone.'))return; await post('/api/clear',{repo}); location.reload(); }

// --- repo bar (index by repo) ---
function renderRepoBar(){
  const counts={}; DATA.memories.forEach(m=>{const r=repoOf(m);counts[r]=(counts[r]||0)+1;});
  const repos=Object.keys(counts).sort((a,b)=> a==='general'?1:(b==='general'?-1:a.localeCompare(b)));
  const chip=(k,l,n)=>`<span class="rchip ${repoFilter===k?'on':''}" data-r="${esc(k)}">📦 ${esc(l)} <b>${n}</b></span>`;
  let html=chip('__all__','All',DATA.memories.length)+repos.map(r=>chip(r,r,counts[r])).join('');
  const lbl=repoFilter==='__all__'?'all':repoFilter;
  html+=`<span class="rchip del" data-clear="${esc(repoFilter)}" data-label="${esc(lbl)}">🗑 clear ${esc(lbl)}</span>`;
  $('#repobar').innerHTML=html;
  $$('#repobar .rchip').forEach(c=>{ if(c.dataset.clear!==undefined&&c.classList.contains('del')) c.onclick=()=>clearRepo(c.dataset.clear,c.dataset.label); else c.onclick=()=>{repoFilter=c.dataset.r;renderRepoBar();renderMems();}; });
}

// --- entity/tag facets ---
function allFacets(){ const ents=new Set(),tags=new Set(); DATA.memories.filter(matchRepo).forEach(m=>{entitiesOf(m).forEach(e=>e.entity&&ents.add(e.entity));tagsOf(m).forEach(t=>tags.add(t));}); return {ents:[...ents].sort(),tags:[...tags].sort()}; }
function renderFilters(){
  const {ents,tags}=allFacets();
  if(!ents.length&&!tags.length){ $('#filters').innerHTML=''; return; }
  const chip=(v,cls)=>`<span class="fchip ${cls} ${active.has(v)?'on':''}" data-f="${esc(v)}">${esc(v)}</span>`;
  const inner='<span class="lbl">entities:</span>'+ents.map(e=>chip(e,'ent')).join('')
    +(tags.length?'<span class="lbl" style="margin-left:10px">tags:</span>'+tags.map(t=>chip('#'+t,'tag')).join(''):'')
    +(active.size?` <span class="fchip" data-f="__clear__" style="border-style:dashed">clear ✕</span>`:'');
  const sum=`filters · <b>${ents.length+tags.length}</b> entities &amp; tags`+(active.size?` · <b>${active.size}</b> active`:'');
  // collapsed by default (they pile up); auto-open while a filter is active so you see what's on
  $('#filters').innerHTML=`<details class="facets"${active.size?' open':''}><summary>${sum}</summary><div class="filters">${inner}</div></details>`;
  $$('#filters .fchip').forEach(c=>c.onclick=()=>{const f=c.dataset.f; f==='__clear__'?(active.clear(),renderFilters(),renderMems()):(active.has(f)?active.delete(f):active.add(f),renderFilters(),renderMems());});
}
function matchRepo(m){ return repoFilter==='__all__'||repoOf(m)===repoFilter; }
function matchFacets(m){ if(!active.size)return true; const ents=entitiesOf(m).map(e=>e.entity),tags=tagsOf(m).map(t=>'#'+t); return [...active].every(f=>ents.includes(f)||tags.includes(f)); }

function renderOverview(){
  const M=DATA.memories||[], W=DATA.wikis||[];
  const repoOf=m=>(m.metadata&&m.metadata.repo)||'general';
  const now=Date.now(), week=6048e5;
  const total=M.length, repos=new Set(M.map(repoOf)).size;
  const addedWeek=M.filter(m=>now-Date.parse(m.created_at||0)<week).length;
  const wk=Array(8).fill(0);
  M.forEach(m=>{const d=Date.parse(m.created_at||0); if(d){const i=Math.floor((now-d)/week); if(i>=0&&i<8)wk[7-i]++;}});
  const wkMax=Math.max(1,...wk);
  const br={}; M.forEach(m=>{const r=repoOf(m); br[r]=(br[r]||0)+1;});
  const repoRows=Object.entries(br).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const repoMax=Math.max(1,...repoRows.map(r=>r[1]));
  const tc={}; M.forEach(m=>((m.metadata&&m.metadata.tags)||[]).forEach(t=>tc[t]=(tc[t]||0)+1));
  const tags=Object.entries(tc).sort((a,b)=>b[1]-a[1]).slice(0,14);
  const bar=(lbl,val,max)=>`<div class="ovbar"><span class="ovbarlbl" title="${esc(lbl)}">${esc(lbl)}</span><span class="ovbartrack"><span class="ovbarfill" style="width:${Math.round(val/max*100)}%"></span></span><span class="ovbarval">${val}</span></div>`;
  const day=864e5;
  // context carried, from instrumented recall activity (aggregate; per-memory reuse is the ♻ badge)
  const A=DATA.activity||[];
  const recalls=A.filter(a=>a.event==='recall');
  const sessions=recalls.length;
  const carriedTotal=recalls.reduce((s,a)=>s+(a.n||0),0);
  const avgCarried=sessions?Math.round(carriedTotal/sessions*10)/10:0;
  const charsTot=recalls.reduce((s,a)=>s+(a.chars||0),0);
  const tokPerSession=sessions?Math.round(charsTot/sessions/4):0;
  const dedupAvoided=A.filter(a=>a.event==='dedup').reduce((s,a)=>s+(a.n||0),0);
  const cr={}; recalls.forEach(a=>{const r=a.repo||'general'; cr[r]=(cr[r]||0)+(a.n||0);});
  const carriedRows=Object.entries(cr).sort((a,b)=>b[1]-a[1]).slice(0,8);
  const carriedMax=Math.max(1,...carriedRows.map(r=>r[1]));
  const days=Array(14).fill(0);
  recalls.forEach(a=>{const d=Date.parse(a.ts||0); if(d){const i=Math.floor((now-d)/day); if(i>=0&&i<14)days[13-i]++;}});
  const daysMax=Math.max(1,...days);
  // cleanup nudges
  const stale=M.filter(m=>(now-Date.parse(m.created_at||0)>30*day)&&(m.importance||0)<0.5).length;
  let dupPairs=0;
  if(M.length<=600){
    const tk=M.map(m=>new Set((m.content||'').toLowerCase().replace(/[^\w\s]/g,' ').split(/\s+/).filter(w=>w)));
    for(let i=0;i<M.length;i++){const a=tk[i]; if(a.size<4)continue;
      for(let j=i+1;j<M.length;j++){const b=tk[j]; if(b.size<4)continue;
        let inter=0; a.forEach(t=>{if(b.has(t))inter++;});
        if(inter/(a.size+b.size-inter)>=0.85)dupPairs++;}}
  } else dupPairs=-1;
  const wikiRepos=new Set((W||[]).map(w=>w.repo));
  const reposNoWiki=[...new Set(M.map(repoOf))].filter(r=>r!=='general'&&!wikiRepos.has(r)).length;
  const rel=ts=>{const s=(now-Date.parse(ts||0))/1000; return s<60?'just now':s<3600?Math.floor(s/60)+'m ago':s<86400?Math.floor(s/3600)+'h ago':Math.floor(s/86400)+'d ago';};
  const feed=A.slice(-12).reverse();

  let h=`<div class="ovgrid">
    <div class="ovcard"><div class="ovnum">${total}</div><div class="ovlbl">memories</div></div>
    <div class="ovcard"><div class="ovnum">${repos}</div><div class="ovlbl">repos</div></div>
    <div class="ovcard"><div class="ovnum">+${addedWeek}</div><div class="ovlbl">this week</div></div>
    <div class="ovcard"><div class="ovnum">${W.length}</div><div class="ovlbl">wikis</div></div>
  </div>`;
  h+=`<h3>Context management</h3><div class="ovgrid">
    <div class="ovcard"><div class="ovnum">${sessions}</div><div class="ovlbl">sessions carried</div></div>
    <div class="ovcard"><div class="ovnum">${avgCarried}</div><div class="ovlbl">avg memories/session</div></div>
    <div class="ovcard"><div class="ovnum">~${tokPerSession.toLocaleString()}</div><div class="ovlbl">tokens/session</div></div>
    <div class="ovcard"><div class="ovnum">${dedupAvoided}</div><div class="ovlbl">dupes avoided</div></div>
  </div>`;
  h+=`<h3>Context carried · last 14 days</h3><div class="ovspark">${days.map(v=>`<span class="b" style="height:${Math.round(v/daysMax*100)}%" title="${v} sessions"></span>`).join('')}</div>`;
  h+=`<div class="ovcols">
    <div><h3>Knowledge by repo</h3>${repoRows.map(r=>bar(r[0],r[1],repoMax)).join('')||'<div class="empty">—</div>'}</div>
    <div><h3>Most carried (by repo)</h3>${carriedRows.length?carriedRows.map(r=>bar(r[0],r[1],carriedMax)).join(''):'<div class="empty">no sessions yet</div>'}</div>
  </div>`;
  const nud=(n,label,cmd)=>n>0?`<div class="ovnudge"><b>${n}</b> ${label} <code>${cmd}</code></div>`:'';
  const nudges=[nud(stale,'old & low-importance — prune them','hr-prune --older-than 30d'),
                nud(dupPairs,'near-duplicate pairs — review','hr-forget <kw>'),
                nud(reposNoWiki,'repos with knowledge but no wiki','wiki-enable')].filter(Boolean).join('');
  h+=`<h3>Cleanup</h3>${nudges||'<div class="empty">✓ nothing to clean up</div>'}`;
  h+=`<h3>Growth · last 8 weeks</h3><div class="ovspark">${wk.map(v=>`<span class="b" style="height:${Math.round(v/wkMax*100)}%" title="${v}"></span>`).join('')}</div>`;
  h+=`<h3>Top topics</h3><div class="chips">${tags.map(t=>`<span class="chip">${esc(t[0])} ${t[1]}</span>`).join('')||'<div class="empty">—</div>'}</div>`;
  const S=DATA.savings;
  if(S){
    const L=S.lifetime||{}, fmt=n=>(n||0).toLocaleString(), tok=L.tokens_saved||0, inTok=L.total_input_tokens||0;
    const pct=inTok?Math.round(tok/inTok*1000)/10:0;
    h+=`<h3>Proxy savings · <span style="color:var(--muted);font-weight:400">headroom</span> <a class="hr" href="http://127.0.0.1:8787/dashboard" target="_blank">full ↗</a></h3><div class="ovgrid">
      <div class="ovcard"><div class="ovnum">${fmt(tok)}</div><div class="ovlbl">tokens saved</div></div>
      <div class="ovcard"><div class="ovnum">${pct}%</div><div class="ovlbl">compression</div></div>
      <div class="ovcard"><div class="ovnum">$${(L.compression_savings_usd||0).toFixed(2)}</div><div class="ovlbl">saved</div></div>
      <div class="ovcard"><div class="ovnum">${fmt(L.requests||0)}</div><div class="ovlbl">requests</div></div>
    </div>`;
  } else {
    h+=`<h3>Proxy savings</h3><div class="empty">headroom proxy not installed — add it (optional, <code>install.sh --with-headroom</code>) for token-compression savings.</div>`;
  }
  h+=`<h3>Recent activity</h3>${feed.length?feed.map(a=>`<div class="ovreuse"><b>${esc(a.event)}</b> · ${esc(a.repo||'general')} · ${a.event==='recall'?(a.n||0)+' carried':(a.n||0)+' avoided'} <span style="color:var(--muted)">${rel(a.ts)}</span></div>`).join(''):'<div class="empty">no activity yet</div>'}`;
  $('#overviewbody').innerHTML=h;
}
function renderMems(){
  renderFilters();
  const f=($('#q').value||'').toLowerCase();
  const items=DATA.memories.filter(matchRepo).filter(matchFacets).filter(m=>{
    if(!f)return true;
    return [m.content||'',(mdOf(m).facts||[]).join(' '),entitiesOf(m).map(e=>e.entity).join(' '),tagsOf(m).join(' ')].join(' ').toLowerCase().includes(f);
  });
  $('#memcount').textContent=items.length+' shown';
  if(!DATA.memories.length){ $('#memlist').innerHTML='<div class="empty">No knowledge yet — it fills up as you work and save.</div>'; return; }
  $('#memlist').innerHTML=items.map(m=>{
    const md=mdOf(m),sc=scopeOf(m),imp=Math.round((m.importance||0)*100);
    const facts=(md.facts||[]).filter(x=>x!==m.content);
    const ents=entitiesOf(m).map(e=>`<span class="chip" data-f="${esc(e.entity)}">${esc(e.entity)}${e.entity_type?` <span class="ty">${esc(e.entity_type)}</span>`:''}</span>`).join('');
    const tags=tagsOf(m).map(t=>`<span class="chip tag" data-f="#${esc(t)}">#${esc(t)}</span>`).join('');
    return `<div class="card">
      <div class="meta">
        <span class="badge ${sc==='USER'?'user':''}">${sc}</span>
        <span class="badge repo">📦 ${esc(repoOf(m))}</span>
        ${md.category?`<span class="badge cat">${esc(md.category)}</span>`:''}
        ${m.access_count?`<span class="badge reuse" title="times recalled into context">♻ ${m.access_count}</span>`:''}
        <span class="impwrap"><span class="imp" style="width:${imp}%"></span></span><span class="count">${imp}%</span>
        <button class="edit-btn" data-edit="${esc(m.id)}">✏️</button>
        <button class="del-btn" data-del="${esc(m.id)}">🗑</button>
      </div>
      <div class="content">${esc(m.content||'')}</div>
      ${facts.length?`<ul class="facts">${facts.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`:''}
      ${(ents||tags)?`<div class="chips">${ents}${tags}</div>`:''}
      <div class="date">${fmtDate(m.created_at)}</div>
    </div>`;
  }).join('');
  $$('#memlist .chip').forEach(c=>c.onclick=()=>{const f=c.dataset.f;active.has(f)?active.delete(f):active.add(f);renderMems();});
  $$('#memlist .del-btn').forEach(b=>b.onclick=()=>delMem(b.dataset.del));
  $$('#memlist .edit-btn').forEach(b=>b.onclick=()=>editMem(b.dataset.edit));
}
$('#q').oninput=renderMems;

// --- wikis ---
function renderWikiNav(){
  if(!DATA.wikis.length){ $('#wikinav').innerHTML='<div class="empty">No wikis yet.<br><small>Run <code>wiki-enable</code> in a repo and push to master.</small></div>'; return; }
  $('#wikinav').innerHTML=DATA.wikis.map((w,wi)=>{
    const order=['Home.md','Architecture.md','Flows.md','Changelog.md'];
    const names=Object.keys(w.pages).sort((a,b)=>{const ia=order.indexOf(a),ib=order.indexOf(b);return (ia<0?9:ia)-(ib<0?9:ib)||a.localeCompare(b);});
    return `<div class="repo">📦 ${esc(w.repo)}</div>`+names.map(n=>`<a data-w="${wi}" data-p="${esc(n)}">${esc(n.replace(/\.md$/,''))}</a>`).join('');
  }).join('');
  $$('#wikinav a').forEach(a=>a.onclick=()=>showPage(+a.dataset.w,a.dataset.p,a));
}
function showPage(wi,name,el){
  $$('#wikinav a').forEach(x=>x.classList.remove('active')); if(el)el.classList.add('active');
  $('#wikibody').innerHTML=marked.parse(DATA.wikis[wi].pages[name]||'');
  $$('#wikibody code.language-mermaid').forEach(async(c,i)=>{const pre=c.closest('pre')||c,div=document.createElement('div');try{const {svg}=await window.__mermaid.render('mm'+Date.now()+i,c.textContent);div.innerHTML=svg;pre.replaceWith(div);}catch(e){}});
}

let PB_SEL=null;
function renderPlaybooks(){
  const list=DATA.playbooks||[];
  let html='<button class="pbadd" onclick="newPlaybook()">+ New playbook</button>';
  html+=list.length? list.map(p=>`<a data-pb="${esc(p.name)}">!${esc(p.name)}</a>`).join('')
                   : '<div class="empty">No playbooks yet.</div>';
  $('#pbnav').innerHTML=html;
  $$('#pbnav a').forEach(a=>a.onclick=()=>selectPlaybook(a.dataset.pb));
  if(PB_SEL && list.some(p=>p.name===PB_SEL)) selectPlaybook(PB_SEL);
}
function selectPlaybook(name){
  const p=(DATA.playbooks||[]).find(x=>x.name===name); if(!p)return;
  PB_SEL=name;
  $$('#pbnav a').forEach(a=>a.classList.toggle('active',a.dataset.pb===name));
  const sel=$('#pbmode');                       // show a custom/unknown mode so Save won't silently drop it
  if(p.mode && !Array.from(sel.options).some(o=>o.value===p.mode)) sel.add(new Option('mode: '+p.mode+' (custom)', p.mode));
  $('#pbname').value=p.name; $('#pbbody').value=p.content||''; sel.value=p.mode||''; $('#pbhint').textContent='';
}
function newPlaybook(){ PB_SEL=null; $$('#pbnav a').forEach(a=>a.classList.remove('active')); $('#pbname').value=''; $('#pbbody').value=''; $('#pbmode').value=''; $('#pbhint').textContent='new — pick a name'; $('#pbname').focus(); }
async function savePlaybook(){
  const name=$('#pbname').value.trim().toLowerCase(), body=$('#pbbody').value, mode=$('#pbmode').value, oldName=PB_SEL;
  if(!/^[a-z][\w-]*$/.test(name)){ $('#pbhint').textContent='invalid name — letters/digits/-, start with a letter'; return; }
  const r=await post('/api/playbook/save',{name,content:body,mode,oldName});
  if(!r||!r.ok){ $('#pbhint').textContent='save failed'; return; }
  let list=DATA.playbooks||(DATA.playbooks=[]);
  if(oldName && oldName!==name) list=DATA.playbooks=list.filter(x=>x.name!==oldName);   // rename: drop the old entry
  const e=list.find(x=>x.name===name);
  if(e){ e.content=body; e.mode=mode; } else { list.push({name,content:body,mode}); list.sort((a,b)=>a.name<b.name?-1:1); }
  PB_SEL=name; renderPlaybooks(); $('#pbhint').textContent=oldName&&oldName!==name?'renamed ✓':'saved ✓';
}
async function deletePlaybook(){
  const name=$('#pbname').value.trim().toLowerCase(); if(!name)return;
  const pb=(DATA.playbooks||[]).find(x=>x.name===name);
  const warn=pb&&pb.shipped?'\n\n(This is a bundled playbook — it returns on the next `carryover update`.)':'';
  if(!confirm('Delete playbook !'+name+'?'+warn))return;
  const r=await post('/api/playbook/delete',{name});
  if(!r||!r.ok){ $('#pbhint').textContent='delete failed'; return; }
  DATA.playbooks=(DATA.playbooks||[]).filter(x=>x.name!==name); newPlaybook(); renderPlaybooks();
}

let TEAM_SEL=null;
function rosterText(m){ return Object.keys(m).map(w=>w+': '+m[w]).join('\n'); }
function parseRoster(text){
  const m={};
  (text||'').split('\n').forEach(line=>{ const s=line.trim(); if(!s)return;
    const i=s.indexOf(':'); const ws=(i<0?s:s.slice(0,i)).trim().toLowerCase().replace(/^@/,'');
    const role=((i<0?'':s.slice(i+1)).trim().toLowerCase())||'member'; if(ws) m[ws]=role; });
  return m;
}
function fillWsPicker(){
  const sel=$('#wspick'); if(!sel) return;
  const ws=DATA.workspaces||[];
  sel.innerHTML='<option value="">— pick a workspace —</option>'+
    ws.map(w=>`<option value="${esc(w.name)}">${esc(w.name)} · ${esc(w.project)}</option>`).join('');
}
function addMember(){
  const ws=$('#wspick').value, role=$('#wsrole').value.trim().toLowerCase()||'member';
  if(!ws){ $('#teamhint').textContent='pick a workspace from the list'; return; }
  const ta=$('#teamroster'), cur=ta.value.replace(/\s*$/,'');
  ta.value=(cur?cur+'\n':'')+ws+': '+role;
  $('#wsrole').value=''; $('#wspick').value=''; $('#teamhint').textContent='';
}
function renderTeams(){
  fillWsPicker();
  const t=DATA.teams||{}, keys=Object.keys(t).sort();
  let html='<button class="pbadd" onclick="newTeam()">+ New team</button>';
  html+=keys.length? keys.map(n=>`<a data-team="${esc(n)}">👥 ${esc(n)}</a>`).join('') : '<div class="empty">No teams yet.</div>';
  $('#teamnav').innerHTML=html;
  $$('#teamnav a').forEach(a=>a.onclick=()=>selectTeam(a.dataset.team));
  if(TEAM_SEL && t[TEAM_SEL]) selectTeam(TEAM_SEL);
}
function selectTeam(name){
  const m=(DATA.teams||{})[name]; if(!m)return;
  TEAM_SEL=name;
  $$('#teamnav a').forEach(a=>a.classList.toggle('active',a.dataset.team===name));
  $('#teamname').value=name; $('#teamroster').value=rosterText(m); $('#teamhint').textContent='';
}
function newTeam(){ TEAM_SEL=null; $$('#teamnav a').forEach(a=>a.classList.remove('active')); $('#teamname').value=''; $('#teamroster').value=''; $('#teamhint').textContent='new — name + members'; $('#teamname').focus(); }
async function saveTeam(){
  const name=$('#teamname').value.trim().toLowerCase(), members=parseRoster($('#teamroster').value), oldName=TEAM_SEL;
  if(!name){ $('#teamhint').textContent='pick a team name'; return; }
  if(!Object.keys(members).length){ $('#teamhint').textContent='add at least one member (ws: role)'; return; }
  const r=await post('/api/team/save',{team:name,members,oldName});   // server writes new, then drops old (safe on failure)
  if(!r||!r.ok){ $('#teamhint').textContent='save failed'; return; }
  if(oldName && oldName!==name) delete (DATA.teams||{})[oldName];
  (DATA.teams||(DATA.teams={}))[name]=members;
  TEAM_SEL=name; renderTeams(); $('#teamhint').textContent=oldName&&oldName!==name?'renamed ✓':'saved ✓';
}
async function deleteTeam(){
  const name=TEAM_SEL; if(!name){ $('#teamhint').textContent='select a team to delete'; return; }
  if(!confirm('Delete team '+name+'?'))return;
  const r=await post('/api/team/delete',{team:name});
  if(!r||!r.ok){ $('#teamhint').textContent='delete failed'; return; }
  delete (DATA.teams||{})[name]; newTeam(); renderTeams();
}

$$('.tab').forEach(t=>t.onclick=()=>{ $$('.tab').forEach(x=>x.classList.remove('active')); t.classList.add('active'); ['overview','mem','wiki','playbooks','teams'].forEach(s=>$('#'+s).classList.toggle('hide',t.dataset.tab!==s)); if(t.dataset.tab==='overview')renderOverview(); if(t.dataset.tab==='playbooks')renderPlaybooks(); if(t.dataset.tab==='teams')renderTeams(); });

renderRepoBar(); renderMems(); renderWikiNav(); renderOverview();
</script>
</body></html>"""


def main():
    socketserver.TCPServer.allow_reuse_address = True
    port, httpd = PORT, None
    for attempt in range(10):
        try:
            httpd = socketserver.TCPServer(("127.0.0.1", port), Handler)
            break
        except OSError as e:
            if e.errno in (48, 98) and attempt < 9:  # EADDRINUSE (macOS 48 / Linux 98) — try the next port
                port += 1
                continue
            print(f"carryover dashboard: can't bind a port near {PORT} ({e}).")
            print(f"  another co-dash may be running — check `lsof -i :{PORT}`, or set CARRYOVER_DASH_PORT.")
            return
    if port != PORT:
        print(f"  (port {PORT} busy → using {port})")
    url = f"http://127.0.0.1:{port}/"
    with httpd:
        print(f"💼 carryover dashboard → {url}  (Ctrl-C to stop)")
        try:
            webbrowser.open(url)
        except Exception:
            pass
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nbye")


if __name__ == "__main__":
    main()
