"""Kitty as a tiny voxel (pixel-3D) model, based on the author's own drawing, plus a small JS renderer.

The model is a list of unit cubes (x, y, z, colour): x = width, y = depth (front of the face is +y), z = height.
The renderer rotates the model around the vertical axis (yaw), keeps only the outer faces, shades them and
projects them in the same 2:1 isometric style as the building map. No 3D library is needed.
"""
import json

FUR, FUR_TOP, TUFT = "#6A7590", "#7783A0", "#353D51"
STRIPE_D, STRIPE_L = "#55607A", "#B4BDCC"
WHITE, PINK, EYE, SHINE, TEAL, NOSE = "#F5F7FB", "#F4A9B8", "#121522", "#FFFFFF", "#5CC8C9", "#2B3142"


def _model():
    v = {}

    def put(x, y, z, c):
        v[(x, y, z)] = c

    # feet
    for x in (1, 2, 5, 6):
        for y in (2, 3, 4):
            put(x, y, 0, WHITE)
    # striped body (the sweater)
    for x in range(1, 7):
        for y in range(1, 5):
            for z in range(1, 6):
                put(x, y, z, STRIPE_D if z % 2 else STRIPE_L)
    # mittens
    for x in (0, 7):
        for z in (2, 3):
            put(x, 3, z, WHITE)
        put(x, 2, 3, STRIPE_L)
    # head
    for x in range(0, 8):
        for y in range(0, 6):
            for z in range(6, 12):
                put(x, y, z, FUR_TOP if z == 11 else FUR)
    # face on the front plane (y = 5)
    for x, z, c in [(1, 9, SHINE), (2, 9, EYE), (1, 8, EYE), (2, 8, TEAL), (1, 7, EYE), (2, 7, EYE),
                    (5, 9, SHINE), (6, 9, EYE), (5, 8, EYE), (6, 8, TEAL), (5, 7, EYE), (6, 7, EYE),
                    (3, 7, NOSE), (4, 7, NOSE), (2, 6, WHITE), (3, 6, WHITE), (4, 6, WHITE), (5, 6, WHITE),
                    (0, 7, PINK), (7, 7, PINK), (3, 10, TUFT), (4, 10, TUFT)]:
        put(x, 5, z, c)
    # tuft of hair on top
    for x, y, z in [(3, 4, 12), (4, 4, 12), (3, 5, 12), (4, 5, 12), (4, 5, 13), (3, 3, 12), (4, 3, 12)]:
        put(x, y, z, TUFT)
    # ears with pink inside
    for ex, inner in ((0, 1), (7, 6)):
        for x in (ex, inner):
            for y in (2, 3):
                put(x, y, 12, FUR)
        put(ex, 2, 13, FUR)
        put(ex, 3, 13, FUR)
        put(inner, 3, 12, PINK)
    # striped tail with a white tip
    for i, (x, y, z) in enumerate([(5, 0, 2), (5, -1, 2), (5, -2, 3), (5, -2, 4), (5, -2, 5), (5, -2, 6)]):
        put(x, y, z, STRIPE_D if i % 2 else STRIPE_L)
    put(5, -2, 7, WHITE)
    # centre the model around x and y (z = 0 is the floor)
    xs = [k[0] for k in v]
    ys = [k[1] for k in v]
    cx, cy = (min(xs) + max(xs) + 1) / 2, (min(ys) + max(ys) + 1) / 2 + 0.5
    return [[x - cx, y - cy, z, c] for (x, y, z), c in v.items()]


MODEL = _model()
MODEL_JSON = json.dumps(MODEL)

