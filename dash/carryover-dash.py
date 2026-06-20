#!/usr/bin/env python3
"""carryover dashboard — a local viewer for your headroom MEMORIES and project WIKIS.

Distinct from headroom's savings dashboard (localhost:8787/dashboard) — this one focuses
on what that doesn't show: the memories stored in the DB and the auto-generated wikis.
It links out to headroom's dashboard for the compression/savings numbers.

Usage:
    python3 carryover-dash.py [port]      # serve on localhost:PORT (default 8788) and open it
Env:
    CARRYOVER_DASH_PORT   port (default 8788)
    HEADROOM_DB           memory db (default ~/.headroom/memory.db)
Wikis are read from ~/.headroom/wikis.list (one repo/wiki path per line, written by
wiki-enable) plus ./wiki if present.
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
HEADROOM = HOME / ".headroom"
DB = os.environ.get("HEADROOM_DB", str(HEADROOM / "memory.db"))
HR_BIN = HEADROOM / "venv" / "bin" / "headroom"
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.environ.get("CARRYOVER_DASH_PORT", "8788"))


def load_memories():
    if not HR_BIN.exists():
        return []
    tmp = HEADROOM / ".dash-export.json"
    try:
        subprocess.run([str(HR_BIN), "memory", "export", "--output", str(tmp), "--db-path", DB],
                       capture_output=True, timeout=20)
        data = json.loads(tmp.read_text() or "[]")
        tmp.unlink(missing_ok=True)
    except Exception:
        return []
    # newest first
    data.sort(key=lambda m: m.get("created_at", ""), reverse=True)
    return data


def wiki_dirs():
    dirs = []
    listfile = HEADROOM / "wikis.list"
    if listfile.exists():
        for line in listfile.read_text().splitlines():
            p = line.strip()
            if p:
                dirs.append(Path(p).expanduser())
    cwd_wiki = Path.cwd() / "wiki"
    if cwd_wiki.exists():
        dirs.append(Path.cwd())
    # normalize: each entry is a repo root; the wiki lives in <root>/wiki
    seen, out = set(), []
    for d in dirs:
        root = d if (d / "wiki").exists() else (d.parent if d.name == "wiki" else d)
        key = str(root)
        if key not in seen and (root / "wiki").exists():
            seen.add(key)
            out.append(root)
    return out


def load_wikis():
    wikis = []
    for root in wiki_dirs():
        wdir = root / "wiki"
        pages = {}
        for md in sorted(wdir.glob("*.md")):
            try:
                pages[md.name] = md.read_text()
            except Exception:
                pass
        if pages:
            wikis.append({"repo": root.name, "path": str(wdir), "pages": pages})
    return wikis


def build_html():
    mems = load_memories()
    wikis = load_wikis()
    data = json.dumps({"memories": mems, "wikis": wikis}, ensure_ascii=False)
    return HTML.replace("/*__DATA__*/", data)


class Handler(http.server.BaseHTTPRequestHandler):
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

    def log_message(self, *a):
        pass


HTML = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>💼 carryover — local dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
<script type="module">
  import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
  window.__mermaid = mermaid; mermaid.initialize({ startOnLoad:false, theme:'neutral' });
</script>
<style>
  :root{
    --bg:#f6efe4; --panel:#fffaf2; --ink:#3a2f25; --muted:#8a7a68; --line:#e6dac8;
    --accent:#b5651d; --accent2:#7a5230; --tan:#d9c3a3; --ok:#3f7d52; --chip:#efe2cd;
  }
  *{box-sizing:border-box}
  body{margin:0;font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
    background:var(--bg);color:var(--ink)}
  header{display:flex;align-items:center;gap:14px;padding:18px 24px;border-bottom:2px solid var(--tan);
    background:linear-gradient(180deg,#fffaf2,#f3e8d6)}
  header .brand{font-size:26px;font-weight:800;letter-spacing:.5px}
  header .tag{color:var(--muted);font-size:13px}
  header .spacer{flex:1}
  header a.hr{font-size:13px;color:var(--accent2);text-decoration:none;border:1px solid var(--tan);
    padding:6px 12px;border-radius:20px;background:#fff}
  header a.hr:hover{background:var(--chip)}
  .tabs{display:flex;gap:6px;padding:14px 24px 0}
  .tab{padding:8px 18px;border:1px solid var(--line);border-bottom:none;border-radius:10px 10px 0 0;
    cursor:pointer;background:#f0e6d6;color:var(--muted);font-weight:600}
  .tab.active{background:var(--panel);color:var(--ink);box-shadow:0 -2px 0 var(--accent) inset}
  main{padding:20px 24px;max-width:1100px;margin:0 auto}
  .toolbar{display:flex;gap:10px;align-items:center;margin-bottom:16px;flex-wrap:wrap}
  input[type=search]{flex:1;min-width:220px;padding:10px 14px;border:1px solid var(--line);
    border-radius:10px;background:#fff;font-size:14px}
  .count{color:var(--muted);font-size:13px}
  .card{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:14px 16px;
    margin-bottom:12px;box-shadow:0 1px 2px rgba(120,90,50,.05)}
  .card .meta{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:6px}
  .badge{font-size:11px;font-weight:700;padding:2px 9px;border-radius:20px;background:var(--chip);color:var(--accent2)}
  .badge.user{background:#dcebd8;color:var(--ok)}
  .date{color:var(--muted);font-size:12px;margin-left:auto}
  .imp{height:6px;border-radius:4px;background:var(--accent);display:inline-block;vertical-align:middle}
  .impwrap{width:80px;height:6px;border-radius:4px;background:var(--line);display:inline-block;overflow:hidden}
  .content{white-space:pre-wrap;word-break:break-word}
  .chips{margin-top:8px}
  .chip{display:inline-block;font-size:11px;background:#fff;border:1px solid var(--tan);color:var(--accent2);
    padding:1px 8px;border-radius:20px;margin:2px 4px 0 0}
  .empty{color:var(--muted);text-align:center;padding:50px;font-style:italic}
  /* wikis */
  .wikiwrap{display:flex;gap:18px}
  .wikinav{width:240px;flex-shrink:0}
  .wikinav .repo{font-weight:700;margin:14px 0 4px;color:var(--accent2);font-size:13px}
  .wikinav a{display:block;padding:5px 10px;border-radius:8px;color:var(--ink);text-decoration:none;font-size:14px;cursor:pointer}
  .wikinav a:hover{background:var(--chip)}
  .wikinav a.active{background:var(--accent);color:#fff}
  .wikibody{flex:1;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:22px 28px;min-width:0}
  .wikibody h1,.wikibody h2{border-bottom:1px solid var(--line);padding-bottom:6px}
  .wikibody pre{background:#f3e8d6;padding:12px;border-radius:8px;overflow:auto}
  .wikibody code{background:#f3e8d6;padding:1px 5px;border-radius:5px}
  .wikibody table{border-collapse:collapse}.wikibody td,.wikibody th{border:1px solid var(--line);padding:6px 10px}
  .hide{display:none}
</style></head>
<body>
<header>
  <div class="brand">💼 carryover</div>
  <div class="tag">local dashboard · memories &amp; wikis</div>
  <div class="spacer"></div>
  <a class="hr" href="http://127.0.0.1:8787/dashboard" target="_blank">headroom savings ↗</a>
</header>
<div class="tabs">
  <div class="tab active" data-tab="mem">🧠 Memories</div>
  <div class="tab" data-tab="wiki">📄 Wikis</div>
</div>
<main>
  <section id="mem">
    <div class="toolbar">
      <input type="search" id="q" placeholder="Search memories…">
      <span class="count" id="memcount"></span>
    </div>
    <div id="memlist"></div>
  </section>
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

// tabs
$$('.tab').forEach(t=>t.onclick=()=>{
  $$('.tab').forEach(x=>x.classList.remove('active')); t.classList.add('active');
  $('#mem').classList.toggle('hide', t.dataset.tab!=='mem');
  $('#wiki').classList.toggle('hide', t.dataset.tab!=='wiki');
});

// memories
function fmtDate(s){ if(!s) return ''; try{return new Date(s).toLocaleString();}catch(e){return s;} }
function scopeOf(m){ if(m.turn_id)return'TURN'; if(m.agent_id)return'AGENT'; if(m.session_id)return'SESSION'; return'USER'; }
function renderMems(filter=''){
  const f=filter.toLowerCase();
  const items=DATA.memories.filter(m=>!f || (m.content||'').toLowerCase().includes(f)
      || (m.entity_refs||[]).join(' ').toLowerCase().includes(f));
  $('#memcount').textContent = items.length+' / '+DATA.memories.length+' memories';
  if(!DATA.memories.length){ $('#memlist').innerHTML='<div class="empty">No memories yet — they fill up as you work.</div>'; return; }
  $('#memlist').innerHTML = items.map(m=>{
    const sc=scopeOf(m), imp=Math.round((m.importance||0)*100);
    const chips=(m.entity_refs||[]).map(e=>`<span class="chip">${esc(e)}</span>`).join('');
    return `<div class="card">
      <div class="meta">
        <span class="badge ${sc==='USER'?'user':''}">${sc}</span>
        <span class="impwrap"><span class="imp" style="width:${imp}%"></span></span>
        <span class="count">${imp}%</span>
        <span class="date">${fmtDate(m.created_at)}</span>
      </div>
      <div class="content">${esc(m.content||'')}</div>
      ${chips?`<div class="chips">${chips}</div>`:''}
    </div>`;
  }).join('');
}
function esc(s){return (s+'').replace(/[&<>]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;'}[c]));}
$('#q').oninput=e=>renderMems(e.target.value);
renderMems();

// wikis
let curPage=null;
function renderWikiNav(){
  if(!DATA.wikis.length){ $('#wikinav').innerHTML='<div class="empty">No wikis yet.<br><small>Run <code>wiki-enable</code> in a repo and push to master.</small></div>'; return; }
  $('#wikinav').innerHTML = DATA.wikis.map((w,wi)=>{
    const order=['Home.md','Architecture.md','Flows.md','Changelog.md'];
    const names=Object.keys(w.pages).sort((a,b)=>{
      const ia=order.indexOf(a), ib=order.indexOf(b);
      return (ia<0?9:ia)-(ib<0?9:ib) || a.localeCompare(b);
    });
    return `<div class="repo">📦 ${esc(w.repo)}</div>`+names.map(n=>
      `<a data-w="${wi}" data-p="${esc(n)}">${esc(n.replace(/\.md$/,''))}</a>`).join('');
  }).join('');
  $$('#wikinav a').forEach(a=>a.onclick=()=>showPage(+a.dataset.w, a.dataset.p, a));
}
function showPage(wi,name,el){
  $$('#wikinav a').forEach(x=>x.classList.remove('active')); if(el)el.classList.add('active');
  const md=DATA.wikis[wi].pages[name]||'';
  $('#wikibody').innerHTML = marked.parse(md);
  // render mermaid blocks
  $$('#wikibody pre code.language-mermaid, #wikibody code.language-mermaid').forEach(async (c,i)=>{
    const pre=c.closest('pre')||c; const div=document.createElement('div');
    try{ const {svg}=await window.__mermaid.render('mm'+Date.now()+i, c.textContent); div.innerHTML=svg; pre.replaceWith(div);}catch(e){}
  });
}
renderWikiNav();
</script>
</body></html>"""


def main():
    socketserver.TCPServer.allow_reuse_address = True
    url = f"http://127.0.0.1:{PORT}/"
    with socketserver.TCPServer(("127.0.0.1", PORT), Handler) as httpd:
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
