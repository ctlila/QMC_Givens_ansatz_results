"""
Plot energy error vs HQC cost for Givens ansatz on H1-1 and H1-1E backends.
Creates one plot per molecule with main plot and statevector subplot.
"""

import json
import os
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict

include_uccsd = False

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIVENS_DIR = os.path.join(BASE_DIR, "Givens_results")
UCCSD_DIR = os.path.join(BASE_DIR, "UCCSD_results")
OUTPUT_DIR = os.path.join(BASE_DIR, "figures")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def load_results(backend_dir):
    """Load all VQE results from a backend directory."""
    results = defaultdict(list)

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

            # Handle energy error (could be single value or [mean, std])
            energy_error = data.get("energy_error", 0)
            if isinstance(energy_error, list):
                error_mean, error_std = energy_error
            else:
                error_mean, error_std = energy_error, 0

            # Handle final_params (could be single list or list of lists)
            final_params = data.get("final_params", [])
            if final_params and isinstance(final_params[0], list):
                nb_params = len(final_params[0])
            else:
                nb_params = len(final_params)

            results[molecule].append(
                {
                    "HQC_cost": data.get("HQC_cost", 0),
                    "energy_error_mean": abs(error_mean),
                    "energy_error_std": error_std,
                    "nb_params": nb_params,
                    "circuit": data.get("circuit", circuit_dir),
                }
            )

    return results


def plot_molecule(molecule, h1_1_data, h1_1e_data, statevector_data, uccsd_data=None):
    """Create plot for a single molecule."""
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8), height_ratios=[3, 1], sharex=True
    )

    # Get HF baseline from statevector 0_givens circuit
    hf_baseline = None
    if statevector_data:
        for r in statevector_data:
            if r["circuit"] == "0_givens" and r["nb_params"] == 0:
                hf_baseline = r["energy_error_mean"]
                break

    # Create mapping from circuit name to HQC cost from H1-1E data
    circuit_to_hqc = {}
    if h1_1e_data:
        for r in h1_1e_data:
            circuit_to_hqc[r["circuit"]] = r["HQC_cost"]

    # Plot H1-1E data
    if h1_1e_data:
        h1_1e_sorted = sorted(h1_1e_data, key=lambda x: x["HQC_cost"])
        costs = [r["HQC_cost"] for r in h1_1e_sorted]
        errors = [r["energy_error_mean"] for r in h1_1e_sorted]
        error_bars = [r["energy_error_std"] for r in h1_1e_sorted]
        params = [r["nb_params"] for r in h1_1e_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="o-",
            label="H1-1E (Givens)",
            color="steelblue",
            markersize=8,
            linewidth=2,
            capsize=4,
            capthick=1.5,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(5, 5),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                color="darkblue",
            )

    # Plot H1-1 data
    if h1_1_data:
        h1_1_sorted = sorted(h1_1_data, key=lambda x: x["HQC_cost"])
        costs = [r["HQC_cost"] for r in h1_1_sorted]
        errors = [r["energy_error_mean"] for r in h1_1_sorted]
        error_bars = [r["energy_error_std"] for r in h1_1_sorted]
        params = [r["nb_params"] for r in h1_1_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="^-",
            label="H1-1 (Givens)",
            color="darkorange",
            markersize=8,
            linewidth=2,
            capsize=4,
            capthick=1.5,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(5, -15),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                color="darkred",
            )

    # Plot UCCSD data (H1-1E)
    if uccsd_data:
        uccsd_sorted = sorted(uccsd_data, key=lambda x: x["HQC_cost"])
        costs = [r["HQC_cost"] for r in uccsd_sorted]
        errors = [r["energy_error_mean"] for r in uccsd_sorted]
        params = [r["nb_params"] for r in uccsd_sorted]

        ax1.plot(
            costs,
            errors,
            "s-",
            label="H1-1E (UCCSD)",
            color="darkred",
            markersize=8,
            linewidth=2,
            alpha=0.8,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(5, 10),
                textcoords="offset points",
                fontsize=9,
                fontweight="bold",
                color="darkred",
            )

    # Plot statevector data in subplot - match circuit names to HQC costs
    if statevector_data and circuit_to_hqc:
        # Only plot statevector points that have matching H1-1E circuits
        sv_with_hqc = []
        for r in statevector_data:
            if r["circuit"] in circuit_to_hqc:
                sv_with_hqc.append(
                    {
                        "HQC_cost": circuit_to_hqc[r["circuit"]],
                        "energy_error_mean": r["energy_error_mean"],
                    }
                )

        if sv_with_hqc:
            sv_sorted = sorted(sv_with_hqc, key=lambda x: x["HQC_cost"])
            costs = [r["HQC_cost"] for r in sv_sorted]
            errors = [r["energy_error_mean"] for r in sv_sorted]

            ax2.plot(
                costs,
                errors,
                "o-",
                label="Statevector",
                color="green",
                markersize=6,
                linewidth=1.5,
            )

    # Plot HF baseline if available
    if hf_baseline is not None:
        ax1.axhline(y=hf_baseline, color='gray', linestyle=':', linewidth=2, 
                   label='HF (SV)', alpha=0.7, zorder=1)

    # Format main plot
    ax1.set_ylabel("Energy Error (Ha)", fontsize=12, fontweight="bold")
    ax1.set_yscale("log")
    ax1.legend(fontsize=11, loc="best")
    ax1.grid(True, alpha=0.3)
    ax1.set_title(
        f"{molecule} - Energy Error vs HQC Cost", fontsize=14, fontweight="bold"
    )

    # Format statevector subplot
    ax2.set_xlabel("HQC Cost", fontsize=12, fontweight="bold")
    ax2.set_ylabel("SV Error (Ha)", fontsize=11, fontweight="bold")
    ax2.set_yscale("log")
    ax2.legend(fontsize=10)
    ax2.grid(True, alpha=0.3)

    plt.tight_layout()

    # Save figure
    molecule_dir = os.path.join(OUTPUT_DIR, molecule)
    os.makedirs(molecule_dir, exist_ok=True)
    output_path = os.path.join(molecule_dir, "energy_vs_hqc_cost.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"Saved: {output_path}")

    plt.close()


def main():
    """Main function to generate all plots."""
    print("Loading results...")

    # Load results from different backends
    h1_1_results = load_results(os.path.join(GIVENS_DIR, "H1-1"))
    h1_1e_results = load_results(os.path.join(GIVENS_DIR, "H1-1E"))
    statevector_results = load_results(os.path.join(GIVENS_DIR, "statevector"))
    if include_uccsd:
        uccsd_results = load_results(os.path.join(UCCSD_DIR, "H1-1E"))
    else:
        uccsd_results = {}

    # Get all molecules
    all_molecules = set(
        list(h1_1_results.keys())
        + list(h1_1e_results.keys())
        + list(statevector_results.keys())
        + list(uccsd_results.keys())
    )

    print(f"Found molecules: {sorted(all_molecules)}")

    # Create plot for each molecule
    for molecule in sorted(all_molecules):
        print(f"\nProcessing {molecule}...")
        plot_molecule(
            molecule,
            h1_1_results.get(molecule, []),
            h1_1e_results.get(molecule, []),
            statevector_results.get(molecule, []),
            uccsd_results.get(molecule, []),
        )

    print(f"\n✓ All plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
