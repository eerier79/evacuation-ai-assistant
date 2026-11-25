"""Minimal isometric 'pseudo-3D' scene of the building with an animated kitty token (pure SVG + JS, no libraries)."""
import base64
import json
import os

from evacuation.model import zone_of

W, H, WALL = 64, 32, 11
ZONE_FLOOR = ["#FBD5DD", "#FDECB8", "#CDEFD8", "#CFE0FB"]
ZONE_SIDE = ["#E9B7C3", "#E8D08C", "#A9DDB9", "#A9C3EE"]
_TOKEN = None


def _token_uri():
    global _TOKEN
    if _TOKEN is None:
        path = os.path.join(os.path.dirname(__file__), "assets", "kitty_token.png")
        try:
            with open(path, "rb") as f:
                _TOKEN = "data:image/png;base64," + base64.b64encode(f.read()).decode()
        except OSError:
            _TOKEN = ""
    return _TOKEN


def _poly(pts, fill, extra=""):
    return f"<polygon points='{' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)}' fill='{fill}' {extra}/>"


def _risk_colour(p):
    p = max(0.0, min(1.0, p))
    r, g, b = 255, int(236 - 160 * p), int(230 - 170 * p)
    return f"rgb({r},{g},{b})"


def scene_html(world, route=None, zone_risk=None, blocked=None, caption=""):
    rows, cols = world["rows"], world["cols"]
    x0, y0 = rows * W / 2 + 30, 50

    def top(r, c):
        return (c - r) * W / 2 + x0, (c + r) * H / 2 + y0

    def centre(r, c):
        x, y = top(r, c)
        return x, y + H / 2

    route = route or []
    route_set = set(route)
    floor, objects = [], []
    for r in range(rows):
        for c in range(cols):
            x, y = top(r, c)
            if (r, c) in world["walls"]:
                continue
            z = zone_of(r, c)
            fill = _risk_colour(zone_risk[z]) if zone_risk is not None else ZONE_FLOOR[z]
            if (r, c) in world["exits"]:
                fill = "#22C55E"
            floor.append(_poly([(x, y), (x + W / 2, y + H / 2), (x, y + H), (x - W / 2, y + H / 2)], fill,
                               "stroke='#ffffff' stroke-width='1.5'"))
            if (r, c) in route_set and (r, c) != world["start"]:
                cx, cy = centre(r, c)
                floor.append(f"<ellipse cx='{cx}' cy='{cy}' rx='9' ry='4.5' fill='#16A34A' opacity='.85'/>")
    # walls and objects in painter's order (back to front)
    cells = sorted(((r, c) for r in range(rows) for c in range(cols)), key=lambda t: (t[0] + t[1], t[1]))
    for r, c in cells:
        x, y = top(r, c)
        cx, cy = centre(r, c)
        if (r, c) in world["walls"]:
            objects.append(_poly([(x - W / 2, y + H / 2 - WALL), (x, y + H - WALL), (x, y + H), (x - W / 2, y + H / 2)], "#94A3B8"))
            objects.append(_poly([(x + W / 2, y + H / 2 - WALL), (x, y + H - WALL), (x, y + H), (x + W / 2, y + H / 2)], "#64748B"))
            objects.append(_poly([(x, y - WALL), (x + W / 2, y + H / 2 - WALL), (x, y + H - WALL), (x - W / 2, y + H / 2 - WALL)],
                                 "#CBD5E1", "stroke='#E2E8F0' stroke-width='1'"))
            continue
        z = zone_of(r, c)
        if blocked is not None and blocked[z] and (r + c) % 2 == 0 and (r, c) != world["start"]:
            objects.append(f"<g class='flame' transform='translate({cx},{cy + 2})'>"
                           "<path d='M0,0 C-10,-4 -8,-16 0,-26 C1,-17 10,-14 8,-5 C7,0 3,1 0,0Z' fill='#F97316'/>"
                           "<path d='M0,-1 C-5,-3 -4,-10 0,-15 C1,-10 5,-8 4,-3 C3,-1 1,0 0,-1Z' fill='#FDE047'/></g>")
        if (r, c) in world["exits"]:
            objects.append(f"<g transform='translate({cx},{cy})'><rect x='-16' y='-34' width='32' height='15' rx='5' fill='#16A34A'/>"
                           "<text x='0' y='-23' text-anchor='middle' font-size='10' font-weight='700' fill='#fff'>EXIT</text></g>")
        if (r, c) == world["door"]:
            objects.append(f"<g transform='translate({cx},{cy})'><rect x='-10' y='-22' width='20' height='13' rx='3' fill='#0F172A'/>"
                           "<circle cx='0' cy='-15.5' r='4' fill='#38BDF8'/></g>")

    pts = [centre(r, c) for r, c in route] if route else [centre(*world["start"])]
    token = _token_uri()
    width, height = int(x0 * 2), int((rows + cols) * H / 2 + y0 + 40)
    svg = (f"<svg viewBox='0 0 {width} {height}' width='100%' style='max-width:640px;display:block;margin:auto'>"
           f"<defs><clipPath id='clip'><circle cx='0' cy='0' r='19'/></clipPath>"
           f"<filter id='sh' x='-50%' y='-50%' width='200%' height='200%'><feDropShadow dx='0' dy='3' stdDeviation='2.5' flood-opacity='.35'/></filter></defs>"
           + "".join(floor) + "".join(objects)
           + f"<g id='cat'><ellipse cx='0' cy='4' rx='16' ry='6' fill='#000' opacity='.18'/>"
           f"<g class='bob'><circle cx='0' cy='-20' r='21' fill='#fff' filter='url(#sh)'/>"
           + (f"<image href='{token}' x='-19' y='-39' width='38' height='38' clip-path='circle(19px at 19px 19px)'/>" if token
              else "<text x='0' y='-12' text-anchor='middle' font-size='26'>🐱</text>")
           + "</g></g></svg>")
    js = f"""
<script>
const P = {json.dumps([[round(x, 1), round(y, 1)] for x, y in pts])};
const cat = document.getElementById('cat');
let i = 0, t0 = null; const SEG = 420, PAUSE = 1400;
function place(x, y) {{ cat.setAttribute('transform', `translate(${{x}},${{y}})`); }}
place(P[0][0], P[0][1]);
function frame(ts) {{
  if (P.length < 2) return;
  if (t0 === null) t0 = ts;
  const total = (P.length - 1) * SEG, k = ts - t0;
  if (k > total + PAUSE) {{ t0 = ts; }}
  const s = Math.min(k, total) / SEG, j = Math.min(Math.floor(s), P.length - 2), f = s - j;
  place(P[j][0] + (P[j+1][0] - P[j][0]) * f, P[j][1] + (P[j+1][1] - P[j][1]) * f);
  requestAnimationFrame(frame);
}}
requestAnimationFrame(frame);
</script>"""
    css = """<style>
body{margin:0;background:transparent;font-family:'DM Sans',sans-serif}
.bob{animation:bob .42s ease-in-out infinite alternate}
@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-4px)}}
.flame{animation:fl .5s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:bottom}
@keyframes fl{from{opacity:.85}to{opacity:1}}
.cap{text-align:center;color:#64748B;font-size:13px;margin-top:4px}
</style>"""
    return css + svg + (f"<div class='cap'>{caption}</div>" if caption else "") + js


def scene_height(world):
    return int(((world["rows"] + world["cols"]) * H / 2 + 110) * 1.0) + 40
