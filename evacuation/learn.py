"""Learning the HMM from data: Baum-Welch (EM) on logs of the 4 smoke sensors.

The question it answers: "where do 0.9 / 0.3 / 0.7 come from?". We generate sensor logs from a
'true' model, hide the fire zones, and let EM estimate the transition matrix T and the alarm
probabilities E from the alarms alone. If the estimates come back close to the truth, the same
procedure could fit the model to real sensor logs.
"""
import math
import random

from .model import Config, transition_matrix, emission_matrix, ZONE_ADJACENT
from .simulate import _sample


def generate(n_seq=300, length=20, cfg=Config(), seed=0):
    """Sensor logs (lists of 4-bool tuples) plus the hidden zones (kept only for checking)."""
    rng = random.Random(seed)
    T, E = transition_matrix(cfg), emission_matrix(cfg)
    data, zones = [], []
    for _ in range(n_seq):
        z, seq, zs = rng.randrange(4), [], []
        for _ in range(length):
            z = _sample(rng, T[z])
            zs.append(z)
            seq.append(tuple(rng.random() < E[k][z] for k in range(4)))
        data.append(seq)
        zones.append(zs)
    return data, zones


def _emit(E, obs, z):
    p = 1.0
    for k, o in enumerate(obs):
        p *= E[k][z] if o else 1.0 - E[k][z]
    return p


def _forward_backward(seq, pi, T, E):
    n, L = len(pi), len(seq)
    alpha, scale = [], []
    a = [pi[z] * _emit(E, seq[0], z) for z in range(n)]
    for t in range(L):
        if t:
            a = [sum(alpha[-1][i] * T[i][j] for i in range(n)) * _emit(E, seq[t], j) for j in range(n)]
        c = sum(a)
        a = [x / c for x in a]
        alpha.append(a)
        scale.append(c)
    beta = [[1.0] * n for _ in range(L)]
    for t in range(L - 2, -1, -1):
        e = [_emit(E, seq[t + 1], j) for j in range(n)]
        beta[t] = [sum(T[i][j] * e[j] * beta[t + 1][j] for j in range(n)) / scale[t + 1] for i in range(n)]
    return alpha, beta, scale


def baum_welch(data, iterations=30, seed=1):
    """EM for T (4x4), E (sensor x zone) and the start distribution pi.
    Initialisation is anchored (sensor k slightly prefers zone k) so state k keeps meaning 'fire in zone k'."""
    rng = random.Random(seed)
    n = 4
    pi = [0.25] * n
    T = [[rng.uniform(0.5, 1.5) for _ in range(n)] for _ in range(n)]
    T = [[x / sum(row) for x in row] for row in T]
    E = [[0.6 if k == z else 0.35 for z in range(n)] for k in range(n)]
    history = []
    for _ in range(iterations):
        A = [[1e-9] * n for _ in range(n)]
        G = [0.0] * n
        G_all = [1e-9] * n
        Ek = [[1e-9] * n for _ in range(n)]
        P0 = [1e-9] * n
        loglik = 0.0
        for seq in data:
            alpha, beta, scale = _forward_backward(seq, pi, T, E)
            loglik += sum(math.log(c) for c in scale)
            for t, obs in enumerate(seq):
                gamma = [alpha[t][z] * beta[t][z] for z in range(n)]
                s = sum(gamma)
                gamma = [g / s for g in gamma]
                if t == 0:
                    P0 = [p + g for p, g in zip(P0, gamma)]
                for z in range(n):
                    G_all[z] += gamma[z]
                    for k in range(4):
                        if obs[k]:
                            Ek[k][z] += gamma[z]
                    if t < len(seq) - 1:
                        G[z] += gamma[z]
                if t < len(seq) - 1:
                    e = [_emit(E, seq[t + 1], j) for j in range(n)]
                    for i in range(n):
                        for j in range(n):
                            A[i][j] += alpha[t][i] * T[i][j] * e[j] * beta[t + 1][j] / scale[t + 1]
        T = [[A[i][j] / sum(A[i]) for j in range(n)] for i in range(n)]
        E = [[min(0.999, max(0.001, Ek[k][z] / G_all[z])) for z in range(n)] for k in range(n)]
        pi = [p / sum(P0) for p in P0]
        history.append(loglik)
    return {"T": T, "E": E, "pi": pi, "loglik": history}


def tied_summary(T, E):
    """Average the learned matrices back into the model's few parameters, for comparison with Config."""
    n = 4
    same = [E[k][k] for k in range(n)]
    adj = [E[k][z] for k in range(n) for z in range(n) if z in ZONE_ADJACENT[k]]
    far = [E[k][z] for k in range(n) for z in range(n) if z != k and z not in ZONE_ADJACENT[k]]
    return {"p_stay": sum(T[i][i] for i in range(n)) / n, "alarm_same": sum(same) / len(same),
            "alarm_adjacent": sum(adj) / len(adj), "alarm_far": sum(far) / len(far)}


def learning_experiment(sizes=(25, 100, 400), length=20, iterations=25, seed=0):
    """Estimation error of each parameter as the amount of data grows."""
    truth = Config()
    rows = []
    for m in sizes:
        data, _ = generate(m, length, truth, seed)
        est = tied_summary(**{k: v for k, v in baum_welch(data, iterations).items() if k in ("T", "E")})
        rows.append({"sequences": m, **est})
    return rows, {"p_stay": truth.p_stay, "alarm_same": truth.alarm_same,
                  "alarm_adjacent": truth.alarm_adjacent, "alarm_far": truth.alarm_far}
