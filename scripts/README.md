# Plotting Scripts

This folder contains Python scripts to visualize the QMC Givens ansatz results.

## Scripts

### 1. `plot_energy_vs_hqc_cost.py`
Generates plots of energy error vs HQC cost for Givens ansatz on H1-1 and H1-1E backends.

**Features:**
- One plot per molecule (BeH2, HeH, LiH_6_spinorbs, N2)
- Main plot shows H1-1 and H1-1E results with error bars
- Subplot shows statevector energy errors
- Parameter counts annotated on data points
- Log scale for energy error

**Usage:**
```bash
python scripts/plot_energy_vs_hqc_cost.py
```

**Output:** Saves PNG files to `figures/` directory:
- `{molecule}_energy_vs_hqc_cost.png`

---

### 2. `plot_energy_vs_params.py`
Compares energy error vs number of parameters for UCCSD and Givens ansatzes.

**Features:**
- One plot per molecule
- Compares Givens (H1-1E) and UCCSD (H1-1E) on same plot
- Log scale for energy error
- Error bars for Givens data

**Usage:**
```bash
python scripts/plot_energy_vs_params.py
```

**Output:** Saves PNG files to `figures/` directory:
- `{molecule}_energy_vs_params.png`

### 3. `compare_shots_methods.py`
Overlays the 1000-shot results of **all four ansatz methods** on the same axes,
one figure per molecule:

| method | source |
| --- | --- |
| QMC-Givens | `Givens_results/shots` |
| QMC-UCC | `UCCSD_results/shots` |
| ADAPT-VQE (UCC pool) | `ADAPT-VQE_results/uccsd/shots_results` |
| ADAPT-VQE (generalized pool) | `ADAPT-VQE_results/generalized/shots_results` |

**Features:**
- Left panel: `|energy error|` vs #params, log scale, each method's noiseless
  statevector run drawn faintly behind it (toggle `SHOW_STATEVECTOR`)
- Right panel: signed error in mHa, linear, with sample-std error bars
  (QMC-Givens ran `nb_samples = 10`; the others are single draws), plus a
  ±chemical-accuracy band
- Only BeH2 and LiH_6_spinorbs have QMC-Givens/QMC-UCC shots data; N2 shows the
  two ADAPT pools only

**Usage:**
```bash
python3 scripts/compare_shots_methods.py
```

**Output:** Saves to `figures/shots_comparison/`:
- `methods_{molecule}_shots.png`
- `methods_all_molecules_shots.png`
- `shots_methods_summary.csv`

---

## Customization

Both scripts are designed to be simple and easy to modify:

- **Change backend:** Edit the `GIVENS_DIR` or `UCCSD_DIR` paths in the script
- **Adjust plot styling:** Modify colors, markers, and sizes in the `plot_molecule()` function
- **Change output format:** Replace `plt.savefig()` format (e.g., 'pdf' instead of 'png')
- **Filter data:** Add conditions in the `load_results()` functions

## Dependencies

- Python 3.6+
- matplotlib
- json (standard library)
- os (standard library)

Install matplotlib if needed:
```bash
pip install matplotlib
```
