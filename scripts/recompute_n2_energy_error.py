#!/usr/bin/env python3
"""
Recompute energy_error for all N2 JSON result files in the repository.

New value:
    energy_error = final_elec_energy - corrected_reference_energy
"""

import json
from pathlib import Path


# Set your corrected N2 reference energy here.
CORRECTED_REFERENCE_ENERGY = -131.2680802372299

# Optional settings
ROOT_DIR = Path(__file__).resolve().parent.parent
DRY_RUN = False


def iter_json_files(root_dir: Path):
    """Yield JSON files under root_dir, skipping hidden directories."""
    for path in root_dir.rglob("*.json"):
        if any(part.startswith(".") for part in path.parts):
            continue
        yield path


def recompute_energy_errors(
    root_dir: Path, corrected_reference_energy: float, dry_run: bool
):
    """Update energy_error for JSON files with molecule == N2 and numeric final_elec_energy."""
    scanned = 0
    matched_n2 = 0
    updated = 0
    skipped_missing_or_invalid = 0
    skipped_decode_error = 0

    for file_path in iter_json_files(root_dir):
        scanned += 1

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            skipped_decode_error += 1
            continue

        if not isinstance(data, dict) or data.get("molecule") != "N2":
            continue

        matched_n2 += 1

        final_elec_energy = data.get("final_elec_energy")
        if not isinstance(final_elec_energy, (int, float)):
            skipped_missing_or_invalid += 1
            continue

        data["energy_error"] = float(final_elec_energy) - corrected_reference_energy

        if not dry_run:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
                f.write("\n")

        updated += 1

    print(f"Scanned JSON files: {scanned}")
    print(f"Matched N2 files: {matched_n2}")
    print(f"Updated files: {updated}")
    print(f"Skipped (missing/invalid final_elec_energy): {skipped_missing_or_invalid}")
    print(f"Skipped (decode/read errors): {skipped_decode_error}")


def main():
    recompute_energy_errors(
        root_dir=ROOT_DIR.resolve(),
        corrected_reference_energy=CORRECTED_REFERENCE_ENERGY,
        dry_run=DRY_RUN,
    )


if __name__ == "__main__":
    main()
