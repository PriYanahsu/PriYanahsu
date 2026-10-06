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
ROLE = "Full Stack Engineer @ Cognivac"
LOCATION = "Noida, India"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PORTRAIT = os.path.join(ROOT, "assets", "fog-portrait.png")
OUT = os.path.join(ROOT, "assets", "dashboard.svg")

QUERY = """query($login:String!){user(login:$login){
  followers{totalCount}
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


# ---------- theme ----------
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, GREEN, BLUE = "#e6edf3", "#7d8590", "#3fb950", "#79c0ff"
LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
W = 1000


def prompt(x, y, cmd, size=13):
    return (f'<text x="{x}" y="{y}" font-size="{size}"><tspan fill="{GREEN}">{HANDLE}@github</tspan>'
            f'<tspan fill="{MUTED}"> ~ $ </tspan><tspan fill="{TEXT}">{escape(cmd)}</tspan></text>')


def render(u):
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

    nz = sorted(d["contributionCount"] for d in days if d["contributionCount"])
    q = [nz[int(len(nz) * f)] for f in (0.25, 0.5, 0.75)] if nz else [1, 2, 3]

    def level(c):
        if c == 0:
            return 0
        return 1 + sum(c > t for t in q)

    out = []
    a = out.append

    # ---------- title bar ----------
    a(f'<rect x="0.5" y="0.5" width="{W-1}" height="{{H}}" rx="12" fill="{BG}" stroke="{BORDER}"/>')
    a(f'<path d="M0.5 36V12.5a12 12 0 0 1 12-12h{W-25}a12 12 0 0 1 12 12V36z" fill="{PANEL}"/>')
    a(f'<line x1="0" y1="36.5" x2="{W}" y2="36.5" stroke="{BORDER}"/>')
    for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        a(f'<circle cx="{22 + i*20}" cy="18.5" r="6" fill="{c}"/>')
    a(f'<text x="{W/2}" y="23" font-size="12" fill="{MUTED}" text-anchor="middle">{HANDLE}@github: ~/profile — zsh</text>')

    # ---------- contributions heatmap ----------
    a(prompt(24, 66, "./contributions.sh --last 365d"))
    cell, step, hx, hy = 13, 16.5, 62, 104
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
            a(f'<rect class="hm" style="animation-delay:{wi*18}ms" x="{hx + wi*step:.1f}" y="{hy + wd*step:.1f}" '
              f'width="{cell}" height="{cell}" rx="2.5" fill="{LEVELS[lv]}"{edge if not lv else ""}>'
              f'<title>{d["contributionCount"]} on {d["date"]}</title></rect>')
    for wd, lab in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        a(f'<text x="{hx - 10}" y="{hy + wd*step + 10}" font-size="10" fill="{MUTED}" text-anchor="end">{lab}</text>')
    cap_y = hy + 7 * step + 18
    a(f'<text x="{hx}" y="{cap_y}" font-size="12" fill="{MUTED}"><tspan fill="{TEXT}" font-weight="700">{total:,}</tspan> contributions in the last year</text>')
    lx = W - 24 - 5 * 16 - 34
    a(f'<text x="{lx - 8}" y="{cap_y}" font-size="10" fill="{MUTED}" text-anchor="end">Less</text>')
    for i, c in enumerate(LEVELS):
        a(f'<rect x="{lx + i*16}" y="{cap_y - 10}" width="12" height="12" rx="2.5" fill="{c}"/>')
    a(f'<text x="{lx + 5*16 + 4}" y="{cap_y}" font-size="10" fill="{MUTED}">More</text>')

    # ---------- whoami panel ----------
    py = cap_y + 22
    a(f'<line x1="24" y1="{py}" x2="{W-24}" y2="{py}" stroke="{BORDER}" stroke-dasharray="3 4"/>')
    py += 32
    a(prompt(24, py, "whoami"))
    a(prompt(404, py, "./stats.sh"))
    px, pw, ph = 24, 360, 420
    a(f'<rect x="{px}" y="{py+14}" width="{pw}" height="{ph}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    with open(PORTRAIT, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    a(f'<image class="pt" x="{px+20}" y="{py+24}" width="320" height="340" href="data:image/png;base64,{b64}"/>')
    a(f'<rect class="scan" x="{px+1}" y="{py+15}" width="{pw-2}" height="3" fill="{GREEN}" opacity=".0"/>')
    ny = py + 14 + ph - 50
    a(f'<text x="{px+20}" y="{ny}" font-size="16" font-weight="700" fill="{TEXT}">{NAME}</text>')
    a(f'<text x="{px+20}" y="{ny+20}" font-size="12" fill="{MUTED}">{ROLE} · {LOCATION}</text>')
    a(f'<circle cx="{px+pw-26}" cy="{ny-5}" r="4" fill="{GREEN}" class="pulse"/>')
    a(f'<text x="{px+pw-36}" y="{ny-1}" font-size="11" fill="{GREEN}" text-anchor="end">open to work</text>')

    # ---------- stat tiles ----------
    sx, sw = 404, W - 24 - 404
    tw, th, gap = (sw - 2 * 12) / 3, 74, 12
    tiles = [
        ("contributions", f"{total:,}", "last 12 months"),
        ("current streak", f"{cur}d", "consecutive days"),
        ("longest streak", f"{longest}d", "in the last year"),
        ("commits", f"{commits:,}", "last 12 months"),
        ("pull requests", f"{prs:,}", "last 12 months"),
        ("public repos", f"{repos}", f"★ {stars} · {followers} followers"),
    ]
    for i, (lab, val, sub) in enumerate(tiles):
        x = sx + (i % 3) * (tw + gap)
        y = py + 14 + (i // 3) * (th + gap)
        a(f'<rect x="{x:.1f}" y="{y}" width="{tw:.1f}" height="{th}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
        a(f'<text x="{x+14:.1f}" y="{y+22}" font-size="11" fill="{MUTED}">› {lab}</text>')
        a(f'<text x="{x+14:.1f}" y="{y+50}" font-size="24" font-weight="700" fill="{GREEN if i == 1 else TEXT}">{val}</text>')
        a(f'<text x="{x+14:.1f}" y="{y+66}" font-size="10" fill="{MUTED}">{escape(sub)}</text>')

    # ---------- weekly bars ----------
    by = py + 14 + 2 * (th + gap)
    bh = 132
    a(f'<rect x="{sx}" y="{by}" width="{sw}" height="{bh}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    a(f'<text x="{sx+14}" y="{by+22}" font-size="11" fill="{MUTED}">› contributions / week · last 26 weeks</text>')
    wk = [sum(d["contributionCount"] for d in w["contributionDays"]) for w in weeks[-26:]]
    peak = max(wk) or 1
    a(f'<text x="{sx+sw-14}" y="{by+22}" font-size="11" fill="{MUTED}" text-anchor="end">peak {peak}</text>')
    area_x, area_w, base, area_h = sx + 14, sw - 28, by + bh - 16, bh - 50
    bw = area_w / len(wk)
    a(f'<line x1="{area_x}" y1="{base+0.5}" x2="{area_x+area_w}" y2="{base+0.5}" stroke="{BORDER}"/>')
    for i, v in enumerate(wk):
        hgt = max(2, v / peak * area_h)
        col = LEVELS[4] if i == len(wk) - 1 else LEVELS[3] if v >= peak * 0.6 else LEVELS[2]
        a(f'<rect class="bar" style="animation-delay:{300 + i*25}ms" x="{area_x + i*bw + 2:.1f}" y="{base - hgt:.1f}" '
          f'width="{bw - 4:.1f}" height="{hgt:.1f}" rx="2" fill="{col}"><title>{v} contributions</title></rect>')

    # ---------- languages ----------
    ly = by + bh + gap
    lh = py + 14 + ph - ly
    langs, colors = defaultdict(int), {}
    for r in u["repositories"]["nodes"]:
        lang = r.get("primaryLanguage")
        if lang and lang["name"] not in ("Jupyter Notebook", "HTML", "CSS"):
            langs[lang["name"]] += 1
            colors[lang["name"]] = lang["color"] or MUTED
    top = sorted(langs.items(), key=lambda kv: -kv[1])[:6]
    tot = sum(v for _, v in top) or 1
    a(f'<rect x="{sx}" y="{ly}" width="{sw}" height="{lh}" rx="8" fill="{PANEL}" stroke="{BORDER}"/>')
    a(f'<text x="{sx+14}" y="{ly+22}" font-size="11" fill="{MUTED}">› top languages · by repo</text>')
    a(f'<clipPath id="lb"><rect x="{sx+14}" y="{ly+34}" width="{sw-28}" height="8" rx="4"/></clipPath><g clip-path="url(#lb)">')
    cx = sx + 14
    for n, v in top:
        wseg = v / tot * (sw - 28)
        a(f'<rect x="{cx:.1f}" y="{ly+34}" width="{wseg+0.5:.1f}" height="8" fill="{colors[n]}"/>')
        cx += wseg
    a("</g>")
    colw = (sw - 28) / 3
    for i, (n, v) in enumerate(top):
        x = sx + 14 + (i % 3) * colw
        y = ly + 66 + (i // 3) * 22
        a(f'<circle cx="{x+4:.1f}" cy="{y-4}" r="4" fill="{colors[n]}"/>')
        a(f'<text x="{x+14:.1f}" y="{y}" font-size="11" fill="{TEXT}">{escape(n)} <tspan fill="{MUTED}">{v/tot*100:.0f}%</tspan></text>')

    # ---------- footer ----------
    fy = py + 14 + ph + 36
    a(prompt(24, fy, ""))
    a(f'<rect class="cursor" x="{24 + 7.8*len(HANDLE + "@github ~ $ ")}" y="{fy-12}" width="8" height="15" fill="{TEXT}"/>')
    a(f'<text x="{W-24}" y="{fy}" font-size="11" fill="{MUTED}" text-anchor="end">updated {dt.date.today():%d %b %Y} · auto-refreshes daily</text>')
    H = fy + 22

    style = f"""<style>
