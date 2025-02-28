#  Copyright (c) 2025 Medical Imaging and Data Resource Center (MIDRC).
#
#      Licensed under the Apache License, Version 2.0 (the "License");
#      you may not use this file except in compliance with the License.
#      You may obtain a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#      Unless required by applicable law or agreed to in writing, software
#      distributed under the License is distributed on an "AS IS" BASIS,
#      WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#      See the License for the specific language governing permissions and
#      limitations under the License.
#

"""
This module contains functions for calculating various numerical distance metrics between datasets.
"""

import itertools
import logging
from types import SimpleNamespace

import numpy as np
from scipy.stats import ks_2samp, wasserstein_distance
from sklearn.preprocessing import MaxAbsScaler, MinMaxScaler, RobustScaler, StandardScaler

from midrc_react.core.aggregate_jsd_calc import calc_jsd_from_counts_dict
from midrc_react.core.cucconi import cucconi_test


def calc_numerical_metric_by_feature(df, feature: str, dataset_column: str, metric_function):
    """
    Calculate a specified metric based on a single feature for input datasets.

    Parameters:
    - df: pandas DataFrame containing the data
    - feature: a string representing the feature to calculate the metric for
    - sampling_data: an instance of SamplingData class with dataset information
    - metric_function: a function to calculate the desired metric (e.g., cucconi, ks_2samp)

    Returns:
    - A dictionary containing metric results for each dataset combination.
    """
    dataset_names = df[dataset_column].unique()
    metric_dict = {}

    # Compare each dataset combination
    for dataset1, dataset2 in itertools.combinations(dataset_names, 2):
        # Extract feature values for both datasets
        values1 = df.loc[df[dataset_column] == dataset1, feature]
        values2 = df.loc[df[dataset_column] == dataset2, feature]

        # Calculate the metric
        metric_result = metric_function(values1, values2)
        metric_dict[f"{dataset1} vs {dataset2}"] = metric_result.statistic

    # Compare each dataset to all other datasets combined
    if len(dataset_names) > 2:
        for dataset in dataset_names:
            # Extract feature values for the current dataset and all other datasets
            values1 = df.loc[df[dataset_column] == dataset, feature]
            values_other = df.loc[df[dataset_column] != dataset, feature]

            # Calculate the metric
            metric_result = metric_function(values1, values_other)
            metric_dict[f"{dataset} vs All Other Datasets"] = metric_result.statistic

    return metric_dict


def calc_cucconi_by_feature(df, feature: str, dataset_column: str = '_dataset_', scaling: str = None):
    """
    Calculate the Cucconi test for a specific feature.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        feature (str): The name of the feature to calculate the metric for.
        dataset_column (str, optional): The name of the column containing the dataset information.
                                        Defaults to '_dataset_'.
        scaling (str, optional): The scaling method to use for the feature. Defaults to None.
                                 (e.g., 'standard', 'minmax', 'maxabs', or 'robust')

    Returns:
        dict: A dictionary containing the metric results for each dataset combination.
    """
    if scaling is not None:
        logging.warning('Cucconi test is not affected by scaling. Ignoring scaling method.')
    calc_df = df  # if scaling is None else scale_feature(df, feature, method=scaling)

    def cucconi_2samp_test(values1, values2):
        return cucconi_test(values1, values2, method='permutation')
    return calc_numerical_metric_by_feature(calc_df, feature, dataset_column, cucconi_2samp_test)


def calc_ks2_samp_by_feature(df, feature: str, dataset_column: str = '_dataset_', scaling: str = None):
    """
    Calculate the Kolmogorov-Smirnov test for a specific feature.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        feature (str): The name of the feature to calculate the metric for.
        dataset_column (str, optional): The name of the column containing the dataset information.
                                        Defaults to '_dataset_'.
        scaling (str, optional): The scaling method to use for the feature. Defaults to None.
                                (e.g., 'standard', 'minmax', 'maxabs', or 'robust')

    Returns:
        dict: A dictionary containing the metric results for each dataset combination.
    """
    if scaling is not None:
        logging.warning('Kolmogorov-Smirnov test is not affected by scaling. Ignoring scaling method.')
    calc_df = df  # if scaling is None else scale_feature(df, feature, method=scaling)
    return calc_numerical_metric_by_feature(calc_df, feature, dataset_column, ks_2samp)


