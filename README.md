# Emergency Evacuation Assistant

AI Fundamentals final project (QAIRU). Single author: Yernur Baltabay.

A person stands at S on an 8x8 building map with two exits. Smoke sensors give noisy alarms about a hidden fire. The program decides whether to take the fast route, take a safer detour, or wait.

## AI topics and how they work together
| Topic | File | Role |
|---|---|---|
| Hidden Markov Model | `evacuation/hmm.py` | Filters the hidden fire zone from 4 noisy smoke sensors |
| Bayes' theorem | `evacuation/bayes.py` | Updates P(fast route blocked) with the door camera reading |
| A* search | `evacuation/astar.py` | Finds the fast route and a risk-aware safe route (cell cost = 1 + 10 * P(blocked)) |
| MDP (value iteration) | `evacuation/mdp.py` | Chooses PROCEED / DETOUR / WAIT by expected value |

Chain: sensors -> HMM belief -> cell risk -> A* routes -> Bayes with door camera -> MDP decision (`evacuation/planner.py`).

## Run
```
python -m pip install -r requirements.txt
python main.py                 # console demo, 3 scenarios
python -m pytest               # 12 tests
python -m streamlit run app.py # web UI
```

## Sample output (scenario 2: alarm in Z1 twice, door camera SMOKE)
```
HMM    belief: [0.012, 0.976, 0.000, 0.012] -> Z1 north-east
BAYES  P(fast route blocked): prior 0.687 -> posterior 0.925
MDP    expected value: {'PROCEED': -163.7, 'DETOUR': 43.8, 'WAIT': 21.5}
OUTPUT decision: DETOUR, go to exit (7, 2) via 6 steps
```

## Assumptions (all probabilities and rewards are assumed, not measured)
All numbers are in `evacuation/model.py` (`Config`): fire stays in its zone with 0.7, sensor alarm 0.90/0.30/0.05 for same/adjacent/far zone, door camera 0.85/0.15, rewards ARRIVE 100, HARM 300, WAIT cost 20, discount 0.9.

## Limitations
The MDP treats WAIT as a state-based action (an approximation of a POMDP), the map is fixed, and the model is a teaching example, not a real safety system.
