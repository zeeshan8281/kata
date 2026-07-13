#!/usr/bin/env python3
"""Render leaderboard.yaml into the README table and docs/leaderboard.html.

Single source of truth is leaderboard.yaml. Run after any leaderboard change
(CI does this). No runtime fetching — data is baked into the HTML so GitHub
Pages serves it from any subpath without CORS/relative-path grief.
"""
from __future__ import annotations

import json
import os

import yaml

KATAS = {
    "001": "pr-review", "002": "refactor-async", "003": "cron-next",
    "004": "bug-hunt", "005": "secure-query", "006": "optimize",
    "007": "task-pool", "008": "semver",
}
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
    payload = {k: ordered(data.get(k, [])) for k in KATAS}
    names = json.dumps(KATAS)
    html = HTML_TMPL.replace("__DATA__", json.dumps(payload, default=str)).replace("__NAMES__", names)
    # index.html = the deployed site root (Vercel/Pages); leaderboard.html kept for the README link.
    for fn in ("index.html", "leaderboard.html"):
        open(os.path.join(HERE, "docs", fn), "w").write(html)


HTML_TMPL = """<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kata — Leaderboard</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
:root{--bg:#0a0a0a;--fg:#fafafa;--muted:#a3a3a3;--card:#171717;--border:#ffffff1a;
--primary:#1a0c6d;--accent:#7c6cff;--good:#4ade80}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
font-family:'Geist',ui-sans-serif,system-ui,sans-serif;line-height:1.5}
.wrap{max-width:900px;margin:0 auto;padding:48px 20px 80px}
header h1{font-size:3rem;letter-spacing:-1.44px;font-weight:700;margin:0}
header p{color:var(--muted);margin:.5rem 0 0}
header .bar{height:4px;width:64px;background:linear-gradient(90deg,var(--primary),var(--accent));border-radius:9999px;margin:20px 0 8px}
h2{font-size:1.5rem;letter-spacing:-.48px;margin:40px 0 12px}
.kata-sub{color:var(--muted);font-family:'Geist Mono',monospace;font-size:.8rem}
.card{background:var(--card);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-top:12px}
table{width:100%;border-collapse:collapse}
th,td{text-align:left;padding:12px 14px;border-bottom:1px solid var(--border);font-size:.92rem}
th{color:var(--muted);font-weight:500;font-size:.75rem;text-transform:uppercase;letter-spacing:.04em}
tr:last-child td{border-bottom:none}
.rank{width:34px;font-size:1.1rem}
.solver{font-weight:600}
.score{font-family:'Geist Mono',monospace;font-weight:600;font-size:1.05rem}
.brk{font-family:'Geist Mono',monospace;color:var(--muted);font-size:.78rem}
.chip{display:inline-block;background:var(--primary);color:#fff;border-radius:9999px;
padding:2px 10px;font-size:.72rem;font-family:'Geist Mono',monospace}
.flag{color:var(--muted);font-size:.72rem;border:1px solid var(--border);border-radius:9999px;padding:1px 7px;margin-left:6px}
.empty{padding:20px 14px;color:var(--muted)}
footer{margin-top:56px;color:var(--muted);font-size:.8rem}
a{color:var(--accent)}
</style></head><body><div class="wrap">
<header>
<h1>Kata</h1><div class="bar"></div>
<p>A coding kata is a practiced form. Each task is a kata — you submit a Skill that solves it. Cheaper, shorter, fewer tries wins.</p>
</header>
<div id="board"></div>
<footer>Lower score wins · <span class="flag">⚑</span> self-reported (endpoint CI can't re-run) · built for the Eigen Builder Collective</footer>
</div>
<script>
const DATA=__DATA__, NAMES=__NAMES__;
const board=document.getElementById('board');
for(const [kid,name] of Object.entries(NAMES)){
  const rows=DATA[kid]||[];
  const h=document.createElement('div');
  h.innerHTML=`<h2>${kid} · ${name} <span class="kata-sub">${rows.length} submission${rows.length!==1?'s':''}</span></h2>`;
  const card=document.createElement('div');card.className='card';
  if(!rows.length){card.innerHTML='<div class="empty">No submissions yet — be first.</div>';}
  else{
    card.innerHTML=`<table><thead><tr><th class="rank"></th><th>Solver</th><th>Skill</th><th>Score</th><th>Breakdown</th><th>Model</th></tr></thead><tbody>`+
    rows.map((r,i)=>`<tr>
      <td class="rank">${i===0?'🏆':i+1}</td>
      <td class="solver">@${r.solver}${r.self_reported?'<span class="flag">⚑</span>':''}</td>
      <td><code>${r.name}</code></td>
      <td class="score">${r.score}</td>
      <td class="brk">$${r.cost.toFixed(4)} · ${r.attempts} att · ${r.chars} ch</td>
      <td><span class="chip">${r.model}</span></td>
    </tr>`).join('')+`</tbody></table>`;
  }
  h.appendChild(card);board.appendChild(h);
}
</script></body></html>"""


if __name__ == "__main__":
    data = yaml.safe_load(open(os.path.join(HERE, "leaderboard.yaml")))
    os.makedirs(os.path.join(HERE, "docs"), exist_ok=True)
    table = readme_table(data)
    write_html(data)
    update_readme(table)
    print("rendered leaderboard -> README.md + docs/leaderboard.html")