def calc_wasserstein_by_feature(df, feature: str, dataset_column: str = '_dataset_', scaling: str = None):
    """
    Calculate the Wasserstein distance for a specific feature.

    Args:
        df (pd.DataFrame): The DataFrame containing the data.
        feature (str): The name of the feature to calculate the metric for.
        dataset_column (str, optional): The name of the column containing the dataset information.
                                        Defaults to '_dataset_'.
        scaling (str, optional): The scaling method to use for the feature. Defaults to None.
                                (e.g., 'standard', 'minmax', 'maxabs', or 'robust')

    Returns:
        dict: A dictionary containing the metric results for each dataset combination.
    """
    # We need to define a function that returns a SimpleNamespace with a 'statistic' attribute
    def w_d_calc(values1, values2):
        return SimpleNamespace(statistic=wasserstein_distance(values1, values2))
    calc_df = df if scaling is None else scale_feature(df, feature, method=scaling)
    return calc_numerical_metric_by_feature(calc_df, feature, dataset_column, w_d_calc)


_scale_values_supported_methods_dict = {
        'StandardScaler': ['std', 'standard', 'Standard', 'StandardScaler', 'norm', 'normal', 'Normal', 'Norm'],
        'MinMaxScaler': ['minmax', 'min-max', 'MinMax', 'MinMaxScaler'],
        'MaxAbsScaler': ['maxabs', 'max-abs', 'MaxAbs', 'MaxAbsScaler'],
        'RobustScaler': ['robust', 'rob', 'Robust', 'Rob', 'RobustScalar'],
    }


def get_supported_scaling_methods():
    """
    Get a list of supported scaling methods.

    Returns:
        list: A list of supported scaling methods.
    """
    return [*itertools.chain(*_scale_values_supported_methods_dict.values())]


def scale_values(values, method: str = 'standard'):
    """
    Normalize a feature to mean 0 and standard deviation 1.

    Parameters:
    - values: a list of values to normalize

    Returns:
    - A copy of the DataFrame with the feature normalized.
    """
    if method is None or not method.strip():
        logging.warning("No scaling method specified. Returning original DataFrame.")
        return values

    if method in _scale_values_supported_methods_dict['StandardScaler']:
        scaler = StandardScaler()
    elif method in _scale_values_supported_methods_dict['MinMaxScaler']:
        scaler = MinMaxScaler()
    elif method in _scale_values_supported_methods_dict['MaxAbsScaler']:
        scaler = MaxAbsScaler()
    elif method in _scale_values_supported_methods_dict['RobustScaler']:
        scaler = RobustScaler()
    else:
        raise ValueError(f"Invalid normalization method: {method}. \n\
                           Please use one of the following methods: 'standard', 'minmax', 'maxabs', or 'robust'.")

    values_scaled = scaler.fit_transform(values)
    return values_scaled


def scale_feature(df, feature: str, method: str = 'standard'):
    """
    Normalize a feature to mean 0 and standard deviation 1.

    Parameters:
    - df: pandas DataFrame containing the data
    - feature: a string representing the feature to normalize

    Returns:
    - A copy of the DataFrame with the feature normalized.
    """
    if method is None or not method.strip():
        logging.warning("No scaling method specified. Returning original DataFrame.")
        return df

    df_normalized = df.copy()
    df_normalized[feature] = scale_values(df[[feature]], method=method)
    return df_normalized


def generate_histogram(df, dataset_column, dataset_name, feature_column, bin_width=0.01):
    """
    Generate a histogram for a specific dataset within a DataFrame.

    Parameters:
    - df: DataFrame containing the dataset.
    - x_coordinates: Array of x-coordinates for the histogram.
    - dataset_name: Name of the dataset within the DataFrame.
    - feature_column: Name of the feature column within the DataFrame.
    - bin_width: Width of each histogram bin (default is 0.01).

    Returns:
    - hist: Array of histogram values.
    - bins: Array of bin edges.

    Enhance readability by generating a histogram for a specific dataset based on the provided x-coordinates and bin
    width.
    """
    x_coordinates = df[feature_column].to_numpy()
    d = df.loc[df[dataset_column] == dataset_name, feature_column].to_numpy()
    bins = np.arange(np.floor(min(x_coordinates)), np.ceil(max(x_coordinates)) + bin_width, bin_width)
    hist, bins = np.histogram(d, bins=bins, density=True)
    return hist, bins


