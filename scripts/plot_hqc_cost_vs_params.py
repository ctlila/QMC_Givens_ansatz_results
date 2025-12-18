"""
Plot HQC cost vs number of parameters for Givens and UCCSD ansatzes on H1-1E.
Creates one plot per molecule comparing both methods.
"""

import json
import os
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict
from plot_style import COLORS

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIVENS_DIR = os.path.join(BASE_DIR, "Givens_results")
UCCSD_DIR = os.path.join(BASE_DIR, "UCCSD_results")
OUTPUT_DIR = os.path.join(BASE_DIR, "figures")


# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_givens_results():
    """Load Givens results from H1-1E backend."""
    results = defaultdict(list)
    backend_dir = os.path.join(GIVENS_DIR, "H1-1E")

    if not os.path.exists(backend_dir):
        return results

    for molecule in os.listdir(backend_dir):
        molecule_path = os.path.join(backend_dir, molecule)
        if not os.path.isdir(molecule_path):
            continue

        for circuit_dir in os.listdir(molecule_path):
            result_path = os.path.join(molecule_path, circuit_dir, "vqe_result.json")
            if not os.path.exists(result_path):
                continue

            with open(result_path, "r") as f:
                data = json.load(f)

            # Handle final_params (could be single list or list of lists)
            final_params = data.get("final_params", [])
            if final_params and isinstance(final_params[0], list):
                nb_params = len(final_params[0])
            else:
                nb_params = len(final_params)

            results[molecule].append(
                {
                    "nb_params": nb_params,
                    "HQC_cost": data.get("HQC_cost", 0),
                    "circuit": data.get("circuit", circuit_dir),
                }
            )

    return results


def load_uccsd_results():
    """Load UCCSD results from H1-1E backend."""
    results = defaultdict(list)
    backend_dir = os.path.join(UCCSD_DIR, "H1-1E")

    if not os.path.exists(backend_dir):
        return results

    for molecule in os.listdir(backend_dir):
        molecule_path = os.path.join(backend_dir, molecule)
        if not os.path.isdir(molecule_path):
            continue

        for circuit_dir in os.listdir(molecule_path):
            result_path = os.path.join(molecule_path, circuit_dir, "vqe_result.json")
            if not os.path.exists(result_path):
                continue

            with open(result_path, "r") as f:
                data = json.load(f)

            # Get parameters and HQC cost
            final_params = data.get("final_params", [])
            nb_params = len(final_params)

            results[molecule].append(
                {
                    "nb_params": nb_params,
                    "HQC_cost": data.get("HQC_cost", 0),
                    "circuit": data.get("circuit", circuit_dir),
                }
            )

    return results


def plot_molecule(molecule, givens_data, uccsd_data):
    """Create plot for a single molecule comparing Givens and UCCSD."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Plot Givens data
    if givens_data:
        givens_sorted = sorted(givens_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in givens_sorted]
        costs = [r["HQC_cost"] for r in givens_sorted]

        ax.plot(
            params,
            costs,
            "o-",
            label="QMC-Givens",
            color=COLORS["Statevector"],
            markersize=10,
            linewidth=3,
        )

    # Plot UCCSD data
    if uccsd_data:
        uccsd_sorted = sorted(uccsd_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in uccsd_sorted]
        costs = [r["HQC_cost"] for r in uccsd_sorted]

        ax.plot(
            params,
            costs,
            "s-",
            label="UCCSD",
            color=COLORS["UCCSD"],
            markersize=8,
            linewidth=2,
        )

    # Format plot
    ax.set_xlabel(
        "Number of Parameters",
        fontsize=20,
        fontweight="bold",
    )
    ax.set_ylabel(
        "HQC Cost",
        fontsize=20,
        fontweight="bold",
    )
    # ax.set_title(
    #     f"{molecule} - HQC Cost vs Number of Parameters (H1-1E)",
    #     fontsize=15,
    #     fontweight="bold",
    # )
    ax.legend(fontsize=20, loc="best", frameon=False)

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # Increase tick label font sizes
    ax.tick_params(axis="both", which="major", labelsize=14)

    plt.tight_layout()

    # Save figure
    molecule_dir = os.path.join(OUTPUT_DIR, molecule)
    os.makedirs(molecule_dir, exist_ok=True)
    output_path = os.path.join(molecule_dir, f"{molecule}_hqc_cost_vs_params.pdf")
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Saved: {output_path}")

    plt.close()


def main():
    """Main function to generate all plots."""
    print("Loading results...")

    # Load results
    givens_results = load_givens_results()
    uccsd_results = load_uccsd_results()

    # Get all molecules
    all_molecules = set(list(givens_results.keys()) + list(uccsd_results.keys()))

    print(f"Found molecules: {sorted(all_molecules)}")

    # Create plot for each molecule
    for molecule in sorted(all_molecules):
        givens_data = givens_results.get(molecule, [])
        uccsd_data = uccsd_results.get(molecule, [])

        if not givens_data and not uccsd_data:
            print(f"Skipping {molecule} (no data)")
            continue

        print(f"Processing {molecule}...")
        print(f"  Givens points: {len(givens_data)}")
        print(f"  UCCSD points: {len(uccsd_data)}")

        plot_molecule(molecule, givens_data, uccsd_data)

    print(f"\n✓ All plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
