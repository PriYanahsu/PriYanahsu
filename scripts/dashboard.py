#!/usr/bin/env python3
"""Render assets/dashboard.svg: a terminal-style GitHub dashboard.

Stdlib only so it runs in GitHub Actions without installs.
  GITHUB_TOKEN=... python3 scripts/dashboard.py
  python3 scripts/dashboard.py --data data.json      # offline, from a saved GraphQL response
"""
import base64, datetime as dt, json, os, sys, urllib.request
from collections import defaultdict
from html import escape

USER = "PriYanahsu"
HANDLE = "priyanshu"
NAME = "Priyanshu Kumar"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTRAIT = os.path.join(ROOT, "assets", "fog-portrait.png")
OUT = os.path.join(ROOT, "assets", "dashboard.svg")

# neofetch-style card; {placeholders} are filled from live data
NEOFETCH = [
    ("role", "Full Stack Engineer @ Cognivac"),
    ("location", "Noida, India · UTC+05:30"),
    ("uptime", "{uptime} on GitHub"),
    ("backend", "Java 21 · Spring Boot 3 · FastAPI"),
    ("frontend", "React · Next.js · TypeScript · Tailwind"),
    ("data", "PostgreSQL · Redis · Supabase · pgvector"),
    ("infra", "Docker · AWS · GitHub Actions · Vercel"),
    ("ai", "Gemini · OpenAI · RAG · strict JSON schemas"),
    ("dsa", "450+ solved · 5★ HackerRank (Java, SQL)"),
    ("shipped", "{repos} public repos · {stars} ★ · {followers} followers"),
]
STATUS = "open to SDE-1 / Full Stack / Backend roles"

