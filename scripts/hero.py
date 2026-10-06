#!/usr/bin/env python3
"""Render assets/hero.svg and assets/hero-mobile.svg (static content, animated).

  python3 scripts/hero.py
"""
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG, PANEL, BORDER = "#0d1117", "#161b22", "#30363d"
TEXT, MUTED, GREEN, BLUE = "#e6edf3", "#7d8590", "#3fb950", "#79c0ff"
MONO = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono',monospace"
SANS = "Inter,-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
CHIPS = ["java", "spring-boot", "fastapi", "react", "next.js", "postgresql", "docker", "aws"]

STYLE = f"""<style>
.mono{{font-family:{MONO}}} .sans{{font-family:{SANS}}}
.in{{animation:in .7s cubic-bezier(.2,.8,.2,1) both}}
.typed{{animation:typed 1.1s steps(11,end) .7s both}}
.caret{{animation:blink 1s steps(1) infinite}}
.pulse{{animation:pulse 2.4s ease-in-out infinite}}
.ring{{transform-box:fill-box;transform-origin:center;animation:ring 2.4s ease-out infinite}}
.dash{{animation:flow 1.6s linear infinite}}
@keyframes in{{from{{opacity:0;transform:translateY(8px)}}to{{opacity:1;transform:none}}}}
@keyframes typed{{from{{clip-path:inset(-20% 100% -20% 0)}}to{{clip-path:inset(-20% 0 -20% 0)}}}}
@keyframes blink{{50%{{fill-opacity:0}}}}
@keyframes pulse{{50%{{opacity:.35}}}}
@keyframes ring{{from{{opacity:.7;transform:scale(1)}}to{{opacity:0;transform:scale(2.6)}}}}
@keyframes flow{{to{{stroke-dashoffset:-14}}}}
@media (prefers-reduced-motion:reduce){{*{{animation:none!important}}}}
</style>"""


def defs(w, h):
    return f"""<defs>
<pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><path d="M32 0H0V32" fill="none" stroke="{BORDER}" stroke-width=".6" opacity=".45"/></pattern>
<pattern id="scan" width="4" height="3" patternUnits="userSpaceOnUse"><rect width="4" height="1" fill="#000" opacity=".18"/></pattern>
<radialGradient id="glow" cx="80%" cy="50%" r="45%"><stop offset="0" stop-color="{GREEN}" stop-opacity=".09"/><stop offset="1" stop-color="{GREEN}" stop-opacity="0"/></radialGradient>
<linearGradient id="fadeL" x1="0" x2="1"><stop offset="0" stop-color="{BG}"/><stop offset=".55" stop-color="{BG}" stop-opacity=".6"/><stop offset="1" stop-color="{BG}" stop-opacity="0"/></linearGradient>
<filter id="soft" x="-200%" y="-200%" width="500%" height="500%"><feGaussianBlur stdDeviation="2.5"/></filter>
<clipPath id="card"><rect width="{w}" height="{h}" rx="12"/></clipPath>
</defs>"""


def chips(x, y, items, maxw, delay):
    out, cx, cy = [], x, y
    for i, c in enumerate(items):
        cw = len(c) * 7.4 + 24
        if cx + cw > x + maxw:
            cx, cy = x, cy + 36
        out.append(f'<g class="in" style="animation-delay:{delay + i*60}ms">'
                   f'<rect x="{cx:.1f}" y="{cy}" width="{cw:.1f}" height="26" rx="13" fill="{PANEL}" stroke="{BORDER}"/>'
                   f'<text class="mono" x="{cx + cw/2:.1f}" y="{cy + 17}" font-size="12" fill="{TEXT}" text-anchor="middle">{c}</text></g>')
        cx += cw + 8
    return "\n".join(out)


def headline(x, y, size, second_dy, delay=150):
    # "end to end" is typed in with a CSS clip (visible as-is when motion is off); the caret glyph follows the text
    return f"""<g class="in" style="animation-delay:{delay}ms"><text class="sans" x="{x}" y="{y}" font-size="{size}" font-weight="800" fill="{TEXT}" letter-spacing="-1.5">Production apps,</text></g>
<text class="sans typed" x="{x}" y="{y + second_dy}" font-size="{size}" font-weight="800" fill="{GREEN}" letter-spacing="-1.5">end to end<tspan class="caret" fill="{GREEN}">_</tspan></text>"""


