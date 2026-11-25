# Evaluation (5000 simulated fires per policy, seed 2026)

| Policy | Harm rate | Mean time | Utility | Waited |
|---|---|---|---|---|
| Assistant (HMM + A* + Bayes + MDP) | 0.112 ± 0.004 | 4.87 | 50.5 ± 1.8 | 0.081 |
| No HMM (ignores smoke sensors) | 0.188 ± 0.006 | 6.39 | 18.3 ± 2.2 | 0.325 |
| No Bayes (ignores door camera) | 0.141 ± 0.005 | 4.85 | 38.6 ± 2.0 | 0.080 |
| No MDP, threshold 0.5 (hand-tuned) | 0.113 ± 0.004 | 4.53 | 50.1 ± 1.8 | 0.000 |
| No MDP, threshold 0.2 | 0.118 ± 0.005 | 4.88 | 48.0 ± 1.8 | 0.000 |
| No MDP, threshold 0.8 | 0.129 ± 0.005 | 4.30 | 43.9 ± 1.9 | 0.000 |
| Always shortest route | 0.197 ± 0.006 | 4.00 | 17.2 ± 2.3 | 0.000 |
| Always safe detour | 0.330 ± 0.007 | 6.66 | -38.7 ± 2.7 | 0.000 |

## Sensitivity to sensor quality

| P(alarm, same zone) | Assistant harm | Always shortest harm |
|---|---|---|
| 0.55 | 0.130 | 0.190 |
| 0.65 | 0.113 | 0.190 |
| 0.75 | 0.117 | 0.190 |
| 0.85 | 0.113 | 0.190 |
| 0.95 | 0.103 | 0.190 |
