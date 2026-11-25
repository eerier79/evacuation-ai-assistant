import random
import streamlit as st
from evacuation.model import ZONE_NAMES, zone_of
from evacuation.planner import plan
from evacuation.simulate import POLICIES, evaluate, run_episode, OBS_STEPS, WAIT_TIME

st.set_page_config(page_title="Emergency Evacuation Assistant", layout="wide")
st.title("Emergency Evacuation Assistant")
st.caption("HMM filtering → risk-aware A* search → Bayes update → MDP decision, on one building map")

ZONE_COLOURS = ["#fde2e2", "#fdf0d5", "#e6f4ea", "#e3eefc"]
EXPLAIN = {"PROCEED": "The fast route is probably clear: take the shortest way out.",
           "DETOUR": "The fast route is too risky for its speed: take the longer safe route.",
           "WAIT": "The situation is unclear: stay in place and read the sensors again."}


def draw_map(world, route=None, blocked_zones=None, zone_risk=None):
    route = set(route or [])
    html = "<table style='border-collapse:collapse'>"
    for r in range(world["rows"]):
        html += "<tr>"
        for c in range(world["cols"]):
            cell, txt = (r, c), ""
            if cell in world["walls"]:
                bg = "#333"
            else:
                z = zone_of(r, c)
                bg = ZONE_COLOURS[z]
                if zone_risk is not None:
                    a = min(1.0, zone_risk[z])
                    bg = f"rgba(229,83,75,{0.15 + 0.75 * a:.2f})"
                if blocked_zones is not None and blocked_zones[z]:
                    txt = "🔥"
                if cell == world["start"]:
                    txt = "S"
                elif cell in world["exits"]:
                    txt = "E"
                elif cell == world["door"]:
                    txt = txt or "D"
                if cell in route and cell != world["start"]:
                    bg, txt = "#3DBE7A", txt or "•"
            html += (f"<td style='width:40px;height:40px;text-align:center;background:{bg};"
                     f"border:1px solid #999;color:#000;font-weight:600'>{txt}</td>")
        html += "</tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)


def values_table(values):
    return [{"Action": a, "Expected value": round(v, 1)} for a, v in sorted(values.items(), key=lambda x: -x[1])]


planner_tab, sim_tab, eval_tab, how_tab = st.tabs(["Planner", "Simulation", "Evaluation", "How it works"])

with planner_tab:
    if "history" not in st.session_state:
        st.session_state.history = []
    left, right = st.columns([1, 2])
    with left:
        st.subheader("1. Smoke sensors")
        flags = tuple(st.checkbox(f"Alarm in {name}", key=f"s{i}") for i, name in enumerate(ZONE_NAMES))
        c1, c2 = st.columns(2)
        if c1.button("Add sensor step"):
            st.session_state.history.append(flags)
        if c2.button("Reset"):
            st.session_state.history = []
        hist = st.session_state.history
        st.write("Steps so far:", " | ".join("".join(str(int(x)) for x in o) for o in hist) or "none")
        st.caption("Each step is 4 digits for Z0 Z1 Z2 Z3 (1 = alarm).")
        st.subheader("2. Door camera")
        door = st.radio("Reading at door D", ["No reading", "CLEAR", "SMOKE"], horizontal=True)

    result = plan(st.session_state.history, None if door == "No reading" else door)
    with right:
        action = result["action"]
        st.subheader(f"Decision: {action}")
        (st.success if action == "PROCEED" else st.warning if action == "DETOUR" else st.info)(EXPLAIN[action])
        m1, m2 = st.columns([3, 2])
        with m1:
            show_risk = st.toggle("Colour cells by risk instead of zone", value=False)
            draw_map(result["world"], result["route"]["path"] if result["route"] else None,
                     zone_risk=result["zone_risk"] if show_risk else None)
            st.caption("S start · E exits · D door with camera · green = chosen route")
        with m2:
            st.metric("Most likely fire zone", ZONE_NAMES[max(range(4), key=lambda z: result["belief"][z])])
            st.metric("P(fast route blocked)", f"{result['p_fast_posterior']:.3f}",
                      delta=f"{result['p_fast_posterior'] - result['p_fast_prior']:+.3f} from camera",
                      delta_color="inverse")
            st.table(values_table(result["action_values"]))
        a, b = st.columns(2)
        with a:
            st.write("**HMM belief about the fire zone**")
            st.bar_chart({n: v for n, v in zip(ZONE_NAMES, result["belief"])})
        with b:
            st.write("**Routes found by A***")
            st.table([{"Route": "Fast", "Exit": str(result["fast"]["exit"]), "Steps": result["fast"]["steps"],
                       "P(blocked)": round(result["fast"]["risk"], 3)},
                      {"Route": "Safe", "Exit": str(result["safe"]["exit"]), "Steps": result["safe"]["steps"],
                       "P(blocked)": round(result["safe"]["risk"], 3)}])

