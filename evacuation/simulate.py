"""Monte Carlo simulator: random fires, noisy sensors, and policies that decide how to evacuate.

Design choices for a fair comparison:
* common random numbers: episode i always starts from the same seed, so every policy meets the same
  fire, the same first sensor readings and the same "luck" when it walks a route;
* the true world (world_cfg) may differ from what the assistant believes (cfg): this is the
  model-mismatch / robustness test.
"""
import random
from dataclasses import replace

from . import pomdp
from .model import Config, transition_matrix, emission_matrix, block_matrix
from .planner import plan, route_zones, _shortest_routes

WAIT_TIME = 3      # time steps lost by one WAIT
MAX_WAITS = 3      # after this the policy must move
OBS_STEPS = 2      # sensor steps before the first decision
SPREAD = 0.3       # per-step chance factor that the fire blocks a new zone


def _sample(rng, probs):
    x, acc = rng.random(), 0.0
    for i, p in enumerate(probs):
        acc += p
        if x < acc:
            return i
    return len(probs) - 1


class Episode:
    """Hidden truth of one fire: the fire zone moves, sensors and the camera are sampled from it."""

    def __init__(self, rng, cfg):
        self.rng, self.cfg = rng, cfg
        self.T, self.E, self.B = transition_matrix(cfg), emission_matrix(cfg), block_matrix(cfg)
        self.zone = rng.randrange(4)
        self.observations = []
        for _ in range(OBS_STEPS):
            self.step()
        # blockages at the moment of the first decision depend on where the fire is now
        self.blocked = [self.rng.random() < self.B[self.zone][w] for w in range(4)]

    def step(self):
        self.zone = _sample(self.rng, self.T[self.zone])
        self.observations.append(tuple(self.rng.random() < self.E[k][self.zone] for k in range(4)))
        if not hasattr(self, "blocked"):
            self.blocked = [self.rng.random() < self.B[self.zone][w] for w in range(4)]
        else:
            # a blocked zone stays blocked, and the fire can block new zones over time
            self.blocked = [b or self.rng.random() < SPREAD * self.B[self.zone][w]
                            for w, b in enumerate(self.blocked)]

    def route_blocked(self, path):
        return any(self.blocked[w] for w in route_zones(path))

    def door_reading(self, fast_path):
        p = self.cfg.p_smoke_if_blocked if self.route_blocked(fast_path) else self.cfg.p_smoke_if_clear
        return "SMOKE" if self.rng.random() < p else "CLEAR"


def _fast_path():
    return min(_shortest_routes(), key=lambda x: x["cost"])["path"]


POLICIES = {
    "Assistant (HMM + A* + Bayes + MDP)": dict(use_hmm=True, use_bayes=True, solver="mdp"),
    "Assistant with exact POMDP": dict(use_hmm=True, use_bayes=True, solver="pomdp"),
    "No HMM (ignores smoke sensors)": dict(use_hmm=False, use_bayes=True, solver="mdp"),
    "No Bayes (ignores door camera)": dict(use_hmm=True, use_bayes=False, solver="mdp"),
    "No MDP, threshold 0.5 (hand-tuned)": dict(use_hmm=True, use_bayes=True, solver="threshold", threshold=0.5),
    "No MDP, threshold 0.2": dict(use_hmm=True, use_bayes=True, solver="threshold", threshold=0.2),
    "No MDP, threshold 0.8": dict(use_hmm=True, use_bayes=True, solver="threshold", threshold=0.8),
    "Always shortest route": "PROCEED",
    "Always safe detour": "DETOUR",
}
ASSISTANT = POLICIES["Assistant (HMM + A* + Bayes + MDP)"]


def q_state(r, waited, bins=10):
    """Discrete state for Q-learning: risk of the fast route in 10 bins, and how often we already waited."""
    return min(bins - 1, int(r["p_fast_posterior"] * bins)), waited


def make_decider(policy, cfg):
    """policy -> function(observations, door, waited) returning (action, plan result)."""
    def decide(observations, door, waited):
        if isinstance(policy, str):
            return policy, plan(observations, door, cfg)
        r = plan(observations, door, cfg, use_hmm=policy.get("use_hmm", True), use_bayes=policy.get("use_bayes", True))
        solver = policy.get("solver", "mdp")
        if solver == "mdp":
            action = r["action"]
        elif solver == "threshold":
            action = "DETOUR" if r["p_fast_posterior"] > policy["threshold"] else "PROCEED"
        elif solver == "pomdp":
            action, values = pomdp.decide(r["fast"]["steps"], r["safe"]["steps"], r["safe"]["risk"],
                                          r["p_fast_posterior"], cfg)
            r = dict(r, action=action, action_values=values)
        elif solver == "q":
            q = policy["table"].get(q_state(r, waited), {})
            action = max(("PROCEED", "DETOUR", "WAIT"), key=lambda a: q.get(a, 0.0))
        else:
            raise ValueError(f"unknown solver {solver}")
        return action, r
    return decide


def utility(outcome, cfg=Config()):
    return -outcome["time"] + cfg.arrive_reward * (not outcome["harmed"]) - cfg.harm_penalty * outcome["harmed"]