text{{font-family:{MONO}}}
.hm{{animation:pop .5s ease-out both}}
.bar{{transform-box:fill-box;transform-origin:bottom;animation:grow .7s cubic-bezier(.2,.8,.2,1) both}}
.pt{{animation:fade 1.6s ease-out both}}
.scan{{animation:scan 3.2s ease-in-out .2s 1 both}}
.cursor{{animation:blink 1.1s steps(1) infinite}}
.pulse{{animation:pulse 2s ease-in-out infinite}}
@keyframes pop{{from{{opacity:0}}to{{opacity:1}}}}
@keyframes grow{{from{{transform:scaleY(0)}}to{{transform:scaleY(1)}}}}
@keyframes fade{{from{{opacity:0;filter:blur(6px)}}to{{opacity:1;filter:blur(0)}}}}
@keyframes scan{{0%{{opacity:.0;transform:translateY(0)}}10%{{opacity:.55}}90%{{opacity:.55}}100%{{opacity:0;transform:translateY(360px)}}}}
@keyframes blink{{50%{{opacity:0}}}}
@keyframes pulse{{50%{{opacity:.35}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}.scan{{opacity:0}}}}
</style>"""
    body = "\n".join(out).replace("{H}", str(H - 1))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" '
            f'role="img" aria-label="{NAME} GitHub dashboard: {total} contributions in the last year">\n{style}\n{body}\n</svg>\n')


if __name__ == "__main__":
    svg = render(fetch())
    with open(OUT, "w") as f:
        f.write(svg)
    print(f"wrote {OUT} ({len(svg)/1024:.0f} KB)")
