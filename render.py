#!/usr/bin/env python3
"""Render leaderboard.yaml into the README table and the docs/ site (index.html).

Single source of truth is leaderboard.yaml. The site is one self-contained HTML file
with the leaderboard data + kata list + SKILL template baked in — no runtime fetching,
so GitHub Pages / Vercel serve it from any subpath. Run after any change (CI does too).
"""
from __future__ import annotations

import json
import os

import yaml

REPO = "https://github.com/zeeshan8281/kata"

# id -> (name, one-line description, difficulty 1-3)
KATA_META = {
    "001": ("pr-review", "Audit a PR diff → JSON of security concerns, perf hotspots, missing tests.", 1),
    "002": ("refactor-async", "Convert a sync Python module to async/await, behaviour unchanged.", 1),
    "003": ("cron-next", "next_run(expr, after) for 5-field cron — steps, ranges, the day-of-month/day-of-week OR rule, leap years.", 3),
    "004": ("bug-hunt", "Make a failing test pass with the smallest fix.", 1),
    "005": ("secure-query", "Rewrite an injectable DB module to parameterized queries — functional AND injection tests.", 3),
    "006": ("optimize", "Rewrite an O(n²) function to O(n). Correct on edge cases, or it times out.", 2),
    "007": ("task-pool", "async run_pool(tasks, limit) — bounded concurrency, results in input order.", 3),
    "008": ("semver", "compare(a, b) per SemVer 2.0.0 — the full pre-release precedence chain.", 2),
}
KATAS = {k: v[0] for k, v in KATA_META.items()}
HERE = os.path.dirname(__file__)


def ordered(rows):
    # lower score wins; tie -> earlier created date takes the crown (PRD open q #4)
    return sorted(rows, key=lambda r: (r["score"], str(r.get("created", "9999"))))


def readme_table(data) -> str:
    out = []
    for kid, name in KATAS.items():
        out.append(f"\n### {kid} · {name}\n")
        rows = ordered(data.get(kid, []))
        if not rows:
            out.append("_No submissions yet — [be first](#how-to-play)._")
            continue
        out.append("| | Solver | Skill | Score | Breakdown | Model |")
        out.append("|---|---|---|---|---|---|")
        for i, r in enumerate(rows):
            crown = "🏆" if i == 0 else ""
            badge = " ⚑" if r.get("self_reported") else ""
            out.append(
                f"| {crown} | @{r['solver']}{badge} | `{r['name']}` | **{r['score']}** | "
                f"${r['cost']:.4f} · {r['attempts']} att · {r['chars']} chars | "
                f"{r['model']} ({r.get('provider','?')}) |"
            )
    return "\n".join(out)


def update_readme(table: str):
    path = os.path.join(HERE, "README.md")
    txt = open(path).read()
    a, b = "<!-- LEADERBOARD:START -->", "<!-- LEADERBOARD:END -->"
    pre, rest = txt.split(a)
    _, post = rest.split(b)
    open(path, "w").write(f"{pre}{a}\n{table}\n{b}{post}")


def write_html(data):
    board = {k: ordered(data.get(k, [])) for k in KATAS}
    katas = [{"id": k, "name": n, "desc": d, "diff": diff} for k, (n, d, diff) in KATA_META.items()]
    template = open(os.path.join(HERE, "submissions", "_template", "SKILL.md")).read()
    subst = {
        "__DATA__": json.dumps(board, default=str),
        "__KATAS__": json.dumps(katas),
        "__TEMPLATE__": json.dumps(template),
        "__REPO__": json.dumps(REPO),
    }
    html = HTML_TMPL
    for k, v in subst.items():
        html = html.replace(k, v)
    for fn in ("index.html", "leaderboard.html"):
        open(os.path.join(HERE, "docs", fn), "w").write(html)


HTML_TMPL = r"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kata — write one Skill, beat the leaderboard</title>
<meta name="description" content="Write a single SKILL.md that solves a coding task, run it against sealed tests, post your score. Cheaper, shorter, fewer tries wins.">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
/* Tokens verbatim from @layr-labs/eigen-design (dark). Accent = system indigo
   (chart-1 #6366f1); brand primary #1a0c6d. Radii + component styling match the
   library's button/badge/card CVA (rounded-md 3px, cards rounded-xl 6px). */
