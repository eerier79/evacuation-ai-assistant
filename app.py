"""Kitty Escape - Emergency Evacuation Assistant, web interface (v4)."""
import base64
import math
import os
import random
from datetime import datetime

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from evacuation.explain import walkthrough, why
from evacuation.planner import plan
from evacuation.simulate import POLICIES, evaluate, run_episode
from icons import icon, icon_uri
from iso_scene import scene_html
from voxel_cat import viewer_html

HERE = os.path.dirname(os.path.abspath(__file__))


def _page_icon():
    try:
        from PIL import Image
        return Image.open(os.path.join(HERE, "assets", "kitty_token.png"))
    except Exception:
        return None


st.set_page_config(page_title="Kitty Escape · Evacuation Assistant", page_icon=_page_icon(), layout="wide")

# colours chosen so that white text keeps a contrast ratio of at least 4.5
BLUE, PURPLE, GREEN, RED, ORANGE, NAVY = "#0369A1", "#6D28D9", "#15803D", "#B91C1C", "#C2410C", "#123F63"
ACCENT = "#1CB0F6"
ZONE_SHORT = ["Z0 · north-west", "Z1 · north-east", "Z2 · south-west", "Z3 · south-east"]
DECISION = {
    "PROCEED": ("bolt", "green", GREEN, "#16A34A", "Proceed", "The fast route is probably clear. Kitty runs the shortest way out."),
    "DETOUR": ("shield", "orange", ORANGE, "#EA580C", "Detour", "The fast route is too risky. Kitty takes the longer, safer route."),
    "WAIT": ("hourglass", "blue", BLUE, "#0284C7", "Wait", "Not enough information yet. Kitty stays put and listens to the sensors."),
}
TERMS = {
    "HMM": "Hidden Markov Model: keeps a probability for every zone and updates it after each sensor step.",
    "A*": "A-star search: finds the cheapest route; risky cells cost more.",
    "Bayes": "Bayes' rule: updates a probability after new evidence (here, the door camera).",
    "MDP": "Markov Decision Process: gives every action an expected score and picks the best one.",
}

