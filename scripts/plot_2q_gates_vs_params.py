"""
Plot number of 2-qubit gates vs number of parameters for Givens and UCCSD
ansatzes on H1-1E. Creates one plot per molecule comparing both methods.
"""

import json
import os
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict
from plot_style import COLORS, finalize_panel

# Configuration
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GIVENS_DIR = os.path.join(BASE_DIR, "Givens_results")
UCCSD_DIR = os.path.join(BASE_DIR, "UCCSD_results")
ADAPT_DIR = os.path.join(BASE_DIR, "ADAPT-VQE_results")
# Non-final ADAPT-VQE results (e.g. new H1-Emulator_results not yet promoted
# to ADAPT-VQE_results) are kept here but should be plotted identically.
# TEMP_ADAPT_DIR = os.path.join(BASE_DIR, "temp_results", "ADAPT-VQE_results")
OUTPUT_DIR = os.path.join(BASE_DIR, "figures")

# For these molecules the UCC-pool and generalized-pool ADAPT-VQE results are
# identical, so only the generalised pool is loaded and plotted, labelled
# plainly "ADAPT-VQE". N2 differs between the pools and keeps the pool label.
ADAPT_POOLS_IDENTICAL = {"BeH2", "LiH_6_spinorbs"}


def adapt_label(molecule):
    if molecule in ADAPT_POOLS_IDENTICAL:
        return "ADAPT-VQE"
    return "ADAPT-VQE (generalised pool)"


# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)


