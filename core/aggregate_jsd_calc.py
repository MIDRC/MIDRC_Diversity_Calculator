import numpy as np
import pandas as pd
from scipy.spatial import distance
import itertools


def calc_jsd_from_counts_dict(counts_dict, dataset_names):
    output_dict = {}

    # Compare each dataset combination
    for dataset1, dataset2 in itertools.combinations(dataset_names, 2):
        count1 = counts_dict[dataset1]
        count2 = counts_dict[dataset2]

        # Calculate JSD
        jsd = distance.jensenshannon(count1, count2, base=2.0)
        output_dict[f"{dataset1} vs {dataset2}"] = jsd

    # Compare each dataset to all other datasets combined
    if len(dataset_names) > 2:
        total_counts = sum([np.array(counts_dict[dataset]) for dataset in dataset_names])

        for dataset in dataset_names:
            count1 = counts_dict[dataset]
            count2 = total_counts - count1

            # Calculate JSD
            jsd = distance.jensenshannon(count1, count2, base=2.0)
            output_dict[f"{dataset} vs All Other Datasets"] = jsd

    return output_dict

def calc_jsd_by_features(df_list: list[pd.DataFrame], cols_to_use: list[str]) -> dict[str, float]:
    """
    Calculate Jensen-Shannon Distance (JSD) based on features based on input datasets.

    Parameters:
    - df: pandas DataFrame containing the data
    - sampling_data: an instance of SamplingData class with dataset information
    - age_bins: a boolean indicating whether to consider age bins in the calculation

    Returns:
    - dictionary of JSD values for each dataset combination
    """
    dataset_column = '_dataset_'  # Temporary column name to store dataset information
    combined_df = pd.concat(
        [df.assign(**{dataset_column: i}) for i, df in enumerate(df_list)],
        ignore_index=True
    )

    # Pivot table to get counts for each combination
    pivot_table = combined_df.pivot_table(index=cols_to_use, columns=dataset_column, aggfunc='size', fill_value=0)
    pivot_table = pivot_table.reset_index()

    # Convert dataset columns to string in case they are integers
    pivot_table.columns = pivot_table.columns.astype(str)

    # Create a dictionary to hold counts for each dataset
    dataset_names = range(len(df_list))
    counts_dict = {dataset: pivot_table[dataset].values if dataset in pivot_table else np.zeros(len(pivot_table)) for dataset in dataset_names}

    return calc_jsd_from_counts_dict(counts_dict, dataset_names)

def calc_jsd_by_features(df1: pd.DataFrame, df2: pd.DataFrame, cols_to_use: list[str]) -> dict[str, float]:
    """
    Calculate Jensen-Shannon Distance (JSD) based on features between two datasets.

    Parameters:
    - df1: pandas DataFrame containing the first dataset
    - df2: pandas DataFrame containing the second dataset
    - cols_to_use: list of columns to use for the JSD calculation

    Returns:
    - dictionary of JSD values for each feature
    """
    jsd_dict = calc_jsd_by_features([df1, df2], cols_to_use)

    return jsd_dict['0 vs 1']