def build_histogram_dict(df, dataset_column, datasets, feature_column, bin_width, scaling_method=None):
    """
    Build a dictionary of histogram data for a specific dataset.

    Parameters:
    - df: DataFrame containing the dataset.
    - dataset_column: Name of the dataset column within the DataFrame.
    - feature_column: Name of the feature column within the DataFrame.
    - bin_width: Width of each histogram bin (default is 0.01).
    - scaling_method: Method to use for scaling the feature column (default is None).

    Returns:
    - hist_dict: Dictionary containing histogram data for the specified dataset.
    """
    hist_dict = {}
    for dataset in datasets:
        calc_df = df if scaling_method is None else scale_feature(df, feature_column, method=scaling_method)
        hist, bins = generate_histogram(calc_df, dataset_column, dataset, feature_column, bin_width)
        hist_dict[dataset] = hist
        if hist_dict.get('bins') is None:
            hist_dict['bins'] = bins

    return hist_dict


def calc_distances_via_df(famd_df, feature_column, dataset_column: str = '_dataset_', *,
                          distance_metrics: tuple[str] = ('all'), jsd_scaled_bin_width=0.01):
    """
    Calculate various distance metrics based on histogram data.

    This function computes Jensen-Shannon Divergence (JSD),
    Wasserstein distance, Kolmogorov-Smirnov (KS) statistics,
    and Cucconi distance, with optional scaling methods for
    Wasserstein and KS distances. The results are returned as a
    dictionary where keys represent the metric names.

    Parameters:
    - famd_df (DataFrame): A DataFrame containing FAMD (Factorial Analysis of Mixed Data) results.
    - hist_dict (dict): A dictionary containing histogram data for each dataset.
    - sampling_data: An object containing dataset sampling information, including
                     dataset_column and datasets attributes.
    - distance_metric (tuple): A tuple of strings specifying which distance metrics to compute.
                               Use 'all' to compute all available metrics or specify individual metrics
                               (e.g., 'jsd', 'wass', 'ks2', 'cuc') along with optional scaling
                               options (e.g., 'wass(std)', 'ks2(rob)', etc.).

    Returns:
    - dict: A dictionary with keys as distance metric names and values as the computed metrics.
            For example, output could include keys like 'jsd', 'wass', 'ks2', 'cuc', etc.
            If specific scaling options are computed, keys would include these as well,
            such as 'wass(std)', 'jsd(rob)', etc.
    """
    output = {}
    calc_all = 'all' in distance_metrics

    # Mapping of distance metrics to their respective functions
    distance_metric_functions = {
        'jsd': {'func': lambda scaling=None: calc_jsd_from_counts_dict(
                                 build_histogram_dict(famd_df, dataset_column, famd_df[dataset_column].unique(),
                                                      feature_column, bin_width=jsd_scaled_bin_width,
                                                      scaling_method=scaling),
                                 famd_df[dataset_column].unique()),
                'scaling': True},
        'wass': {'func': lambda scaling=None: calc_wasserstein_by_feature(famd_df, feature_column, dataset_column,
                                                                          scaling=scaling),
                 'scaling': True},
        'ks2': {'func': lambda: calc_ks2_samp_by_feature(famd_df, feature_column, dataset_column),
                'scaling': False},
        'cuc': {'func': lambda: calc_cucconi_by_feature(famd_df, feature_column, dataset_column),
                'scaling': False},
    }

    # Additional scaling options for metrics that are affected by scaling
    scaling_options = _scale_values_supported_methods_dict

    for metric, func in distance_metric_functions.items():
        if calc_all or metric in distance_metrics:
            output[metric] = func['func']()

        # Check for scaling options
        if func['scaling']:
            for scale_list in scaling_options.values():
                for scale in scale_list:
                    if calc_all or f'{metric}({scale})' in distance_metrics:
                        output[f'{metric}({scale})'] = func['func'](scaling=scale)
                        if calc_all:
                            break

    if not calc_all:
        calculated_metrics = list(output.keys())
        for metric in distance_metrics:
            if metric not in calculated_metrics:
                logging.warning("Metric %s was not calculated. Please check your input.", metric)
                if distance_metric_functions[metric.split('(')[0]]['scaling'] is False:
                    logging.warning("Metric %s is not affected by scaling.", metric.split('(')[0])

    return output