# JS: catFaces(model, yaw, scale) -> [{p: [[x, y] x4], f: fill, s: stroke}] in drawing order
RENDER_JS = """
const CAT_FACES = [
  [[1,0,0],[1,0,0],[1,1,0],[1,1,1],[1,0,1]], [[-1,0,0],[0,1,0],[0,0,0],[0,0,1],[0,1,1]],
  [[0,1,0],[0,1,0],[1,1,0],[1,1,1],[0,1,1]], [[0,-1,0],[1,0,0],[0,0,0],[0,0,1],[1,0,1]],
  [[0,0,1],[0,0,1],[1,0,1],[1,1,1],[0,1,1]]];
const CAT_V = [1, 1, 0.833], CAT_L = (() => { const l = [-0.35, 0.8, 1.1], n = Math.hypot(...l); return l.map(a => a / n); })();
function catShade(hex, k) {
  const n = parseInt(hex.slice(1), 16), c = [n >> 16, (n >> 8) & 255, n & 255].map(v => Math.max(0, Math.min(255, Math.round(v * k))));
  return 'rgb(' + c.join(',') + ')';
}
function catFaces(M, yaw, s) {
  const key = (x, y, z) => x.toFixed(1) + ',' + y.toFixed(1) + ',' + z;
  const occ = new Set(M.map(v => key(v[0], v[1], v[2])));
  const c = Math.cos(yaw), sn = Math.sin(yaw);
  const rot = (x, y, z) => [x * c - y * sn, x * sn + y * c, z];
  const out = [];
  for (const [x, y, z, col] of M) {
    for (const [n, ...corners] of CAT_FACES) {
      if (occ.has(key(x + n[0], y + n[1], z + n[2]))) continue;
      const rn = rot(n[0], n[1], n[2]);
      if (rn[0] * CAT_V[0] + rn[1] * CAT_V[1] + rn[2] * CAT_V[2] <= 0.001) continue;
      const pts = corners.map(k => rot(x + k[0], y + k[1], z + k[2]));
      const ctr = pts.reduce((a, p) => [a[0] + p[0] / 4, a[1] + p[1] / 4, a[2] + p[2] / 4], [0, 0, 0]);
      const light = 0.62 + 0.42 * Math.max(0, rn[0] * CAT_L[0] + rn[1] * CAT_L[1] + rn[2] * CAT_L[2]);
      out.push({d: ctr[0] * CAT_V[0] + ctr[1] * CAT_V[1] + ctr[2] * CAT_V[2],
                p: pts.map(q => [(q[0] - q[1]) * s, (q[0] + q[1]) * s * 0.5 - q[2] * s * 1.15]),
                f: catShade(col, light), s: catShade(col, light * 0.86)});
    }
  }
  out.sort((a, b) => a.d - b.d);
  return out;
}
function catSVG(M, yaw, s) {
  return catFaces(M, yaw, s).map(f => "<polygon points='" + f.p.map(q => q[0].toFixed(1) + ',' + q[1].toFixed(1)).join(' ')
    + "' fill='" + f.f + "' stroke='" + f.s + "' stroke-width='0.35' stroke-linejoin='round'/>").join('');
}
function catCanvas(ctx, M, yaw, s, ox, oy) {
  for (const f of catFaces(M, yaw, s)) {
    ctx.beginPath(); f.p.forEach((q, i) => i ? ctx.lineTo(ox + q[0], oy + q[1]) : ctx.moveTo(ox + q[0], oy + q[1]));
    ctx.closePath(); ctx.fillStyle = f.f; ctx.fill(); ctx.strokeStyle = f.s; ctx.lineWidth = 0.8; ctx.stroke();
  }
}
"""


def viewer_html(height=300, sketch_uri=""):
    """Home-page viewer: Kitty slowly turns around; drag to spin, click to make Kitty jump."""
    sketch = (f"<img class='sk' src='{sketch_uri}' alt='original drawing' title='Made from my own drawing'/>"
              if sketch_uri else "")
    return f"""<style>
body{{margin:0;background:transparent;font-family:'DM Sans',sans-serif}}
.wrap{{position:relative;height:{height}px;border-radius:28px;overflow:hidden;cursor:grab;
 background:radial-gradient(120% 90% at 50% 15%,#FFFFFF 0%,#E6F4FF 55%,#CDE8FB 100%);
 box-shadow:inset 0 1px 0 #fff,0 8px 24px rgba(15,23,42,.12)}}
.wrap:active{{cursor:grabbing}} canvas{{width:100%;height:100%;display:block}}
.hint{{position:absolute;left:0;right:0;bottom:10px;text-align:center;font-size:12.5px;color:#475569}}
.sk{{position:absolute;right:12px;top:12px;width:58px;height:58px;border-radius:18px;object-fit:cover;
 border:3px solid #fff;box-shadow:0 4px 12px rgba(15,23,42,.2)}}
</style>
<div class='wrap' id='w'><canvas id='cv'></canvas>{sketch}<div class='hint'>Drag to spin Kitty · click to jump</div></div>
<script>{RENDER_JS}
const M = {MODEL_JSON};
const cv = document.getElementById('cv'), w = document.getElementById('w'), ctx = cv.getContext('2d');
let yaw = -0.8, spin = 0.5, drag = null, jump = 0, last = null;
function size() {{ const r = devicePixelRatio || 1; cv.width = w.clientWidth * r; cv.height = w.clientHeight * r; ctx.setTransform(r,0,0,r,0,0); }}
size(); addEventListener('resize', size);
w.addEventListener('pointerdown', e => {{ drag = {{x: e.clientX, moved: false}}; w.setPointerCapture(e.pointerId); }});
w.addEventListener('pointermove', e => {{ if (!drag) return; const dx = e.clientX - drag.x; if (Math.abs(dx) > 2) drag.moved = true;
  yaw += dx * 0.012; spin = dx * 0.6; drag.x = e.clientX; }});
w.addEventListener('pointerup', () => {{ if (drag && !drag.moved) jump = 1; drag = null; }});
function frame(t) {{
  const dt = last === null ? 0 : Math.min(0.05, (t - last) / 1000); last = t;
  if (!drag) {{ spin += (0.5 - spin) * dt * 1.5; yaw += spin * dt; }}
  jump = Math.max(0, jump - dt * 1.6);
  const W = w.clientWidth, H = w.clientHeight, s = Math.min(W, H) / 26;
  const hop = Math.sin(jump * Math.PI) * s * 5 + Math.sin(t / 260) * s * 0.25;
  ctx.clearRect(0, 0, W, H);
  ctx.fillStyle = 'rgba(15,23,42,.14)'; ctx.beginPath();
  ctx.ellipse(W / 2, H * 0.78, s * 6.5 * (1 - jump * 0.3), s * 2.4 * (1 - jump * 0.3), 0, 0, 7); ctx.fill();
  catCanvas(ctx, M, yaw, s, W / 2, H * 0.78 - hop);
  requestAnimationFrame(frame);
}}
requestAnimationFrame(frame);
</script>"""
