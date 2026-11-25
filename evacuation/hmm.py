"""HMM filtering: hidden state = zone of the main fire, observations = 4 smoke sensors."""
from math import prod


def predict(belief, T):
    n = len(belief)
    return [sum(belief[i] * T[i][j] for i in range(n)) for j in range(n)]


def likelihood(observation, E):
    """P(sensor readings | fire in zone z), sensors independent given the zone."""
    n = len(E)
    return [prod(E[k][z] if observation[k] else 1.0 - E[k][z] for k in range(len(observation)))
            for z in range(n)]


def update(predicted, lik):
    weights = [predicted[z] * lik[z] for z in range(len(predicted))]
    total = sum(weights)
    return [w / total for w in weights], weights, total


def filter_sequence(prior, T, E, observations):
    """Run predict -> update -> normalize for every observation; return all steps."""
    belief, steps = list(prior), []
    for obs in observations:
        pred = predict(belief, T)
        lik = likelihood(obs, E)
        belief, weights, total = update(pred, lik)
        steps.append({"observation": tuple(obs), "predicted": pred, "likelihood": lik,
                      "weights": weights, "total": total, "posterior": belief})
    return steps
