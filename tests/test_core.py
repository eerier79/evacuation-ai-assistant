import pytest
from evacuation import hmm, bayes, astar, mdp
from evacuation.model import Config, parse_map, transition_matrix, emission_matrix, zone_of
from evacuation.planner import plan

QUIET = (False, False, False, False)
Z1_ALARM = (False, True, False, False)


def test_transition_rows_sum_to_one():
    for row in transition_matrix():
        assert sum(row) == pytest.approx(1.0)


def test_hmm_posterior_sums_to_one_and_alarm_raises_zone():
    steps = hmm.filter_sequence([0.25] * 4, transition_matrix(), emission_matrix(), [Z1_ALARM, Z1_ALARM])
    for s in steps:
        assert sum(s["posterior"]) == pytest.approx(1.0)
    assert max(range(4), key=lambda z: steps[-1]["posterior"][z]) == 1
    assert steps[-1]["posterior"][1] > steps[0]["posterior"][1] > 0.25


def test_bayes_known_value():
    post, evidence = bayes.posterior(0.3, 0.85, 0.15)
    assert post == pytest.approx(0.255 / 0.36)
    assert evidence == pytest.approx(0.36)


def test_bayes_clear_lowers_and_none_keeps_prior():
    assert bayes.door_update(0.3, "CLEAR", 0.85, 0.15)[0] < 0.3
    assert bayes.door_update(0.3, None, 0.85, 0.15)[0] == 0.3


def test_astar_shortest_path_length():
    w = parse_map()
    res = astar.astar(w["start"], (0, 5), w["walls"], w["rows"], w["cols"], lambda c: 1.0)
    assert len(res["path"]) - 1 == 4
    assert res["path"][0] == w["start"] and res["path"][-1] == (0, 5)


def test_astar_avoids_risky_cells():
    w = parse_map()
    cost = lambda c: 1.0 + 50.0 * (zone_of(*c) == 0)
    res = astar.astar(w["start"], (7, 2), w["walls"], w["rows"], w["cols"], cost)
    assert all(zone_of(*c) != 0 for c in res["path"][1:])


def test_astar_no_path_returns_none():
    walls = {(0, 1), (1, 0), (1, 1)}
    assert astar.astar((0, 0), (2, 2), walls, 3, 3, lambda c: 1.0) is None


def test_mdp_extremes():
    cfg = Config()
    model = mdp.build_mdp(4, 6, 0.155, cfg)
    V, Q, _ = mdp.value_iteration(model, cfg.gamma)
    assert mdp.decide(Q, 0.0)[0] == "PROCEED"
    assert mdp.decide(Q, 1.0)[0] == "DETOUR"


def test_plan_all_quiet_proceeds_to_nearest_exit():
    r = plan([QUIET, QUIET], "CLEAR")
    assert r["action"] == "PROCEED" and r["route"]["exit"] == (0, 5)


def test_plan_fire_in_z1_and_smoke_at_door_detours():
    r = plan([Z1_ALARM, Z1_ALARM], "SMOKE")
    assert r["action"] == "DETOUR" and r["route"]["exit"] == (7, 2)
    assert all(zone_of(*c) != 1 for c in r["route"]["path"][1:])


def test_plan_fire_in_z1_but_door_clear_still_detours():
    assert plan([Z1_ALARM, Z1_ALARM], "CLEAR")["action"] == "DETOUR"


def test_plan_fire_far_from_fast_route_proceeds():
    assert plan([(False, False, False, True)] * 2, "CLEAR")["action"] == "PROCEED"


def test_wait_has_no_route():
    r = plan([], None)
    if r["action"] == "WAIT":
        assert r["route"] is None
    else:
        assert r["route"] is not None


def test_route_risk_is_probability():
    from evacuation.planner import route_risk
    r = plan([Z1_ALARM, Z1_ALARM], None)
    for route in (r["fast"], r["safe"]):
        assert 0.0 <= route_risk(route["path"], r["belief"]) <= 1.0
    assert r["fast"]["risk"] > r["safe"]["risk"]


def test_simulation_is_reproducible():
    from evacuation.simulate import evaluate, POLICIES
    p = POLICIES["Assistant (HMM + A* + Bayes + MDP)"]
    assert evaluate(p, 200, 5) == evaluate(p, 200, 5)


def test_assistant_beats_baselines_in_simulation():
    from evacuation.simulate import evaluate, POLICIES
    full = evaluate(POLICIES["Assistant (HMM + A* + Bayes + MDP)"], 2000, 11)
    shortest = evaluate("PROCEED", 2000, 11)
    no_hmm = evaluate(POLICIES["No HMM (ignores smoke sensors)"], 2000, 11)
    assert full["harm_rate"] < shortest["harm_rate"]
    assert full["utility"] > shortest["utility"]
    assert full["utility"] > no_hmm["utility"]


def test_explanation_names_the_decision_and_numbers():
    from evacuation.explain import why
    r = plan([Z1_ALARM, Z1_ALARM], "SMOKE")
    text = " ".join(why(r))
    assert "safe detour" in text and "93%" in text and "Z1" in text


