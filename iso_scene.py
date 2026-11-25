"""Minimal isometric 'pseudo-3D' scene of the building with an animated kitty token (pure SVG + JS, no libraries)."""
import json
import os

from evacuation.model import zone_of
from voxel_cat import MODEL_JSON, RENDER_JS

W, H, WALL = 64, 32, 11
ZONE_FLOOR = ["#FBD5DD", "#FDECB8", "#CDEFD8", "#CFE0FB"]
ZONE_SIDE = ["#E9B7C3", "#E8D08C", "#A9DDB9", "#A9C3EE"]


def _poly(pts, fill, extra=""):
    return f"<polygon points='{' '.join(f'{x:.1f},{y:.1f}' for x, y in pts)}' fill='{fill}' {extra}/>"


def _risk_colour(p):
    p = max(0.0, min(1.0, p))
    r, g, b = 255, int(236 - 160 * p), int(230 - 170 * p)
    return f"rgb({r},{g},{b})"


ZONE_DEEP = ["#BE185D", "#B45309", "#15803D", "#1D4ED8"]
ZONE_LABEL = ["Z0 north-west", "Z1 north-east", "Z2 south-west", "Z3 south-east"]


def _legend(zone_risk, blocked):
    chip = "<span class='chip'><i style='background:{}'></i>{}</span>"
    items = []
    if zone_risk is not None:
        items.append("<span class='chip'><i class='grad'></i>safe → dangerous</span>")
    else:
        items += [chip.format(ZONE_FLOOR[z], ZONE_LABEL[z]) for z in range(4)]
    items += [chip.format("#22C55E", "exit"), chip.format("#16A34A;border-radius:50%", "Kitty's route"),
              chip.format("#0F172A", "door camera")]
    if blocked is not None:
        items.append(chip.format("#F97316", "really blocked"))
    return "<div class='legend'>" + "".join(items) + "</div>"


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

    # zone name tags (with the risk when the map is coloured by risk)
    for z in range(4):
        cells = [(r, c) for r in range(rows) for c in range(cols)
                 if (r, c) not in world["walls"] and zone_of(r, c) == z
                 and (r, c) not in (*world["exits"], world["door"], world["start"])]
        if not cells:
            continue
        ar = sum(r for r, _ in cells) / len(cells)
        ac = sum(c for _, c in cells) / len(cells)
        br, bc = min(cells, key=lambda t: (t[0] - ar) ** 2 + (t[1] - ac) ** 2)
        tx, ty = top(br, bc)
        label = f"Z{z}" + (f" · {zone_risk[z] * 100:.0f}%" if zone_risk is not None else "")
        w = 26 + (34 if zone_risk is not None else 0)
        objects.append(f"<g transform='translate({tx:.1f},{ty + H / 2:.1f})' opacity='.95'>"
                       f"<rect x='{-w / 2}' y='-9' width='{w}' height='18' rx='9' fill='#fff' stroke='{ZONE_DEEP[z]}' "
                       f"stroke-width='1.5'/><text x='0' y='4.2' text-anchor='middle' font-size='11' font-weight='700' "
                       f"fill='{ZONE_DEEP[z]}'>{label}</text></g>")

    pts = [centre(r, c) for r, c in route] if route else [centre(*world["start"])]
    grid = [list(t) for t in route] if route else [list(world["start"])]
    width, height = int(x0 * 2), int((rows + cols) * H / 2 + y0 + 40)
    svg = (f"<svg viewBox='0 0 {width} {height}' width='100%' style='max-width:640px;display:block;margin:auto' "
           "role='img' aria-label='Isometric map of the house with Kitty and the chosen route'>"
           + "".join(floor) + "".join(objects)
           + "<g id='cat'><ellipse cx='0' cy='2' rx='15' ry='6' fill='#0F172A' opacity='.18'/>"
             "<g class='bob'><g id='catbody'></g></g></g></svg>")
    js = f"""
<script>{RENDER_JS}
const M = {MODEL_JSON};
const P = {json.dumps([[round(x, 1), round(y, 1)] for x, y in pts])}, G = {json.dumps(grid)};
const cat = document.getElementById('cat'), body = document.getElementById('catbody');
const FRONT = -Math.PI / 4, SEG = 430, PAUSE = 1500, SCALE = 2.7;
let yaw = FRONT, drawn = null, t0 = null, last = null;
function face(dr, dc) {{ return dr > 0 ? 0 : dr < 0 ? Math.PI : dc > 0 ? -Math.PI / 2 : Math.PI / 2; }}
function draw() {{ if (drawn === null || Math.abs(drawn - yaw) > 0.01) {{ body.innerHTML = catSVG(M, yaw, SCALE); drawn = yaw; }} }}
function place(x, y) {{ cat.setAttribute('transform', `translate(${{x}},${{y}})`); }}
place(P[0][0], P[0][1]); draw();
function frame(ts) {{
  const dt = last === null ? 0 : Math.min(0.05, (ts - last) / 1000); last = ts;
  if (t0 === null) t0 = ts;
  let target = FRONT;
  if (P.length > 1) {{
    const total = (P.length - 1) * SEG; let k = ts - t0;
    if (k > total + PAUSE) {{ t0 = ts; k = 0; yaw = face(G[1][0] - G[0][0], G[1][1] - G[0][1]); }}
    const s = Math.min(k, total) / SEG, j = Math.min(Math.floor(s), P.length - 2), f = s - j;
    place(P[j][0] + (P[j+1][0] - P[j][0]) * f, P[j][1] + (P[j+1][1] - P[j][1]) * f);
    if (k < total) target = face(G[j+1][0] - G[j][0], G[j+1][1] - G[j][1]);
  }}
  let d = target - yaw; d = Math.atan2(Math.sin(d), Math.cos(d));
  yaw += d * Math.min(1, dt * 12);
  draw();
  requestAnimationFrame(frame);
}}
requestAnimationFrame(frame);
</script>"""
    css = """<meta charset="utf-8"><style>
body{margin:0;background:transparent;font-family:'DM Sans',sans-serif}
.bob{animation:bob .42s ease-in-out infinite alternate}
@keyframes bob{from{transform:translateY(0)}to{transform:translateY(-4px)}}
.flame{animation:fl .5s ease-in-out infinite alternate;transform-box:fill-box;transform-origin:bottom}
@keyframes fl{from{opacity:.85}to{opacity:1}}
.cap{text-align:center;color:#64748B;font-size:13px;margin-top:4px}
.legend{display:flex;flex-wrap:wrap;justify-content:center;gap:6px 14px;margin-top:6px;font-size:12.5px;color:#334155}
.chip{display:inline-flex;align-items:center;gap:6px}
.chip i{display:inline-block;width:13px;height:13px;border-radius:4px;border:1px solid rgba(15,23,42,.12)}
.chip i.grad{width:70px;background:linear-gradient(90deg,rgb(255,236,230),rgb(255,76,60))}
</style>"""
    return (css + svg + _legend(zone_risk, blocked) + (f"<div class='cap'>{caption}</div>" if caption else "") + js)


def scene_height(world):
    return int(((world["rows"] + world["cols"]) * H / 2 + 110) * 1.0) + 40
