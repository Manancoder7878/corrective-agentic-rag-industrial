from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def generate_benchmark_plots():
    csv_path = Path("tests/evaluation/ab_comparison_results.csv")
    df = pd.read_csv(csv_path)

    metrics = ["Faithfulness", "Answer Relevance", "Context Precision"]
    naive_means = [
        df["naive_faithfulness"].mean(),
        df["naive_relevance"].mean(),
        df["naive_precision"].mean(),
    ]
    crag_means = [
        df["crag_faithfulness"].mean(),
        df["crag_relevance"].mean(),
        df["crag_precision"].mean(),
    ]

    fig = plt.figure(figsize=(13, 6), dpi=300)

    # Bar chart
    ax1 = fig.add_subplot(1, 2, 1)
    x = np.arange(len(metrics))
    width = 0.35

    bar1 = ax1.bar(x - width / 2, naive_means, width, label="Naive RAG", color="#94a3b8", edgecolor="#475569")
    bar2 = ax1.bar(x + width / 2, crag_means, width, label="CRAG", color="#2563eb", edgecolor="#1d4ed8")

    ax1.set_ylabel("Score (0.0 to 1.0)", fontsize=11, fontweight="bold")
    ax1.set_title("Evaluation of Conventional RAG vs. Corrective RAG", fontsize=12, fontweight="bold", pad=12)
    ax1.set_xticks(x)
    ax1.set_xticklabels(metrics, fontsize=10)
    ax1.set_ylim(0, 1.15)
    ax1.grid(axis="y", linestyle="--", alpha=0.5)
    ax1.legend(loc="upper left", frameon=True)

    for bar in bar1:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.02, f"{yval:.3f}", ha="center", va="bottom", fontsize=9)
    for bar in bar2:
        yval = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width() / 2, yval + 0.02, f"{yval:.3f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    # Radar chart
    ax2 = fig.add_subplot(1, 2, 2, polar=True)
    angles = np.linspace(0, 2 * np.pi, len(metrics), endpoint=False).tolist()
    angles += angles[:1]

    n_vals = naive_means + naive_means[:1]
    c_vals = crag_means + crag_means[:1]

    ax2.plot(angles, n_vals, "o--", linewidth=1.8, label="Naive RAG", color="#94a3b8")
    ax2.fill(angles, n_vals, alpha=0.15, color="#94a3b8")

    ax2.plot(angles, c_vals, "o-", linewidth=2.2, label="CRAG", color="#2563eb")
    ax2.fill(angles, c_vals, alpha=0.25, color="#2563eb")

    ax2.set_thetagrids(np.degrees(angles[:-1]), metrics, fontsize=10, fontweight="bold")
    ax2.set_ylim(0, 1.0)
    ax2.set_title("RAG Triad Coverage Polygon", fontsize=12, fontweight="bold", pad=20)
    ax2.legend(loc="upper right", bbox_to_anchor=(1.25, 1.1))

    plt.tight_layout()
    output_png = Path("tests/evaluation/benchmark_comparison.png")
    plt.savefig(output_png, bbox_inches="tight")
    plt.close()
    print(f" Chart visual exported at: {output_png}")


if __name__ == "__main__":
    generate_benchmark_plots()