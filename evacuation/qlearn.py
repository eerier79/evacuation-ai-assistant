"""Model-free comparison: tabular Q-learning that learns PROCEED / DETOUR / WAIT by trial and error.

State  = (risk of the fast route after HMM + Bayes, in 10 bins; number of waits so far).
Reward = -1 per time step (WAIT costs 3), then +100 for escaping or -300 for getting hurt.
The MDP gets its policy from the model in one value-iteration run; Q-learning needs thousands of
simulated fires to learn a similar one. That contrast is the point of this module.
"""
import random

from .model import Config
from .simulate import MAX_WAITS, WAIT_TIME, make_decider, play, q_state, summarize, episode_seeds

ACTIONS = ("PROCEED", "DETOUR", "WAIT")


def train(episodes=30000, epsilon0=0.3, seed=7, cfg=Config(), window=1500):
    """Q-learning with a sample-average step size (alpha = 1 / visits) and epsilon-greedy exploration.
    The bootstrap max(Q(s', a')) only uses actions already tried in s', so untried actions do not look
    falsely attractive (their value starts unknown, not at 0)."""
    rng = random.Random(seed)
    Q, N = {}, {}
    base = make_decider(dict(use_hmm=True, use_bayes=True, solver="mdp"), cfg)
    curve, recent = [], []
    for e in range(episodes):
        eps = max(0.05, epsilon0 * (1 - e / episodes))
        trail = []

        def decide(obs, door, waited):
            _, r = base(obs, door, waited)
            s = q_state(r, waited)
            options = ACTIONS if waited < MAX_WAITS else ACTIONS[:2]
            q = Q.get(s, {})
            untried = [x for x in options if x not in q]
            if untried:
                a = rng.choice(untried)
            elif rng.random() < eps:
                a = rng.choice(options)
            else:
                a = max(options, key=q.get)
            trail.append((s, a))
            return a, r

        out = play(rng.randrange(10 ** 9), decide, cfg)
        walk = out["time"] - out["waits"] * WAIT_TIME
        terminal = cfg.arrive_reward * (not out["harmed"]) - cfg.harm_penalty * out["harmed"] - walk
        for i, (s, a) in enumerate(trail):
            if a == "WAIT" and i + 1 < len(trail):
                q2 = Q.get(trail[i + 1][0], {})
                target = -WAIT_TIME + (max(q2.values()) if q2 else terminal)
            else:
                target = terminal
            q, n = Q.setdefault(s, {}), N.setdefault(s, {})
            n[a] = n.get(a, 0) + 1
            q[a] = q.get(a, 0.0) + (target - q.get(a, 0.0)) / n[a]
        recent.append(out["utility"])
        if len(recent) == window:
            curve.append({"episodes": e + 1, "avg_utility": sum(recent) / window})
            recent = []
    return Q, curve


def policy(Q):
    return {"solver": "q", "table": Q, "use_hmm": True, "use_bayes": True}


def greedy_table(Q):
    """For display: best learned action in every risk bin (first decision, no waits yet)."""
    rows = []
    for b in range(10):
        q = Q.get((b, 0), {})
        rows.append({"risk": f"{b / 10:.1f}–{(b + 1) / 10:.1f}",
                     "learned action": max(q, key=q.get) if q else "—",
                     **{a: round(q.get(a, 0.0), 1) for a in ACTIONS}})
    return rows


def evaluate_learned(Q, n=2000, seed=2026, cfg=Config()):
    decide = make_decider(policy(Q), cfg)
    return summarize([play(s, decide, cfg) for s in episode_seeds(n, seed)])
