"""POMDP solved in belief space (the exact problem behind the QMDP shortcut used by mdp.decide).

Hidden state: is the fast route LOW (clear) or HIGH (blocked)?   Belief: p = P(HIGH).
Actions:  PROCEED / DETOUR end the episode with the same rewards as the MDP.
          WAIT costs wait_cost, the route may become blocked (LOW -> HIGH with 0.3, HIGH stays HIGH),
          and then a new door-camera reading arrives (SMOKE 0.85 if blocked, 0.15 if clear).
The belief is one number in [0, 1], so value iteration runs on a grid of beliefs with linear interpolation.

Why it matters: QMDP assumes the hidden state becomes known after one step, so it can misjudge WAIT,
the only action whose value comes from new information. The POMDP prices that information correctly.
"""
from bisect import bisect_left
from functools import lru_cache

from .mdp import build_mdp, value_iteration
from .model import Config

P_GET_BLOCKED = 0.30   # same as the MDP's LOW -> HIGH transition under WAIT


def _interp(grid, values, p):
    if p <= 0.0:
        return values[0]
    if p >= 1.0:
        return values[-1]
    i = bisect_left(grid, p)
    x0, x1 = grid[i - 1], grid[i]
    return values[i - 1] + (values[i] - values[i - 1]) * (p - x0) / (x1 - x0)


def wait_outcomes(p, cfg):
    """[(probability of reading, belief after reading)] for the two camera readings after one WAIT."""
    pred = p + (1.0 - p) * P_GET_BLOCKED
    out = []
    for p_if_blocked, p_if_clear in ((cfg.p_smoke_if_blocked, cfg.p_smoke_if_clear),
                                     (1 - cfg.p_smoke_if_blocked, 1 - cfg.p_smoke_if_clear)):
        prob = pred * p_if_blocked + (1.0 - pred) * p_if_clear
        out.append((prob, pred * p_if_blocked / prob if prob > 0 else pred))
    return out


def solve(fast_length, alt_length, alt_blocked_prob, cfg=Config(), n=201, theta=1e-6):
    """Belief-space value iteration. Returns grid, V(p) and Q(p, a) for every action."""
    mdp = build_mdp(fast_length, alt_length, alt_blocked_prob, cfg)
    r_low, r_high = mdp[("LOW", "PROCEED")][0][2], mdp[("HIGH", "PROCEED")][0][2]
    r_detour = mdp[("LOW", "DETOUR")][0][2]
    grid = [i / (n - 1) for i in range(n)]
    outcomes = [wait_outcomes(p, cfg) for p in grid]
    proceed = [(1 - p) * r_low + p * r_high for p in grid]
    V = [max(a, r_detour) for a in proceed]
    iterations = 0
    while True:
        iterations += 1
        wait = [-cfg.wait_cost + cfg.gamma * sum(pr * _interp(grid, V, b) for pr, b in outcomes[i]) for i in range(n)]
        new_V = [max(proceed[i], r_detour, wait[i]) for i in range(n)]
        delta = max(abs(a - b) for a, b in zip(new_V, V))
        V = new_V
        if delta < theta:
            break
    return {"grid": grid, "V": V, "iterations": iterations,
            "Q": {"PROCEED": proceed, "DETOUR": [r_detour] * n, "WAIT": wait}}


@lru_cache(maxsize=4096)
def _solve_cached(fast_length, alt_length, alt_blocked_key, cfg):
    return solve(fast_length, alt_length, alt_blocked_key / 1000.0, cfg)


def decide(fast_length, alt_length, alt_blocked_prob, p, cfg=Config()):
    """POMDP action for belief p (the solution is cached per route situation)."""
    sol = _solve_cached(fast_length, alt_length, round(alt_blocked_prob * 1000), cfg)
    values = {a: _interp(sol["grid"], q, p) for a, q in sol["Q"].items()}
    return max(values, key=values.get), values


def qmdp_curves(fast_length, alt_length, alt_blocked_prob, cfg=Config(), n=101):
    """QMDP expected value of each action as a function of p (for the decision-boundary chart)."""
    V, Q, _ = value_iteration(build_mdp(fast_length, alt_length, alt_blocked_prob, cfg), cfg.gamma)
    grid = [i / (n - 1) for i in range(n)]
    return grid, {a: [(1 - p) * Q[("LOW", a)] + p * Q[("HIGH", a)] for p in grid] for a in ("PROCEED", "DETOUR", "WAIT")}


def boundaries(grid, curves):
    """Beliefs where the best action changes: [(p, old action, new action)]."""
    best = [max(curves, key=lambda a: curves[a][i]) for i in range(len(grid))]
    return [(round((grid[i - 1] + grid[i]) / 2, 3), best[i - 1], best[i]) for i in range(1, len(grid)) if best[i] != best[i - 1]]
