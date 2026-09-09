"""
Compare finite-sampling (1000-shot) energy results across *all four ansatz
methods* on the same axes, one figure per molecule:

    * QMC-Givens              Givens_results/shots
    * QMC-UCC                 UCCSD_results/shots
    * ADAPT-VQE (UCC pool)    ADAPT-VQE_results/uccsd/shots_results
    * ADAPT-VQE (gen. pool)   ADAPT-VQE_results/generalized/shots_results

Each method's noiseless statevector curve is drawn faintly (dashed) behind
its shots curve as a reference. y is the absolute energy error vs the FCI
reference; error bars are shown for methods that stored a sample std
(QMC-Givens ran ``nb_samples = 10``; the others are single draws).

Usage:
    python3 scripts/compare_shots_methods.py

Output (under ``figures/shots_comparison/``):
    methods_<molecule>_shots.png        one figure per molecule
    methods_all_molecules_shots.png     combined grid
    shots_methods_summary.csv           per (molecule, method, nb_params) row
"""

import csv
import json
import os
from collections import defaultdict

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from plot_style import COLORS

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "figures", "shots_comparison")

CHEM_ACC = 1.6e-3  # Ha
SHOW_STATEVECTOR = True  # draw the noiseless reference curve behind each method

# label -> (shots dir, statevector dir, colour, marker)
METHODS = [
    (
        "QMC-Givens",
        "Givens_results/shots",
        "Givens_results/statevector",
        COLORS["H1-1E"],
        "o",
    ),
    (
        "QMC-UCC",
        "UCCSD_results/shots",
        "UCCSD_results/statevector",
        COLORS["QMC-UCC"],
        "s",
    ),
    (
        "ADAPT-VQE (UCC pool)",
        "ADAPT-VQE_results/uccsd/shots_results",
        "ADAPT-VQE_results/uccsd/statevector",
        COLORS["ADAPT-UCC"],
        "^",
    ),
    (
        "ADAPT-VQE (generalized pool)",
        "ADAPT-VQE_results/generalized/shots_results",
        "ADAPT-VQE_results/generalized/statevector",
        COLORS["ADAPT-generalized"],
        "D",
    ),
]


def _nb_params(data):
    """Parameter count for a result, tolerating the several storage styles."""
    for key in ("nb_params", "nb_givens"):
        if data.get(key) is not None:
            return data[key]
    final_params = data.get("final_params") or []
    if final_params and isinstance(final_params[0], list):
        return len(final_params[0])
    return len(final_params)


def load_method(rel_dir):
    """Return {molecule: {nb_params: {'err': mean, 'std': std_or_0}}}.

    Layout is always ``<rel_dir>/<molecule>/<circuit>/vqe_result.json``.
    ``energy_error`` is signed and may be ``[mean, std]`` (multi-sample) or a
    scalar. When several circuits map to the same nb_params the one with the
    smaller |mean error| is kept.
    """
    out = defaultdict(dict)
    root = os.path.join(BASE_DIR, rel_dir)
    if not os.path.isdir(root):
        return out

    for molecule in sorted(os.listdir(root)):
        mol_path = os.path.join(root, molecule)
        if not os.path.isdir(mol_path):
            continue
        for circuit in sorted(os.listdir(mol_path)):
            result_path = os.path.join(mol_path, circuit, "vqe_result.json")
            if not os.path.exists(result_path):
                continue
            with open(result_path) as fh:
                data = json.load(fh)

            err = data.get("energy_error")
            if err is None:
                continue
            if isinstance(err, list):
                mean, std = err[0], (err[1] if len(err) > 1 else 0.0)
            else:
                mean, std = err, 0.0

            npar = _nb_params(data)
            prev = out[molecule].get(npar)
            if prev is None or abs(mean) < abs(prev["err"]):
                out[molecule][npar] = {
                    "err": mean,
                    "std": std or 0.0,
                    "nb_samples": data.get("nb_samples"),
                    "circuit": data.get("circuit", circuit),
                }
    return out


def _series(records):
    xs = sorted(records)
    return (
        xs,
        [records[x]["err"] for x in xs],           # signed error (Ha)
        [records[x]["std"] for x in xs],           # sample std (Ha)
    )


