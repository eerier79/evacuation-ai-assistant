"""Bayes' theorem for one binary hypothesis (route blocked) and one sensor reading."""


def posterior(prior, p_reading_if_true, p_reading_if_false):
    score_true = prior * p_reading_if_true
    score_false = (1.0 - prior) * p_reading_if_false
    evidence = score_true + score_false
    if evidence == 0:
        raise ValueError("The reading has probability zero under both hypotheses.")
    return score_true / evidence, evidence


def door_update(prior_blocked, reading, p_smoke_if_blocked, p_smoke_if_clear):
    """reading: 'SMOKE', 'CLEAR' or None (no reading, the prior is kept)."""
    if reading is None:
        return prior_blocked, None
    if reading == "SMOKE":
        return posterior(prior_blocked, p_smoke_if_blocked, p_smoke_if_clear)
    if reading == "CLEAR":
        return posterior(prior_blocked, 1.0 - p_smoke_if_blocked, 1.0 - p_smoke_if_clear)
    raise ValueError("reading must be 'SMOKE', 'CLEAR' or None")
