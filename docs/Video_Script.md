# Demo video script (target 2:50)

Before recording: start the app (`python -m streamlit run app.py`), open the Evaluation page once so the numbers are
cached, dismiss any Streamlit pop-up, and record the screen with the microphone on (Win+G or OBS).

**0:00 – 0:15  Problem (Home page)**
Drag the 3D Kitty once. "Hello, I am Yernur Baltabay. Kitty is trapped in a burning house. Smoke alarms are noisy and
the fire moves, so the shortest way out can be the most dangerous. My assistant decides: proceed, detour or wait."

**0:15 – 0:35  Idea (How it works or slide 3)**
"Four AI topics work as one pipeline. An HMM estimates where the fire is. A* finds a fast and a safe route. Bayes'
theorem updates the danger of the fast route with the door camera. An MDP picks the action with the best expected score."

**0:35 – 1:20  Planner**
1. Click the scenario **All quiet · camera CLEAR** → PROCEED. "All quiet: take the shortest way."
2. Click **Fire in Z1 · camera SMOKE** → DETOUR. Read one line of *Why this decision?*: "The HMM is 98% sure the fire is
   in Z1, the camera raises the risk of the fast route from 69 to 93 percent, so Kitty detours." Point at the red zone on the map.
3. Click **One alarm in Z1 · camera CLEAR** → WAIT. Show the **Decision boundary** chart: "Kitty is in the zone where waiting is best."
4. Switch **Decision method** to **Exact POMDP**: "The exact POMDP knows waiting can make things worse, so it detours. QMDP over-values waiting."

**1:20 – 1:45  You vs AI**
Play one fire: choose an action, show both results side by side. "Same fire, same luck: I can compare my choice with the AI."

**1:45 – 2:25  Evaluation**
- Policies tab: "On 5000 simulated fires the assistant lowers harm from 19.5% to 11.5%."
- Statistics tab: "Paired confidence intervals: without the HMM or Bayes the assistant is clearly worse; against the best hand-tuned threshold it is a tie, but the MDP needs no tuning."
- Robustness tab: "Even when the real world is worse than my model, it stays far better than the naive strategies."
- Learning the HMM tab: "Baum-Welch learns my probabilities back from alarm logs alone."

**2:25 – 2:50  Conclusion**
"The probabilities are assumptions, but I tested what happens when they are wrong and showed how to learn them from
data. 28 tests pass on GitHub Actions. Code, report and every version are in my repository. Thank you."
