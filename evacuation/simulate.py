"""Monte Carlo simulator: random fires, noisy sensors, and policies that decide how to evacuate."""
import random
from dataclasses import replace
from .model import Config, transition_matrix, emission_matrix, block_matrix
from .planner import plan, route_zones, _shortest_routes, WORLD

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


def _routes():
    fast = min(_shortest_routes(), key=lambda x: x["cost"])
    return fast["path"], plan([], None)["safe"]["path"]


POLICIES = {
    "Assistant (HMM + A* + Bayes + MDP)": dict(use_hmm=True, use_bayes=True, mdp=True),
    "No HMM (ignores smoke sensors)": dict(use_hmm=False, use_bayes=True, mdp=True),
    "No Bayes (ignores door camera)": dict(use_hmm=True, use_bayes=False, mdp=True),
    "No MDP, threshold 0.5 (hand-tuned)": dict(use_hmm=True, use_bayes=True, mdp=False, threshold=0.5),
    "No MDP, threshold 0.2": dict(use_hmm=True, use_bayes=True, mdp=False, threshold=0.2),
    "No MDP, threshold 0.8": dict(use_hmm=True, use_bayes=True, mdp=False, threshold=0.8),
    "Always shortest route": "PROCEED",
    "Always safe detour": "DETOUR",
}


def run_episode(policy, rng, cfg=Config(), log=None):
    ep = Episode(rng, cfg)
    fast_path, _ = _routes()
    waited = 0
    while True:
        door = ep.door_reading(fast_path)
        if isinstance(policy, str):
            action, route = policy, None
            r = plan(ep.observations, door, cfg)
            route = r["fast"] if action == "PROCEED" else r["safe"]
        else:
            r = plan(ep.observations, door, cfg, use_hmm=policy["use_hmm"], use_bayes=policy["use_bayes"])
            if policy["mdp"]:
                action = r["action"]
            else:
                action = "DETOUR" if r["p_fast_posterior"] > policy["threshold"] else "PROCEED"
            if action == "WAIT" and waited >= MAX_WAITS:
                action = max(("PROCEED", "DETOUR"), key=lambda a: r["action_values"][a])
            route = r["fast"] if action == "PROCEED" else r["safe"]
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
        blocked = ep.route_blocked(route["path"])
        harm_p = cfg.harm_if_blocked if blocked else cfg.harm_if_clear
        harmed = rng.random() < harm_p
        time = waited * WAIT_TIME + route["steps"]
        return {"harmed": harmed, "time": time, "waits": waited, "action": action, "blocked": blocked,
                "route": route["path"], "exit": route["exit"]}


def evaluate(policy, n=2000, seed=0, cfg=Config()):
    rng = random.Random(seed)
    res = [run_episode(policy, rng, cfg) for _ in range(n)]
    harm = sum(r["harmed"] for r in res) / n
    time = sum(r["time"] for r in res) / n
    blocked = sum(r["blocked"] for r in res) / n
    utils = [-r["time"] + cfg.arrive_reward * (not r["harmed"]) - cfg.harm_penalty * r["harmed"] for r in res]
    utility = sum(utils) / n
    se = (sum((u - utility) ** 2 for u in utils) / (n - 1)) ** 0.5 / n ** 0.5
    return {"harm_rate": harm, "harm_se": (harm * (1 - harm) / n) ** 0.5, "mean_time": time,
            "blocked_rate": blocked, "utility": utility, "utility_se": se,
            "wait_rate": sum(r["waits"] > 0 for r in res) / n}


def sensitivity(values=(0.55, 0.65, 0.75, 0.85, 0.95), n=1500, seed=1):
    """Harm rate when the smoke sensors get better (alarm_same) and worse."""
    rows = []
    for v in values:
        cfg = replace(Config(), alarm_same=v)
        rows.append({"alarm_same": v,
                     "assistant": evaluate(POLICIES["Assistant (HMM + A* + Bayes + MDP)"], n, seed, cfg)["harm_rate"],
                     "shortest": evaluate("PROCEED", n, seed, cfg)["harm_rate"]})
    return rows
