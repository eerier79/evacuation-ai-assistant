"""Plain-language explanations of one plan() result (used by the web interface)."""
from .model import ZONE_NAMES

ACTION_WORDS = {"PROCEED": "take the fast route", "DETOUR": "take the safe detour", "WAIT": "wait and listen to the sensors"}


def pct(p):
    return f"{p * 100:.0f}%"


def why(r):
    """Return 3-4 short sentences that explain the decision with the numbers of this run."""
    fast, safe = r["fast"], r["safe"]
    prior, post = r["p_fast_prior"], r["p_fast_posterior"]
    values = r["action_values"]
    out = []
    if r["steps"]:
        z = max(range(len(r["belief"])), key=lambda k: r["belief"][k])
        if r["belief"][z] >= 0.4:
            out.append(f"The sensors point to a fire in {ZONE_NAMES[z]} ({pct(r['belief'][z])} sure).")
        else:
            out.append(f"The sensors do not point to any zone yet: the most likely one, {ZONE_NAMES[z]}, "
                       f"is only {pct(r['belief'][z])}.")
    else:
        out.append("No sensor readings yet, so every zone is equally likely to be on fire.")
    out.append(f"The fast route ({fast['steps']} steps) is blocked with probability {pct(prior)}; "
               f"the safe detour ({safe['steps']} steps) with {pct(safe['risk'])}.")
    if r["door_reading"] is None:
        out.append("The door camera gave no reading, so this risk stays as it is.")
    else:
        direction = "raised" if post > prior else "lowered"
        out.append(f"The door camera shows {r['door_reading']}, which {direction} the risk of the fast route "
                   f"from {pct(prior)} to {pct(post)}.")
    best = r["action"]
    runner = max((a for a in values if a != best), key=values.get)
    out.append(f"So Kitty should {ACTION_WORDS[best]}: it scores {values[best]:.1f} points, "
               f"ahead of '{ACTION_WORDS[runner]}' with {values[runner]:.1f}.")
    return out


def walkthrough(r):
    """Five guided steps (key, title, text) for the 'walk me through it' mode."""
    b = r["belief"]
    zones = ", ".join(f"Z{k} {pct(p)}" for k, p in enumerate(b))
    n = len(r["steps"])
    fast, safe = r["fast"], r["safe"]
    values = r["action_values"]
    cam = r["door_reading"] or "no reading"
    return [
        ("sensors", "1 · Sensors",
         f"Kitty's house has 4 smoke alarms (one per zone) and a camera at the door. So far there "
         f"{'is' if n == 1 else 'are'} {n} sensor step{'s' if n != 1 else ''}, and the camera shows {cam}. "
         "Alarms are noisy: they can ring without fire and stay quiet near a fire."),
        ("hmm", "2 · HMM: where is the fire?",
         "The fire is hidden. Each step the HMM first lets the fire spread (stay 70%, move to a neighbour 15%), "
         f"then trusts zones whose alarm matches the readings more. Current belief: {zones}."),
        ("astar", "3 · A*: which roads exist?",
         f"A* finds the fast route ({fast['steps']} steps, through the door) and a safe route "
         f"({safe['steps']} steps) where every risky cell costs extra (1 + 10 × risk). "
         f"Chance each is blocked: fast {pct(fast['risk'])}, safe {pct(safe['risk'])}."),
        ("bayes", "4 · Bayes: what does the camera add?",
         "The camera sees smoke 85% of the time when the route is blocked and 15% when it is clear. "
         f"Bayes' rule turns the risk of the fast route from {pct(r['p_fast_prior'])} into "
         f"{pct(r['p_fast_posterior'])}."),
        ("mdp", "5 · MDP: what should Kitty do?",
         "Each action gets a score: +100 for escaping, −300 for getting hurt, −1 per step, −20 for waiting. "
         f"Scores now: proceed {values['PROCEED']:.1f}, detour {values['DETOUR']:.1f}, wait {values['WAIT']:.1f}. "
         f"The highest wins: {r['action']}."),
    ]
