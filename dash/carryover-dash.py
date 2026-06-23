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
import socketserver
import subprocess
import sys
import webbrowser
from pathlib import Path

HOME = Path.home()
CARRYOVER = HOME / ".carryover"    # carryover's own files (memory backend, wikis.list, dash export)
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


def build_html():
    data = json.dumps({"memories": load_memories(), "wikis": load_wikis()}, ensure_ascii=False)
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
  window.__mermaid = mermaid; mermaid.initialize({ startOnLoad:false, theme:'neutral' });
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
  main{padding:20px 24px;max-width:1100px;margin:0 auto}
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
  .wikibody,.graphbody{flex:1;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px 28px;min-width:0}
  .wikibody h1,.wikibody h2{border-bottom:1px solid var(--line);padding-bottom:6px}
  .wikibody pre{background:#f3e8d6;padding:12px;border-radius:8px;overflow:auto}
  .wikibody code{background:#f3e8d6;padding:1px 5px;border-radius:5px}
  .wikibody table{border-collapse:collapse}.wikibody td,.wikibody th{border:1px solid var(--line);padding:6px 10px}
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
  <div class="tab" data-tab="graph">🕸 Graph</div>
  <div class="tab" data-tab="wiki">📄 Wikis</div>
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
    <div id="memlist"></div>
  </section>
  <section id="graph" class="hide"><div class="graphbody" id="graphbody"></div></section>
  <section id="wiki" class="hide">
    <div class="wikiwrap">
      <div class="wikinav" id="wikinav"></div>
      <div class="wikibody" id="wikibody"><div class="empty">Pick a page</div></div>
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
  const reuse=M.filter(m=>(m.access_count||0)>0).sort((a,b)=>(b.access_count||0)-(a.access_count||0)).slice(0,6);
  const tc={}; M.forEach(m=>((m.metadata&&m.metadata.tags)||[]).forEach(t=>tc[t]=(tc[t]||0)+1));
  const tags=Object.entries(tc).sort((a,b)=>b[1]-a[1]).slice(0,14);
  const bar=(lbl,val,max)=>`<div class="ovbar"><span class="ovbarlbl" title="${esc(lbl)}">${esc(lbl)}</span><span class="ovbartrack"><span class="ovbarfill" style="width:${Math.round(val/max*100)}%"></span></span><span class="ovbarval">${val}</span></div>`;
  let h=`<div class="ovgrid">
    <div class="ovcard"><div class="ovnum">${total}</div><div class="ovlbl">memories</div></div>
    <div class="ovcard"><div class="ovnum">${repos}</div><div class="ovlbl">repos</div></div>
    <div class="ovcard"><div class="ovnum">+${addedWeek}</div><div class="ovlbl">this week</div></div>
    <div class="ovcard"><div class="ovnum">${W.length}</div><div class="ovlbl">wikis</div></div>
  </div>`;
  h+=`<h3>Growth · last 8 weeks</h3><div class="ovspark">${wk.map(v=>`<span class="b" style="height:${Math.round(v/wkMax*100)}%" title="${v}"></span>`).join('')}</div>`;
  h+=`<div class="ovcols">
    <div><h3>By repo</h3>${repoRows.map(r=>bar(r[0],r[1],repoMax)).join('')||'<div class="empty">—</div>'}</div>
    <div><h3>Most reused</h3>${reuse.map(m=>`<div class="ovreuse"><b>${m.access_count}×</b> ${esc((m.content||'').slice(0,72))}</div>`).join('')||'<div class="empty">nothing recalled yet</div>'}</div>
  </div>`;
  h+=`<h3>Top topics</h3><div class="chips">${tags.map(t=>`<span class="chip">${esc(t[0])} ${t[1]}</span>`).join('')||'<div class="empty">—</div>'}</div>`;
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

// --- graph ---
async function renderGraph(){
  const rels=[]; DATA.memories.forEach(m=>(mdOf(m).relationships||[]).forEach(r=>{ if(r&&r.source&&r.destination)rels.push(r); }));
  if(!rels.length){ $('#graphbody').innerHTML='<div class="empty">No relationships yet.</div>'; return; }
  const id=s=>'n_'+(s+'').replace(/[^a-zA-Z0-9]/g,'_'); const lines=['graph LR'];
  rels.forEach(r=>lines.push(`  ${id(r.source)}["${(r.source+'').replace(/"/g,"'")}"] -->|${(r.relationship||'').replace(/"/g,"'")}| ${id(r.destination)}["${(r.destination+'').replace(/"/g,"'")}"]`));
  try{ const {svg}=await window.__mermaid.render('kg'+Date.now(),lines.join('\n')); $('#graphbody').innerHTML=svg; }catch(e){ $('#graphbody').innerHTML='<div class="empty">Could not render graph.</div>'; }
}

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

$$('.tab').forEach(t=>t.onclick=()=>{ $$('.tab').forEach(x=>x.classList.remove('active')); t.classList.add('active'); ['overview','mem','graph','wiki'].forEach(s=>$('#'+s).classList.toggle('hide',t.dataset.tab!==s)); if(t.dataset.tab==='graph')renderGraph(); if(t.dataset.tab==='overview')renderOverview(); });

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
