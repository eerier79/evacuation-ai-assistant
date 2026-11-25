"""Building map and all assumed probabilities (nothing here is measured data)."""
from dataclasses import dataclass

MAP = [
    "#####E##",
    "#......#",
    "#......#",
    "#####D##",
    "#....S.#",
    "#..###.#",
    "#......#",
    "##E#####",
]

ZONE_NAMES = ["Z0 north-west", "Z1 north-east", "Z2 south-west", "Z3 south-east"]
ZONE_ADJACENT = {0: {1, 2}, 1: {0, 3}, 2: {0, 3}, 3: {1, 2}}


def zone_of(row, col):
    return 2 * (row >= 4) + (col >= 4)


def parse_map(rows=MAP):
    walls, start, exits, door = set(), None, [], None
    for r, line in enumerate(rows):
        for c, ch in enumerate(line):
            if ch == "#":
                walls.add((r, c))
            elif ch == "S":
                start = (r, c)
            elif ch == "E":
                exits.append((r, c))
            elif ch == "D":
                door = (r, c)
    return {"rows": len(rows), "cols": len(rows[0]), "walls": walls,
            "start": start, "exits": exits, "door": door}


def pair_value(z1, z2, same, adjacent, far):
    if z1 == z2:
        return same
    return adjacent if z2 in ZONE_ADJACENT[z1] else far


@dataclass(frozen=True)
class Config:
    # HMM: the main fire zone stays or spreads to a neighbouring zone
    p_stay: float = 0.70
    # smoke sensor k (one per zone): P(alarm | fire in same / adjacent / far zone)
    alarm_same: float = 0.90
    alarm_adjacent: float = 0.30
    alarm_far: float = 0.05
    # P(a cell is blocked | fire in same / adjacent / far zone)
    block_same: float = 0.70
    block_adjacent: float = 0.15
    block_far: float = 0.02
    # Bayes: door camera reading about the fastest route
    p_smoke_if_blocked: float = 0.85
    p_smoke_if_clear: float = 0.15
    # A*: cost of entering a cell = 1 + risk_weight * P(blocked)
    risk_weight: float = 10.0
    # MDP
    arrive_reward: float = 100.0
    harm_penalty: float = 300.0
    harm_if_clear: float = 0.02
    harm_if_blocked: float = 0.70
    wait_cost: float = 20.0
    gamma: float = 0.90


def transition_matrix(cfg=Config()):
    n = len(ZONE_NAMES)
    move = (1.0 - cfg.p_stay) / 2.0
    return [[cfg.p_stay if i == j else (move if j in ZONE_ADJACENT[i] else 0.0)
             for j in range(n)] for i in range(n)]


def emission_matrix(cfg=Config()):
    """E[k][z] = P(sensor k raises an alarm | the fire is in zone z)."""
    n = len(ZONE_NAMES)
    return [[pair_value(z, k, cfg.alarm_same, cfg.alarm_adjacent, cfg.alarm_far)
             for z in range(n)] for k in range(n)]


def block_matrix(cfg=Config()):
    """B[z][w] = P(a cell in zone w is blocked | the fire is in zone z)."""
    n = len(ZONE_NAMES)
    return [[pair_value(z, w, cfg.block_same, cfg.block_adjacent, cfg.block_far)
             for w in range(n)] for z in range(n)]
