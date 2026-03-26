"""
Plot energy error vs number of parameters for UCCSD and Givens ansatzes.
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


def load_givens_results(backend="H1-1E"):
    """Load Givens results from specified backend."""
    results = defaultdict(list)
    backend_dir = os.path.join(GIVENS_DIR, backend)

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
                    "nb_params": nb_params,
                    "energy_error_mean": abs(error_mean),
                    "energy_error_std": error_std,
                    "circuit": data.get("circuit", circuit_dir),
                }
            )

    return results


def load_uccsd_results(backend="H1-1E"):
    """Load UCCSD results from specified backend."""
    results = defaultdict(list)
    backend_dir = os.path.join(UCCSD_DIR, backend)

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

            if isinstance(error_mean, float):
                results[molecule].append(
                    {
                        "nb_params": nb_params,
                        "energy_error_mean": abs(error_mean),
                        "energy_error_std": error_std,
                        "circuit": data.get("circuit", circuit_dir),
                    }
                )

    return results


def plot_molecule(molecule, givens_data, uccsd_data, givens_sv_data, uccsd_sv_data):
    """Create plot for a single molecule comparing Givens and UCCSD."""
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 8), height_ratios=[4, 1], sharex=True, dpi=300
    )

    # Get HF baseline from statevector 0_givens circuit
    hf_baseline = None
    if givens_sv_data:
        for r in givens_sv_data:
            if r.get("circuit") == "0_givens" and r.get("nb_params") == 0:
                hf_baseline = r["energy_error_mean"]
                break

    # Plot Givens data on main plot
    if givens_data:
        givens_sorted = sorted(givens_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in givens_sorted]
        errors = [r["energy_error_mean"] for r in givens_sorted]
        error_bars = [r["energy_error_std"] for r in givens_sorted]

        ax1.errorbar(
            params,
            errors,
            yerr=error_bars,
            fmt="o-",
            label="QMC-Givens",
            color=COLORS["H1-1E"],
            markersize=10,
            linewidth=3,
            capsize=3,
            capthick=1.2,
            zorder=3,
        )

    # Plot UCCSD data on main plot
    if uccsd_data:
        uccsd_sorted = sorted(uccsd_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in uccsd_sorted]
        errors = [r["energy_error_mean"] for r in uccsd_sorted]
        error_bars = [r["energy_error_std"] for r in uccsd_sorted]
        has_errors = any(e > 0 for e in error_bars)

        if has_errors:
            ax1.errorbar(
                params,
                errors,
                yerr=error_bars,
                fmt="s-",
                label="QMC-UCC",
                color=COLORS["QMC-UCC"],
                markersize=8,
                linewidth=2,
                capsize=3,
                capthick=1.2,
                zorder=1,
            )
        else:
            ax1.plot(
                params,
                errors,
                "s-",
                label="QMC-UCC",
                color=COLORS["QMC-UCC"],
                markersize=8,
                linewidth=2,
                zorder=1,
            )

    # Plot Givens statevector data in subplot
    if givens_sv_data:
        givens_sv_sorted = sorted(givens_sv_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in givens_sv_sorted]
        errors = [r["energy_error_mean"] for r in givens_sv_sorted]

        ax2.plot(
            params,
            errors,
            "o-",
            label="QMC-Givens",
            color=COLORS["Statevector"],
            markersize=6,
            linewidth=2,
            zorder=3,
        )

    # Plot UCCSD statevector data in subplot
    if uccsd_sv_data:
        uccsd_sv_sorted = sorted(uccsd_sv_data, key=lambda x: x["nb_params"])
        params = [r["nb_params"] for r in uccsd_sv_sorted]
        errors = [r["energy_error_mean"] for r in uccsd_sv_sorted]
        error_bars = [r["energy_error_std"] for r in uccsd_sv_sorted]
        has_errors = any(e > 0 for e in error_bars)

        if has_errors:
            ax2.errorbar(
                params,
                errors,
                yerr=error_bars,
                fmt="s-",
                label="QMC-UCC",
                color=COLORS["QMC-UCC"],
                markersize=7,
                linewidth=2,
                capsize=3,
                capthick=1.2,
                zorder=1,
            )
        else:
            ax2.plot(
                params,
                errors,
                "s-",
                label="QMC-UCC",
                color=COLORS["QMC-UCC"],
                markersize=7,
                linewidth=2,
                zorder=1,
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
    # ax1.set_title(
    #     f"{molecule} - Energy Error vs Number of Parameters",
    #     fontsize=14,
    #     fontweight="bold",
    # )

    # Reorder legend handles: QMC-Givens, UCCSD, then Hartree-Fock last
    handles, labels = ax1.get_legend_handles_labels()
    desired_order = ["QMC-Givens", "QMC-UCC", "Hartree–Fock"]
    reordered_handles = []
    reordered_labels = []
    for label in desired_order:
        if label in labels:
            idx = labels.index(label)
            reordered_handles.append(handles[idx])
            reordered_labels.append(label)
    ax1.legend(
        reordered_handles, reordered_labels, fontsize=20, loc="best", frameon=False
    )

    # Remove top and right spines
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    # Increase tick label font sizes
    ax1.tick_params(axis="both", which="major", labelsize=14)

    # Format statevector subplot
    ax2.set_xlabel(
        "Number of Parameters",
        fontsize=20,
        fontweight="bold",
        labelpad=6,
    )
    ax2.set_yscale("log")
    # ax2.set_ylim([1e-2, 0])

    # Reorder legend handles to match ax1: QMC-Givens, UCCSD, then Hartree-Fock last
    handles2, labels2 = ax2.get_legend_handles_labels()
    desired_order = ["QMC-Givens", "QMC-UCC", "Hartree–Fock"]
    reordered_handles2 = []
    reordered_labels2 = []
    for label in desired_order:
        if label in labels2:
            idx = labels2.index(label)
            reordered_handles2.append(handles2[idx])
            reordered_labels2.append(label)
    ax2.legend(
        reordered_handles2, reordered_labels2, fontsize=20, loc="best", frameon=False
    )
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
    plt.subplots_adjust(left=0.12)

    # Save figure
    molecule_dir = os.path.join(OUTPUT_DIR, molecule)
    os.makedirs(molecule_dir, exist_ok=True)
    output_path = os.path.join(molecule_dir, f"{molecule}_energy_vs_params.pdf")
    plt.savefig(output_path, bbox_inches="tight")
    print(f"Saved: {output_path}")

    plt.close()


def main():
    """Main function to generate all plots."""
    print("Loading results...")

    # Load H1-1E results
    givens_results = load_givens_results("H1-1E")
    uccsd_results = load_uccsd_results("H1-1E")

    # Load statevector results
    givens_sv_results = load_givens_results("statevector")
    uccsd_sv_results = load_uccsd_results("statevector")

    # Get all molecules
    all_molecules = set(
        list(givens_results.keys())
        + list(uccsd_results.keys())
        + list(givens_sv_results.keys())
        + list(uccsd_sv_results.keys())
    )

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

        plot_molecule(
            molecule,
            givens_data,
            uccsd_data,
            givens_sv_results.get(molecule, []),
            uccsd_sv_results.get(molecule, []),
        )

    print(f"\n✓ All plots saved to {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