def play(seed, decide, cfg=Config(), world_cfg=None, log=None):
    """One fire. decide(observations, door, waited) -> (action, r); returning (None, r) pauses the game
    (used by the 'You vs AI' challenge to wait for the player's click)."""
    world_cfg = world_cfg or cfg
    ep = Episode(random.Random(seed), world_cfg)
    luck = random.Random(seed * 7919 + 17).random()      # the same luck for every policy on this fire
    fast_path = _fast_path()
    waited = 0
    while True:
        door = ep.door_reading(fast_path)
        action, r = decide(ep.observations, door, waited)
        if action is None:
            return {"pending": True, "observations": list(ep.observations), "door": door, "waited": waited, "plan": r}
        if action == "WAIT" and waited >= MAX_WAITS:
            action = max(("PROCEED", "DETOUR"), key=lambda a: r["action_values"][a])
        if log is not None:
            log.append({"round": waited + 1, "true_fire_zone": ep.zone, "sensors": list(ep.observations),
                        "door": door, "belief": r["belief"], "p_prior": r["p_fast_prior"],
                        "p_posterior": r["p_fast_posterior"], "values": r["action_values"], "action": action,
                        "blocked_zones": list(ep.blocked)})
        if action == "WAIT":
            waited += 1
            for _ in range(WAIT_TIME):
                ep.step()
            continue
        route = r["fast"] if action == "PROCEED" else r["safe"]
        blocked = ep.route_blocked(route["path"])
        harmed = luck < (world_cfg.harm_if_blocked if blocked else world_cfg.harm_if_clear)
        out = {"harmed": harmed, "time": waited * WAIT_TIME + route["steps"], "waits": waited, "action": action,
               "blocked": blocked, "route": route["path"], "exit": route["exit"], "true_fire_zone": ep.zone,
               "blocked_zones": list(ep.blocked)}
        out["utility"] = utility(out, world_cfg)
        return out


def run_episode(policy, rng_or_seed, cfg=Config(), log=None, world_cfg=None):
    seed = rng_or_seed if isinstance(rng_or_seed, int) else rng_or_seed.randrange(10 ** 9)
    return play(seed, make_decider(policy, cfg), cfg, world_cfg, log)


def episode_seeds(n, seed):
    return [seed * 1_000_003 + i for i in range(n)]


def run_many(policy, n=2000, seed=0, cfg=Config(), world_cfg=None):
    decide = make_decider(policy, cfg)
    return [play(s, decide, cfg, world_cfg) for s in episode_seeds(n, seed)]


def summarize(res):
    n = len(res)
    harm = sum(r["harmed"] for r in res) / n
    utils = [r["utility"] for r in res]
    mean_u = sum(utils) / n
    se = (sum((u - mean_u) ** 2 for u in utils) / (n - 1)) ** 0.5 / n ** 0.5
    return {"harm_rate": harm, "harm_se": (harm * (1 - harm) / n) ** 0.5,
            "mean_time": sum(r["time"] for r in res) / n, "blocked_rate": sum(r["blocked"] for r in res) / n,
            "utility": mean_u, "utility_se": se, "wait_rate": sum(r["waits"] > 0 for r in res) / n}


def evaluate(policy, n=2000, seed=0, cfg=Config(), world_cfg=None):
    return summarize(run_many(policy, n, seed, cfg, world_cfg))


def paired_bootstrap(res_a, res_b, key="utility", B=2000, seed=0):
    """95% CI of mean(a - b) over the same fires (paired, because both met identical episodes)."""
    diffs = [float(a[key]) - float(b[key]) for a, b in zip(res_a, res_b)]
    n, rng = len(diffs), random.Random(seed)
    means = sorted(sum(diffs[rng.randrange(n)] for _ in range(n)) / n for _ in range(B))
    return {"mean": sum(diffs) / n, "low": means[int(0.025 * B)], "high": means[int(0.975 * B) - 1]}


def paired_ci(res_a, res_b, key="utility"):
    """Fast paired 95% CI (normal approximation); used by the web app. evaluate.py uses the bootstrap."""
    d = [float(a[key]) - float(b[key]) for a, b in zip(res_a, res_b)]
    n = len(d)
    m = sum(d) / n
    se = (sum((x - m) ** 2 for x in d) / (n - 1)) ** 0.5 / n ** 0.5
    return {"mean": m, "low": m - 1.96 * se, "high": m + 1.96 * se}


ROBUSTNESS = {
    "Model is right": {},
    "Sensors worse than assumed": dict(alarm_same=0.75, alarm_adjacent=0.40, alarm_far=0.10),
    "Fire spreads faster": dict(p_stay=0.50),
    "Camera worse than assumed": dict(p_smoke_if_blocked=0.70, p_smoke_if_clear=0.30),
    "Everything worse": dict(alarm_same=0.75, alarm_adjacent=0.40, alarm_far=0.10, p_stay=0.50,
                             p_smoke_if_blocked=0.70, p_smoke_if_clear=0.30),
}


def robustness(policies=("Assistant (HMM + A* + Bayes + MDP)", "No MDP, threshold 0.5 (hand-tuned)",
                         "Always shortest route", "Always safe detour"), n=1500, seed=3):
    """The assistant keeps its assumed model; only the true world changes."""
    rows = []
    for name, change in ROBUSTNESS.items():
        world = replace(Config(), **change)
        row = {"world": name}
        for p in policies:
            row[p] = evaluate(POLICIES[p], n, seed, Config(), world)
        rows.append(row)
    return rows


def sensitivity(values=(0.55, 0.65, 0.75, 0.85, 0.95), n=1500, seed=1):
    """Harm rate when the smoke sensors get better (alarm_same) and worse (model and world agree)."""
    rows = []
    for v in values:
        cfg = replace(Config(), alarm_same=v)
        rows.append({"alarm_same": v, "assistant": evaluate(ASSISTANT, n, seed, cfg)["harm_rate"],
                     "shortest": evaluate("PROCEED", n, seed, cfg)["harm_rate"]})
    return rows
