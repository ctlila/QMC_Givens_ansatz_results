"""
Plot the total number of 2-qubit gates (summed over the 16 measurement
circuits) vs number of parameters for BeH2: QMC-UCC, the original
generalized-pool ADAPT-VQE circuits, and the same ADAPT circuits re-synthesised
UCC-style (GivensVQE: givens_vqe/utils/recompile_adapt_generalized.py). Shows that, compiled the
same way, ADAPT and UCC give the same 2-qubit gate count for the same ansatz.
"""

import json
import os

import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from plot_style import COLORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MOLECULE = "BeH2"
UCC_DIR = os.path.join(BASE_DIR, "UCCSD_results", "H1-1E", MOLECULE)
ADAPT_DIR = os.path.join(
    BASE_DIR, "ADAPT-VQE_results", "generalized", "H1-Emulator_results", MOLECULE
)
RECOMPILED_DIR = os.path.join(
    BASE_DIR, "ADAPT-VQE_results", "generalized_recompiled", MOLECULE
)
OUTPUT_DIR = os.path.join(BASE_DIR, "figures", "SI")


def load(root, filename):
    """-> sorted [(nb_params, total n_2q_gates)] over the circuit dirs in root."""
    points = []
    for d in os.listdir(root):
        path = os.path.join(root, d, filename)
        if not os.path.exists(path):
            continue
        data = json.load(open(path))
        points.append(
            (data["nb_params"], data["circuit_gate_counts"]["total"]["n_2q_gates"])
        )
    return sorted(points)


def main():
    series = [
        (load(UCC_DIR, "vqe_result.json"), "QMC-UCC", "s-", COLORS["QMC-UCC"], {}),
        (
            load(ADAPT_DIR, "vqe_result.json"),
            "ADAPT-VQE (original compilation)",
            "o--",
            COLORS["ADAPT-generalized"],
            {"alpha": 0.5},
        ),
        (
            load(RECOMPILED_DIR, "recompiled_result.json"),
            "ADAPT-VQE (UCC-style compilation)",
            "o-",
            COLORS["ADAPT-generalized"],
            {"markerfacecolor": "none", "markeredgewidth": 2, "markersize": 12},
        ),
    ]

    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)
    for points, label, fmt, color, kwargs in series:
        params, gates = zip(*points)
        print(label, dict(points))
        ax.plot(
            params,
            gates,
            fmt,
            label=label,
            color=color,
            **{"markersize": 8, "linewidth": 2, **kwargs},
        )

    ax.set_xlabel("Number of parameters", fontsize=20)
    ax.set_ylabel("Two-qubit Gate Count", fontsize=20)
    ax.legend(fontsize=16, loc="best", frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="both", which="major", labelsize=14)
    plt.tight_layout()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    for ext in ("pdf", "svg"):
        output_path = os.path.join(
            OUTPUT_DIR, f"{MOLECULE}_2q_gates_adapt_recompiled.{ext}"
        )
        plt.savefig(output_path, bbox_inches="tight")
        print(f"Saved {output_path}")
    plt.close()


if __name__ == "__main__":
    main()
