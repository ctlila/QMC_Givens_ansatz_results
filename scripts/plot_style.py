"""
Shared plotting style configuration for QMC Givens ansatz figures.

Import COLORS from this module in plotting scripts to keep styling consistent.
"""

# Color Scheme
COLORS = {
    "H1-1": "#F24236",
    "H1-1E": "#0077B6",
    "H1-1_annotation": "#7D2528",
    "H1-1E_annotation": "#001f3f",
    "QMC-Givens": "#0077B6",  # same colour for noisy and noiseless Givens
    "QMC-UCC": "#784c00",
    "UCC_annotatation": "#291211",
    "Statevector": "#48C9B0",
    "HF_baseline": "#444444",
    "ADAPT-UCC": "#001f3f",
    "ADAPT-generalized": "#5A189A",
}


# Panel letters for the 3x3 multi-panel figure (rows: energy vs 2q gates,
# 2q gates vs params, energy vs params; columns: LiH, BeH2, N2).
PANEL_LETTERS = {
    ("energy_vs_2q_gates", "LiH_6_spinorbs"): "a",
    ("energy_vs_2q_gates", "BeH2"): "b",
    ("energy_vs_2q_gates", "N2"): "c",
    ("2q_gates_vs_params", "LiH_6_spinorbs"): "d",
    ("2q_gates_vs_params", "BeH2"): "e",
    ("2q_gates_vs_params", "N2"): "f",
    ("energy_vs_params", "LiH_6_spinorbs"): "g",
    ("energy_vs_params", "BeH2"): "h",
    ("energy_vs_params", "N2"): "i",
}

# Fixed margins (inches) shared by every panel. All panels are 10 in wide and
# saved WITHOUT bbox_inches="tight", so at equal width in LaTeX the axes and
# the panel letters line up across the whole 3x3 grid.
PANEL_MARGINS_IN = {"left": 1.25, "right": 0.3, "top": 0.25, "bottom": 0.85}
YLABEL_X_IN = 0.3  # centre of the y-axis label, from the left edge
LETTER_POS_IN = (0.08, 0.08)  # top-left corner of the letter, from the top-left


def finalize_panel(fig, figure_kind, molecule, ylabel_ax=None):
    """Apply the shared margins, place the y label and add the panel letter.
    `ylabel_ax`: axis whose own ylabel should be moved to the shared x position
    (for figures that use fig.supylabel instead, call with None)."""
    from matplotlib.transforms import blended_transform_factory

    w, h = fig.get_size_inches()
    m = PANEL_MARGINS_IN
    fig.subplots_adjust(
        left=m["left"] / w,
        right=1 - m["right"] / w,
        top=1 - m["top"] / h,
        bottom=m["bottom"] / h,
    )
    if fig._supylabel is not None:
        fig._supylabel.set_x(YLABEL_X_IN / w)
        fig._supylabel.set_ha("center")
    if ylabel_ax is not None:
        ylabel_ax.yaxis.set_label_coords(
            YLABEL_X_IN / w,
            0.5,
            transform=blended_transform_factory(fig.transFigure, ylabel_ax.transAxes),
        )
    letter = PANEL_LETTERS.get((figure_kind, molecule))
    if letter is not None:
        fig.text(
            LETTER_POS_IN[0] / w,
            1 - LETTER_POS_IN[1] / h,
            f"({letter})",
            ha="left",
            va="top",
            fontsize=24,
            fontweight="bold",
        )
