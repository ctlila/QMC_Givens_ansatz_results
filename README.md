# QMC Givens Ansatz Results

This repository contains research data comparing the Givens rotation-based quantum ansatz with the standard Unitary Coupled Cluster Singles and Doubles (UCCSD) method for quantum chemistry calculations. The results are organized by ansatz type, molecular system, and simulation environment.

## Repository Structure

### 1. Givens_results/
Results from quantum simulations using the Givens rotation ansatz.

#### Simulation Environments:
- **`H1-1/`**: Results from Quantinuum's H1 quantum hardware
- **`H1-1E/`**: Results from noisy emulators of the H1 machine
- **`shots/`**: Noiseless simulations with finite sampling (shot noise only)
- **`statevector/`**: Exact statevector simulations (no noise, no sampling error)

#### Molecular Systems:
Each environment contains subdirectories for different molecules:
- **BeH2**: Beryllium Hydride
- **LiH_6_spinorbs**: Lithium Hydride
- **HeH**: Helium Hydride
- **N2**: Nitrogen molecule

#### Circuit Variations:
Within each molecular system, results are organized by the number of Givens rotation gates:
- `0_givens/`: No Givens rotations (HF)
- `1_givens/`, `2_givens/`, `3_givens/`, etc.: Increasing numbers of Givens rotation gates
- Special cases (e.g., `N2`): `X_dets_Y_givens/` indicates X determinants with Y Givens rotations

### 2. UCCSD_results/
Results from quantum simulations using the UCCSD ansatz for comparison.

#### Simulation Environments:
- **`H1-1E/`**: Results from H1 emulator
- **`shots/`**: Noiseless simulations with finite sampling
- **`statevector/`**: Exact statevector simulations

#### Molecular Systems:
Same molecular systems as Givens results (BeH2, LiH_6_spinorbs, HeH)

#### Parameter Variations:
Results are organized by the number of excitations (parameters):
- `BeH2_1/`, `BeH2_2/`, etc.: Different numbers of UCCSD excitation parameters
- The number suffix indicates the number of excitations in the ansatz

### 3. figures/
Contains figures and visualizations generated from the results.

### 4. scripts/
Scripts for data analysis and processing.

## Key Output Files

Within each result directory, you'll find:

- **`vqe_result.json`**: **Primary output file** containing the VQE (Variational Quantum Eigensolver) results, including optimized energies and parameters
- `circuits.json`: Quantum circuit definitions
- `pauli_expvals.json`: Pauli observable expectation values
- `circuit_expvals.json`: Circuit-based expectation values (used alongside pauli_expvals in some directories)
- `measurement_expectation.json`: Measurement statistics
- `operator.json`: Hamiltonian operator information
- `jobs.json`: Job metadata (for hardware/emulator runs)
- `counts.json`: Measurement counts (for shot-based simulations)

The additional files are included for completeness and reproducibility.

## File Naming Conventions

### Directory Organization
- **Givens results**: `/Givens_results/{Environment}/{Molecule}/{CircuitName}/`
  - Example: `Givens_results/H1-1E/BeH2/3_givens/`
  
- **UCCSD results**: `/UCCSD_results/{Environment}/{Molecule}/{ExcitationNumber}/`
  - Example: `UCCSD_results/shots/BeH2/BeH2_2/`

### Primary Output Files
All result directories follow a **unified naming convention**:
- **Primary VQE output**: `vqe_result.json`

## Purpose

This repository stores research data for publication, comparing the performance of:
1. **Givens rotation-based ansatz** (novel method)
2. **UCCSD ansatz** (standard benchmark)

across different molecular systems and quantum computing environments (hardware, emulators, and simulators).

## Data Organization Summary

```
QMC_Givens_ansatz_results/
├── Givens_results/
│   ├── H1-1/           # Quantinuum H1 hardware
│   ├── H1-1E/          # H1 emulator (noisy)
│   ├── shots/          # Finite sampling, no noise
│   └── statevector/    # Exact simulation
├── UCCSD_results/
│   ├── H1-1E/
│   ├── shots/
│   └── statevector/
├── figures/
└── scripts/
```

Each molecular system subdirectory contains multiple ansatz configurations, allowing for systematic comparison of performance as the ansatz complexity increases.
