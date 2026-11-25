"""Emergency Evacuation Assistant - web interface (v3)."""
import random
from datetime import datetime

import pandas as pd
import streamlit as st

from evacuation.model import ZONE_NAMES, zone_of
from evacuation.planner import plan
from evacuation.simulate import POLICIES, evaluate, run_episode, WAIT_TIME

st.set_page_config(page_title="Evacuation Assistant", page_icon="🧯", layout="wide")

BLUE, PURPLE, GREEN, RED, ORANGE, NAVY = "#1CB0F6", "#7C3AED", "#16A34A", "#EF4444", "#F59E0B", "#123F63"
ZONE_FILL = ["#FDE2E7", "#FEF3C7", "#DCFCE7", "#DBEAFE"]
ZONE_SHORT = ["Z0 · north-west", "Z1 · north-east", "Z2 · south-west", "Z3 · south-east"]

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;700&display=swap');
html, body, [class*="css"], .stMarkdown, button, input {{ font-family: 'DM Sans', sans-serif; }}
.block-container {{ padding-top: 2rem; max-width: 1250px; }}
[data-testid="stSidebar"] {{ background: {NAVY}; }}
[data-testid="stSidebar"] * {{ color: #E6F1FA; }}
[data-testid="stSidebar"] .stButton button {{
  width: 100%; justify-content: flex-start; text-align: left; border: none; border-radius: 14px;
  background: transparent; color: #DCEBF7; font-size: 1.02rem; font-weight: 500; padding: .6rem .9rem; }}
[data-testid="stSidebar"] .stButton button:hover {{ background: rgba(255,255,255,.10); color: #fff; }}
[data-testid="stSidebar"] .stButton button[kind="primary"] {{ background: #fff; color: {NAVY}; font-weight: 700; }}
[data-testid="stSidebar"] .stButton button[kind="primary"] * {{ color: {NAVY}; }}
.brand {{ font-size: 1.7rem; font-weight: 700; color: #fff; padding: .2rem .4rem 1rem; }}
.brand span {{ color: {BLUE}; }}
.side-label {{ font-size: .78rem; letter-spacing: .08em; color: #8FB4D3 !important; margin: 1rem 0 .3rem .5rem; font-weight: 700; }}
.card {{ background: #fff; border: 1px solid #E3EAF2; border-radius: 22px; padding: 1.3rem 1.5rem; margin-bottom: 1rem;
         box-shadow: 0 2px 8px rgba(15,23,42,.04); }}
.hero h1 {{ font-size: 2.6rem; font-weight: 700; margin: 0; color: #0F172A; }}
.hero h1 span {{ color: #64748B; }}
.hero p {{ font-size: 1.15rem; color: #64748B; margin: .4rem 0 0; }}
.tile {{ background: #fff; border: 1px solid #E3EAF2; border-radius: 18px; padding: 1rem; text-align: center; }}
.tile b {{ display: block; font-size: 2rem; color: #0F172A; line-height: 1.1; }}
.tile small {{ color: #64748B; font-size: .82rem; letter-spacing: .04em; text-transform: uppercase; }}
.step {{ border-radius: 18px; padding: 1rem; color: #fff; min-height: 128px; }}
.step b {{ font-size: 1.2rem; display: block; margin-bottom: .3rem; }}
.option {{ border: 2px solid #E3EAF2; border-radius: 18px; padding: .8rem 1rem; margin-bottom: .6rem; display: flex;
           align-items: center; gap: .8rem; background: #fff; font-size: 1.02rem; }}
.option .dot {{ width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
               font-weight: 700; border: 2px solid #CBD5E1; color: #334155; flex: none; }}
.option.best {{ border-color: {GREEN}; background: #ECFDF3; color: #166534; }}
.option.best .dot {{ background: {GREEN}; border-color: {GREEN}; color: #fff; }}
.option.bad {{ border-color: #FCA5A5; background: #FEF2F2; color: #991B1B; }}
.option.bad .dot {{ background: {RED}; border-color: {RED}; color: #fff; }}
.option .val {{ margin-left: auto; font-weight: 700; }}
.pill {{ display: inline-block; padding: .25rem .7rem; border-radius: 999px; background: #E0F2FE; color: #0369A1;
         font-weight: 600; margin: 0 .3rem .3rem 0; font-size: .9rem; }}
.banner {{ border-radius: 20px; padding: 1.1rem 1.4rem; color: #fff; margin-bottom: 1rem; }}
.banner h2 {{ margin: 0; font-size: 1.8rem; color: #fff; }}
.banner p {{ margin: .2rem 0 0; font-size: 1.05rem; color: #fff; }}
.muted {{ color: #64748B; }}
.stButton button {{ border-radius: 999px; font-weight: 600; }}
h3 {{ font-weight: 700 !important; }}
</style>
""", unsafe_allow_html=True)

PAGES = [("🏠", "Home"), ("🧭", "Planner"), ("🔥", "Simulation"), ("📊", "Evaluation"), ("📘", "How it works")]
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "history" not in st.session_state:
    st.session_state.history = []


def go(page):
    st.session_state.page = page


with st.sidebar:
    st.markdown("<div class='brand'>🧯 Evac<span>AI</span></div>", unsafe_allow_html=True)
    for icon, name in PAGES:
        st.button(f"{icon}  {name}", key=f"nav_{name}", on_click=go, args=(name,),
                  type="primary" if st.session_state.page == name else "secondary")
    st.markdown("<div class='side-label'>PROJECT</div>", unsafe_allow_html=True)
    st.markdown("<div style='padding:0 .6rem;font-size:.92rem;line-height:1.6'>Fundamentals of AI<br>Final Project<br>"
                "<b>Yernur Baltabay</b></div>", unsafe_allow_html=True)


def card(html):
    st.markdown(f"<div class='card'>{html}</div>", unsafe_allow_html=True)


def map_html(world, route=None, zone_risk=None, blocked=None):
    route = set(route or [])
    out = "<table style='border-collapse:separate;border-spacing:4px;margin:auto'>"
    for r in range(world["rows"]):
        out += "<tr>"
        for c in range(world["cols"]):
            cell, txt = (r, c), ""
            if cell in world["walls"]:
                bg = "#1E293B"
            else:
                z = zone_of(r, c)
                bg = ZONE_FILL[z] if zone_risk is None else f"rgba(239,68,68,{0.12 + 0.8 * min(1, zone_risk[z]):.2f})"
                if blocked is not None and blocked[z]:
                    txt = "🔥"
                if cell == world["start"]:
                    txt = "🧍"
                elif cell in world["exits"]:
                    txt = "🚪"
                elif cell == world["door"] and not txt:
                    txt = "📷"
                if cell in route and cell != world["start"]:
                    bg = GREEN
                    txt = txt or "<span style='color:#fff'>●</span>"
            out += (f"<td style='width:44px;height:44px;border-radius:10px;text-align:center;font-size:18px;"
                    f"background:{bg}'>{txt}</td>")
        out += "</tr>"
    return out + "</table>"


def bar_chart(labels, values, color=BLUE, fmt=".2f", height=230):
    df = pd.DataFrame({"label": labels, "value": values})
    try:
        import altair as alt
        base = alt.Chart(df).encode(
            y=alt.Y("label:N", sort=None, title=None, axis=alt.Axis(labelLimit=260, labelFontSize=13)),
            x=alt.X("value:Q", title=None, axis=alt.Axis(grid=True, gridColor="#EEF2F7")))
        bars = base.mark_bar(cornerRadiusEnd=8, color=color, height=22)
        text = base.mark_text(align="left", dx=6, fontSize=13, color="#0F172A").encode(text=alt.Text("value:Q", format=fmt))
        st.altair_chart((bars + text).properties(height=height).configure_view(strokeWidth=0))
    except Exception:
        st.bar_chart(df.set_index("label"))


def decision_options(values, chosen):
    letters = {"PROCEED": "A", "DETOUR": "B", "WAIT": "C"}
    names = {"PROCEED": "Proceed on the fast route", "DETOUR": "Take the safe detour", "WAIT": "Wait for more information"}
    html = ""
    for a in ("PROCEED", "DETOUR", "WAIT"):
        cls = "best" if a == chosen else "bad"
        mark = "✓" if a == chosen else "✕"
        html += (f"<div class='option {cls}'><div class='dot'>{mark}</div><div><b>{letters[a]}.</b> {names[a]}</div>"
                 f"<div class='val'>{values[a]:.1f}</div></div>")
    return html


page = st.session_state.page

# ---------------------------------------------------------------- HOME
if page == "Home":
    hour = datetime.now().hour
    greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
    st.markdown(f"<div class='hero'><h1>{greet}, <span>let's get everyone out safely</span></h1>"
                "<p>An AI assistant that reads noisy smoke sensors and chooses the safest way out of a burning building.</p></div>",
                unsafe_allow_html=True)
    st.write("")
    c1, c2, _ = st.columns([1.2, 1.2, 3])
    c1.button("Open the planner  →", type="primary", on_click=go, args=("Planner",))
    c2.button("Watch a simulation", on_click=go, args=("Simulation",))
    st.write("")
    tiles = [("4", "AI algorithms"), ("16", "passing tests"), ("5000", "simulated fires"), ("11.2%", "harm rate (vs 19.7%)")]
    for col, (num, lab) in zip(st.columns(4), tiles):
        col.markdown(f"<div class='tile'><b>{num}</b><small>{lab}</small></div>", unsafe_allow_html=True)
    st.write("")
    st.markdown("### How the assistant decides")
    steps = [("Sensors", "4 noisy smoke sensors and a door camera", "#334155"),
             ("HMM", "estimates the hidden fire zone", BLUE),
             ("A* search", "finds a fast and a safe route", GREEN),
             ("Bayes", "updates the danger with the camera", ORANGE),
             ("MDP", "chooses proceed, detour or wait", PURPLE)]
    for col, (t, d, colr) in zip(st.columns(5), steps):
        col.markdown(f"<div class='step' style='background:{colr}'><b>{t}</b>{d}</div>", unsafe_allow_html=True)
    st.write("")
    card("<h3 style='margin-top:0'>Try it in 30 seconds</h3>"
         "<span class='pill'>1</span> Open <b>Planner</b> &nbsp; <span class='pill'>2</span> Tick the alarm in <b>Z1</b> and press "
         "<b>Add sensor step</b> twice &nbsp; <span class='pill'>3</span> Set the camera to <b>SMOKE</b> → the assistant "
         "switches to the safe detour.")

# ---------------------------------------------------------------- PLANNER
elif page == "Planner":
    st.markdown("<div class='hero'><h1>Planner</h1><p>Give the assistant sensor readings and see its decision step by step.</p></div>",
                unsafe_allow_html=True)
    st.write("")
    left, right = st.columns([1, 1.9], gap="large")
    with left:
        with st.container(border=True):
            st.markdown("#### 1 · Smoke sensors")
            st.caption("Tick the zones whose alarm is ringing, then add the step.")
            flags = tuple(st.checkbox(f"Alarm in {ZONE_SHORT[i]}", key=f"s{i}") for i in range(4))
            b1, b2 = st.columns(2)
            if b1.button("＋ Add sensor step", type="primary"):
                st.session_state.history.append(flags)
            if b2.button("↺ Reset"):
                st.session_state.history = []
            hist = st.session_state.history
            if hist:
                pills = "".join(f"<span class='pill'>Step {i + 1}: "
                                + (", ".join(f"Z{k}" for k in range(4) if o[k]) or "quiet") + "</span>"
                                for i, o in enumerate(hist))
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.markdown("<span class='muted'>No sensor steps yet.</span>", unsafe_allow_html=True)
        with st.container(border=True):
            st.markdown("#### 2 · Door camera")
            door = st.radio("What does the camera at the door show?", ["No reading", "CLEAR", "SMOKE"],
                            horizontal=True, label_visibility="collapsed")
        show_risk = st.toggle("Colour the map by risk", value=False)

    r = plan(st.session_state.history, None if door == "No reading" else door)
    action = r["action"]
    with right:
        colr = {"PROCEED": GREEN, "DETOUR": ORANGE, "WAIT": BLUE}[action]
        text = {"PROCEED": "The fast route is probably clear. Take the shortest way out.",
                "DETOUR": "The fast route is too risky. Take the longer, safer route.",
                "WAIT": "Not enough information. Stay in place and read the sensors again."}[action]
        st.markdown(f"<div class='banner' style='background:{colr}'><h2>{action}</h2><p>{text}</p></div>",
                    unsafe_allow_html=True)
        m, o = st.columns([1.05, 1], gap="medium")
        with m:
            with st.container(border=True):
                st.markdown(map_html(r["world"], r["route"]["path"] if r["route"] else None,
                                     zone_risk=r["zone_risk"] if show_risk else None), unsafe_allow_html=True)
                st.caption("🧍 you · 🚪 exits · 📷 door camera · green = chosen route")
        with o:
            st.markdown("**MDP: expected value of each action**")
            st.markdown(decision_options(r["action_values"], action), unsafe_allow_html=True)
            t1, t2 = st.columns(2)
            t1.markdown(f"<div class='tile'><b>{r['p_fast_prior']:.2f}</b><small>risk before camera</small></div>",
                        unsafe_allow_html=True)
            t2.markdown(f"<div class='tile'><b>{r['p_fast_posterior']:.2f}</b><small>risk after camera</small></div>",
                        unsafe_allow_html=True)
    st.write("")
    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### 🔎 HMM · where is the fire?")
            bar_chart(ZONE_SHORT, r["belief"], color=BLUE)
    with b:
        with st.container(border=True):
            st.markdown("#### 🗺️ A* · routes found")
            for name, rt in (("Fast route", r["fast"]), ("Safe route", r["safe"])):
                st.markdown(f"<div class='option'><div class='dot'>{'⚡' if name == 'Fast route' else '🛡'}</div>"
                            f"<div><b>{name}</b><br><span class='muted'>{rt['steps']} steps to exit {rt['exit']}</span></div>"
                            f"<div class='val'>P(blocked) {rt['risk']:.2f}</div></div>", unsafe_allow_html=True)

# ---------------------------------------------------------------- SIMULATION
elif page == "Simulation":
    st.markdown("<div class='hero'><h1>Simulation</h1><p>One random fire. The assistant sees only noisy sensors; "
                "the real fire is revealed so you can check it.</p></div>", unsafe_allow_html=True)
    st.write("")
    if "seed" not in st.session_state:
        st.session_state.seed = 1
    c1, c2, _ = st.columns([1, 1, 3])
    st.session_state.seed = int(c1.number_input("Fire number (seed)", 0, 100000, st.session_state.seed))
    c2.write("")
    if c2.button("🎲 New random fire", type="primary"):
        st.session_state.seed = random.randint(0, 100000)
        st.rerun()
    log = []
    out = run_episode(POLICIES["Assistant (HMM + A* + Bayes + MDP)"], random.Random(st.session_state.seed), log=log)
    left, right = st.columns([1.3, 1], gap="large")
    with left:
        for e in log:
            believed = max(range(4), key=lambda z: e["belief"][z])
            ok = believed == e["true_fire_zone"]
            steps_txt = "".join(f"<span class='pill'>" + (", ".join(f"Z{k}" for k in range(4) if o[k]) or "quiet")
                                + "</span>" for o in e["sensors"])
            card(f"<b>Decision round {e['round']}</b> &nbsp;·&nbsp; decision: "
                 f"<span class='pill' style='background:#EDE9FE;color:{PURPLE}'>{e['action']}</span><br>"
                 f"<span class='muted'>Sensor steps:</span> {steps_txt}<br>"
                 f"<span class='muted'>Door camera:</span> <b>{e['door']}</b> &nbsp;·&nbsp; "
                 f"<span class='muted'>risk</span> {e['p_prior']:.2f} → <b>{e['p_posterior']:.2f}</b><br>"
                 f"<span class='muted'>Believed fire:</span> {ZONE_SHORT[believed]} ({max(e['belief']):.2f}) &nbsp; "
                 f"<span class='muted'>Real fire:</span> {ZONE_SHORT[e['true_fire_zone']]} {'✅' if ok else '❌'}")
    with right:
        with st.container(border=True):
            st.markdown(map_html(plan([])["world"], out["route"], blocked=log[-1]["blocked_zones"]), unsafe_allow_html=True)
            st.caption("🔥 = zone that is really blocked (hidden from the assistant)")
        t1, t2, t3 = st.columns(3)
        t1.markdown(f"<div class='tile'><b>{out['time']}</b><small>steps</small></div>", unsafe_allow_html=True)
        t2.markdown(f"<div class='tile'><b>{out['waits']}</b><small>waits</small></div>", unsafe_allow_html=True)
        t3.markdown(f"<div class='tile'><b>{'yes' if out['blocked'] else 'no'}</b><small>route blocked</small></div>",
                    unsafe_allow_html=True)
        st.write("")
        if out["harmed"]:
            note = "" if out["blocked"] else " The route was clear: even a clear route keeps a 2% risk."
            st.markdown(f"<div class='banner' style='background:{RED}'><h2>Harmed</h2><p>Bad outcome.{note}</p></div>",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='banner' style='background:{GREEN}'><h2>Safe</h2><p>The person evacuated safely.</p></div>",
                        unsafe_allow_html=True)

# ---------------------------------------------------------------- EVALUATION
elif page == "Evaluation":
    st.markdown("<div class='hero'><h1>Evaluation</h1><p>Every policy faces the same random fires. "
                "Lower harm and higher utility are better.</p></div>", unsafe_allow_html=True)
    st.write("")
    n = st.select_slider("Simulated fires per policy", options=[200, 500, 1000, 2000], value=500)

    @st.cache_data(show_spinner="Simulating fires...")
    def run_all(n):
        return [{"Policy": k, **evaluate(p, n, 2026)} for k, p in POLICIES.items()]

    rows = run_all(n)
    full = rows[0]
    shortest = next(x for x in rows if x["Policy"] == "Always shortest route")
    tiles = [(f"{full['harm_rate'] * 100:.1f}%", "assistant harm rate"),
             (f"{shortest['harm_rate'] * 100:.1f}%", "always shortest route"),
             (f"{(1 - full['harm_rate'] / shortest['harm_rate']) * 100:.0f}%", "fewer people harmed"),
             (f"{n}", "fires per policy")]
    for col, (num, lab) in zip(st.columns(4), tiles):
        col.markdown(f"<div class='tile'><b>{num}</b><small>{lab}</small></div>", unsafe_allow_html=True)
    st.write("")
    names = [x["Policy"].split(" (")[0] for x in rows]
    a, b = st.columns(2, gap="large")
    with a:
        with st.container(border=True):
            st.markdown("#### Harm rate (lower is better)")
            bar_chart(names, [x["harm_rate"] for x in rows], color=RED, fmt=".3f", height=300)
    with b:
        with st.container(border=True):
            st.markdown("#### Expected utility (higher is better)")
            bar_chart(names, [x["utility"] for x in rows], color=GREEN, fmt=".1f", height=300)
    card("<b>What this shows.</b> Removing the HMM or the Bayes update makes results clearly worse, so each algorithm "
         "contributes. The MDP matches the best hand-tuned threshold but finds the decision boundary from the rewards. "
         "<span class='muted'>Full run with 5000 fires: <code>python evaluate.py</code>.</span>")
    st.dataframe(pd.DataFrame([{"Policy": x["Policy"], "Harm rate": round(x["harm_rate"], 3),
                                "Mean time": round(x["mean_time"], 2), "Utility": round(x["utility"], 1),
                                "Waited": round(x["wait_rate"], 3)} for x in rows]), hide_index=True)

# ---------------------------------------------------------------- HOW IT WORKS
else:
    st.markdown("<div class='hero'><h1>How it works</h1><p>Four AI topics, each feeding the next.</p></div>",
                unsafe_allow_html=True)
    st.write("")
    algos = [
        ("🔎", "HMM filtering", BLUE, "The hidden state is the zone of the fire. Each step: <b>predict</b> how the fire moves "
         "(stay 0.7, neighbour 0.15), <b>correct</b> with the 4 noisy sensors, <b>normalize</b> to get the belief."),
        ("🗺️", "A* search", GREEN, "Cell cost = 1 + 10 × P(cell blocked). The Manhattan heuristic is admissible because "
         "every step costs at least 1, so A* finds the cheapest route."),
        ("🧮", "Bayes' theorem", ORANGE, "Prior = P(fast route blocked) from the belief. The camera shows SMOKE with 0.85 "
         "if blocked and 0.15 if clear. Posterior = likelihood × prior / evidence."),
        ("🎯", "MDP + value iteration", PURPLE, "States LOW / HIGH / DONE, actions PROCEED / DETOUR / WAIT, γ = 0.9. "
         "Decision = argmax of (1 − p)·Q(LOW, a) + p·Q(HIGH, a)."),
    ]
    for i in range(0, 4, 2):
        cols = st.columns(2, gap="large")
        for col, (ic, t, colr, d) in zip(cols, algos[i:i + 2]):
            col.markdown(f"<div class='card'><div style='width:46px;height:46px;border-radius:50%;background:{colr};"
                         f"display:flex;align-items:center;justify-content:center;font-size:22px'>{ic}</div>"
                         f"<h3>{t}</h3><p class='muted' style='font-size:1.02rem'>{d}</p></div>", unsafe_allow_html=True)
    card("<b>Assumptions.</b> All probabilities and rewards are assumed (see <code>evacuation/model.py</code>). "
         "This is a teaching model, not a real safety system.")
