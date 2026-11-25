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