def test_walkthrough_has_five_steps_matching_the_plan():
    from evacuation.explain import walkthrough
    r = plan([Z1_ALARM], "CLEAR")
    steps = walkthrough(r)
    assert [k for k, _, _ in steps] == ["sensors", "hmm", "astar", "bayes", "mdp"]
    assert r["action"] in steps[-1][2]


# ---------------------------------------------------------------- v6: new modules and property checks
import random as _random


def test_property_hmm_belief_is_a_distribution():
    from evacuation import hmm
    from evacuation.model import transition_matrix, emission_matrix
    rng = _random.Random(0)
    for _ in range(200):
        obs = [tuple(rng.random() < 0.4 for _ in range(4)) for _ in range(rng.randint(1, 6))]
        b = hmm.filter_sequence([0.25] * 4, transition_matrix(), emission_matrix(), obs)[-1]["posterior"]
        assert abs(sum(b) - 1) < 1e-9 and all(0 <= x <= 1 for x in b)


def test_property_bayes_moves_belief_the_right_way():
    from evacuation.bayes import door_update
    rng = _random.Random(1)
    for _ in range(200):
        p = rng.uniform(0.01, 0.99)
        assert door_update(p, "SMOKE", 0.85, 0.15)[0] > p > door_update(p, "CLEAR", 0.85, 0.15)[0]


def test_property_astar_matches_bfs_on_unit_costs():
    from collections import deque
    from evacuation.astar import astar
    rng = _random.Random(2)
    for _ in range(60):
        walls = {(r, c) for r in range(7) for c in range(7) if rng.random() < 0.25} - {(0, 0), (6, 6)}
        res = astar((0, 0), (6, 6), walls, 7, 7, lambda c: 1.0)
        dist, q = {(0, 0): 0}, deque([(0, 0)])
        while q:
            r, c = q.popleft()
            for nr, nc in ((r + 1, c), (r - 1, c), (r, c + 1), (r, c - 1)):
                if 0 <= nr < 7 and 0 <= nc < 7 and (nr, nc) not in walls and (nr, nc) not in dist:
                    dist[(nr, nc)] = dist[(r, c)] + 1
                    q.append((nr, nc))
        assert (res is None) == ((6, 6) not in dist)
        if res:
            assert len(res["path"]) - 1 == dist[(6, 6)]


def test_pomdp_extremes_and_qmdp_overvalues_waiting():
    from evacuation import pomdp
    assert pomdp.decide(4, 6, 0.174, 0.0)[0] == "PROCEED"
    assert pomdp.decide(4, 6, 0.174, 1.0)[0] == "DETOUR"
    sol = pomdp.solve(4, 6, 0.174)
    grid, q = pomdp.qmdp_curves(4, 6, 0.174, n=len(sol["grid"]))
    # QMDP assumes waiting reveals the state, so it never values WAIT below the exact POMDP
    assert all(a >= b - 1e-6 for a, b in zip(q["WAIT"], sol["Q"]["WAIT"]))


def test_wait_outcome_probabilities_sum_to_one():
    from evacuation.pomdp import wait_outcomes
    from evacuation.model import Config
    for p in (0.0, 0.3, 0.9):
        assert abs(sum(pr for pr, _ in wait_outcomes(p, Config())) - 1) < 1e-9


def test_common_random_numbers_same_fire_for_every_policy():
    from evacuation.simulate import run_many
    a = run_many("PROCEED", 50, 4)
    b = run_many("DETOUR", 50, 4)
    assert [x["true_fire_zone"] for x in a] == [x["true_fire_zone"] for x in b]


def test_paired_bootstrap_interval_contains_mean():
    from evacuation.simulate import run_many, paired_bootstrap, ASSISTANT
    ci = paired_bootstrap(run_many(ASSISTANT, 300, 9), run_many("PROCEED", 300, 9), B=300)
    assert ci["low"] <= ci["mean"] <= ci["high"]


def test_assistant_still_beats_naive_baselines_when_model_is_wrong():
    from dataclasses import replace
    from evacuation.model import Config
    from evacuation.simulate import evaluate, ASSISTANT, ROBUSTNESS
    world = replace(Config(), **ROBUSTNESS["Everything worse"])
    assert evaluate(ASSISTANT, 1500, 3, Config(), world)["utility"] > evaluate("PROCEED", 1500, 3, Config(), world)["utility"]


def test_baum_welch_recovers_parameters_and_likelihood_rises():
    from evacuation.learn import generate, baum_welch, tied_summary
    data, _ = generate(150, 20, seed=5)
    res = baum_welch(data, 15)
    assert all(b >= a - 1e-6 for a, b in zip(res["loglik"], res["loglik"][1:]))
    est = tied_summary(res["T"], res["E"])
    assert abs(est["alarm_same"] - 0.9) < 0.05 and abs(est["p_stay"] - 0.7) < 0.06


def test_q_learning_learns_something_useful():
    from evacuation.qlearn import train, evaluate_learned
    from evacuation.simulate import evaluate
    Q, curve = train(episodes=8000, window=1000)
    assert evaluate_learned(Q, 1500, 1)["utility"] > evaluate("PROCEED", 1500, 1)["utility"]
    assert curve[-1]["avg_utility"] > curve[0]["avg_utility"]
