#!/usr/bin/env python3
"""
Find all excluded VQE result files (named _vqe_result.json).
These are files that have been intentionally excluded by renaming.
"""

import os
from pathlib import Path


def find_excluded_results(root_dir="."):
    """Recursively find all _vqe_result.json files and print their paths."""
    excluded_files = list(Path(root_dir).rglob("_vqe_result.json"))

    if not excluded_files:
        print("No excluded result files found.")
        return

    print(f"Found {len(excluded_files)} excluded result file(s):\n")
    for file_path in sorted(excluded_files):
        print(file_path)


if __name__ == "__main__":
    # Change to the repository root (parent of scripts directory)
    repo_root = Path(__file__).parent.parent
    os.chdir(repo_root)
    find_excluded_results()
