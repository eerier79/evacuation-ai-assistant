# Demo video script (target 2:45)

Before recording: open a terminal in the project folder and start the app (`python -m streamlit run app.py`). Record the screen with the microphone on (Win+G or OBS).

**0:00 – 0:20  Problem**
"Hello, I am Yernur Baltabay. My project is an Emergency Evacuation Assistant. In a fire, smoke sensors are noisy and the fire moves, so the shortest way out can be the most dangerous. The assistant decides: proceed, detour or wait."

**0:20 – 0:40  Idea (slide 3)**
"It combines four AI topics. An HMM estimates where the fire is. A* finds a fast route and a safe route. Bayes' theorem updates the danger of the fast route with the door camera. An MDP chooses the best action."

**0:40 – 0:55  Tests (terminal)**
Run `python -m pytest`. "Sixteen tests check every algorithm, the full scenarios and the simulator. All pass."

**0:55 – 1:45  Planner tab**
1. No alarms, camera CLEAR, press Add sensor step → PROCEED. "All quiet: take the shortest way."
2. Reset. Tick Z1, press Add sensor step twice, camera SMOKE → DETOUR. "The HMM is 97.6% sure the fire is in zone Z1. The fast route has a 0.687 chance to be blocked, the smoke reading raises it to 0.925, and the MDP values say DETOUR."
3. Switch the camera to CLEAR. "Even with a clear camera the fire evidence keeps the fast route risky, so DETOUR still wins."
4. Turn on "Colour cells by risk". "Here is the risk map that A* uses."

**1:45 – 2:05  Simulation tab**
Change the seed two or three times. "One random fire. The assistant only sees the noisy sensors; the real fire is shown so we can check the decision."

**2:05 – 2:30  Evaluation tab**
"On thousands of simulated fires the assistant lowers the harm rate from about 20% for always taking the shortest route to about 11%. Removing the HMM or the Bayes update makes it clearly worse, so every algorithm contributes."

**2:30 – 2:45  Conclusion**
"All probabilities are assumptions, and the MDP is a simplification of a POMDP. Code, tests, evaluation and report are in my GitHub repository. Thank you."
