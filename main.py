"""Console demo: three scenarios, each printed as input -> key calculation -> output."""
from evacuation.model import ZONE_NAMES
from evacuation.planner import plan

Q = (False, False, False, False)
Z1 = (False, True, False, False)

SCENARIOS = [
    ("1. All quiet, door camera shows CLEAR", [Q, Q], "CLEAR"),
    ("2. Alarm in Z1 for two steps, door camera shows SMOKE", [Z1, Z1], "SMOKE"),
    ("3. Alarm in Z1 for two steps, door camera shows CLEAR", [Z1, Z1], "CLEAR"),
]


def fmt(values):
    return "[" + ", ".join(f"{v:.3f}" for v in values) + "]"


def show(title, observations, door):
    r = plan(observations, door)
    print("=" * 70)
    print(title)
    print("INPUT  sensors per step (Z0,Z1,Z2,Z3):", [tuple(int(x) for x in o) for o in observations])
    print("       door camera:", door)
    print("HMM    belief about the fire zone:", fmt(r["belief"]),
          "->", ZONE_NAMES[max(range(4), key=lambda z: r["belief"][z])])
    print("RISK   P(cell blocked) per zone  :", fmt(r["zone_risk"]))
    print(f"A*     fast route to {r['fast']['exit']}: {r['fast']['steps']} steps, risk {r['fast']['risk']:.3f}")
    print(f"       safe route to {r['safe']['exit']}: {r['safe']['steps']} steps, risk {r['safe']['risk']:.3f}")
    print(f"BAYES  P(fast route blocked): prior {r['p_fast_prior']:.3f} -> posterior {r['p_fast_posterior']:.3f}")
    print("MDP    expected value:", {a: round(v, 1) for a, v in r["action_values"].items()})
    print(f"OUTPUT decision: {r['action']}, go to exit {r['route']['exit']} via {len(r['route']['path']) - 1} steps")
    print("       path:", r["route"]["path"])
    why = {"PROCEED": "the fast route is probably clear, so the shortest way is best.",
           "DETOUR": "the fast route is too risky for its speed, so the longer safe way has the higher expected value.",
           "WAIT": "the situation is unclear, so waiting for more information scores best."}[r["action"]]
    print("WHY    ", why)


if __name__ == "__main__":
    for s in SCENARIOS:
        show(*s)
