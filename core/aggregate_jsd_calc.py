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
    labels = [f'Dataset {i}' for i in range(len(df_list))]  # Dataset labels
    combined_df = pd.concat(
        [df.assign(**{dataset_column: label}) for label, df in zip(labels, df_list)],
        ignore_index=True
    )

    # Pivot table to get counts for each combination
    pivot_table = combined_df.pivot_table(index=cols_to_use, columns=dataset_column, aggfunc='size', fill_value=0)
    pivot_table = pivot_table.reset_index()

    # Convert dataset columns to string in case they are integers
    pivot_table.columns = pivot_table.columns.astype(str)

    # Create a dictionary to hold counts for each dataset
    counts_dict = {dataset: pivot_table[dataset].values if dataset in pivot_table else np.zeros(len(pivot_table)) for dataset in labels}

    return calc_jsd_from_counts_dict(counts_dict, labels)

def calc_jsd_by_features_2df(df1: pd.DataFrame, df2: pd.DataFrame, cols_to_use: list[str]) -> float:
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

    return jsd_dict['Dataset 0 vs Dataset 1']

def calc_aggregate_jsd_at_date(df1: pd.DataFrame, df2: pd.DataFrame, cols_to_use: list[str], date) -> float:
    """
    Calculate Jensen-Shannon Distance (JSD) based on features between two datasets at a specific date.

    Parameters:
    - df1: pandas DataFrame containing the first dataset
    - df2: pandas DataFrame containing the second dataset
    - cols_to_use: list of columns to use for the JSD calculation
    - date: date at which to calculate the JSD

    Returns:
    - dictionary of JSD values for each feature
    """
    df1_at_date = df1[df1['date'] <= date]
    df2_at_date = df2[df2['date'] <= date]

    return calc_jsd_by_features_2df(df1_at_date, df2_at_date, cols_to_use)
