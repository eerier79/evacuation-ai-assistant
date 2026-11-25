"""Evaluation: Monte Carlo comparison with baselines, ablation study and sensor sensitivity.
Run: python evaluate.py   (writes results/evaluation.md, results/*.csv, results/*.png)"""
import csv
import os
from evacuation.simulate import POLICIES, evaluate, sensitivity

N = 5000
SEED = 2026
OUT = "results"


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, policy in POLICIES.items():
        r = evaluate(policy, N, SEED)
        rows.append({"policy": name, **r})
        print(f"{name:40s} harm {r['harm_rate']:.3f} +- {r['harm_se']:.3f}  time {r['mean_time']:.2f}  "
              f"utility {r['utility']:.1f} +- {r['utility_se']:.1f}  waited {r['wait_rate']:.3f}")
    with open(f"{OUT}/policies.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader()
        w.writerows(rows)

    sens = sensitivity(n=2000, seed=SEED)
    with open(f"{OUT}/sensitivity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=sens[0].keys())
        w.writeheader()
        w.writerows(sens)
    print("\nSensor quality P(alarm | fire in same zone) -> harm rate")
    for s in sens:
        print(f"  {s['alarm_same']:.2f}: assistant {s['assistant']:.3f}, always shortest {s['shortest']:.3f}")

    with open(f"{OUT}/evaluation.md", "w") as f:
        f.write(f"# Evaluation ({N} simulated fires per policy, seed {SEED})\n\n")
        f.write("| Policy | Harm rate | Mean time | Utility | Waited |\n|---|---|---|---|---|\n")
        for r in rows:
            f.write(f"| {r['policy']} | {r['harm_rate']:.3f} ± {r['harm_se']:.3f} | {r['mean_time']:.2f} | "
                    f"{r['utility']:.1f} ± {r['utility_se']:.1f} | {r['wait_rate']:.3f} |\n")
        f.write("\n## Sensitivity to sensor quality\n\n| P(alarm, same zone) | Assistant harm | Always shortest harm |\n|---|---|---|\n")
        for s in sens:
            f.write(f"| {s['alarm_same']:.2f} | {s['assistant']:.3f} | {s['shortest']:.3f} |\n")

    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed: charts skipped")
        return
    names = [r["policy"].split(" (")[0].replace(" (hand-tuned)", "") for r in rows]
    colors = ["#2E7D4F" if i == 0 else "#9AA5B1" for i in range(len(rows))]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].barh(names[::-1], [r["harm_rate"] for r in rows][::-1], xerr=[1.96 * r["harm_se"] for r in rows][::-1], color=colors[::-1])
    axes[0].set_xlabel("Harm rate (lower is better)")
    axes[1].barh(names[::-1], [r["utility"] for r in rows][::-1], xerr=[1.96 * r["utility_se"] for r in rows][::-1], color=colors[::-1])
    axes[1].set_xlabel("Expected utility (higher is better)")
    axes[1].set_yticklabels([])
    for ax in axes:
        ax.spines[["top", "right"]].set_visible(False)
    fig.suptitle(f"Policies on {N} simulated fires (95% confidence intervals)")
    fig.tight_layout()
    fig.savefig(f"{OUT}/policies.png", dpi=150)

    fig, ax = plt.subplots(figsize=(6, 4))
    xs = [s["alarm_same"] for s in sens]
    ax.plot(xs, [s["assistant"] for s in sens], "o-", color="#2E7D4F", label="Assistant")
    ax.plot(xs, [s["shortest"] for s in sens], "s--", color="#9AA5B1", label="Always shortest route")
    ax.set_xlabel("Sensor quality: P(alarm | fire in the same zone)")
    ax.set_ylabel("Harm rate")
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(f"{OUT}/sensitivity.png", dpi=150)
    print(f"\nCharts saved to {OUT}/")


if __name__ == "__main__":
    main()
