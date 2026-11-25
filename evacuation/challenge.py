"""'You vs AI' game: the player and the assistant face exactly the same fire (same seed, same luck)."""
from .model import Config
from .planner import plan
from .simulate import ASSISTANT, MAX_WAITS, play, run_episode


def player_round(seed, actions, cfg=Config()):
    """Replay the player's actions so far. Returns a 'pending' state (needs a click) or the final outcome."""
    def decide(observations, door, waited):
        r = plan(observations, door, cfg)
        return (actions[waited] if waited < len(actions) else None), r
    return play(seed, decide, cfg)


def ai_round(seed, cfg=Config()):
    log = []
    out = run_episode(ASSISTANT, seed, cfg, log=log)
    out["log"] = log
    return out


def can_wait(state):
    return state.get("waited", 0) < MAX_WAITS
