import streamlit as st
from evacuation.model import ZONE_NAMES, zone_of
from evacuation.planner import plan

st.set_page_config(page_title="Emergency Evacuation Assistant", layout="wide")
st.title("Emergency Evacuation Assistant")
st.caption("HMM + Bayes + A* + MDP on one building map")

if "history" not in st.session_state:
    st.session_state.history = []

left, right = st.columns([1, 2])
with left:
    st.subheader("Sensors (one step)")
    flags = tuple(st.checkbox(f"Smoke alarm in {name}", key=f"s{i}") for i, name in enumerate(ZONE_NAMES))
    c1, c2 = st.columns(2)
    if c1.button("Add step"):
        st.session_state.history.append(flags)
    if c2.button("Reset"):
        st.session_state.history = []
    door = st.radio("Door camera", ["No reading", "CLEAR", "SMOKE"], horizontal=True)
    st.write("Steps so far:", [tuple(int(x) for x in o) for o in st.session_state.history])

result = plan(st.session_state.history, None if door == "No reading" else door)

with right:
    st.subheader(f"Decision: {result['action']}")
    explain = {"PROCEED": "Fast route is probably clear.",
               "DETOUR": "Fast route is too risky, take the safe route.",
               "WAIT": "Unclear situation, wait for more information."}
    st.info(explain[result["action"]])
    world, route = result["world"], result["route"]["path"]
    colours = ["#fde2e2", "#fdf0d5", "#e6f4ea", "#e3eefc"]
    html = "<table style='border-collapse:collapse'>"
    for r in range(world["rows"]):
        html += "<tr>"
        for c in range(world["cols"]):
            cell = (r, c)
            if cell in world["walls"]:
                bg, txt = "#333", ""
            else:
                bg = colours[zone_of(r, c)]
                txt = "S" if cell == world["start"] else "E" if cell in world["exits"] else "D" if cell == world["door"] else ""
                if cell in route and cell != world["start"]:
                    bg, txt = "#7bd88f", txt or "•"
            html += f"<td style='width:42px;height:42px;text-align:center;background:{bg};border:1px solid #bbb;color:#000'>{txt}</td>"
        html += "</tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)
    st.caption("S start, E exits, D door, green = chosen route, colours = zones")

    a, b, c = st.columns(3)
    a.metric("Most likely fire zone", ZONE_NAMES[max(range(4), key=lambda z: result["belief"][z])])
    b.metric("P(fast route blocked) prior", f"{result['p_fast_prior']:.3f}")
    c.metric("after door reading", f"{result['p_fast_posterior']:.3f}")
    st.write("HMM belief per zone:")
    st.bar_chart({n: v for n, v in zip(ZONE_NAMES, result["belief"])})
    st.write("MDP expected value per action:", {k: round(v, 1) for k, v in result["action_values"].items()})
    st.write(f"Fast route: {result['fast']['steps']} steps, risk {result['fast']['risk']:.3f}. "
             f"Safe route: {result['safe']['steps']} steps, risk {result['safe']['risk']:.3f}.")