QUERY = """query($login:String!){user(login:$login){
  createdAt followers{totalCount}
  repositories(ownerAffiliations:OWNER,first:100,privacy:PUBLIC,isFork:false){
    totalCount nodes{stargazerCount primaryLanguage{name color}}}
  contributionsCollection{totalCommitContributions totalPullRequestContributions
    contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""


def fetch():
    if "--data" in sys.argv:
        return json.load(open(sys.argv[sys.argv.index("--data") + 1]))["data"]["user"]
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        sys.exit("set GITHUB_TOKEN (or pass --data file.json)")
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    body = json.load(urllib.request.urlopen(req, timeout=30))
    if "errors" in body:
        sys.exit(body["errors"])
    return body["data"]["user"]


def streaks(days):
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] else 0
        longest = max(longest, run)
    current, i = 0, len(days) - 1
    if i >= 0 and days[i]["contributionCount"] == 0:  # today not counted yet
        i -= 1
    while i >= 0 and days[i]["contributionCount"]:
        current += 1
        i -= 1
    return current, longest


def uptime(created_at, today):
    start = dt.date.fromisoformat(created_at[:10])
    months = (today.year - start.year) * 12 + today.month - start.month - (today.day < start.day)
    return f"{months // 12}y {months % 12}m"


# ---------- theme ----------
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, GREEN, BLUE, FOG = "#e6edf3", "#7d8590", "#3fb950", "#79c0ff", "#d6dde8"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
W = 1000
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def prompt(x, y, cmd, size=13):
    return (f'<text x="{x}" y="{y}" font-size="{size}"><tspan fill="{GREEN}">{HANDLE}@github</tspan>'
            f'<tspan fill="{MUTED}"> ~ $ </tspan><tspan fill="{TEXT}">{escape(cmd)}</tspan></text>')


def tip(n, when):
    return f'{n or "No"} contribution{"" if n == 1 else "s"} on {when}'


def render(u):
    now = dt.datetime.now(IST)
    cal = u["contributionsCollection"]["contributionCalendar"]
    weeks = cal["weeks"]
    days = [d for w in weeks for d in w["contributionDays"]]
    total = cal["totalContributions"]
    cur, longest = streaks(days)
    commits = u["contributionsCollection"]["totalCommitContributions"]
    prs = u["contributionsCollection"]["totalPullRequestContributions"]
    repos = u["repositories"]["totalCount"]
    stars = sum(r["stargazerCount"] for r in u["repositories"]["nodes"])
    followers = u["followers"]["totalCount"]
    active = sum(1 for d in days if d["contributionCount"])

    nz = sorted(d["contributionCount"] for d in days if d["contributionCount"])
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]

    def level(c):
        return 0 if c == 0 else 1 + sum(c > t for t in q)

    out = []
    a = out.append

    # ---------- window chrome ----------
    a(f'<rect x="0.5" y="0.5" width="{W-1}" height="{{H}}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    a(f'<rect x="1" y="1" width="{W-2}" height="{{H2}}" rx="11.5" fill="url(#dots)"/>')
    a(f'<path d="M0.5 36V12.5a12 12 0 0 1 12-12h{W-25}a12 12 0 0 1 12 12V36z" fill="{PANEL}"/>')
    a(f'<line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="{BORDER}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{22 + i*20}" cy="18.5" r="6" fill="{c}"/>')
    a(f'<text x="{W/2}" y="23" font-size="12" fill="{MUTED}" text-anchor="middle">{HANDLE}@github: ~/profile — zsh</text>')
    a(f'<text x="{W-24}" y="23" font-size="11" fill="{MUTED}" text-anchor="end">{now:%a %d %b}</text>')

    # ---------- whoami: fog portrait + neofetch ----------
    y = 66
    a(prompt(24, y, "whoami && neofetch"))
    py, ph = y + 14, 356
    a(f'<rect x="24" y="{py}" width="{W-48}" height="{ph}" rx="10" fill="{PANEL}" stroke="{BORDER}"/>')
    # portrait viewport
    vx, vy, vw, vh = 36, py + 12, 316, ph - 24
    a(f'<clipPath id="pv"><rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" rx="6"/></clipPath>')
    a(f'<g clip-path="url(#pv)">')
    a(f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#vig)"/>')
    with open(PORTRAIT, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    a(f'<image class="pt" x="{vx + 3}" y="{vy + 4}" width="310" height="329" href="data:image/png;base64,{b64}"/>')
    # drifting fog: static turbulence, only translated (cheap to animate)
    a(f'<g mask="url(#fogmask)"><g class="drift"><rect x="{vx-vw}" y="{vy}" width="{vw*3}" height="{vh}" filter="url(#fog)"/></g>'
      f'<g class="drift2"><rect x="{vx-vw}" y="{vy}" width="{vw*3}" height="{vh}" filter="url(#fog2)"/></g></g>')
    a(f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" fill="url(#scan)"/>')
    a(f'<rect class="sweep" x="{vx}" y="{vy}" width="{vw}" height="2" fill="{GREEN}"/>')
    a("</g>")
    # corner brackets
    for cx, cy, dx, dy in ((vx, vy, 1, 1), (vx + vw, vy, -1, 1), (vx, vy + vh, 1, -1), (vx + vw, vy + vh, -1, -1)):
        a(f'<path d="M{cx} {cy + 14*dy}V{cy}H{cx + 14*dx}" fill="none" stroke="{GREEN}" stroke-width="1.5" opacity=".8"/>')
    a(f'<text x="{vx + 10}" y="{vy + vh - 10}" font-size="9" fill="{GREEN}" opacity=".8">● REC  fog.render(priyanshu.png)</text>')

    # neofetch text
    nx = vx + vw + 32
    ny = py + 40
    a(f'<text class="ln" style="animation-delay:200ms" x="{nx}" y="{ny}" font-size="17" font-weight="700">'
      f'<tspan fill="{GREEN}">{HANDLE}</tspan><tspan fill="{MUTED}">@</tspan><tspan fill="{GREEN}">github</tspan></text>')
    a(f'<text class="ln" style="animation-delay:260ms" x="{nx}" y="{ny + 14}" font-size="12" fill="{BORDER}">{"─" * 46}</text>')
    vals = {"uptime": uptime(u["createdAt"], now.date()), "repos": repos, "stars": stars, "followers": followers}
    for i, (k, v) in enumerate(NEOFETCH):
        ly = ny + 38 + i * 22
        a(f'<text class="ln" style="animation-delay:{320 + i*70}ms" x="{nx}" y="{ly}" font-size="13">'
          f'<tspan fill="{BLUE}" font-weight="700">{k}</tspan><tspan fill="{MUTED}">{"·" * (10 - len(k))} </tspan>'
          f'<tspan fill="{TEXT}">{escape(v.format(**vals))}</tspan></text>')
    sy = ny + 38 + len(NEOFETCH) * 22 + 6
    a(f'<circle class="pulse" cx="{nx + 5}" cy="{sy - 4}" r="4.5" fill="{GREEN}"/>')
    a(f'<text class="ln" style="animation-delay:{320 + len(NEOFETCH)*70}ms" x="{nx + 18}" y="{sy}" font-size="13" fill="{GREEN}">{STATUS}</text>')
    for i, c in enumerate(("#0d1117", "#ff7b72", "#3fb950", "#d29922", "#79c0ff", "#d2a8ff", "#56d4dd", "#e6edf3")):
        a(f'<rect x="{nx + i*26}" y="{sy + 16}" width="24" height="12" fill="{c}" stroke="{BORDER}" stroke-width=".5"/>')

    # ---------- contributions heatmap ----------
    y = py + ph + 40
    a(prompt(24, y, "git log --since='1 year' | heatmap"))
    cell, step, hx, hy = 13, 16.5, 62, y + 40
    edge = f' stroke="{BORDER}" stroke-opacity=".5"'
    month_seen = None
    for wi, w in enumerate(weeks):
        first = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        if first.month != month_seen and first.day <= 7 and wi < len(weeks) - 1:
            a(f'<text x="{hx + wi*step}" y="{hy - 8}" font-size="10" fill="{MUTED}">{first.strftime("%b")}</text>')
            month_seen = first.month
        for d in w["contributionDays"]:
            wd = (dt.date.fromisoformat(d["date"]).weekday() + 1) % 7  # Sunday = 0
            lv = level(d["contributionCount"])
            t = tip(d["contributionCount"], dt.date.fromisoformat(d["date"]).strftime("%a, %d %b %Y"))
            a(f'<rect class="hm" data-tip="{t}" style="animation-delay:{wi*14}ms" x="{hx + wi*step:.1f}" y="{hy + wd*step:.1f}" '
              f'width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lv]}"{edge if not lv else ""}>'
              f'<title>{t}</title></rect>')
    # today marker
    last = days[-1]
    lwd = (dt.date.fromisoformat(last["date"]).weekday() + 1) % 7
    a(f'<rect class="pulse" x="{hx + (len(weeks)-1)*step - 1.5:.1f}" y="{hy + lwd*step - 1.5:.1f}" width="{cell+3}" height="{cell+3}" rx="3.5" fill="none" stroke="{TEXT}" stroke-width="1.2"/>')
    for wd, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        a(f'<text x="{hx - 10}" y="{hy + wd*step + 10}" font-size="10" fill="{MUTED}" text-anchor="end">{lab}</text>')
    cap_y = hy + 7 * step + 18
    a(f'<text x="{hx}" y="{cap_y}" font-size="12" fill="{MUTED}"><tspan fill="{TEXT}" font-weight="700">{total:,}</tspan> contributions'
      f' · <tspan fill="{TEXT}" font-weight="700">{active}</tspan> active days in the last year</text>')
    lx = W - 24 - 5 * 16 - 34
    a(f'<text x="{lx - 8}" y="{cap_y}" font-size="10" fill="{MUTED}" text-anchor="end">Less</text>')
    for i, c in enumerate(LEVELS):
        a(f'<rect x="{lx + i*16}" y="{cap_y - 10}" width="12" height="12" rx="2.5" fill="{c}"/>')
    a(f'<text x="{lx + 5*16 + 4}" y="{cap_y}" font-size="10" fill="{MUTED}">More</text>')

    # ---------- stat tiles ----------
    y = cap_y + 44
    a(prompt(24, y, "./stats.sh --live"))
    ty, th, gap = y + 14, 78, 12
    tw = (W - 48 - 5 * gap) / 6
    tiles = [
        ("contributions", f"{total:,}", "last 12 months", TEXT),
        ("current streak", f"{cur}d", "consecutive days", GREEN),
        ("longest streak", f"{longest}d", "in the last year", TEXT),
        ("commits", f"{commits:,}", "last 12 months", TEXT),
        ("pull requests", f"{prs:,}", "last 12 months", TEXT),
        ("stars", f"{stars}", f"across {repos} repos", TEXT),
    ]
    for i, (lab, val, sub, col) in enumerate(tiles):
        x = 24 + i * (tw + gap)
        a(f'<rect x="{x:.1f}" y="{ty}" width="{tw:.1f}" height="{th}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
        a(f'<rect x="{x:.1f}" y="{ty}" width="3" height="{th}" rx="1.5" fill="{col if col != TEXT else BORDER}"/>')
        a(f'<text x="{x+14:.1f}" y="{ty+22}" font-size="10.5" fill="{MUTED}">› {lab}</text>')
        a(f'<text class="num" style="animation-delay:{150 + i*80}ms" x="{x+14:.1f}" y="{ty+52}" font-size="25" font-weight="700" fill="{col}">{val}</text>')
        a(f'<text x="{x+14:.1f}" y="{ty+69}" font-size="10" fill="{MUTED}">{escape(sub)}</text>')

    # ---------- weekly bars ----------
    by, bh = ty + th + gap, 176
    bw_panel = 600
    a(f'<rect x="24" y="{by}" width="{bw_panel}" height="{bh}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    a(f'<text x="38" y="{by+22}" font-size="11" fill="{MUTED}">› contributions / week · last 26 weeks</text>')
    last26 = weeks[-26:]
    wk = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in last26]
    peak = max(wk) or 1
    avg = sum(wk) / len(wk)
    a(f'<text x="{24+bw_panel-14}" y="{by+22}" font-size="11" fill="{MUTED}" text-anchor="end">peak <tspan fill="{TEXT}">{peak}</tspan> · avg <tspan fill="{TEXT}">{avg:.0f}</tspan></text>')
    area_x, area_w, base, area_h = 38, bw_panel - 28, by + bh - 26, bh - 70
    bw = area_w / len(wk)
    for g in (0.5, 1.0):
        gy = base - g * area_h
        a(f'<line x1="{area_x}" y1="{gy:.1f}" x2="{area_x+area_w}" y2="{gy:.1f}" stroke="{BORDER}" stroke-dasharray="2 4" opacity=".6"/>')
    ay = base - avg / peak * area_h
    a(f'<line x1="{area_x}" y1="{ay:.1f}" x2="{area_x+area_w}" y2="{ay:.1f}" stroke="{BLUE}" stroke-dasharray="4 3" opacity=".55"/>')
    a(f'<line x1="{area_x}" y1="{base+0.5}" x2="{area_x+area_w}" y2="{base+0.5}" stroke="{BORDER}"/>')
    for i, (v, w) in enumerate(zip(wk, last26)):
        hgt = max(2, v / peak * area_h)
        cx = area_x + i * bw + bw / 2
        col = LEVELS[4] if i == len(wk) - 1 else LEVELS[3] if v >= peak * 0.6 else LEVELS[2]
        d0 = dt.date.fromisoformat(w["contributionDays"][0]["date"])
        d1 = dt.date.fromisoformat(w["contributionDays"][-1]["date"])
        span = f'week of {d0:%d %b} – {d1:%d %b %Y}' + (" (this week)" if i == len(wk) - 1 else "")
        # full-height hit area so the tooltip works even on short bars
        a(f'<g class="wk" data-tip="{tip(v, span)}"><title>{tip(v, span)}</title>'
          f'<rect x="{area_x + i*bw:.1f}" y="{base - area_h - 14:.1f}" width="{bw:.1f}" height="{area_h + 14:.1f}" fill="transparent"/>'
          f'<rect class="bar" style="animation-delay:{300 + i*25}ms" x="{area_x + i*bw + 2:.1f}" y="{base - hgt:.1f}" '
          f'width="{bw - 4:.1f}" height="{hgt:.1f}" rx="2" fill="{col}"/></g>')
        if v:
            a(f'<text class="ln" style="animation-delay:{500 + i*25}ms" x="{cx:.1f}" y="{base - hgt - 4:.1f}" font-size="9" '
              f'fill="{TEXT if i == len(wk) - 1 else MUTED}" text-anchor="middle">{v}</text>')
        if (i % 4 == 0 and i < len(wk) - 2) or i == len(wk) - 1:
            lab = "now" if i == len(wk) - 1 else f"{d0:%d %b}"
            a(f'<text x="{cx:.1f}" y="{base + 15}" font-size="9" fill="{MUTED}" text-anchor="middle">{lab}</text>')

    # ---------- languages ----------
    lx0 = 24 + bw_panel + gap
    lw = W - 24 - lx0
    langs, colors = defaultdict(int), {}
    for r in u["repositories"]["nodes"]:
        lang = r.get("primaryLanguage")
        if lang and lang["name"] not in ("Jupyter Notebook", "HTML", "CSS"):
            langs[lang["name"]] += 1
            colors[lang["name"]] = lang["color"] or MUTED
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:5]
    tot = sum(v for _, v in top) or 1
    a(f'<rect x="{lx0}" y="{by}" width="{lw}" height="{bh}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    a(f'<text x="{lx0+14}" y="{by+22}" font-size="11" fill="{MUTED}">› top languages · by repo</text>')
    rw = lw - 106 - 52
    for i, (n, v) in enumerate(top):
        ry = by + 46 + i * 23
        a(f'<text x="{lx0+14}" y="{ry}" font-size="11" fill="{TEXT}">{escape(n)}</text>')
        a(f'<rect x="{lx0+106}" y="{ry-8}" width="{rw}" height="7" rx="3.5" fill="{BG}"/>')
        a(f'<rect class="lbar" style="animation-delay:{400 + i*90}ms" x="{lx0+106}" y="{ry-8}" width="{max(4, v/top[0][1]*rw):.1f}" height="7" rx="3.5" fill="{colors[n]}"/>')
        a(f'<text x="{lx0+lw-14}" y="{ry}" font-size="10.5" fill="{MUTED}" text-anchor="end">{v/tot*100:.0f}%</text>')

    # ---------- footer ----------
    fy = by + bh + 34
    a(prompt(24, fy, ""))
    a(f'<rect class="cursor" x="{24 + 7.8*len(HANDLE + "@github ~ $ ")}" y="{fy-12}" width="8" height="15" fill="{TEXT}"/>')
    a(f'<text x="{W-24}" y="{fy}" font-size="11" fill="{MUTED}" text-anchor="end">updated {now:%d %b %Y, %H:%M} IST · auto-refreshes hourly</text>')
    H = int(fy + 22)

    defs = f"""<defs>
<pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r=".9" fill="{BORDER}" opacity=".45"/></pattern>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".14"/></pattern>
<radialGradient id="vig" cx="50%" cy="40%" r="70%"><stop offset="0" stop-color="#1f2630"/><stop offset="1" stop-color="{PANEL}"/></radialGradient>
<filter id="fog" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".006 .018" numOctaves="4" seed="3"/>
<feColorMatrix values="0 0 0 0 .84  0 0 0 0 .87  0 0 0 0 .91  0 0 0 .9 -.42"/></filter>
<filter id="fog2" x="0" y="0" width="100%" height="100%"><feTurbulence type="fractalNoise" baseFrequency=".012 .03" numOctaves="3" seed="11"/>
<feColorMatrix values="0 0 0 0 .84  0 0 0 0 .87  0 0 0 0 .91  0 0 0 .8 -.42"/></filter>
<linearGradient id="fogfade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".35"/><stop offset=".45" stop-color="#fff" stop-opacity=".12"/><stop offset=".75" stop-color="#fff" stop-opacity=".5"/><stop offset="1" stop-color="#fff" stop-opacity="1"/></linearGradient>
<mask id="fogmask"><rect x="0" y="0" width="{W}" height="2000" fill="url(#fogfade)"/></mask>
</defs>"""
    style = f"""<style>