with sim_tab:
    st.write("One random fire. The assistant sees only the noisy sensors; the true fire is shown for checking.")
    seed = st.number_input("Random seed", min_value=0, max_value=100000, value=7, step=1)
    log = []
    out = run_episode(POLICIES["Assistant (HMM + A* + Bayes + MDP)"], random.Random(int(seed)), log=log)
    for entry in log:
        with st.container(border=True):
            st.write(f"**Decision round {entry['round']}** · true fire zone: {ZONE_NAMES[entry['true_fire_zone']]} · "
                     f"believed: {ZONE_NAMES[max(range(4), key=lambda z: entry['belief'][z])]} "
                     f"({max(entry['belief']):.2f})")
            st.write("Sensor steps: " + " | ".join("".join(str(int(x)) for x in o) for o in entry["sensors"])
                     + f" · door camera: {entry['door']}")
            st.write(f"P(fast route blocked): {entry['p_prior']:.3f} → {entry['p_posterior']:.3f} · "
                     f"decision: **{entry['action']}**")
    c1, c2 = st.columns([3, 2])
    with c1:
        draw_map(plan([])["world"], out["route"], blocked_zones=log[-1]["blocked_zones"])
        st.caption("🔥 = zone that is really blocked (hidden from the assistant)")
    with c2:
        st.metric("Exit", str(out["exit"]))
        st.metric("Evacuation time", f"{out['time']} steps", help=f"each WAIT costs {WAIT_TIME} steps")
        (st.error if out["harmed"] else st.success)("Person was harmed" if out["harmed"] else "Person evacuated safely")

with eval_tab:
    st.write("Monte Carlo evaluation: every policy faces the same random fires (same seed).")
    n = st.select_slider("Simulated fires per policy", options=[200, 500, 1000, 2000], value=500)

    @st.cache_data
    def run_all(n):
        return [{"Policy": k, **{key: round(v, 3) for key, v in evaluate(p, n, 2026).items()}} for k, p in POLICIES.items()]

    rows = run_all(n)
    st.dataframe(rows, hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        st.write("**Harm rate (lower is better)**")
        st.bar_chart({r["Policy"].split(" (")[0]: r["harm_rate"] for r in rows}, horizontal=True)
    with c2:
        st.write("**Expected utility (higher is better)**")
        st.bar_chart({r["Policy"].split(" (")[0]: r["utility"] for r in rows}, horizontal=True)
    st.caption("Full results with 5000 fires and 95% confidence intervals: run `python evaluate.py` (results/ folder).")

with how_tab:
    st.markdown("""
1. **HMM filtering.** Hidden state = zone of the fire. Predict with the transition model (stay 0.7, move 0.15),
   correct with 4 noisy smoke sensors, normalize → belief b(z).
2. **Risk-aware A\\*.** Cell cost = 1 + 10 · P(cell blocked), Manhattan heuristic (admissible because every cost ≥ 1).
   Gives the fast route and the safe route.
3. **Bayes' theorem.** Prior = P(fast route blocked) from the belief; the door camera (SMOKE 0.85 / 0.15) updates it.
4. **MDP + value iteration.** States LOW / HIGH / DONE, actions PROCEED / DETOUR / WAIT, γ = 0.9.
   Decision = argmax of (1 − p)·Q(LOW, a) + p·Q(HIGH, a), where p is the Bayes posterior.

All probabilities and rewards are assumptions (see `evacuation/model.py`). This is a teaching model, not a safety system.
""")
