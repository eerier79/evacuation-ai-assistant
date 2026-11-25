# Evaluation (5000 simulated fires per policy, seed 2026, common random numbers)

| Policy | Harm rate | Mean time | Utility | Waited |
|---|---|---|---|---|
| Assistant (HMM + A* + Bayes + MDP) | 0.115 ± 0.005 | 4.91 | 49.3 ± 1.8 | 0.091 |
| Assistant with exact POMDP | 0.112 ± 0.004 | 4.72 | 50.6 ± 1.8 | 0.020 |
| No HMM (ignores smoke sensors) | 0.190 ± 0.006 | 6.54 | 17.5 ± 2.2 | 0.342 |
| No Bayes (ignores door camera) | 0.137 ± 0.005 | 4.83 | 40.4 ± 1.9 | 0.076 |
| No MDP, threshold 0.5 (hand-tuned) | 0.120 ± 0.005 | 4.51 | 47.6 ± 1.8 | 0.000 |
| No MDP, threshold 0.2 | 0.124 ± 0.005 | 4.90 | 45.6 ± 1.9 | 0.000 |
| No MDP, threshold 0.8 | 0.130 ± 0.005 | 4.30 | 43.7 ± 1.9 | 0.000 |
| Always shortest route | 0.195 ± 0.006 | 4.00 | 18.0 ± 2.2 | 0.000 |
| Always safe detour | 0.337 ± 0.007 | 6.64 | -41.4 ± 2.7 | 0.000 |
| Q-learning (30000 training fires) | 0.121 ± 0.005 | 4.96 | 46.6 ± 1.9 | 0.107 |

## Paired bootstrap: assistant minus other policy (95% CI)

| Other policy | Utility difference | Harm difference |
|---|---|---|
| Assistant with exact POMDP | -1.4 [-2.8, -0.0] | +0.003 [-0.000, +0.007] |
| No HMM (ignores smoke sensors) | +31.7 [+28.2, +35.2] | -0.075 [-0.084, -0.067] |
| No Bayes (ignores door camera) | +8.9 [+6.5, +11.5] | -0.022 [-0.029, -0.017] |
| No MDP, threshold 0.5 (hand-tuned) | +1.7 [-0.3, +3.6] | -0.005 [-0.010, -0.000] |
| No MDP, threshold 0.2 | +3.7 [+1.3, +6.1] | -0.009 [-0.015, -0.003] |
| No MDP, threshold 0.8 | +5.6 [+3.4, +7.8] | -0.015 [-0.021, -0.010] |
| Always shortest route | +31.3 [+27.9, +34.9] | -0.080 [-0.089, -0.072] |
| Always safe detour | +90.7 [+85.8, +96.4] | -0.222 [-0.237, -0.210] |

## Robustness: harm rate when the real world differs from the model

| World | Assistant | No MDP, threshold 0.5 | Always shortest route | Always safe detour |
|---|---|---|---|---|
| Model is right | 0.109 | 0.112 | 0.205 | 0.336 |
| Sensors worse than assumed | 0.121 | 0.114 | 0.205 | 0.336 |
| Fire spreads faster | 0.106 | 0.099 | 0.191 | 0.339 |
| Camera worse than assumed | 0.129 | 0.149 | 0.205 | 0.336 |
| Everything worse | 0.149 | 0.145 | 0.191 | 0.339 |

## Sensitivity to sensor quality

| P(alarm, same zone) | Assistant harm | Always shortest harm |
|---|---|---|
| 0.55 | 0.118 | 0.188 |
| 0.65 | 0.116 | 0.188 |
| 0.75 | 0.112 | 0.188 |
| 0.85 | 0.108 | 0.188 |
| 0.95 | 0.102 | 0.188 |

## Baum-Welch: parameters learned from sensor logs (20 steps per log)

| Logs | p_stay | alarm_same | alarm_adjacent | alarm_far |
|---|---|---|---|---|
| 25 | 0.712 | 0.897 | 0.284 | 0.052 |
| 100 | 0.697 | 0.904 | 0.288 | 0.069 |
| 400 | 0.707 | 0.899 | 0.296 | 0.054 |
| **true** | 0.700 | 0.900 | 0.300 | 0.050 |
