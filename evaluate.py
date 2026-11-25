"""Full evaluation study. Run: python evaluate.py   (about 1-2 minutes)

Writes to results/:
  policies.csv / policies.png      every policy on the same 5000 fires (common random numbers)
  paired.csv                       paired bootstrap 95% CIs: assistant minus each other policy
  robustness.csv / robustness.png  the true world differs from the assistant's model
  sensitivity.csv / sensitivity.png
  learning.csv / learning.png      Baum-Welch recovers the HMM parameters from sensor logs
  qlearning.csv / qlearning.png    learning curve of model-free Q-learning vs the MDP
  boundary.png                     QMDP vs exact POMDP decision boundaries
  evaluation.md                    everything above as tables
"""
import csv
import os

from evacuation import pomdp
from evacuation.learn import learning_experiment
from evacuation.qlearn import evaluate_learned, train
from evacuation.simulate import POLICIES, paired_bootstrap, robustness, run_many, sensitivity, summarize

N = 5000
SEED = 2026
OUT = "results"
MAIN = "Assistant (HMM + A* + Bayes + MDP)"


def write_csv(name, rows):
    with open(f"{OUT}/{name}", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)


def main():
    os.makedirs(OUT, exist_ok=True)
    print(f"1/6 policies on {N} fires")
    episodes = {name: run_many(p, N, SEED) for name, p in POLICIES.items()}
    rows = [{"policy": k, **summarize(v)} for k, v in episodes.items()]
    for r in rows:
        print(f"  {r['policy']:40s} harm {r['harm_rate']:.3f} ± {r['harm_se']:.3f}  utility {r['utility']:.1f} ± {r['utility_se']:.1f}"
              f"  waited {r['wait_rate']:.3f}")
    write_csv("policies.csv", rows)

    print("2/6 paired bootstrap (assistant minus other policy)")
    paired = []
    for k, v in episodes.items():
        if k == MAIN:
            continue
        u = paired_bootstrap(episodes[MAIN], v, "utility")
        h = paired_bootstrap(episodes[MAIN], v, "harmed")
        paired.append({"other": k, "utility_diff": u["mean"], "utility_low": u["low"], "utility_high": u["high"],
                       "harm_diff": h["mean"], "harm_low": h["low"], "harm_high": h["high"]})
        print(f"  vs {k:38s} utility {u['mean']:+6.1f} [{u['low']:+.1f}, {u['high']:+.1f}]   "
              f"harm {h['mean']:+.3f} [{h['low']:+.3f}, {h['high']:+.3f}]")
    write_csv("paired.csv", paired)

    print("3/6 robustness: the real world differs from the model")
    rob = robustness(n=2000)
    rob_rows = [{"world": r["world"], **{f"{p} harm": v["harm_rate"] for p, v in r.items() if p != "world"},
                 **{f"{p} utility": v["utility"] for p, v in r.items() if p != "world"}} for r in rob]
    write_csv("robustness.csv", rob_rows)
    for r in rob:
        print(f"  {r['world']:28s} " + "  ".join(f"{p.split(' (')[0][:18]} {v['harm_rate']:.3f}" for p, v in r.items() if p != "world"))

    print("4/6 sensor sensitivity")
    sens = sensitivity(n=2000, seed=SEED)
    write_csv("sensitivity.csv", sens)

    print("5/6 Baum-Welch learning")
    learn_rows, truth = learning_experiment()
    write_csv("learning.csv", learn_rows + [{"sequences": "true value", **truth}])
    for r in learn_rows:
        print("  ", {k: round(v, 3) for k, v in r.items()})

    print("6/6 Q-learning")
    Q, curve = train()
    q_eval = evaluate_learned(Q, N, SEED)
    write_csv("qlearning.csv", curve)
    print(f"  learned policy: harm {q_eval['harm_rate']:.3f}, utility {q_eval['utility']:.1f}")

    with open(f"{OUT}/evaluation.md", "w") as f:
        f.write(f"# Evaluation ({N} simulated fires per policy, seed {SEED}, common random numbers)\n\n")
        f.write("| Policy | Harm rate | Mean time | Utility | Waited |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['policy']} | {r['harm_rate']:.3f} ± {r['harm_se']:.3f} | {r['mean_time']:.2f} | "
                    f"{r['utility']:.1f} ± {r['utility_se']:.1f} | {r['wait_rate']:.3f} |\n")
        f.write(f"| Q-learning (30000 training fires) | {q_eval['harm_rate']:.3f} ± {q_eval['harm_se']:.3f} | "
                f"{q_eval['mean_time']:.2f} | {q_eval['utility']:.1f} ± {q_eval['utility_se']:.1f} | {q_eval['wait_rate']:.3f} |\n")
        f.write("\n## Paired bootstrap: assistant minus other policy (95% CI)\n\n| Other policy | Utility difference | Harm difference |\n|---|---|---|\n")
        for p in paired:
            f.write(f"| {p['other']} | {p['utility_diff']:+.1f} [{p['utility_low']:+.1f}, {p['utility_high']:+.1f}] | "
                    f"{p['harm_diff']:+.3f} [{p['harm_low']:+.3f}, {p['harm_high']:+.3f}] |\n")
        names = [p for p in rob[0] if p != "world"]
        f.write("\n## Robustness: harm rate when the real world differs from the model\n\n| World | "
                + " | ".join(n.split(" (")[0] for n in names) + " |\n|" + "---|" * (len(names) + 1) + "\n")
        for r in rob:
            f.write(f"| {r['world']} | " + " | ".join(f"{r[n]['harm_rate']:.3f}" for n in names) + " |\n")
        f.write("\n## Sensitivity to sensor quality\n\n| P(alarm, same zone) | Assistant harm | Always shortest harm |\n|---|---|---|\n")
        for s in sens:
            f.write(f"| {s['alarm_same']:.2f} | {s['assistant']:.3f} | {s['shortest']:.3f} |\n")
        f.write("\n## Baum-Welch: parameters learned from sensor logs (20 steps per log)\n\n| Logs | p_stay | alarm_same | alarm_adjacent | alarm_far |\n|---|---|---|---|---|\n")
        for r in learn_rows + [{"sequences": "**true**", **truth}]:
            f.write(f"| {r['sequences']} | {r['p_stay']:.3f} | {r['alarm_same']:.3f} | {r['alarm_adjacent']:.3f} | {r['alarm_far']:.3f} |\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: charts skipped")
        return
    green, grey = "#2E7D4F", "#9AA5B1"
    names = [r["policy"].split(" (")[0].replace(" (hand-tuned)", "") for r in rows]
    colors = [green if i == 0 else ("#6D28D9" if "POMDP" in r["policy"] else grey) for i, r in enumerate(rows)]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.8))
    axes[0].barh(names[::-1], [r["harm_rate"] for r in rows][::-1], xerr=[1.96 * r["harm_se"] for r in rows][::-1], color=colors[::-1])
    axes[0].set_xlabel("Harm rate (lower is better)")
    axes[1].barh(names[::-1], [r["utility"] for r in rows][::-1], xerr=[1.96 * r["utility_se"] for r in rows][::-1], color=colors[::-1])
    axes[1].set_xlabel("Expected utility (higher is better)")
    axes[1].set_yticklabels([])
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Policies on the same {N} simulated fires (95% confidence intervals)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/policies.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [s["alarm_same"] for s in sens]
    ax.plot(xs, [s["assistant"] for s in sens], "o-", color=green, label="Assistant")
    ax.plot(xs, [s["shortest"] for s in sens], "s--", color=grey, label="Always shortest route")
    ax.set_xlabel("Sensor quality: P(alarm | fire in the same zone)")
    ax.set_ylabel("Harm rate")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/sensitivity.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.5, 4))
    worlds = [r["world"] for r in rob]
    names = [p for p in rob[0] if p != "world"]
    width = 0.8 / len(names)
    pal = [green, "#0369A1", grey, "#E11D48"]
    for i, n in enumerate(names):
        ax.bar([j + i * width for j in range(len(worlds))], [r[n]["harm_rate"] for r in rob], width,
               label=n.split(" (")[0], color=pal[i % 4])
    ax.set_xticks([j + 0.4 - width / 2 for j in range(len(worlds))], worlds, fontsize=8)
    ax.set_ylabel("Harm rate")
    ax.set_title("Robustness: the assistant keeps its assumed model, the real world changes", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.12))
    fig.tight_layout()
    fig.savefig(f"{OUT}/robustness.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    keys = ["p_stay", "alarm_same", "alarm_adjacent", "alarm_far"]
    xs = [r["sequences"] for r in learn_rows]
    for k, c in zip(keys, [green, "#0369A1", "#C2410C", "#6D28D9"]):
        ax.plot(xs, [r[k] for r in learn_rows], "o-", color=c, label=k)
        ax.axhline(truth[k], color=c, ls=":", lw=1)
    ax.set_xscale("log")
    ax.set_xticks(xs, [str(x) for x in xs])
    ax.minorticks_off()
    ax.set_xlabel("Number of sensor logs (20 steps each)")
    ax.set_ylabel("Estimated value (dotted = true value)")
    ax.set_title("Baum-Welch learns the HMM from alarms alone", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/learning.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(6.5, 4))
    mdp_u = next(r["utility"] for r in rows if r["policy"] == MAIN)
    ax.plot([c["episodes"] for c in curve], [c["avg_utility"] for c in curve], "o-", color="#C2410C", label="Q-learning (while exploring)")
    ax.axhline(mdp_u, color=green, ls="--", label=f"MDP from the model ({mdp_u:.1f})")
    ax.axhline(q_eval["utility"], color="#C2410C", ls=":", label=f"Learned policy, greedy ({q_eval['utility']:.1f})")
    ax.set_xlabel("Training fires")
    ax.set_ylabel("Average utility")
    ax.set_title("Model-free learning needs many trials to approach the MDP", fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
    fig.tight_layout()
    fig.savefig(f"{OUT}/qlearning.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    for ax, (title, risk) in zip(axes, (("Alarm in Z1 (safe route risk 0.17)", 0.174), ("No readings (safe route risk 0.46)", 0.46))):
        g, cq = pomdp.qmdp_curves(4, 6, risk)
        sol = pomdp.solve(4, 6, risk)
        for a, c in (("PROCEED", green), ("DETOUR", "#C2410C"), ("WAIT", "#0369A1")):
            ax.plot(g, cq[a], color=c, lw=1.4, ls="--", label=f"{a} (QMDP)")
            ax.plot(sol["grid"], sol["Q"][a], color=c, lw=2.2, label=f"{a} (POMDP)")
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("P(fast route blocked)")
        ax.set_ylim(-120, 100)
        ax.spines[["top", "right"]].set_visible(False)
    axes[0].set_ylabel("Expected value")
    axes[1].legend(frameon=False, fontsize=7.5, ncol=2)
    fig.suptitle("Decision boundaries: QMDP (dashed) vs exact POMDP (solid)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/boundary.png", dpi=150)
    plt.close(fig)
    print(f"\nCharts and tables saved to {OUT}/")


if __name__ == "__main__":
    main()