# custom icons for buttons (Streamlit adds the class st-key-<key> to every keyed widget)
BUTTON_ICONS = {
    "nav_0": "home", "nav_1": "compass", "nav_2": "flame", "nav_3": "chart", "nav_4": "book",
    "home_play": "play", "home_sim": "flame", "add_step": "plus", "reset": "reset", "new_fire": "dice",
    "scn_quiet": "check", "scn_fire": "flame", "scn_unclear": "hourglass", "scn_two": "sensor",
    "tour_back": "back", "tour_next": "next",
}
icon_css = "".join(
    f".st-key-{k} button::before{{content:'';width:26px;height:26px;flex:none;margin-right:8px;"
    f"background:url('{icon_uri(n)}') center/contain no-repeat;}}" for k, n in BUTTON_ICONS.items())

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input {{ font-family: 'DM Sans', sans-serif; }}
.block-container {{ padding-top: 2rem; max-width: 1250px; }}
[data-testid="stSidebar"] {{ background: {NAVY}; }}
[data-testid="stSidebar"] * {{ color: #E6F1FA; }}
[data-testid="stSidebar"] .stButton button {{
  width: 100%; justify-content: flex-start; text-align: left; border: none; border-radius: 16px;
  background: transparent; color: #DCEBF7; font-size: 1.02rem; font-weight: 500; padding: .45rem .7rem; }}
[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(255,255,255,.10); color: #fff; }}
[data-testid="stSidebar"] .stButton button[kind="primary"] {{ background: rgba(255,255,255,.95); color: {NAVY}; font-weight: 700;
  box-shadow: 0 6px 18px rgba(0,0,0,.18); }}
[data-testid="stSidebar"] .stButton button[kind="primary"] * {{ color: {NAVY}; }}
.brand {{ display:flex; align-items:center; gap:.6rem; font-size: 1.6rem; font-weight: 700; color: #fff; padding: .2rem .2rem 1rem; }}
.brand span {{ color: {ACCENT}; }}
.side-label {{ font-size: .78rem; letter-spacing: .08em; color: #8FB4D3 !important; margin: 1rem 0 .3rem .5rem; font-weight: 700; }}
.card {{ background: rgba(255,255,255,.85); backdrop-filter: blur(8px); border: 1px solid #E3EAF2; border-radius: 22px;
         padding: 1.2rem 1.4rem; margin-bottom: 1rem; box-shadow: 0 4px 16px rgba(15,23,42,.05); }}
.hero h1 {{ font-size: 2.5rem; font-weight: 700; margin: 0; color: #0F172A; line-height: 1.15; }}
.hero h1 span {{ color: #64748B; }}
.hero p {{ font-size: 1.12rem; color: #475569; margin: .4rem 0 0; }}
.tile {{ background: #fff; border: 1px solid #E3EAF2; border-radius: 20px; padding: .9rem 1rem; display:flex; align-items:center; gap:.8rem; }}
.tile b {{ display: block; font-size: 1.7rem; color: #0F172A; line-height: 1.1; }}
.tile small {{ color: #475569; font-size: .8rem; letter-spacing: .04em; text-transform: uppercase; }}
.step {{ border-radius: 22px; padding: 1rem; color: #fff; min-height: 150px; position: relative; overflow: hidden;
         box-shadow: inset 0 1px 0 rgba(255,255,255,.35), 0 6px 16px rgba(15,23,42,.10); }}
.step::after {{ content:''; position:absolute; left:8%; right:8%; top:0; height:40%; border-radius:0 0 50% 50%;
               background: linear-gradient(rgba(255,255,255,.28), rgba(255,255,255,0)); }}
.step b {{ font-size: 1.15rem; display: block; margin: .5rem 0 .25rem; }}
.qs {{ display:flex; gap:.8rem; align-items:flex-start; }}
.qs b {{ display:block; font-size:1.05rem; color:#0F172A; }}
.qs span {{ color:#475569; }}
.option {{ border: 2px solid #E3EAF2; border-radius: 18px; padding: .6rem .9rem; margin-bottom: .55rem; display: flex;
           align-items: center; gap: .8rem; background: #fff; font-size: 1.0rem; }}
.option.best {{ border-color: #16A34A; background: #ECFDF3; color: #14532D; }}
.option.bad {{ border-color: #FECACA; background: #FFF5F5; color: #7F1D1D; }}
.option .val {{ margin-left: auto; font-weight: 700; }}
.pill {{ display: inline-block; padding: .22rem .7rem; border-radius: 999px; background: #E0F2FE; color: #075985;
         font-weight: 600; margin: 0 .3rem .3rem 0; font-size: .88rem; }}
.banner {{ border-radius: 24px; padding: 1rem 1.3rem; color: #fff; margin-bottom: 1rem; display:flex; gap:1rem; align-items:center;
           position: relative; overflow: hidden; box-shadow: inset 0 1px 0 rgba(255,255,255,.4), 0 10px 24px rgba(15,23,42,.12); }}
.banner::after {{ content:''; position:absolute; left:4%; right:4%; top:0; height:45%; border-radius: 0 0 40% 40%;
                 background: linear-gradient(rgba(255,255,255,.22), rgba(255,255,255,0)); pointer-events:none; }}
.banner h2 {{ margin: 0; font-size: 1.7rem; color: #fff; padding: 0; }}
.banner p {{ margin: .15rem 0 0; font-size: 1.03rem; color: #fff; }}
.why {{ border-left: 5px solid #F59E0B; }}
.why ol {{ margin: .4rem 0 0 1.1rem; padding: 0; color: #1E293B; }}
.why li {{ margin-bottom: .25rem; }}
.sec {{ display:flex; align-items:center; gap:.6rem; font-weight:700; font-size:1.2rem; color:#0F172A; margin:.1rem 0 .6rem; }}
.term {{ border-bottom: 2px dotted #94A3B8; cursor: help; }}
.empty {{ display:flex; gap:.9rem; align-items:center; background:#F8FAFC; border:2px dashed #CBD5E1; border-radius:18px;
          padding:.8rem 1rem; color:#334155; }}
.tour-dots {{ display:flex; gap:.5rem; flex-wrap:wrap; margin-bottom:.8rem; }}
.tour-dots div {{ padding:.25rem .65rem; border-radius:999px; background:#F1F5F9; color:#475569; font-size:.85rem; font-weight:600; }}
.tour-dots div.on {{ background:{NAVY}; color:#fff; }}
.tour-body {{ display:flex; gap:1rem; align-items:flex-start; font-size:1.05rem; color:#1E293B; }}
.tour-body h4 {{ margin:0 0 .3rem; padding:0; }}
.muted {{ color: #475569; }}
.stButton button {{ border-radius: 999px; font-weight: 600; }}
h3 {{ font-weight: 700 !important; }}
{icon_css}
@media (max-width: 768px) {{
  .block-container {{ padding: 1rem .7rem; }}
  .hero h1 {{ font-size: 1.75rem; }}
  .hero p {{ font-size: 1rem; }}
  .step {{ min-height: auto; }}
  .banner h2 {{ font-size: 1.35rem; }}
  .tile b {{ font-size: 1.35rem; }}
  .tour-body {{ flex-direction: column; }}
}}
</style>
""", unsafe_allow_html=True)

PAGES = ["Home", "Planner", "Simulation", "Evaluation", "How it works"]
defaults = {"page": "Home", "history": [], "door": "No reading", "tour": 0, "seed": 1}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def go(page):
    st.session_state.page = page


with st.sidebar:
    st.markdown(f"<div class='brand'>{icon('cat', 44)}<div>Kitty<span>Escape</span></div></div>", unsafe_allow_html=True)
    for i, name in enumerate(PAGES):
        st.button(name, key=f"nav_{i}", on_click=go, args=(name,),
                  type="primary" if st.session_state.page == name else "secondary")
    st.markdown("<div class='side-label'>PROJECT</div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0 .6rem;font-size:.92rem;line-height:1.6'>Fundamentals of AI<br>Final Project<br>"
                "<b>Yernur Baltabay</b></div>", unsafe_allow_html=True)


# ------------------------------------------------------------------ helpers
def card(html, cls=""):
    st.markdown(f"<div class='card {cls}'>{html}</div>", unsafe_allow_html=True)


def section(icon_name, text, colour=None):
    st.markdown(f"<div class='sec'>{icon(icon_name, 34, colour)}<span>{text}</span></div>", unsafe_allow_html=True)


def term(word):
    return f"<span class='term' title=\"{TERMS[word]}\">{word}</span>"


def tile(col, icon_name, value, label, colour=None):
    col.markdown(f"<div class='tile'>{icon(icon_name, 44, colour)}<div><b>{value}</b><small>{label}</small></div></div>",
                 unsafe_allow_html=True)


def bar_chart(labels, values, color, fmt=".2f", height=230, highlight=None):
    df = pd.DataFrame({"label": labels, "value": values})
    try:
        import altair as alt
        colour = (alt.condition(alt.datum.label == highlight, alt.value(color), alt.value("#CBD5E1"))
                  if highlight else alt.value(color))
        base = alt.Chart(df).encode(
            y=alt.Y("label:N", sort=None, title=None, axis=alt.Axis(labelLimit=260, labelFontSize=13)),
            x=alt.X("value:Q", title=None, axis=alt.Axis(grid=True, gridColor="#EEF2F7")))
        bars = base.mark_bar(cornerRadiusEnd=8, height=22).encode(color=colour)
        text = base.mark_text(align="left", dx=6, fontSize=13, color="#0F172A").encode(text=alt.Text("value:Q", format=fmt))
        st.altair_chart((bars + text).properties(height=height).configure_view(strokeWidth=0))
    except Exception:
        st.bar_chart(df.set_index("label"))


def decision_banner(action):
    ic, ic_col, deep, light, word, text = DECISION[action]
    st.markdown(f"<div class='banner' style='background:linear-gradient(135deg,{light},{deep})' role='status'>"
                f"{icon(ic, 58, ic_col)}<div><h2>{word.upper()}</h2><p>{text}</p></div></div>", unsafe_allow_html=True)


def decision_options(values, chosen):
    names = {"PROCEED": "Proceed on the fast route", "DETOUR": "Take the safe detour", "WAIT": "Wait for more information"}
    html = ""
    for a in ("PROCEED", "DETOUR", "WAIT"):
        best = a == chosen
        html += (f"<div class='option {'best' if best else 'bad'}'>{icon(DECISION[a][0], 34, DECISION[a][1])}"
                 f"<div><b>{names[a]}</b>{' · chosen' if best else ''}</div>"
                 f"<div class='val'>{values[a]:.1f}</div>{icon('check' if best else 'cross', 26)}</div>")
    return html


def outcome_banner(ok, text):
    """Result banner of a simulated fire; a short confetti burst when Kitty escapes (pure canvas, no library)."""
    title, ic, a, b = ("Kitty escaped!", "cat_happy", "#22C55E", GREEN) if ok else ("Kitty got hurt", "cat_hurt", "#EF4444", RED)
    confetti = """
<canvas id='c'></canvas><script>
const c=document.getElementById('c'),x=c.getContext('2d');c.width=innerWidth;c.height=innerHeight;
const col=['#FDE047','#38BDF8','#F472B6','#A78BFA','#FFFFFF','#FB923C'];
const P=Array.from({length:90},()=>({x:Math.random()*c.width,y:-20-Math.random()*c.height,
 r:3+Math.random()*4,v:1.5+Math.random()*2.5,w:Math.random()*6,s:Math.random()*.2-.1,k:col[Math.floor(Math.random()*6)]}));
let t=0;(function f(){x.clearRect(0,0,c.width,c.height);P.forEach(p=>{p.y+=p.v;p.w+=p.s;
 x.fillStyle=p.k;x.beginPath();x.ellipse(p.x+Math.sin(p.w)*6,p.y,p.r,p.r*.6,p.w,0,7);x.fill();});
 if(++t<200)requestAnimationFrame(f);else x.clearRect(0,0,c.width,c.height);})();
</script>""" if ok else ""
    html = f"""<style>@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@500;700&display=swap');
body{{margin:0;font-family:'DM Sans',sans-serif}}
.b{{position:relative;overflow:hidden;border-radius:24px;padding:16px 20px;color:#fff;display:flex;gap:16px;align-items:center;
background:linear-gradient(135deg,{a},{b});box-shadow:inset 0 1px 0 rgba(255,255,255,.4)}}
.b h2{{margin:0;font-size:26px}} .b p{{margin:4px 0 0;font-size:16px}}
canvas{{position:absolute;inset:0;pointer-events:none}}</style>
<div class='b' role='status'>{icon(ic, 62)}<div><h2>{title}</h2><p>{text}</p></div>{confetti}</div>"""
    components.html(html, height=112)


SCENARIOS = {
    "scn_quiet": ("All quiet · camera CLEAR", [(False,) * 4, (False,) * 4], "CLEAR"),
    "scn_fire": ("Fire in Z1 · camera SMOKE", [(False, True, False, False)] * 2, "SMOKE"),
    "scn_unclear": ("One alarm in Z1 · camera CLEAR", [(False, True, False, False)], "CLEAR"),
    "scn_two": ("Alarms in Z1 and Z3 · no camera", [(False, True, False, True)], "No reading"),
}


def load_scenario(key):
    _, hist, door = SCENARIOS[key]
    st.session_state.history = list(hist)
    st.session_state.door = door
    st.session_state.tour = 0
    for i in range(4):
        st.session_state[f"s{i}"] = False


def add_step():
    st.session_state.history.append(tuple(st.session_state.get(f"s{i}", False) for i in range(4)))


def reset_planner():
    st.session_state.history = []
    st.session_state.door = "No reading"
    st.session_state.tour = 0


def move_tour(d):
    st.session_state.tour = max(0, min(4, st.session_state.tour + d))


page = st.session_state.page

# ------------------------------------------------------------------ HOME
if page == "Home":
    hour = datetime.now().hour
    greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    hero_l, hero_r = st.columns([2.2, 1], gap="large")
    with hero_l:
        st.markdown(f"<div class='hero'><h1>{greet}! <span>Help Kitty escape the burning house</span></h1>"
                    "<p>Kitty is trapped inside. Smoke sensors are noisy and the fire moves. Four AI algorithms "
                    "work together to choose the safest way out.</p></div>", unsafe_allow_html=True)
        st.write("")
        c1, c2 = st.columns(2)
        c1.button("Play: guide Kitty", key="home_play", type="primary", on_click=go, args=("Planner",))
        c2.button("Watch a random fire", key="home_sim", on_click=go, args=("Simulation",))
    with hero_r:
        kpath = os.path.join(HERE, "assets", "kitty.jpg")
        sketch = ""
        if os.path.exists(kpath):
            with open(kpath, "rb") as f:
                sketch = "data:image/jpeg;base64," + base64.b64encode(f.read()).decode()
        components.html(viewer_html(300, sketch), height=310)
    st.write("")
    section("sparkle", "Start in three steps")
    qs = [("compass", "purple", "Open the Planner", "Press <b>Play</b> above or pick <b>Planner</b> on the left."),
          ("sensor", "slate", "Give it readings", "Tick an alarm and press <b>Add sensor step</b>, or choose a quick scenario."),
          ("bulb", "yellow", "Read the decision", "The coloured banner shows what Kitty does, and <b>Why?</b> explains it.")]
    for col, (ic, c, t, d) in zip(st.columns(3), qs):
        col.markdown(f"<div class='card qs'>{icon(ic, 46, c)}<div><b>{t}</b><span>{d}</span></div></div>",
                     unsafe_allow_html=True)
    tiles = [("brain", "purple", "4", "AI algorithms"), ("badge", "green", "18", "passing tests"),
             ("flame", "orange", "5000", "simulated fires"), ("shield", "blue", "11.2%", "harm rate (vs 19.7%)")]
    for col, (ic, c, num, lab) in zip(st.columns(4), tiles):
        tile(col, ic, num, lab, c)
    st.write("")
    section("route", "How the assistant decides")
    steps = [("sensor", "slate", "Sensors", "4 noisy smoke alarms and a door camera", "#64748B", "#334155"),
             ("search", "blue", "HMM", "estimates the hidden fire zone", "#38BDF8", BLUE),
             ("route", "green", "A* search", "finds a fast and a safe route", "#4ADE80", GREEN),
             ("scale", "orange", "Bayes", "updates the danger with the camera", "#FB923C", ORANGE),
             ("target", "purple", "MDP", "chooses proceed, detour or wait", "#A78BFA", PURPLE)]
    for col, (ic, c, t, d, a, b) in zip(st.columns(5), steps):
        col.markdown(f"<div class='step' style='background:linear-gradient(150deg,{a},{b})'>{icon(ic, 44, c)}<b>{t}</b>{d}</div>",
                     unsafe_allow_html=True)

# ------------------------------------------------------------------ PLANNER
elif page == "Planner":
    st.markdown("<div class='hero'><h1>Planner</h1><p>Give the assistant sensor readings and see its decision, "
                "explained step by step.</p></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("**Quick scenarios** <span class='muted'>· one click fills the sensors and the camera</span>",
                unsafe_allow_html=True)
    for col, (key, (label, _, _)) in zip(st.columns(4), SCENARIOS.items()):
        col.button(label, key=key, on_click=load_scenario, args=(key,), width="stretch")
    st.write("")

    left, right = st.columns([1, 1.9], gap="large")
    with left:
        with st.container(border=True):
            section("sensor", "1 · Smoke sensors")
            st.caption("Tick the zones whose alarm is ringing, then add the step. Each step is one moment in time.")
            for i in range(4):
                st.checkbox(f"Alarm in {ZONE_SHORT[i]}", key=f"s{i}",
                            help="Rings with 90% if the fire is in this zone, 30% if next door, 5% if far away.")
            b1, b2 = st.columns(2)
            b1.button("Add sensor step", key="add_step", type="primary", on_click=add_step)
            b2.button("Reset", key="reset", on_click=reset_planner)
            hist = st.session_state.history
            if hist:
                st.markdown("".join(f"<span class='pill'>Step {i + 1}: "
                                    + (", ".join(f"Z{k}" for k in range(4) if o[k]) or "quiet") + "</span>"
                                    for i, o in enumerate(hist)), unsafe_allow_html=True)
            else:
                st.markdown(f"<div class='empty'>{icon('sensor', 40)}<div><b>No sensor readings yet.</b><br>"
                            "Tick alarms and press <b>Add sensor step</b>, or pick a quick scenario above. "
                            "Without readings every zone is equally likely.</div></div>", unsafe_allow_html=True)
        with st.container(border=True):
            section("camera", "2 · Door camera")
            st.radio("What does the camera at the door show?", ["No reading", "CLEAR", "SMOKE"], key="door",
                     horizontal=True, help="It looks at the door on the fast route. It sees smoke 85% of the time "
                                           "when the route is blocked and 15% when it is clear.")
        show_risk = st.toggle("Colour the map by risk", value=True,
                              help="Redder zones are more likely to be blocked. Turn off to see the plain zone colours.")

    door = st.session_state.door
    r = plan(st.session_state.history, None if door == "No reading" else door)
    action = r["action"]
    with right:
        decision_banner(action)
        card(f"<div class='sec'>{icon('bulb', 34)}<span>Why this decision?</span></div><ol>"
             + "".join(f"<li>{s}</li>" for s in why(r)) + "</ol>", cls="why")
        with st.container(border=True):
            components.html(scene_html(r["world"], r["route"]["path"] if r["route"] else None,
                                       zone_risk=r["zone_risk"] if show_risk else None,
                                       caption="Kitty is the round token" + ("" if r["route"] else " (waiting in place)")),
                            height=450)

    st.write("")
    with st.container(border=True):
        section("play", "Walk me through it", "purple")
        tour = walkthrough(r)
        k = st.session_state.tour
        icons5 = [("sensor", "slate"), ("search", "blue"), ("route", "green"), ("scale", "orange"), ("target", "purple")]
        st.markdown("<div class='tour-dots'>" + "".join(
            f"<div class='{'on' if i == k else ''}'>{t.split(' · ')[1].split(':')[0]}</div>" for i, (_, t, _) in enumerate(tour))
                    + "</div>", unsafe_allow_html=True)
        _, title, text = tour[k]
        st.markdown(f"<div class='tour-body'>{icon(icons5[k][0], 64, icons5[k][1])}<div><h4>{title}</h4>{text}</div></div>",
                    unsafe_allow_html=True)
        if k == 1:
            bar_chart(ZONE_SHORT, r["belief"], color=BLUE, height=170)
        st.write("")
        n1, n2, _ = st.columns([1, 1, 4])
        n1.button("Back", key="tour_back", on_click=move_tour, args=(-1,), disabled=k == 0)
        n2.button("Next", key="tour_next", type="primary", on_click=move_tour, args=(1,), disabled=k == 4)

    with st.expander("Show all the numbers (HMM, A*, Bayes, MDP)"):
        a, b = st.columns(2, gap="large")
        with a:
            section("search", "HMM · where is the fire?")
            bar_chart(ZONE_SHORT, r["belief"], color=BLUE)
            if r["steps"]:
                st.dataframe(pd.DataFrame([{"step": i + 1, **{f"Z{z}": round(s["posterior"][z], 3) for z in range(4)}}
                                           for i, s in enumerate(r["steps"])]), hide_index=True)
        with b:
            section("route", "A* · routes found")
            for name, rt, ic, c in (("Fast route", r["fast"], "bolt", "green"), ("Safe route", r["safe"], "shield", "orange")):
                st.markdown(f"<div class='option'>{icon(ic, 34, c)}<div><b>{name}</b><br><span class='muted'>"
                            f"{rt['steps']} steps to exit {rt['exit']}</span></div>"
                            f"<div class='val'>P(blocked) {rt['risk']:.2f}</div></div>", unsafe_allow_html=True)
            section("scale", "Bayes · door camera")
            t1, t2 = st.columns(2)
            tile(t1, "camera", f"{r['p_fast_prior']:.2f}", "risk before camera")
            tile(t2, "scale", f"{r['p_fast_posterior']:.2f}", "risk after camera")
        section("target", "MDP · expected score of each action")
        st.markdown(decision_options(r["action_values"], action), unsafe_allow_html=True)

# ------------------------------------------------------------------ SIMULATION
elif page == "Simulation":
    st.markdown("<div class='hero'><h1>Simulation</h1><p>A random fire breaks out. Kitty's assistant sees only noisy sensors; "
                "the real fire is revealed so you can check its choice.</p></div>", unsafe_allow_html=True)
    st.write("")
    c1, c2, _ = st.columns([1, 1.1, 3])
    st.session_state.seed = int(c1.number_input("Fire number (seed)", 0, 100000, st.session_state.seed,
                                                help="The same number always replays the same fire."))
    c2.write("")
    if c2.button("New random fire", key="new_fire", type="primary"):
        st.session_state.seed = random.randint(0, 100000)
        st.rerun()
    log = []
    out = run_episode(POLICIES["Assistant (HMM + A* + Bayes + MDP)"], random.Random(st.session_state.seed), log=log)
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        for e in log:
            believed = max(range(4), key=lambda z: e["belief"][z])
            ok = believed == e["true_fire_zone"]
            ic, c = DECISION[e["action"]][:2]
            steps_txt = "".join("<span class='pill'>" + (", ".join(f"Z{k}" for k in range(4) if o[k]) or "quiet")
                                + "</span>" for o in e["sensors"])
            card(f"<div class='sec'>{icon(ic, 36, c)}<span>Decision round {e['round']}: {e['action']}</span></div>"
                 f"<span class='muted'>Sensor steps:</span> {steps_txt}<br>"
                 f"<span class='muted'>Door camera:</span> <b>{e['door']}</b> &nbsp;·&nbsp; "
                 f"<span class='muted'>risk of the fast route</span> {e['p_prior']:.2f} → <b>{e['p_posterior']:.2f}</b><br>"
                 f"<span class='muted'>Believed fire:</span> {ZONE_SHORT[believed]} ({max(e['belief']):.2f}) &nbsp; "
                 f"<span class='muted'>Real fire:</span> {ZONE_SHORT[e['true_fire_zone']]} "
                 f"{icon('check' if ok else 'cross', 22)} <span class='muted'>{'guessed right' if ok else 'guessed wrong'}</span>")
    with right:
        with st.container(border=True):
            components.html(scene_html(plan([])["world"], out["route"], blocked=log[-1]["blocked_zones"],
                                       caption="Flames show the zones that are really blocked (hidden from the assistant)"),
                            height=450)
        t1, t2, t3 = st.columns(3)
        tile(t1, "steps", out["time"], "time steps")
        tile(t2, "pause", out["waits"], "waits")
        tile(t3, "block", "yes" if out["blocked"] else "no", "route blocked")
        st.write("")
        if out["harmed"]:
            note = "Kitty's route was really blocked." if out["blocked"] else "The route was clear: even a clear route keeps a 2% risk."
            outcome_banner(False, note)
        else:
            outcome_banner(True, "Kitty got out of the burning house safely.")

# ------------------------------------------------------------------ EVALUATION
elif page == "Evaluation":
    st.markdown("<div class='hero'><h1>Evaluation</h1><p>Every policy faces the same random fires. "
                "Lower harm and higher utility are better.</p></div>", unsafe_allow_html=True)
    st.write("")
    n = st.select_slider("Simulated fires per policy", options=[500, 1000, 2000, 5000], value=2000,
                         help="More fires = smaller random noise, but a longer run. 5000 matches the report.")

    @st.cache_data(show_spinner="Simulating fires...")
    def run_all(n):
        return [{"Policy": k, **evaluate(p, n, 2026)} for k, p in POLICIES.items()]

    rows = run_all(n)
    full = rows[0]
    shortest = next(x for x in rows if x["Policy"] == "Always shortest route")
    thr = next(x for x in rows if x["Policy"].startswith("No MDP, threshold 0.5"))
    tiles = [("shield", "green", f"{full['harm_rate'] * 100:.1f}%", "assistant harm rate"),
             ("bolt", "red", f"{shortest['harm_rate'] * 100:.1f}%", "always shortest route"),
             ("sparkle", "yellow", f"{(1 - full['harm_rate'] / shortest['harm_rate']) * 100:.0f}%", "fewer harmed"),
             ("flame", "orange", f"{n}", "fires per policy")]
    for col, (ic, c, num, lab) in zip(st.columns(4), tiles):
        tile(col, ic, num, lab, c)
    st.write("")
    names = [x["Policy"].split(" (")[0] for x in rows]
    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            section("cross", "Harm rate", "red")
            st.caption("Share of fires in which Kitty got hurt · lower is better · the assistant is highlighted")
            bar_chart(names, [x["harm_rate"] for x in rows], color=RED, fmt=".3f", height=300, highlight="Assistant")
    with b:
        with st.container(border=True):
            section("chart", "Expected utility")
            st.caption("Average score: +100 escape, −300 hurt, −1 per step · higher is better")
            bar_chart(names, [x["utility"] for x in rows], color=GREEN, fmt=".1f", height=300, highlight="Assistant")
    noise = 1.96 * math.hypot(full["harm_se"], thr["harm_se"])
    diff = full["harm_rate"] - thr["harm_rate"]
    verdict = ("so the two are <b>tied within the random noise</b>" if abs(diff) < noise else
               "and this difference is larger than the random noise")
    card(f"<div class='sec'>{icon('bulb', 34)}<span>What this shows</span></div>"
         f"Removing the {term('HMM')} or the {term('Bayes')} update makes results clearly worse, so each algorithm "
         f"contributes. The {term('MDP')} and the best hand-tuned threshold (0.5) differ by {abs(diff) * 100:.1f} points "
         f"of harm (noise ±{noise * 100:.1f}), {verdict}. The MDP finds this boundary from the rewards, without tuning. "
         "<span class='muted'>Full run: <code>python evaluate.py</code>.</span>")
    st.dataframe(pd.DataFrame([{"Policy": x["Policy"], "Harm rate": round(x["harm_rate"], 3),
                                "± (95%)": round(1.96 * x["harm_se"], 3), "Mean time": round(x["mean_time"], 2),
                                "Utility": round(x["utility"], 1), "Waited": round(x["wait_rate"], 3)} for x in rows]),
                 hide_index=True)

# ------------------------------------------------------------------ HOW IT WORKS
else:
    st.markdown("<div class='hero'><h1>How it works</h1><p>Four AI topics, each feeding the next. "
                "Hover over a dotted word for a one-line definition.</p></div>", unsafe_allow_html=True)
    st.write("")
    algos = [
        ("search", "blue", "HMM filtering", "The hidden state is the zone of the fire. Each step: <b>predict</b> how the fire "
         "moves (stay 0.7, neighbour 0.15), <b>correct</b> with the 4 noisy sensors, <b>normalize</b> to get the belief.",
         "Like a detective who updates the suspect list after every clue."),
        ("route", "green", "A* search", "Cell cost = 1 + 10 × P(cell blocked). The Manhattan heuristic is admissible "
         "because every step costs at least 1, so A* finds the cheapest route.",
         "Like a GPS that adds a penalty for dangerous streets."),
        ("scale", "orange", "Bayes' theorem", "Prior = P(fast route blocked) from the belief. The camera shows SMOKE with "
         "0.85 if blocked and 0.15 if clear. Posterior = likelihood × prior / evidence.",
         "Smoke on camera: 69% → 93%. Clear camera: 69% → 28%."),
        ("target", "purple", "MDP + value iteration", "States LOW / HIGH / DONE, actions PROCEED / DETOUR / WAIT, γ = 0.9. "
         "Decision = argmax of (1 − p)·Q(LOW, a) + p·Q(HIGH, a).",
         "Like comparing the average score of each move before playing it."),
    ]
    for i in range(0, 4, 2):
        cols = st.columns(2, gap="large")
        for col, (ic, c, t, d, plain) in zip(cols, algos[i:i + 2]):
            col.markdown(f"<div class='card'>{icon(ic, 54, c)}<h3>{t}</h3><p style='font-size:1.02rem;color:#1E293B'>{d}</p>"
                         f"<p class='muted'><i>In plain words:</i> {plain}</p></div>", unsafe_allow_html=True)
    card(f"<div class='sec'>{icon('book', 34)}<span>Glossary</span></div>"
         + " &nbsp;·&nbsp; ".join(term(w) for w in TERMS)
         + "<br><br><b>Assumptions.</b> All probabilities and rewards are assumed (see <code>evacuation/model.py</code>). "
           "This is a teaching model, not a real safety system.")