def get_n_2q_gates(data):
    """Extract the total number of 2-qubit gates saved by save_gate_counts.py."""
    gate_counts = data.get("circuit_gate_counts")
    if not gate_counts:
        return None
    return gate_counts.get("total", {}).get("n_2q_gates")


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

            n_2q_gates = get_n_2q_gates(data)
            if n_2q_gates is None:
                continue

            # Handle final_params (could be single list or list of lists)
            final_params = data.get("final_params", [])
            if final_params and isinstance(final_params[0], list):
                nb_params = len(final_params[0])
            else:
                nb_params = len(final_params)

            results[molecule].append(
                {
                    "nb_params": nb_params,
                    "n_2q_gates": n_2q_gates,
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

            n_2q_gates = get_n_2q_gates(data)
            if n_2q_gates is None:
                continue

            # Get parameters and 2q gate count
            final_params = data.get("final_params", [])
            if final_params and isinstance(final_params[0], list):
                nb_params = len(final_params[0])
            else:
                nb_params = len(final_params)

            results[molecule].append(
                {
                    "nb_params": nb_params,
                    "n_2q_gates": n_2q_gates,
                    "circuit": data.get("circuit", circuit_dir),
                }
            )

    return results


def load_adapt_results(pool, backend="H1-Emulator_results"):
    """Load ADAPT-VQE results for a given operator pool ('uccsd' or 'generalized').

    Searches both the final ADAPT_DIR and TEMP_ADAPT_DIR (non-final results
    not yet promoted) and merges what it finds, so results are treated
    identically regardless of which of the two they currently live in.
    """
    results = defaultdict(list)

    for base_dir in (ADAPT_DIR,):  # , TEMP_ADAPT_DIR
        pool_dir = os.path.join(base_dir, pool, backend)

        if not os.path.exists(pool_dir):
            continue

        for molecule in os.listdir(pool_dir):
            molecule_path = os.path.join(pool_dir, molecule)
            if not os.path.isdir(molecule_path):
                continue
            if pool == "uccsd" and molecule in ADAPT_POOLS_IDENTICAL:
                continue

            for circuit_dir in os.listdir(molecule_path):
                result_path = os.path.join(
                    molecule_path, circuit_dir, "vqe_result.json"
                )
                if not os.path.exists(result_path):
                    continue

                with open(result_path, "r") as f:
                    data = json.load(f)

                n_2q_gates = get_n_2q_gates(data)
                if n_2q_gates is None:
                    continue

                # ADAPT-VQE results store the parameter count explicitly
                nb_params = data.get("nb_params")
                if nb_params is None:
                    final_params = data.get("final_params", [])
                    if final_params and isinstance(final_params[0], list):
                        nb_params = len(final_params[0])
                    else:
                        nb_params = len(final_params)

                results[molecule].append(
                    {
                        "nb_params": nb_params,
                        "n_2q_gates": n_2q_gates,
                        "circuit": data.get("circuit", circuit_dir),
                    }
                )

    return results


def plot_molecule(
    molecule,
    givens_data,
    uccsd_data,
    adapt_uccsd_data=None,
    adapt_generalized_data=None,
):
    """Create plot for a single molecule comparing Givens and UCCSD."""
    fig, ax = plt.subplots(figsize=(10, 6), dpi=300)

    # Plot Givens data
    if givens_data:
        givens_sorted = sorted(givens_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in givens_sorted]
        costs = [r["n_2q_gates"] for r in givens_sorted]

        ax.plot(
            params,
            costs,
            "o-",
            label="QMC-Givens",
            color=COLORS["QMC-Givens"],
            markersize=10,
            linewidth=3,
        )

    # Plot UCCSD data
    if uccsd_data:
        uccsd_sorted = sorted(uccsd_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in uccsd_sorted]
        costs = [r["n_2q_gates"] for r in uccsd_sorted]
        print(params)
        print(costs)
        ax.plot(
            params,
            costs,
            "s-",
            label="QMC-UCC",
            color=COLORS["QMC-UCC"],
            markersize=8,
            linewidth=2,
        )

    # Plot ADAPT-VQE data
    if adapt_uccsd_data:
        adapt_uccsd_sorted = sorted(adapt_uccsd_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in adapt_uccsd_sorted]
        costs = [r["n_2q_gates"] for r in adapt_uccsd_sorted]

        ax.plot(
            params,
            costs,
            "^-",
            label="ADAPT-VQE (UCC pool)",
            color=COLORS["ADAPT-UCC"],
            markersize=8,
            linewidth=2,
        )

    if adapt_generalized_data:
        adapt_generalized_sorted = sorted(
            adapt_generalized_data, key=lambda x: x["nb_params"]
        )
        params = [r["nb_params"] for r in adapt_generalized_sorted]
        costs = [r["n_2q_gates"] for r in adapt_generalized_sorted]

        ax.plot(
            params,
            costs,
            "D-",
            label=adapt_label(molecule),
            color=COLORS["ADAPT-generalized"],
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
        "Two-qubit Gate Count",
        fontsize=20,
        fontweight="bold",
    )
    # ax.set_title(
    #     f"{molecule} - Number of 2-Qubit Gates vs Number of Parameters (H1-1E)",
    #     fontsize=15,
    #     fontweight="bold",
    # )
    ax.legend(
        fontsize=20,
        loc="best",
        frameon=False,
        # facecolor="white",
        # framealpha=0.7,
        edgecolor="none",
    )

    # Remove top and right spines
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    # Increase tick label font sizes
    ax.tick_params(axis="both", which="major", labelsize=14)

    plt.tight_layout()
    finalize_panel(fig, "2q_gates_vs_params", molecule, ylabel_ax=ax)

    # Save figure
    molecule_dir = os.path.join(OUTPUT_DIR, molecule)
    os.makedirs(molecule_dir, exist_ok=True)
    output_path = os.path.join(molecule_dir, f"{molecule}_2q_gates_vs_params.svg")
    plt.savefig(output_path)  # fixed margins, see plot_style.finalize_panel
    print(f"Saved: {output_path}")

    plt.close()


def main():
    """Main function to generate all plots."""
    print("Loading results...")

    # Load results
    givens_results = load_givens_results()
    uccsd_results = load_uccsd_results()
    adapt_uccsd_results = load_adapt_results("uccsd")
    adapt_generalized_results = load_adapt_results("generalized")

    # Get all molecules
    all_molecules = set(
        list(givens_results.keys())
        + list(uccsd_results.keys())
        + list(adapt_uccsd_results.keys())
        + list(adapt_generalized_results.keys())
    )

    print(f"Found molecules: {sorted(all_molecules)}")
    # all_molecules = ["N2"]
    # Create plot for each molecule
    for molecule in sorted(all_molecules):
        givens_data = givens_results.get(molecule, [])
        uccsd_data = uccsd_results.get(molecule, [])
        adapt_uccsd_data = adapt_uccsd_results.get(molecule, [])
        adapt_generalized_data = adapt_generalized_results.get(molecule, [])

        if not any([givens_data, uccsd_data, adapt_uccsd_data, adapt_generalized_data]):
            print(f"Skipping {molecule} (no data)")
            continue

        print(f"Processing {molecule}...")
        print(f"  Givens points: {len(givens_data)}")
        print(f"  UCCSD points: {len(uccsd_data)}")
        print(f"  ADAPT-VQE (UCC pool) points: {len(adapt_uccsd_data)}")
        print(f"  ADAPT-VQE points: {len(adapt_generalized_data)}")

        plot_molecule(
            molecule, givens_data, uccsd_data, adapt_uccsd_data, adapt_generalized_data
        )

    print(f"\n✓ All plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
