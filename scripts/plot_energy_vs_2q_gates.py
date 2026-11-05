"""
Plot energy error vs number of 2-qubit gates for Givens ansatz on H1-1 and H1-1E backends.
Creates one plot per molecule with main plot and statevector subplot.
"""

import json
import math
import os
import matplotlib

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt
from collections import defaultdict
from plot_style import COLORS, finalize_panel

include_uccsd = False
include_adapt = False

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

            # Statevector results have no compiled circuit of their own; their
            # x-position is borrowed from the matching H1-1E circuit later on,
            # so a missing gate count here must not drop the data point.
            n_2q_gates = get_n_2q_gates(data)

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

            # Skip placeholder results (e.g. "TBD") so they don't break the axes
            if not isinstance(error_mean, (int, float)) or not math.isfinite(
                error_mean
            ):
                continue

            results[molecule].append(
                {
                    "n_2q_gates": n_2q_gates,
                    "energy_error_mean": abs(error_mean),
                    "energy_error_std": error_std,
                    "nb_params": nb_params,
                    "circuit": data.get("circuit", circuit_dir),
                    "nb_qubits": data.get("nb_qubits", 0),
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

                energy_error = data.get("energy_error", 0)
                if isinstance(energy_error, list):
                    error_mean, error_std = energy_error
                else:
                    error_mean, error_std = energy_error, 0

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
                        "n_2q_gates": n_2q_gates,
                        "energy_error_mean": abs(error_mean),
                        "energy_error_std": error_std,
                        "nb_params": nb_params,
                        "circuit": data.get("circuit", circuit_dir),
                        "nb_qubits": data.get("nb_qubits", 0),
                    }
                )

    return results