def architecture(cx, cy, s=1.0):
    """UI / API / DB / AI diamond with request packets flowing between the nodes."""
    d = 108 * s
    nodes = {"UI": (cx, cy - d), "API": (cx - d, cy), "DB": (cx + d, cy), "AI": (cx, cy + d)}
    out = [f'<circle cx="{cx}" cy="{cy}" r="{150*s}" fill="url(#glow)"/>']
    edges = [("UI", "API", "REST"), ("API", "DB", "SQL"), ("API", "AI", "LLM"), ("UI", "DB", ""), ("DB", "AI", "")]
    for a_, b_, lab in edges:
        (x1, y1), (x2, y2) = nodes[a_], nodes[b_]
        dashed = a_ == "API" and b_ == "DB"
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{BLUE if lab else BORDER}" stroke-opacity="{.5 if lab else .9}" stroke-width="1.3"'
                   + (' stroke-dasharray="6 8" class="dash"' if dashed else "") + "/>")
        if lab and not dashed:
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2
            ox = -16 if mx < cx else 16
            out.append(f'<text class="mono" x="{mx + ox*s:.1f}" y="{my + (-8 if my < cy else 16)*s:.1f}" font-size="{10*s:.1f}" fill="{MUTED}" text-anchor="{"end" if ox < 0 else "start"}">{lab}</text>')
    out.append(f'<text class="mono" x="{cx}" y="{cy - 10*s:.1f}" font-size="{10*s:.1f}" fill="{MUTED}" text-anchor="middle">SQL</text>')
    # packets: request loop UI→API→DB→API→UI and an LLM hop API→AI→API
    loop = f"M{nodes['UI'][0]},{nodes['UI'][1]} L{nodes['API'][0]},{nodes['API'][1]} L{nodes['DB'][0]},{nodes['DB'][1]} L{nodes['API'][0]},{nodes['API'][1]} Z"
    llm = f"M{nodes['API'][0]},{nodes['API'][1]} L{nodes['AI'][0]},{nodes['AI'][1]} Z"
    for path, dur, n, col in ((loop, 5.2, 3, GREEN), (llm, 3.4, 2, BLUE)):
        for k in range(n):
            begin = f"{-k * dur / n:.2f}s"
            for r, extra in ((7 * s, ' filter="url(#soft)" opacity=".8"'), (3.2 * s, "")):
                out.append(f'<circle r="{r:.1f}" fill="{col}"{extra}><animateMotion dur="{dur}s" begin="{begin}" repeatCount="indefinite" path="{path}" calcMode="spline" keyPoints="0;1" keyTimes="0;1" keySplines=".45 0 .55 1"/></circle>')
    # hub
    out.append(f'<circle class="ring" cx="{cx}" cy="{cy}" r="{7*s}" fill="none" stroke="{GREEN}" stroke-width="1.5"/>')
    out.append(f'<circle cx="{cx}" cy="{cy}" r="{7*s}" fill="{GREEN}"/>')
    for name, (x, y) in nodes.items():
        w_, h_ = 62 * s, 40 * s
        out.append(f'<rect x="{x - w_/2:.1f}" y="{y - h_/2:.1f}" width="{w_:.1f}" height="{h_:.1f}" rx="{9*s:.1f}" fill="{PANEL}" stroke="{BLUE}" stroke-opacity=".75" stroke-width="1.5"/>')
        out.append(f'<text class="mono" x="{x}" y="{y + 5*s:.1f}" font-size="{14*s:.1f}" font-weight="700" fill="{TEXT}" text-anchor="middle">{name}</text>')
    return "\n".join(out)


def frame(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" '
            f'aria-label="Priyanshu Kumar, Full Stack Engineer. Production apps, end to end.">\n'
            f'<title>Priyanshu Kumar · Full Stack Engineer</title>\n{defs(w, h)}\n{STYLE}\n'
            f'<g clip-path="url(#card)"><rect width="{w}" height="{h}" fill="{BG}"/><rect width="{w}" height="{h}" fill="url(#grid)"/>\n{body}\n'
            f'<rect width="{w}" height="{h}" fill="url(#scan)"/></g>\n'
            f'<rect x=".5" y=".5" width="{w-1}" height="{h-1}" rx="12" fill="none" stroke="{BORDER}"/>\n</svg>\n')


def desktop():
    w, h = 1000, 330
    body = [architecture(830, 165, 0.92),
            f'<rect width="640" height="{h}" fill="url(#fadeL)"/>',
            f'<g class="in"><text class="mono" x="48" y="66" font-size="13" fill="{GREEN}" letter-spacing="3">'
            f'<tspan fill="{MUTED}">~/</tspan>PRIYANSHU KUMAR <tspan fill="{MUTED}">·</tspan> FULL STACK ENGINEER</text></g>',
            headline(46, 136, 58, 64),
            f'<g class="in" style="animation-delay:900ms"><text class="sans" x="48" y="244" font-size="18" fill="{MUTED}">'
            f'<tspan fill="{TEXT}" font-weight="600">Spring Boot</tspan> APIs  ·  <tspan fill="{TEXT}" font-weight="600">Next.js</tspan> frontends  ·  '
            f'<tspan fill="{TEXT}" font-weight="600">LLM</tspan> features that ship</text></g>',
            chips(48, 272, CHIPS, 660, 1100)]
    return frame(w, h, "\n".join(body))


def mobile():
    w, h = 600, 424
    body = [f'<g opacity=".55">{architecture(486, 100, 0.5)}</g>',
            f'<g class="in"><text class="mono" x="32" y="52" font-size="12" fill="{GREEN}" letter-spacing="2.5">'
            f'<tspan fill="{MUTED}">~/</tspan>PRIYANSHU KUMAR</text></g>',
            f'<g class="in"><text class="mono" x="32" y="74" font-size="12" fill="{MUTED}" letter-spacing="2.5">FULL STACK ENGINEER</text></g>',
            headline(30, 200, 50, 58),
            f'<g class="in" style="animation-delay:900ms"><text class="sans" x="32" y="300" font-size="17" fill="{MUTED}">'
            f'<tspan fill="{TEXT}" font-weight="600">Spring Boot</tspan> APIs · <tspan fill="{TEXT}" font-weight="600">Next.js</tspan> frontends</text>'
            f'<text class="sans" x="32" y="324" font-size="17" fill="{MUTED}"><tspan fill="{TEXT}" font-weight="600">LLM</tspan> features that ship</text></g>',
            chips(32, 344, CHIPS, 540, 1100)]
    return frame(w, h, "\n".join(body))


if __name__ == "__main__":
    for name, svg in (("hero.svg", desktop()), ("hero-mobile.svg", mobile())):
        p = os.path.join(ROOT, "assets", name)
        with open(p, "w") as f:
            f.write(svg)
        print(f"wrote {p} ({len(svg)/1024:.1f} KB)")
