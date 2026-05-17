import pandas as pd
import matplotlib.pyplot as plt

colors = ["#8884d8", "#82ca9d", "#ff7c7c", "#8dd1e1", "#a4de6c", "#d0ed57"]

reference_energies = {
    "BeH2": -19.0970412010592,
    "HeH": -4.2251153737259655,
    "LiH_6_spinorbs": -9.078586515068864,
    "LiH_12_spinorbs": -9.012404818534343,
    "N2": -131.2557477396175,
}


def add_nb_parameters(df):
    """Add the number of optimized parameters for each row."""
    for index, row in df.iterrows():
        nb_params = None

        if "used_params_indices" in row and isinstance(
            row["used_params_indices"], list
        ):
            nb_params = len(row["used_params_indices"])
        elif "optimal_params" in row:
            optimal_params = row["optimal_params"]
            if isinstance(optimal_params, list):
                if len(optimal_params) > 0 and isinstance(optimal_params[0], list):
                    nb_params = len(optimal_params[0])
                else:
                    nb_params = len(optimal_params)

        df.at[index, "nb_parameters"] = nb_params


def load_pandas_dataframe(pklfile="experiments/all_results.pkl"):
    """Load a pandas dataframe from pickle file"""
    df = pd.read_pickle(pklfile)
    return df


def plot_general(
    df,
    x_key,
    y_key,
    molecule="HeH",
    filters=None,
    group_by=None,
    reference_line=None,
    title=None,
    xlabel=None,
    ylabel=None,
    annotate=False,
    y_transform=None,
    save_path=None,
    figsize=(10, 6),
    log_x=None,
    log_y=False,
    custom_colors=colors,
):
    """
    A general plotting function for VQE results that handles both old single-value format
    and new format with samples (mean and std).
    """
    plt.figure(figsize=figsize)

    if filters is None:
        filters = {}

    base_filter = df["molecule"] == molecule

    if x_key == "nb_parameters":
        if "nb_parameters" not in df.columns or df["nb_parameters"].isna().any():
            add_nb_parameters(df)

    for col, values in filters.items():
        if isinstance(values, list):
            col_filter = df[col].isin(values)
        else:
            col_filter = df[col] == values
        base_filter = base_filter & col_filter

    filtered_df = df[base_filter].copy()

    if filtered_df.empty:
        print(f"Warning: No data found with the specified filters for {molecule}")
        return

    if x_key == "shots":
        log_x = True

    if group_by:
        groups = filtered_df.groupby(group_by)

        for i, (name, group) in enumerate(groups):
            sorted_group = group.sort_values(x_key)
            has_samples = "nb_samples" in sorted_group.columns

            y_values = []
            y_errors = []

            for _, row in sorted_group.iterrows():
                if (
                    has_samples
                    and isinstance(row[y_key], (list, tuple))
                    and len(row[y_key]) == 2
                ):
                    mean_val = row[y_key][0]
                    std_val = row[y_key][1]

                    if y_transform:
                        mean_val = y_transform(mean_val, molecule)
                        std_val = std_val

                    y_values.append(mean_val)
                    y_errors.append(std_val)
                else:
                    val = row[y_key]
                    if y_transform:
                        val = y_transform(val, molecule)
                    y_values.append(val)
                    y_errors.append(0)

            color_idx = i % len(custom_colors)
            plt.errorbar(
                sorted_group[x_key],
                y_values,
                yerr=y_errors,
                fmt="o-",
                markersize=8,
                label=f"{group_by}={name}",
                color=custom_colors[color_idx],
                capsize=5,
            )

            if annotate:
                for j, (idx, row) in enumerate(sorted_group.iterrows()):
                    if (
                        has_samples
                        and isinstance(row[y_key], (list, tuple))
                        and len(row[y_key]) == 2
                    ):
                        y_val = (
                            y_transform(row[y_key][0], molecule)
                            if y_transform
                            else row[y_key][0]
                        )
                        std_val = row[y_key][1]
                        annotation_text = f"{y_val:.4f} ± {std_val:.4f}"
                    else:
                        y_val = (
                            y_transform(row[y_key], molecule)
                            if y_transform
                            else row[y_key]
                        )
                        annotation_text = f"{y_val:.4f}"

                    plt.annotate(
                        annotation_text,
                        (row[x_key], y_values[j]),
                        textcoords="offset points",
                        xytext=(0, 10),
                        ha="center",
                        fontsize=8,
                    )
    else:
        sorted_df = filtered_df.sort_values(x_key)
        has_samples = "nb_samples" in sorted_df.columns

        y_values = []
        y_errors = []

        for _, row in sorted_df.iterrows():
            if (
                has_samples
                and isinstance(row[y_key], (list, tuple))
                and len(row[y_key]) == 2
            ):
                mean_val = row[y_key][0]
                std_val = row[y_key][1]

                if y_transform:
                    mean_val = y_transform(mean_val, molecule)
                    std_val = std_val

                y_values.append(mean_val)
                y_errors.append(std_val)
            else:
                val = row[y_key]
                if y_transform:
                    val = y_transform(val, molecule)
                y_values.append(val)
                y_errors.append(0)

        plt.errorbar(
            sorted_df[x_key],
            y_values,
            yerr=y_errors,
            fmt="o-",
            markersize=8,
            color=custom_colors[0],
            capsize=5,
        )

        if annotate:
            for j, (idx, row) in enumerate(sorted_df.iterrows()):
                if (
                    has_samples
                    and isinstance(row[y_key], (list, tuple))
                    and len(row[y_key]) == 2
                ):
                    y_val = (
                        y_transform(row[y_key][0], molecule)
                        if y_transform
                        else row[y_key][0]
                    )
                    std_val = row[y_key][1]
                    annotation_text = f"{y_val:.4f} ± {std_val:.4f}"
                else:
                    y_val = (
                        y_transform(row[y_key], molecule) if y_transform else row[y_key]
                    )
                    annotation_text = f"{y_val:.4f}"

                plt.annotate(
                    annotation_text,
                    (row[x_key], y_values[j]),
                    textcoords="offset points",
                    xytext=(0, 10),
                    ha="center",
                    fontsize=8,
                )

    if log_x:
        plt.xscale("log")
    if log_y:
        plt.yscale("log")

    if reference_line:
        plt.axhline(
            y=reference_line["value"],
            color=reference_line.get("color", "r"),
            linestyle=reference_line.get("linestyle", "--"),
            label=reference_line.get("label", "Reference"),
        )

    plt.xlabel(xlabel or x_key, fontsize=20)
    plt.ylabel(ylabel or y_key, fontsize=20)
    plt.xticks(fontsize=14)
    plt.yticks(fontsize=14)

    if title:
        plt.title(title, fontsize=14)

    plt.tight_layout()

    if group_by or reference_line:
        plt.legend(fontsize=15)

    if save_path:
        plt.savefig(save_path, dpi=300, bbox_inches="tight")

    plt.show()