def plot_abs_axis(ax, molecule, shots_data, sv_data):
    """Panel A: |energy error| on a log axis, shots vs statevector, no bars."""
    drew = False
    for label, _, _, color, marker in METHODS:
        if SHOW_STATEVECTOR:
            sv = sv_data[label].get(molecule, {})
            if sv:
                xs, ys, _ = _series(sv)
                ax.plot(
                    xs, [max(abs(y), 1e-12) for y in ys], "--", color=color,
                    alpha=0.4, linewidth=1, marker=marker, markersize=3,
                    zorder=1, label=f"{label} (statevector)",
                )
                drew = True

        sh = shots_data[label].get(molecule, {})
        if sh:
            xs, ys, _ = _series(sh)
            ax.plot(
                xs, [max(abs(y), 1e-12) for y in ys], marker + "-", color=color,
                markersize=7, linewidth=2, zorder=3,
                label=f"{label} (1000 shots)",
            )
            drew = True

    ax.axhline(CHEM_ACC, color="grey", ls=":", lw=1.2, label="chemical accuracy")
    ax.set_yscale("log")
    ax.set_xlabel("Number of parameters", fontsize=12)
    ax.set_ylabel("|Energy error| (Ha)", fontsize=12)
    ax.set_title(f"{molecule}: absolute error", fontsize=12, fontweight="bold")
    ax.grid(True, which="both", alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    return drew


def plot_signed_axis(ax, molecule, shots_data):
    """Panel B: signed shots error in mHa, linear, with sample-std error bars."""
    for label, _, _, color, marker in METHODS:
        sh = shots_data[label].get(molecule, {})
        if not sh:
            continue
        xs, ys, es = _series(sh)
        ys = [y * 1e3 for y in ys]
        es = [e * 1e3 for e in es]
        if any(e > 0 for e in es):
            ax.errorbar(
                xs, ys, yerr=es, fmt=marker + "-", color=color, markersize=7,
                linewidth=2, capsize=3, capthick=1.1, zorder=3, label=label,
            )
        else:
            ax.plot(
                xs, ys, marker + "-", color=color, markersize=7, linewidth=2,
                zorder=3, label=label,
            )

    ax.axhline(0, color="black", lw=0.8)
    ax.axhspan(
        -CHEM_ACC * 1e3, CHEM_ACC * 1e3, color="grey", alpha=0.15,
        label="±chemical accuracy",
    )
    ax.set_xlabel("Number of parameters", fontsize=12)
    ax.set_ylabel(r"$E_{\rm shots} - E_{\rm FCI}$ (mHa)", fontsize=12)
    ax.set_title(f"{molecule}: signed error", fontsize=12, fontweight="bold")
    ax.grid(True, alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)


def write_csv(shots_data, path):
    rows = []
    for label, *_ in METHODS:
        for molecule, records in shots_data[label].items():
            for npar, rec in sorted(records.items()):
                rows.append(
                    {
                        "molecule": molecule,
                        "method": label,
                        "nb_params": npar,
                        "circuit": rec["circuit"],
                        "nb_samples": rec["nb_samples"],
                        "signed_energy_error": rec["err"],
                        "abs_energy_error": abs(rec["err"]),
                        "sample_std": rec["std"],
                    }
                )
    rows.sort(key=lambda r: (r["molecule"], r["method"], r["nb_params"]))
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"Saved: {path}")
    return rows


def print_table(rows):
    hdr = f"{'molecule':<16}{'method':<30}{'nb_p':>5}{'abs_err':>12}{'std':>12}{'nsamp':>7}"
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['molecule']:<16}{r['method']:<30}{r['nb_params']:>5}"
            f"{r['abs_energy_error']:>12.3e}{r['sample_std']:>12.3e}"
            f"{str(r['nb_samples']):>7}"
        )
    print("-" * len(hdr))


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    shots_data = {label: load_method(sh) for label, sh, _, _, _ in METHODS}
    sv_data = {label: load_method(sv) for label, _, sv, _, _ in METHODS}

    molecules = sorted(
        {m for d in shots_data.values() for m in d}
    )
    print(f"Molecules with shots data: {molecules}\n")

    rows = write_csv(shots_data, os.path.join(OUTPUT_DIR, "shots_methods_summary.csv"))
    print()
    print_table(rows)
    print()

    for molecule in molecules:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6), dpi=300)
        plot_abs_axis(ax1, molecule, shots_data, sv_data)
        plot_signed_axis(ax2, molecule, shots_data)
        ax1.legend(fontsize=7.5, frameon=False, ncol=1, loc="lower left")
        ax2.legend(fontsize=8, frameon=False)
        fig.tight_layout()
        out = os.path.join(OUTPUT_DIR, f"methods_{molecule}_shots.png")
        fig.savefig(out, bbox_inches="tight")
        plt.close(fig)
        print(f"Saved: {out}")

    ncols = min(3, len(molecules))
    nrows = (len(molecules) + ncols - 1) // ncols
    fig, axes = plt.subplots(
        nrows, ncols, figsize=(7 * ncols, 5.5 * nrows), dpi=300, squeeze=False
    )
    for idx, molecule in enumerate(molecules):
        ax = axes[idx // ncols][idx % ncols]
        plot_abs_axis(ax, molecule, shots_data, sv_data)
        if idx == 0:
            ax.legend(fontsize=7, frameon=False, loc="lower left")
    for idx in range(len(molecules), nrows * ncols):
        axes[idx // ncols][idx % ncols].set_visible(False)
    fig.suptitle(
        "Finite-sampling (1000 shots) energy error by method",
        fontsize=15, fontweight="bold",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    out = os.path.join(OUTPUT_DIR, "methods_all_molecules_shots.png")
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    print(f"Saved: {out}")


if __name__ == "__main__":
    main()
