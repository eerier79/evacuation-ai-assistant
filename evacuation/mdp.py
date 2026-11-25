"""MDP: state of the fastest route (LOW / HIGH danger), actions PROCEED / DETOUR / WAIT."""

STATES = ("LOW", "HIGH", "DONE")
ACTIONS = ("PROCEED", "DETOUR", "WAIT")


def expected_harm(p_blocked, cfg):
    return cfg.harm_if_clear * (1.0 - p_blocked) + cfg.harm_if_blocked * p_blocked


def trip_reward(length, harm_probability, cfg):
    return -length + cfg.arrive_reward * (1.0 - harm_probability) - cfg.harm_penalty * harm_probability


def build_mdp(fast_length, alt_length, alt_blocked_prob, cfg):
    """Return {(state, action): [(probability, next_state, reward), ...]}."""
    alt_reward = trip_reward(alt_length, expected_harm(alt_blocked_prob, cfg), cfg)
    mdp = {}
    for s, harm in (("LOW", cfg.harm_if_clear), ("HIGH", cfg.harm_if_blocked)):
        mdp[(s, "PROCEED")] = [(1.0, "DONE", trip_reward(fast_length, harm, cfg))]
        mdp[(s, "DETOUR")] = [(1.0, "DONE", alt_reward)]
    mdp[("LOW", "WAIT")] = [(0.70, "LOW", -cfg.wait_cost), (0.30, "HIGH", -cfg.wait_cost)]
    mdp[("HIGH", "WAIT")] = [(1.0, "HIGH", -cfg.wait_cost)]
    for a in ACTIONS:
        mdp[("DONE", a)] = [(1.0, "DONE", 0.0)]
    return mdp


def q_value(mdp, V, s, a, gamma):
    return sum(p * (r + gamma * V[s2]) for p, s2, r in mdp[(s, a)])


def value_iteration(mdp, gamma, theta=1e-8):
    """Repeat the Bellman update until the largest change is below theta."""
    V = {s: 0.0 for s in STATES}
    iterations = 0
    while True:
        iterations += 1
        new_V = {s: max(q_value(mdp, V, s, a, gamma) for a in ACTIONS) for s in STATES}
        delta = max(abs(new_V[s] - V[s]) for s in STATES)
        V = new_V
        if delta < theta:
            break
    Q = {(s, a): q_value(mdp, V, s, a, gamma) for s in STATES for a in ACTIONS}
    return V, Q, iterations


def decide(Q, p_high):
    """Expected value of every action when P(route is HIGH danger) = p_high."""
    values = {a: (1.0 - p_high) * Q[("LOW", a)] + p_high * Q[("HIGH", a)] for a in ACTIONS}
    best = max(values, key=values.get)
    return best, values
