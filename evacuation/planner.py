"""Integration: HMM belief -> cell risk -> A* routes -> Bayes door reading -> MDP decision."""
from .model import (Config, ZONE_NAMES, parse_map, zone_of, transition_matrix,
                    emission_matrix, block_matrix)
from . import hmm, bayes, astar, mdp


def cell_risk(belief, cfg=Config()):
    """P(cell blocked) = sum over fire zones z of P(fire in z) * P(blocked | fire in z)."""
    B = block_matrix(cfg)
    per_zone = [sum(belief[z] * B[z][w] for z in range(len(belief))) for w in range(len(belief))]
    return per_zone


def route_risk(path, zone_risk):
    """A route is as dangerous as its most dangerous cell (start cell excluded)."""
    return max(zone_risk[zone_of(r, c)] for r, c in path[1:])


def plan(observations, door_reading=None, cfg=Config()):
    world = parse_map()
    n = len(ZONE_NAMES)
    prior = [1.0 / n] * n
    steps = hmm.filter_sequence(prior, transition_matrix(cfg), emission_matrix(cfg), observations)
    belief = steps[-1]["posterior"] if steps else prior
    zone_risk = cell_risk(belief, cfg)

    def risky_cost(cell):
        return 1.0 + cfg.risk_weight * zone_risk[zone_of(*cell)]

    def run(goal, cost_fn):
        return astar.astar(world["start"], goal, world["walls"], world["rows"], world["cols"], cost_fn)

    fastest = [dict(run(g, lambda cell: 1.0), exit=g) for g in world["exits"]]
    fast = min(fastest, key=lambda x: x["cost"])
    other_exit = [g for g in world["exits"] if g != fast["exit"]][0]
    safe = dict(run(other_exit, risky_cost), exit=other_exit)
    fast["steps"], safe["steps"] = len(fast["path"]) - 1, len(safe["path"]) - 1
    fast["risk"], safe["risk"] = route_risk(fast["path"], zone_risk), route_risk(safe["path"], zone_risk)

    p_fast_blocked, evidence = bayes.door_update(fast["risk"], door_reading,
                                                 cfg.p_smoke_if_blocked, cfg.p_smoke_if_clear)
    model = mdp.build_mdp(fast["steps"], safe["steps"], safe["risk"], cfg)
    V, Q, iterations = mdp.value_iteration(model, cfg.gamma)
    action, values = mdp.decide(Q, p_fast_blocked)
    return {"world": world, "steps": steps, "belief": belief, "zone_risk": zone_risk,
            "fast": fast, "safe": safe, "door_reading": door_reading,
            "p_fast_prior": fast["risk"], "p_fast_posterior": p_fast_blocked,
            "evidence": evidence, "V": V, "Q": Q, "iterations": iterations,
            "action": action, "action_values": values,
            "route": fast if action == "PROCEED" else safe}
