# Defense preparation: likely questions and short answers

## The problem and the idea
**Why these algorithms?** Each answers one question of the evacuation: where is the fire (HMM), which roads exist
(A*), what does the camera add (Bayes), what should Kitty do (MDP). The output of one is the input of the next.

**What is the common goal?** One safe evacuation decision. Removing any algorithm breaks the chain, and the ablation
study measures how much each part contributes.

## HMM
**What is hidden and what is observed?** Hidden: the zone of the fire (4 values). Observed: four alarms (on/off).

**How does one filtering step work?** Predict with the transition matrix (stay 0.7, neighbour 0.15), multiply by the
likelihood of the alarms (product of four sensor probabilities), normalise so the belief sums to 1.

**Why multiply the four sensor probabilities?** Given the fire zone, the sensors are assumed independent (naive
assumption). Example: fire in Z1 and only Z1 rings: 0.9 × 0.7 × 0.7 × 0.95 = 0.419.

**Where do 0.9 / 0.3 / 0.7 come from?** They are assumptions. Baum-Welch (EM) shows they can be learned from alarm logs:
with 100 logs it recovers 0.70 / 0.90 / 0.29 / 0.07 (true 0.70 / 0.90 / 0.30 / 0.05).

## A*
**Why is the heuristic admissible?** Manhattan distance never overestimates, because every step costs at least 1
(cost = 1 + 10 × risk ≥ 1). So A* returns the cheapest route.

**Why two routes?** The fast route is the shortest path; the safe route is the cheapest path to another exit when risky
cells cost more. The MDP then chooses between them.

## Bayes
**Formula?** P(blocked | SMOKE) = P(SMOKE | blocked) · P(blocked) / P(SMOKE), with
P(SMOKE) = 0.85 · P(blocked) + 0.15 · (1 − P(blocked)). Example: 0.687 → 0.925 on SMOKE, 0.687 → 0.279 on CLEAR.

**Where does the prior come from?** From the HMM belief: the exact probability that any zone on the fast route is blocked.

## MDP and POMDP
**States, actions, rewards?** LOW / HIGH / DONE; PROCEED / DETOUR / WAIT; +100 escape, −300 hurt, −1 per step,
−20 for waiting; γ = 0.9; solved by value iteration.

**The state is not observed. Isn't this a POMDP?** Yes. The main pipeline uses QMDP: value(a) = (1 − p) Q(LOW, a) + p Q(HIGH, a).
I also solved the exact POMDP in belief space (value iteration on 201 beliefs). QMDP assumes waiting reveals the truth,
so it over-values WAIT (a test checks QMDP's WAIT value is never below the POMDP's). The POMDP waits in 2% of fires
instead of 9% and scores 1.4 points more (paired CI [0.0, 2.8]).

**The MDP does not beat the best threshold. Why use it?** It ties with the best hand-tuned threshold (0.5) but finds
the boundary from the rewards with no tuning; thresholds 0.2 and 0.8 are significantly worse. If the rewards change,
the MDP adapts automatically; a threshold would have to be tuned again.

## Evaluation
**How do you know the differences are real?** Every policy meets the same 5000 fires (common random numbers), and I use
paired bootstrap 95% confidence intervals. Without HMM: +31.7 utility [28.2, 35.2]; without Bayes: +8.9 [6.5, 11.5].

**The simulator uses your own assumptions. Isn't that circular?** Partly, so I added a model-mismatch test: the world
has worse sensors, a faster fire and a worse camera while the assistant keeps its old model. Harm rises from 0.109 to
0.149 but stays far below always taking the shortest route (0.191).

**Why compare with Q-learning?** To show the value of a model: Q-learning needs 30 000 simulated fires to reach 46.6
utility; the MDP gets 49.3 immediately from the model.

## Practical questions
**Could this work in a real building?** As a decision-support prototype. It would need real sensor data to fit the
parameters (Baum-Welch shows how), a real floor plan (the Map editor shows the planner works on other maps), and safety
certification.

**What would you do next?** More than one fire, cell-level fire spread with a particle filter, several people, and
fitting the parameters on public fire-sensor data.

**What did you do and what did the AI do?** See `AI_USAGE_DECLARATION.md`. I chose the idea, the algorithms, the design
and the improvements, drew Kitty, ran and checked everything; Claude helped write code and documents. I can explain every file.