def plot_molecule(
    molecule,
    h1_1_data,
    h1_1e_data,
    statevector_data,
    uccsd_data=None,
    adapt_uccsd_data=None,
    adapt_generalized_data=None,
):
    """Create plot for a single molecule."""
    # Statevector points are kept even without a gate count (see load_results);
    # every other series needs its own x-value, so drop points missing one.
    h1_1_data = [r for r in h1_1_data if r["n_2q_gates"] is not None]
    h1_1e_data = [r for r in h1_1e_data if r["n_2q_gates"] is not None]
    uccsd_data = [r for r in (uccsd_data or []) if r["n_2q_gates"] is not None]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8), height_ratios=[4, 1], sharex=True, dpi=300
    )

    # get number of qubits for title
    nb_qubits = None
    if statevector_data:
        nb_qubits = statevector_data[0].get("nb_qubits", None)

    # Get HF baseline from statevector 0_givens circuit
    hf_baseline = None
    if statevector_data:
        for r in statevector_data:
            if r["circuit"] == "0_givens" and r["nb_params"] == 0:
                hf_baseline = r["energy_error_mean"]
                break

    # Create mapping from circuit name to 2q gate count from H1-1E data
    circuit_to_n2q = {}
    if h1_1e_data:
        for r in h1_1e_data:
            circuit_to_n2q[r["circuit"]] = r["n_2q_gates"]

    # Plot H1-1E data
    if h1_1e_data:
        h1_1e_sorted = sorted(h1_1e_data, key=lambda x: x["n_2q_gates"])
        costs = [r["n_2q_gates"] for r in h1_1e_sorted]
        errors = [r["energy_error_mean"] for r in h1_1e_sorted]
        error_bars = [r["energy_error_std"] for r in h1_1e_sorted]
        params = [r["nb_params"] for r in h1_1e_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="o-",
            label="H1-1E (Emulator)",
            color=COLORS["QMC-Givens"],
            markersize=10,
            linewidth=3,
            capsize=3,
            capthick=1.2,
            zorder=2,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(6, -8),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                color=COLORS["H1-1E_annotation"],
            )

    # Plot H1-1 data
    if h1_1_data:
        h1_1_sorted = sorted(h1_1_data, key=lambda x: x["n_2q_gates"])
        costs = [r["n_2q_gates"] for r in h1_1_sorted]
        errors = [r["energy_error_mean"] for r in h1_1_sorted]
        error_bars = [r["energy_error_std"] for r in h1_1_sorted]
        params = [r["nb_params"] for r in h1_1_sorted]

        ax1.plot(
            costs,
            errors,
            "^-",
            label="H1-1 (QPU)",
            color=COLORS["H1-1"],
            markersize=10,
            linewidth=3,
            zorder=3,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(7, -12),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                color=COLORS["H1-1_annotation"],
            )

    # Plot UCCSD data (H1-1E)
    if uccsd_data:
        uccsd_sorted = sorted(uccsd_data, key=lambda x: x["n_2q_gates"])
        costs = [r["n_2q_gates"] for r in uccsd_sorted]
        errors = [r["energy_error_mean"] for r in uccsd_sorted]
        error_bars = [r["energy_error_std"] for r in uccsd_sorted]
        params = [r["nb_params"] for r in uccsd_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="s-",
            label="H1-1E (UCCSD)",
            color=COLORS["QMC-UCC"],
            markersize=9,
            linewidth=2,
            alpha=0.8,
            capsize=3,
            capthick=1.2,
        )

        # Add parameter count annotations
        for cost, error, np in zip(costs, errors, params):
            ax1.annotate(
                str(np),
                (cost, error),
                xytext=(5, 10),
                textcoords="offset points",
                fontsize=10,
                fontweight="bold",
                color=COLORS["UCC_annotatation"],
            )

    # Plot ADAPT-VQE data (H1-Emulator_results)
    if adapt_uccsd_data:
        adapt_uccsd_sorted = sorted(adapt_uccsd_data, key=lambda x: x["n_2q_gates"])
        costs = [r["n_2q_gates"] for r in adapt_uccsd_sorted]
        errors = [r["energy_error_mean"] for r in adapt_uccsd_sorted]
        error_bars = [r["energy_error_std"] for r in adapt_uccsd_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="^-",
            label="ADAPT-VQE (UCC pool)",
            color=COLORS["ADAPT-UCC"],
            markersize=8,
            linewidth=2,
            capsize=3,
            capthick=1.2,
            zorder=2,
        )

    if adapt_generalized_data:
        adapt_generalized_sorted = sorted(
            adapt_generalized_data, key=lambda x: x["n_2q_gates"]
        )
        costs = [r["n_2q_gates"] for r in adapt_generalized_sorted]
        errors = [r["energy_error_mean"] for r in adapt_generalized_sorted]
        error_bars = [r["energy_error_std"] for r in adapt_generalized_sorted]

        ax1.errorbar(
            costs,
            errors,
            yerr=error_bars,
            fmt="D-",
            label=adapt_label(molecule),
            color=COLORS["ADAPT-generalized"],
            markersize=8,
            linewidth=2,
            capsize=3,
            capthick=1.2,
            zorder=2,
        )

    # Plot statevector data in subplot - match circuit names to 2q gate counts
    if statevector_data and circuit_to_n2q:
        # Only plot statevector points that have matching H1-1E circuits
        sv_with_n2q = []
        for r in statevector_data:
            if r["circuit"] in circuit_to_n2q:
                sv_with_n2q.append(
                    {
                        "n_2q_gates": circuit_to_n2q[r["circuit"]],
                        "energy_error_mean": r["energy_error_mean"],
                    }
                )

        if sv_with_n2q:
            sv_sorted = sorted(sv_with_n2q, key=lambda x: x["n_2q_gates"])
            costs = [r["n_2q_gates"] for r in sv_sorted]
            errors = [r["energy_error_mean"] for r in sv_sorted]

            ax2.plot(
                costs,
                errors,
                "o-",
                label="Statevector",
                color=COLORS["QMC-Givens"],
                markersize=7,
                linewidth=2,
            )

    # Plot HF baseline if available
    # if hf_baseline is not None:
    #     ax1.axhline(
    #         y=hf_baseline,
    #         color=COLORS["HF_baseline"],
    #         linestyle="--",
    #         linewidth=1.5,
    #         label="Hartree–Fock",
    #         alpha=0.6,
    #         zorder=1,
    #     )

    # Format main plot
    # ax1.set_yscale("log")

    # Reorder legend handles to put HF baseline last
    handles, labels = ax1.get_legend_handles_labels()
    if "Hartree–Fock" in labels:
        hf_idx = labels.index("Hartree–Fock")
        handles = handles[:hf_idx] + handles[hf_idx + 1 :] + [handles[hf_idx]]
        labels = labels[:hf_idx] + labels[hf_idx + 1 :] + [labels[hf_idx]]
    ax1.legend(handles, labels, fontsize=20, loc="best", frameon=False)

    # Remove top and right spines
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    # Increase tick label font sizes
    ax1.tick_params(axis="both", which="major", labelsize=14)
    # ax1.spines["bottom"].set_visible(False)

    # ax1.set_title(
    #     f"{molecule.replace('_6_spinorbs', '')} ({nb_qubits} qubits)",
    #     fontsize=14,
    #     pad=10,
    # )

    # Format statevector subplot
    ax2.set_xlabel(
        "Two-qubit Gate Count",
        fontsize=20,
        fontweight="bold",
        labelpad=6,
    )
    ax2.set_yscale("log")
    ax2.legend(fontsize=18, frameon=False)

    # Remove top and right spines
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_visible(False)
    # Increase tick label font sizes
    ax2.tick_params(axis="x", which="major", labelsize=14)
    ax2.tick_params(axis="y", which="major", labelsize=12)

    # Figure-level shared Y label
    if hasattr(fig, "supylabel"):
        fig.supylabel("Energy Error (Ha)", fontsize=20, fontweight="bold")
    else:
        fig.text(
            0.02,
            0.5,
            "Energy Error (Ha)",
            rotation="vertical",
            va="center",
            ha="center",
            fontsize=20,
            fontweight="bold",
        )

    plt.tight_layout()
    finalize_panel(fig, "energy_vs_2q_gates", molecule)

    # Save figure
    molecule_dir = os.path.join(OUTPUT_DIR, molecule)
    os.makedirs(molecule_dir, exist_ok=True)
    output_path = os.path.join(molecule_dir, f"{molecule}_energy_vs_2q_gates.svg")
    plt.savefig(output_path)  # fixed margins, see plot_style.finalize_panel
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

    # Load ADAPT-VQE hardware (H1-1E emulator) results (one curve per operator pool)
    if include_adapt:
        adapt_uccsd_results = load_adapt_results("uccsd")
        adapt_generalized_results = load_adapt_results("generalized")
    else:
        adapt_uccsd_results = {}
        adapt_generalized_results = {}

    # Get all molecules
    all_molecules = set(
        list(h1_1_results.keys())
        + list(h1_1e_results.keys())
        + list(statevector_results.keys())
        + list(uccsd_results.keys())
        + list(adapt_uccsd_results.keys())
        + list(adapt_generalized_results.keys())
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
            adapt_uccsd_results.get(molecule, []),
            adapt_generalized_results.get(molecule, []),
        )

    print(f"\n✓ All plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