if __name__ == "__main__":

    df = load_pandas_dataframe("Givens_results/statevector/SI_results.pkl")

    # First SI plot : final energy error vs number of parameters, grouped by number of shots, for BeH2 molecule, only for zeros param mode
    plot_general(
        df=df,
        x_key="nb_parameters",
        y_key="final_elec_energy",
        molecule="BeH2",
        filters={
            "param_mode": ["zeros"],
            "shot_dir": [
                "statevector",
                "no_noise_100_shots",
                "no_noise_1000_shots",
                "no_noise_10000_shots",
                "no_noise_100000_shots",
            ],
        },
        group_by="shot_dir",
        ylabel="Energy Error (Ha)",
        xlabel="Number of Parameters",
        y_transform=lambda y, mol: abs(y - reference_energies[mol]),
        annotate=False,
        title=None,
        save_path="figures/SI/BeH2_final_energy_error_vs_nb_parameters_by_shots.svg",
        log_x=False,
        log_y=False,
        custom_colors=colors,
    )

    # Second SI plot : final energy error vs number of parameters, grouped by param mode (zeros vs load), for BeH2 molecule, only for 1000 shots
    plot_general(
        df=df,
        x_key="nb_parameters",
        y_key="final_elec_energy",
        molecule="BeH2",
        filters={
            "param_mode": ["zeros", "load"],
            "shot_dir": ["no_noise_1000_shots"],
        },
        group_by="param_mode",
        ylabel="Energy Error (Ha)",
        xlabel="Number of Parameters",
        y_transform=lambda y, mol: abs(y - reference_energies[mol]),
        annotate=False,
        title=None,
        save_path="figures/SI/BeH2_final_energy_error_vs_nb_parameters_1000shots_zeros_vs_load_QMC.svg",
        log_x=False,
        log_y=False,
        custom_colors=colors,
    )
