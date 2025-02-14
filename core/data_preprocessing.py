import numpy as np
import pandas as pd

def bin_dataframe_column(df_to_bin, column_name, cut_column_name='CUT', bins=None, labels=None, *, right=False):
    """
    Cuts the age column into bins and adds a column with the bin labels.

    Parameters:
    - df_to_bin: pandas DataFrame containing the data
    - column_name: name of the column to be binned
    - cut_column_name: name of the column to be added with the bin labels
    - bins: list of bins to be used for the binning
    - labels: list of labels for the bins
    - right: whether to use right-inclusive intervals

    Returns:
    - df: pandas DataFrame with the binned column and the labels
    """
    if column_name in df_to_bin.columns:
        if bins is None:
            bins = np.arange(0, 100, 10)  # Default bins
            # print("Generated bins:", bins)  # Uncomment to see the generated bins

        if labels is None:
            labels = []
            for i in range(len(bins) - 1):
                if isinstance(bins[i], int) and isinstance(bins[i + 1], int):
                    if i < len(bins) - 2:
                        # Adjust the upper limit for integer values
                        labels.append(f"{bins[i]}-{bins[i + 1] - 1}")
                    else:
                        # Last bin with '>=' format
                        labels.append(f">={bins[i]}")
                else:
                    # Use raw values for non-integer bins
                    labels.append(f"{bins[i]}-{bins[i + 1]}")
            # print("Generated labels:", labels)  # Uncomment to see the generated labels

        df_out = df_to_bin.assign(**{
            cut_column_name: pd.cut(
                df_to_bin[column_name],
                bins=bins,
                labels=labels,
                right=right  # Use right=False for left-inclusive intervals
            ).astype('string')
        })

        # Check for outliers and assign them to a new category
        if df_out[cut_column_name].isna().any():
            new_text = "Outlier"
            low_text = new_text + "_Low"
            high_text = new_text + "_High"
            print(f"WARNING: There are values outside the bins specified for the '{column_name}' column.")
            df_out.loc[df_out[cut_column_name].isna() & (df_out[column_name] < bins[0]), cut_column_name] = low_text
            df_out.loc[df_out[cut_column_name].isna() & (df_out[column_name] >= bins[-1]), cut_column_name] = high_text
            df_out.loc[df_out[cut_column_name].isna(), cut_column_name] = new_text
            if (df_out[cut_column_name] == low_text).sum() > 0:
                print(f"         {(df_out[cut_column_name] == low_text).sum()} values are below the minimum bin value.\n" 
                      f"         These will be placed in a new '{low_text}' category.")
            if (df_out[cut_column_name] == high_text).sum() > 0:
                print(f"         {(df_out[cut_column_name] == high_text).sum()} values are above the maximum bin value.\n" 
                      f"         These will be placed in a new '{high_text}' category.")
            if (df_out[cut_column_name] == new_text).sum() > 0:
                print(f"         {(df_out[cut_column_name] == new_text).sum()} values are outside the specified bins.\n" 
                      f"         These will be placed in a new '{new_text}' category.")

        return df_out

def combine_datasets_from_list(df_list: list[pd.DataFrame], dataset_column = '_dataset_'):
    labels = [f'Dataset {i}' for i in range(len(df_list))]  # Dataset labels
    combined_df = pd.concat(
        [df.assign(**{dataset_column: label}) for label, df in zip(labels, df_list)],
        ignore_index=True
    )
    return combined_df
