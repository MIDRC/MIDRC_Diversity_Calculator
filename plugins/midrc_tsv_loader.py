import re
from datetime import datetime
import pandas as pd


def extract_earliest_date(submitter_id_series):
    """Extracts the earliest date from datasets.submitter_id column."""

    def get_earliest_date(submitter_id):
        if pd.isna(submitter_id):
            return None
        # Find all date-like strings in the format YYYYMMDD
        dates = re.findall(r'(\d{8})', submitter_id)
        if not dates:
            return None
        # Convert to datetime and find the earliest
        date_objs = [datetime.strptime(date, "%Y%m%d") for date in dates]
        return min(date_objs).strftime("%Y-%m-%d")

    return submitter_id_series.apply(get_earliest_date)


def adjust_age(df):
    """Modifies the age_at_index column based on age_at_index_gt89."""

    def update_age(row):
        if row['age_at_index_gt89'] == "Yes":
            if pd.isna(row['age_at_index']):
                return 90
            return 90  # Explicitly set it to 90
        return row['age_at_index']

    df['age_at_index'] = df.apply(update_age, axis=1)
    return df


def process_dataframe(df, numeric_cols=None):
    """Applies transformations on a pandas DataFrame.

    - Extracts the earliest date from `datasets.submitter_id`.
    - Adjusts `age_at_index` based on `age_at_index_gt89`.
    - Converts numeric values in specified columns to string format "N-N".
    """
    # Extract earliest date
    df['date'] = extract_earliest_date(df['datasets.submitter_id'])

    # Adjust age_at_index
    df = adjust_age(df)

    # Convert numeric columns to string format "N-N"
    if numeric_cols:
        for num_col, str_col in numeric_cols.items():
            if num_col in df.columns:
                df[str_col] = df[num_col].apply(lambda x: f'{int(x)}-{int(x)}' if pd.notna(x) else x)

    return df


def process_tsv_to_tsv(input_file, output_file, numeric_cols=None):
    """Reads a TSV file, processes it, and writes back to a new TSV file."""
    df = pd.read_csv(input_file, sep='\t')
    df = process_dataframe(df, numeric_cols=numeric_cols)
    df.to_csv(output_file, sep='\t', index=False)


def process_tsv_to_dataframe(input_file, numeric_cols=None):
    """Reads a TSV file, processes it, and returns a pandas DataFrame."""
    df = pd.read_csv(input_file, sep='\t')
    return process_dataframe(df, numeric_cols=numeric_cols)


def process_dataframe_to_dataframe(df, numeric_cols=None):
    """Processes a pandas DataFrame and returns a modified DataFrame."""
    return process_dataframe(df, numeric_cols=numeric_cols)
