"""Integration: HMM belief -> cell risk -> A* routes -> Bayes door reading -> MDP decision."""
from math import prod
from functools import lru_cache
from .model import (Config, MAP, ZONE_NAMES, parse_map, zone_of, transition_matrix,
                    emission_matrix, block_matrix)
from . import hmm, bayes, astar, mdp

WORLD = parse_map()


@lru_cache(maxsize=64)
def get_world(map_rows=None):
    return WORLD if map_rows is None else parse_map(list(map_rows))


def validate_map(map_rows):
    """Problems that stop the planner on a user-drawn map (empty list = the map is usable)."""
    rows = list(map_rows)
    problems = []
    if len(rows) != len(MAP) or any(len(r) != len(MAP[0]) for r in rows):
        return [f"The map must be {len(MAP)} x {len(MAP[0])} cells."]
    text = "".join(rows)
    if text.count("S") != 1:
        problems.append("Place exactly one start cell (S).")
    if text.count("E") < 2:
        problems.append("Place at least two exits (E): one for the fast route and one for the detour.")
    if not problems:
        w = parse_map(rows)
        reach = [g for g in w["exits"] if astar.astar(w["start"], g, w["walls"], w["rows"], w["cols"], lambda c: 1.0)]
        if len(reach) < 2:
            problems.append("Kitty must be able to reach at least two exits from the start.")
    return problems


def cell_risk(belief, cfg=Config()):
    """P(a cell in zone w is blocked) = sum over fire zones z of b(z) * B[z][w]."""
    B = block_matrix(cfg)
    n = len(belief)
    return [sum(belief[z] * B[z][w] for z in range(n)) for w in range(n)]


def route_zones(path):
    """Zones the person walks through (the start cell is excluded)."""
    return sorted({zone_of(r, c) for r, c in path[1:]})


def route_risk(path, belief, cfg=Config()):
    """Exact P(route blocked) under the model: the route is blocked if any of its zones is blocked.
    Given the fire zone z the zones are blocked independently, so
    P(blocked) = sum_z b(z) * (1 - prod_{w on route} (1 - B[z][w]))."""
    B = block_matrix(cfg)
    zones = route_zones(path)
    return sum(belief[z] * (1.0 - prod(1.0 - B[z][w] for w in zones)) for z in range(len(belief)))


@lru_cache(maxsize=None)
def _shortest_routes(map_rows=None):
    world = get_world(map_rows)
    out = []
    for g in world["exits"]:
        res = astar.astar(world["start"], g, world["walls"], world["rows"], world["cols"], lambda c: 1.0)
        if res:
            out.append(dict(res, exit=g))
    return out


def plan(observations, door_reading=None, cfg=Config(), use_hmm=True, use_bayes=True, map_rows=None):
    """Full pipeline. use_hmm / use_bayes switch parts off for the ablation study."""
    n = len(ZONE_NAMES)
    prior = [1.0 / n] * n
    obs = observations if use_hmm else []
    steps = hmm.filter_sequence(prior, transition_matrix(cfg), emission_matrix(cfg), obs)
    belief = steps[-1]["posterior"] if steps else prior
    zone_risk = cell_risk(belief, cfg)

    def risky_cost(cell):
        return 1.0 + cfg.risk_weight * zone_risk[zone_of(*cell)]

    world = get_world(map_rows)
    fast = dict(min(_shortest_routes(map_rows), key=lambda x: x["cost"]))
    other_exits = [g for g in world["exits"] if g != fast["exit"]]
    candidates = [dict(res, exit=g) for g in other_exits
                  if (res := astar.astar(world["start"], g, world["walls"], world["rows"], world["cols"], risky_cost))]
    safe = min(candidates, key=lambda x: x["cost"])
    for r in (fast, safe):
        r["steps"] = len(r["path"]) - 1
        r["risk"] = route_risk(r["path"], belief, cfg)

    reading = door_reading if use_bayes else None
    p_fast_blocked, evidence = bayes.door_update(fast["risk"], reading,
                                                 cfg.p_smoke_if_blocked, cfg.p_smoke_if_clear)
    model = mdp.build_mdp(fast["steps"], safe["steps"], safe["risk"], cfg)
    V, Q, iterations = mdp.value_iteration(model, cfg.gamma)
    action, values = mdp.decide(Q, p_fast_blocked)
    route = {"PROCEED": fast, "DETOUR": safe}.get(action)
    return {"world": world, "steps": steps, "belief": belief, "zone_risk": zone_risk,
            "fast": fast, "safe": safe, "door_reading": reading,
            "p_fast_prior": fast["risk"], "p_fast_posterior": p_fast_blocked,
            "evidence": evidence, "V": V, "Q": Q, "iterations": iterations,
            "action": action, "action_values": values, "route": route}
