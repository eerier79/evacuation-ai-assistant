# Emergency Evacuation Assistant

![tests](https://github.com/eerier79/evacuation-ai-assistant/actions/workflows/tests.yml/badge.svg)

AI Fundamentals final project (QAIRU). Individual project by Yernur Baltabay.

A person stands at **S** on an 8x8 building map with two exits. Four smoke sensors give noisy alarms about a hidden, moving fire, and a camera watches the door on the shortest route. The assistant decides: **PROCEED** on the fast route, **DETOUR** on a safe route, or **WAIT** for more information.

## Four AI topics in one pipeline
```
smoke sensors ──► HMM filtering ──► belief b(z) ──► cell risk ──► risk-aware A* ──► fast + safe routes
                                                                     │
door camera ───────────────────────────► Bayes' theorem ◄── P(fast route blocked)
                                                │
                                         posterior p ──► MDP (value iteration) ──► PROCEED / DETOUR / WAIT
```
| Topic | File | Role |
|---|---|---|
| Hidden Markov Model | `evacuation/hmm.py` | Filters the hidden fire zone from 4 noisy sensors (predict → update → normalize) |
| A* search | `evacuation/astar.py` | Cell cost = 1 + 10·P(blocked), admissible Manhattan heuristic |
| Bayes' theorem | `evacuation/bayes.py` | Updates P(fast route blocked) with the door camera reading |
| MDP + value iteration | `evacuation/mdp.py` | Chooses the action with the highest expected value under the Bayes belief |
| Integration | `evacuation/planner.py` | The full chain; exact route risk P(blocked) = Σ_z b(z)·(1 − Π_w (1 − B[z][w])) |
| Simulator | `evacuation/simulate.py` | Random fires, noisy sensors, persistent spreading blockages, policies |

## Run
```
python -m pip install -r requirements.txt
python main.py                  # console demo (input → calculation → output)
python -m pytest                # 16 tests
python evaluate.py              # Monte Carlo evaluation → results/
python -m streamlit run app.py  # web UI: Planner, Simulation, Evaluation, How it works
```

## Results (5000 simulated fires per policy, seed 2026)
| Policy | Harm rate | Mean time | Utility |
|---|---|---|---|
| **Assistant (HMM + A* + Bayes + MDP)** | **0.112 ± 0.004** | 4.87 | **50.5 ± 1.8** |
| No HMM (ignores smoke sensors) | 0.188 ± 0.006 | 6.39 | 18.3 ± 2.2 |
| No Bayes (ignores door camera) | 0.141 ± 0.005 | 4.85 | 38.6 ± 2.0 |
| No MDP, threshold 0.5 (hand-tuned) | 0.113 ± 0.004 | 4.53 | 50.1 ± 1.8 |
| No MDP, threshold 0.2 | 0.118 ± 0.005 | 4.88 | 48.0 ± 1.8 |
| No MDP, threshold 0.8 | 0.129 ± 0.005 | 4.30 | 43.9 ± 1.9 |
| Always shortest route | 0.197 ± 0.006 | 4.00 | 17.2 ± 2.3 |
| Always safe detour | 0.330 ± 0.007 | 6.66 | −38.7 ± 2.7 |

![policies](results/policies.png)

Findings:
- The assistant cuts the harm rate from 19.7% (always shortest) to 11.2%.
- **Ablation:** removing the HMM or the Bayes update makes results clearly worse, so each part contributes.
- The MDP matches the best hand-tuned threshold, but it derives the decision boundary from the rewards; badly chosen thresholds (0.2, 0.8) are worse.
- Better sensors → lower harm (`results/sensitivity.png`).

## Sample console output (alarm in Z1 twice, door camera SMOKE)
```
HMM    belief about the fire zone: [0.012, 0.976, 0.000, 0.012] -> Z1 north-east
BAYES  P(fast route blocked): prior 0.687 -> posterior 0.925
MDP    expected value: {'PROCEED': -163.7, 'DETOUR': 38.7, 'WAIT': 17.1}
OUTPUT decision: DETOUR, go to exit (7, 2) via 6 steps
```

## Assumptions
All numbers are in `evacuation/model.py` (`Config`) and are assumed, not measured: fire stays in its zone 0.7; sensor alarm 0.90 / 0.30 / 0.05 (same / adjacent / far zone); blockage 0.70 / 0.15 / 0.02; camera 0.85 / 0.15; rewards ARRIVE 100, HARM 300, WAIT cost 20, γ = 0.9.

## Limitations
- Probabilities are assumptions; real data would be needed to fit them.
- The MDP mixes Q-values with the Bayes belief (a QMDP-style approximation of a POMDP).
- Fixed map with two exits; within a zone all cells have the same risk.

## Documents
`docs/Technical_Report.docx`, `docs/Presentation.pptx`, `docs/Video_Script.md`, `AI_USAGE_DECLARATION.md`, `TEAM_CONTRIBUTION.md`