:root{--bg:#0a0a0a;--fg:#fafafa;--muted:#a3a3a3;--card:#171717;--card2:#171717;
--secondary:#262626;--secondary-fg:#fafafa;--border:#ffffff1a;--input:#ffffff26;--ring:#737373;
--primary:#1a0c6d;--accent:#6366f1;--good:#4ade80;--destructive:#f87171;
--r-md:3px;--r-lg:4px;--r-xl:6px;--r-2xl:8px}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:'Geist',ui-sans-serif,system-ui,sans-serif;line-height:1.6;-webkit-font-smoothing:antialiased}
a{color:var(--accent);text-decoration:none}
code,kbd{font-family:'Geist Mono',monospace}
.wrap{max-width:940px;margin:0 auto;padding:0 20px}
/* nav */
nav{position:sticky;top:0;z-index:20;background:rgba(10,10,10,.8);backdrop-filter:blur(10px);border-bottom:1px solid var(--border)}
nav .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.brand{display:flex;align-items:center;gap:10px;font-weight:600;font-size:1.05rem;letter-spacing:-.02em}
.brand .dot{width:10px;height:10px;border-radius:var(--r-md);background:linear-gradient(135deg,var(--primary),var(--accent))}
.nav-r{display:flex;align-items:center;gap:14px}
.nav-r a.ghost{color:var(--muted);font-size:.88rem}
.nav-r a.ghost:hover{color:var(--fg)}
/* button — mirrors buttonVariants: rounded-md, text-sm, font-medium, active:opacity-60 */
.btn{border:1px solid transparent;background:var(--fg);color:var(--bg);font-weight:500;font-size:.875rem;
border-radius:var(--r-md);padding:8px 14px;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:8px;transition:all .15s}
.btn:hover{opacity:.9}.btn:active{opacity:.6}
.btn.gh{background:var(--fg);color:var(--bg)}
.btn.outline{background:transparent;color:var(--fg);border-color:var(--input)}
.btn.outline:hover{background:var(--accent-bg,#262626);opacity:1}
.avatar{width:24px;height:24px;border-radius:50%;border:1px solid var(--border)}
.usr{display:flex;align-items:center;gap:8px;font-size:.86rem;font-weight:500}
.usr .signout{color:var(--muted);font-weight:400;font-size:.8rem;cursor:pointer}
.usr .signout:hover{color:var(--fg)}
/* hero — heading-xl scale: 3.75rem / 700 / -2.4px letter-spacing */
.hero{padding:76px 0 52px;text-align:center}
.hero .bar{height:3px;width:56px;background:linear-gradient(90deg,var(--primary),var(--accent));border-radius:9999px;margin:0 auto 26px}
.hero h1{font-size:3.75rem;line-height:1.02;letter-spacing:-2.4px;font-weight:700;margin:0 0 18px}
.hero h1 .g{color:var(--accent)}
.hero p{font-size:1.15rem;color:var(--muted);max-width:640px;margin:0 auto 12px}
.hero p b{color:var(--fg);font-weight:600}
.hero .tags{color:var(--muted);font-family:'Geist Mono',monospace;font-size:.82rem;margin-top:18px}
.hero .cta{display:flex;gap:10px;justify-content:center;margin-top:30px;flex-wrap:wrap}
.hero .btn{padding:10px 18px;font-size:.92rem}
.eyebrow{font-family:'Geist Mono',monospace;font-size:.76rem;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);margin-bottom:12px}
/* sections */
section{padding:46px 0;border-top:1px solid var(--border)}
h2{font-size:1.75rem;letter-spacing:-.9px;font-weight:600;margin:0 0 6px}
.sub{color:var(--muted);margin:0 0 26px}
/* steps */
.steps{display:grid;gap:12px}
.step{display:flex;gap:16px;background:var(--card);border:1px solid var(--border);border-radius:var(--r-xl);padding:18px 20px;box-shadow:0 2px 6px -1px #00000010}
.step .n{flex:0 0 28px;height:28px;border-radius:var(--r-md);background:var(--primary);color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:.85rem;font-family:'Geist Mono',monospace}
.step h3{margin:1px 0 6px;font-size:1rem;font-weight:600}
.step p{margin:0;color:var(--muted);font-size:.94rem}
pre{background:#000;border:1px solid var(--border);border-radius:var(--r-lg);padding:14px 16px;overflow:auto;margin:10px 0 0;
font-family:'Geist Mono',monospace;font-size:.82rem;line-height:1.7}
pre .cmt{color:#6b7280}
pre .h{color:var(--accent)}
.codehead{display:flex;justify-content:space-between;align-items:center;margin-bottom:0}
.copy{background:transparent;border:1px solid var(--input);color:var(--muted);border-radius:var(--r-md);padding:4px 10px;font-size:.76rem;cursor:pointer;font-family:'Geist Mono',monospace}
.copy:hover{color:var(--fg)}
/* katas */
.kgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:12px}
.kcard{background:var(--card);border:1px solid var(--border);border-radius:var(--r-xl);padding:18px;display:flex;flex-direction:column;gap:8px;box-shadow:0 2px 6px -1px #00000010}
.kcard .top{display:flex;align-items:center;justify-content:space-between}
.kcard .id{font-family:'Geist Mono',monospace;color:var(--muted);font-size:.8rem}
.kcard h3{margin:0;font-size:1.05rem;font-weight:500;font-family:'Geist Mono',monospace}
.kcard p{margin:0;color:var(--muted);font-size:.88rem}
.bite{font-family:'Geist Mono',monospace;letter-spacing:1px}
.bite .on{color:var(--accent)}.bite .off{color:#333}
/* scoring */
.formula{background:#000;border:1px solid var(--border);border-radius:var(--r-xl);padding:22px;text-align:center;
font-family:'Geist Mono',monospace;font-size:1.05rem}
.fx{display:flex;gap:12px;flex-wrap:wrap;margin-top:14px}
.fx div{flex:1;min-width:200px;background:var(--card);border:1px solid var(--border);border-radius:var(--r-xl);padding:14px 16px;font-size:.9rem;color:var(--muted)}
.fx b{color:var(--fg);font-weight:600}
/* leaderboard */
.kata-sub{color:var(--muted);font-family:'Geist Mono',monospace;font-size:.8rem;font-weight:400}
.card{background:var(--card2);border:1px solid var(--border);border-radius:var(--r-xl);overflow:hidden;margin-top:12px;box-shadow:0 2px 6px -1px #00000010}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--border);font-size:.92rem}
th{color:var(--muted);font-weight:500;font-size:.72rem;text-transform:uppercase;letter-spacing:.05em}
tr:last-child td{border-bottom:none}
.rank{width:34px;font-size:1.05rem}
.solver{font-weight:600}
.score{font-family:'Geist Mono',monospace;font-weight:600;font-size:1.05rem}
.brk{font-family:'Geist Mono',monospace;color:var(--muted);font-size:.78rem}
/* model tag — secondary badge (rounded-md, bg-secondary) */
.chip{display:inline-block;background:var(--secondary);color:var(--secondary-fg);border-radius:var(--r-md);padding:2px 9px;font-size:.72rem;font-family:'Geist Mono',monospace}
.flag{color:var(--muted);font-size:.72rem;border:1px solid var(--border);border-radius:var(--r-md);padding:1px 7px;margin-left:6px}
.empty{padding:18px 16px;color:var(--muted);font-size:.92rem}
.lb-h{display:flex;align-items:baseline;justify-content:space-between;margin:24px 0 0}
.lb-h h3{margin:0;font-size:1.15rem;font-weight:600}
/* signin modal — dialog styling */
.modal{position:fixed;inset:0;background:rgba(0,0,0,.65);display:none;align-items:center;justify-content:center;z-index:40}
.modal.on{display:flex}
.sheet{background:var(--card);border:1px solid var(--border);border-radius:var(--r-2xl);padding:24px;width:min(400px,92vw);box-shadow:0 16px 48px 8px #00000040}
.sheet h3{margin:0 0 6px;font-size:1.15rem;font-weight:600}
.sheet p{margin:0 0 16px;color:var(--muted);font-size:.9rem}
.sheet input{width:100%;background:#000;border:1px solid var(--input);color:var(--fg);border-radius:var(--r-md);padding:10px 13px;font-family:'Geist Mono',monospace;font-size:.95rem;outline:none}
.sheet input:focus{border-color:var(--ring)}
.sheet .row{display:flex;gap:10px;margin-top:14px}
.sheet .row .btn{flex:1;justify-content:center}
.err{color:var(--destructive);font-size:.82rem;margin-top:8px;min-height:1em}
footer{padding:40px 0 64px;color:var(--muted);font-size:.85rem;border-top:1px solid var(--border);text-align:center}
@media(max-width:600px){.hero h1{font-size:2.5rem;letter-spacing:-1.4px}}
</style></head><body>

<nav><div class="wrap">
  <div class="brand"><span class="dot"></span>Kata</div>
  <div class="nav-r">
    <a class="ghost" href="#how">How to play</a>
    <a class="ghost" href="#leaderboard">Leaderboard</a>
    <a class="ghost" id="repoLink" href="#" target="_blank">GitHub</a>
    <span id="authSlot"></span>
  </div>
</div></nav>

<header class="hero"><div class="wrap">
  <div class="bar"></div>
  <div class="eyebrow">Eigen Builder Collective · Session 6</div>
  <h1>Write one Skill.<br><span class="g">Beat the leaderboard.</span></h1>
  <p>A coding kata is a practiced form. Each task is a kata — you submit a single <code>SKILL.md</code> that makes Claude Code solve it, run it against sealed tests, and post your score.</p>
  <p><b>Cheaper, shorter, fewer tries wins.</b></p>
  <div class="tags">$ cost &nbsp;·&nbsp; iterations &nbsp;·&nbsp; skill length &nbsp; → &nbsp; lowest score takes the crown</div>
  <div class="cta">
    <button class="btn gh" id="heroSignin">Sign in with GitHub</button>
    <a class="btn outline" href="#how">How it works</a>
  </div>
</div></header>

<section id="how"><div class="wrap">
  <h2>How to play</h2>
  <p class="sub" id="howSub">Five steps. Barrier to entry is minutes, not hours.</p>
  <div class="steps">
    <div class="step"><div class="n">1</div><div><h3>Fork the repo</h3><p>Everything lives on GitHub — the runner, the sealed katas, the leaderboard. <a id="forkLink" href="#" target="_blank">Fork it →</a></p></div></div>
    <div class="step"><div class="n">2</div><div><h3>Copy the template</h3><p>Start from the blank Skill and drop it under your handle.</p>
      <div class="codehead"></div><pre><span class="cmt"># your submissions live here</span>
cp submissions/_template/SKILL.md submissions/<span class="h" data-handle>&lt;your-handle&gt;</span>/001.md</pre></div></div>
    <div class="step"><div class="n">3</div><div><h3>Write your Skill</h3><p>The Skill body becomes the system prompt. Short and precise beats long and verbose — length is in the score.</p></div></div>
    <div class="step"><div class="n">4</div><div><h3>Run it against any model</h3><p>Any OpenAI-compatible endpoint. Bring your own key.</p>
      <pre>export ANTHROPIC_API_KEY=...
python runner.py --kata 001 \
  --submission submissions/<span class="h" data-handle>&lt;your-handle&gt;</span>/001.md \
  --model claude-haiku-4-5</pre></div></div>
    <div class="step"><div class="n">5</div><div><h3>Open a PR with your score</h3><p>Add your row to <code>leaderboard.yaml</code>. CI re-runs the submission, confirms the run hash, merges. The board re-renders.</p></div></div>
  </div>
</div></section>

<section id="skill"><div class="wrap">
  <h2>The submission</h2>
  <p class="sub">One file. Valid front-matter, then the Skill body. That's the whole thing.</p>
  <div class="card" style="padding:16px 18px">
    <div class="codehead"><span class="kata-sub">submissions/&lt;handle&gt;/&lt;kata&gt;.md</span><button class="copy" id="copyTpl">Copy template</button></div>
    <pre id="tplBox"></pre>
  </div>
</div></section>

<section id="katas"><div class="wrap">
  <h2>Katas</h2>
  <p class="sub">Three warm-ups and five that punish a lazy Skill. One new kata drops per session.</p>
  <div class="kgrid" id="kgrid"></div>
</div></section>

<section id="scoring"><div class="wrap">
  <h2>Scoring</h2>
  <p class="sub">Lower wins. You must pass every sealed test for a kata or you don't score.</p>
  <div class="formula">score = round( cost<span style="color:#6b7280">·1000</span> &nbsp;+&nbsp; attempts<span style="color:#6b7280">·5</span> &nbsp;+&nbsp; skill_chars<span style="color:#6b7280">/100</span> )</div>
  <div class="fx">
    <div><b>Cost dominates.</b> The cheapest correct Skill wins — a good Skill on a cheap model beats a bad Skill on a frontier one.</div>
    <div><b>Attempts.</b> Each model call it takes to converge. Right shape first try = cheap.</div>
    <div><b>Length.</b> Bloat penalty. Stops the "throw more instructions at it" trap.</div>
  </div>
</div></section>

<section id="leaderboard"><div class="wrap">
  <h2>Leaderboard</h2>
  <p class="sub">🏆 current leader · <span class="flag">⚑</span> self-reported (run on an endpoint CI can't re-run).</p>
  <div id="board"></div>
</div></section>

<footer><div class="wrap">
  Built for the Eigen Builder Collective · <a id="footRepo" href="#" target="_blank">source on GitHub</a><br>
  Sibling to Prompt Golf (S4) and Loop Fail (S5).
</div></footer>

<div class="modal" id="modal"><div class="sheet">
  <h3>Sign in with GitHub</h3>
  <p>Your GitHub handle is your identity — the same one you submit PRs with. No password, no OAuth.</p>
  <input id="handleInput" placeholder="your-github-handle" autocomplete="off" spellcheck="false">
  <div class="err" id="signErr"></div>
  <div class="row">
    <button class="btn outline" id="cancelBtn">Cancel</button>
    <button class="btn gh" id="goBtn">Continue</button>
  </div>
</div></div>

<script>
const DATA=__DATA__, KATAS=__KATAS__, TEMPLATE=__TEMPLATE__, REPO=__REPO__;
const $=s=>document.querySelector(s);

// links
$('#repoLink').href=REPO; $('#footRepo').href=REPO;
$('#forkLink').href=REPO+'/fork';

// template
$('#tplBox').textContent=TEMPLATE;
$('#copyTpl').onclick=()=>{navigator.clipboard.writeText(TEMPLATE);$('#copyTpl').textContent='Copied ✓';setTimeout(()=>$('#copyTpl').textContent='Copy template',1400);};

// katas grid
$('#kgrid').innerHTML=KATAS.map(k=>{
  const bite=[1,2,3].map(i=>`<span class="${i<=k.diff?'on':'off'}">▚</span>`).join('');
  return `<div class="kcard"><div class="top"><span class="id">${k.id}</span><span class="bite">${bite}</span></div>
    <h3>${k.name}</h3><p>${k.desc}</p></div>`;
}).join('');

// leaderboard
const board=$('#board');
for(const k of KATAS){
  const rows=DATA[k.id]||[];
  const wrap=document.createElement('div');
  wrap.innerHTML=`<div class="lb-h"><h3>${k.id} · ${k.name}</h3><span class="kata-sub">${rows.length} submission${rows.length!==1?'s':''}</span></div>`;
  const card=document.createElement('div');card.className='card';
  if(!rows.length){card.innerHTML='<div class="empty">No submissions yet — sign in and be first.</div>';}
  else{card.innerHTML=`<table><thead><tr><th class="rank"></th><th>Solver</th><th>Skill</th><th>Score</th><th>Breakdown</th><th>Model</th></tr></thead><tbody>`+
    rows.map((r,i)=>`<tr><td class="rank">${i===0?'🏆':i+1}</td>
      <td class="solver">@${r.solver}${r.self_reported?'<span class="flag">⚑</span>':''}</td>
      <td><code>${r.name}</code></td><td class="score">${r.score}</td>
      <td class="brk">$${r.cost.toFixed(4)} · ${r.attempts} att · ${r.chars} ch</td>
      <td><span class="chip">${r.model}</span></td></tr>`).join('')+`</tbody></table>`;}
  wrap.appendChild(card);board.appendChild(wrap);
}

// ---- sign in (GitHub handle, validated via public API, no backend) ----
const KEY='kata_user';
function applyUser(u){
  const slot=$('#authSlot');
  document.querySelectorAll('[data-handle]').forEach(el=>el.textContent=u?u.login:'<your-handle>');
  if(u){
    slot.innerHTML=`<span class="usr"><img class="avatar" src="${u.avatar_url}" alt=""> @${u.login} <span class="signout" id="signout">sign out</span></span>`;
    $('#signout').onclick=()=>{localStorage.removeItem(KEY);applyUser(null);};
    $('#heroSignin').textContent='Signed in as @'+u.login;
    $('#howSub').textContent='Signed in as @'+u.login+' — the commands below are filled in for you.';
  }else{
    slot.innerHTML=`<button class="btn gh" id="navSignin">Sign in with GitHub</button>`;
    $('#navSignin').onclick=openModal;
    $('#heroSignin').textContent='Sign in with GitHub';
  }
}
function openModal(){$('#modal').classList.add('on');$('#signErr').textContent='';$('#handleInput').focus();}
function closeModal(){$('#modal').classList.remove('on');}
$('#heroSignin').onclick=openModal;
$('#cancelBtn').onclick=closeModal;
$('#modal').onclick=e=>{if(e.target===$('#modal'))closeModal();};
$('#handleInput').addEventListener('keydown',e=>{if(e.key==='Enter')doSignin();});
$('#goBtn').onclick=doSignin;
async function doSignin(){
  const h=$('#handleInput').value.trim().replace(/^@/,'');
  if(!h)return;
  $('#signErr').textContent='Checking…';
  try{
    const r=await fetch('https://api.github.com/users/'+encodeURIComponent(h));
    if(!r.ok){$('#signErr').textContent='No GitHub user "'+h+'".';return;}
    const u=await r.json();
    localStorage.setItem(KEY,JSON.stringify({login:u.login,avatar_url:u.avatar_url}));
    applyUser({login:u.login,avatar_url:u.avatar_url});
    closeModal();
  }catch(e){$('#signErr').textContent='Network error, try again.';}
}
try{applyUser(JSON.parse(localStorage.getItem(KEY)||'null'));}catch(e){applyUser(null);}
</script>
</body></html>"""


def write_web_data(data):
    """Emit the React app's data from the same single source of truth."""
    payload = {
        "repo": REPO,
        "template": open(os.path.join(HERE, "submissions", "_template", "SKILL.md")).read(),
        "katas": [{"id": k, "name": n, "desc": d, "diff": diff} for k, (n, d, diff) in KATA_META.items()],
        "board": {k: ordered(data.get(k, [])) for k in KATAS},
    }
    path = os.path.join(HERE, "web", "src", "data.json")
    if os.path.isdir(os.path.dirname(path)):
        open(path, "w").write(json.dumps(payload, default=str, indent=2))


if __name__ == "__main__":
    data = yaml.safe_load(open(os.path.join(HERE, "leaderboard.yaml")))
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    write_html(data)
    update_readme(readme_table(data))
    write_web_data(data)
    print("rendered site -> README.md + docs/index.html + web/src/data.json")