text{{font-family:{MONO}}}
.hm{{animation:pop .5s ease-out both}}
.bar{{transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) both}}
.lbar{{transform-box:fill-box;transform-origin:left;animation:growx .9s cubic-bezier(.2,.8,.2,1) both}}
.ln,.num{{animation:type .45s ease-out both}}
.pt{{animation:fade 1.8s ease-out both}}
.drift{{animation:drift 38s linear infinite alternate}}
.drift2{{animation:drift 24s linear infinite alternate-reverse}}
.sweep{{opacity:0;animation:sweep 6s ease-in-out 1s infinite}}
.cursor{{animation:blink 1.1s steps(1) infinite}}
.pulse{{animation:pulse 2s ease-in-out infinite}}
.hm:hover{{stroke:{TEXT};stroke-width:1.5;stroke-opacity:1}}
.wk:hover .bar{{fill:{LEVELS[4]}}}
[data-tip]{{cursor:pointer}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes growx{{from{{transform:scaleX(0)}}to{{transform:scaleX(1)}}}}
@keyframes type{{from{{opacity:0;transform:translateX(-6px)}}to{{opacity:1;transform:none}}}}
@keyframes fade{{from{{opacity:0;filter:blur(8px)}}to{{opacity:1;filter:blur(0)}}}}
@keyframes drift{{from{{transform:translateX(0)}}to{{transform:translateX(300px)}}}}
@keyframes sweep{{0%{{opacity:0;transform:translateY(0)}}8%{{opacity:.5}}40%{{opacity:.5;transform:translateY(330px)}}45%,100%{{opacity:0;transform:translateY(330px)}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes pulse{{50%{{opacity:.3}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.sweep{{opacity:0}}}}
</style>"""
    body = "\n".join(out).replace("{H}", str(H - 1)).replace("{H2}", str(H - 2))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{NAME} GitHub dashboard: {total} contributions, {cur}-day streak">\n'
            f'<title>{NAME} · GitHub dashboard</title>\n{defs}\n{style}\n{body}\n</svg>\n')


PAGE = os.path.join(ROOT, "docs", "index.html")


def page(svg):
    # README images can't show hover tooltips; inline SVG on GitHub Pages can.
    # The native <title> tooltip is slow and absent on touch, so show our own.
    css = (f'html,body{{margin:0;background:{BG}}}main{{max-width:{W}px;margin:24px auto;padding:0 16px}}'
           f'svg{{width:100%;height:auto;display:block}}'
           f'#tip{{position:fixed;pointer-events:none;z-index:9;padding:6px 9px;border-radius:6px;'
           f'background:{TEXT};color:{BG};font:12px/1.3 {MONO};white-space:nowrap;'
           f'transform:translate(-50%,calc(-100% - 10px));opacity:0;transition:opacity .08s}}'
           f'#tip b{{font-weight:700}}')
    js = """
const tip = document.getElementById('tip');
function show(el) {
  const r = (el.querySelector('.bar') || el).getBoundingClientRect(), t = el.dataset.tip, i = t.indexOf(' on ');
  tip.innerHTML = '';
  const b = document.createElement('b'); b.textContent = t.slice(0, i);
  tip.append(b, t.slice(i));
  tip.style.left = Math.min(Math.max(r.left + r.width / 2, 120), innerWidth - 120) + 'px';
  tip.style.top = r.top + 'px';
  tip.style.opacity = 1;
}
document.querySelectorAll('[data-tip] > title').forEach(t => t.remove());
document.addEventListener('pointerover', e => {
  const el = e.target.closest('[data-tip]');
  el ? show(el) : (tip.style.opacity = 0);
});
addEventListener('scroll', () => (tip.style.opacity = 0), {passive: true});
"""
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{NAME} · GitHub dashboard</title><style>{css}</style></head>'
            f'<body><main>{svg}</main><div id="tip" role="tooltip"></div><script>{js}</script></body></html>\n')

if __name__ == "__main__":
    svg = render(fetch())
    with open(OUT, "w") as f:
        f.write(svg)
    os.makedirs(os.path.dirname(PAGE), exist_ok=True)
    with open(PAGE, "w") as f:
        f.write(page(svg))
    print(f"wrote {OUT} ({len(svg)/1024:.0f} KB) and {PAGE}")
