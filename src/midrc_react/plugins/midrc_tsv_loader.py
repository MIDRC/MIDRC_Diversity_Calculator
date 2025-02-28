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
This module contains functions for processing TSV files downloaded from the data.MIDRC.org website.
"""

from datetime import datetime
import re

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
        return min(date_objs)

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


def combine_race_ethnicity(df):
    """
    Combines 'race' and 'ethnicity' columns into a new 'Race and Ethnicity' column.

    Criteria:
    - If either 'race' or 'ethnicity' is 'Not Reported', the new column contains 'Not Reported'.
    - If 'ethnicity' is 'Hispanic or Latino', the new column contains 'Hispanic or Latino'.
    - If 'ethnicity' is 'Not Hispanic or Latino', the new column contains '{race}, {ethnicity}'.

    Args:
        df (pd.DataFrame): Input DataFrame with 'race' and 'ethnicity' columns.

    Returns:
        pd.DataFrame: Modified DataFrame with the new 'Race and Ethnicity' column.
    """

    def classify(row):
        race, ethnicity = row['race'], row['ethnicity']

        if race == 'Not Reported' or ethnicity == 'Not Reported':
            return 'Not Reported'
        if ethnicity == 'Hispanic or Latino':
            return ethnicity
        return f'{race}, {ethnicity}'

    df['Race and Ethnicity'] = df.apply(classify, axis=1)
    return df


def adjust_column_names(df):
    """Adjusts column names to be more readable."""
    df = df.rename(columns={
        'sex': 'Sex',
        'race': 'Race',
        'ethnicity': 'Ethnicity',
        'covid19_positive': 'COVID-19 Positive',
    })
    return df


def process_dataframe(df):
    """Applies both transformations on a pandas DataFrame."""
    df['date'] = extract_earliest_date(df['datasets.submitter_id'])
    df = adjust_age(df)
    df = combine_race_ethnicity(df)
    df = adjust_column_names(df)
    return df


def process_tsv_to_tsv(input_file, output_file):
    """Reads a TSV file, processes it, and writes back to a new TSV file."""
    df = pd.read_csv(input_file, sep='\t')
    df = process_dataframe(df)
    df.to_csv(output_file, sep='\t', index=False)


def process_tsv_to_dataframe(input_file):
    """Reads a TSV file, processes it, and returns a pandas DataFrame."""
    df = pd.read_csv(input_file, sep='\t')
    return process_dataframe(df)


def process_dataframe_to_dataframe(df):
    """Processes a pandas DataFrame and returns a modified DataFrame."""
    return process_dataframe(df)


def preprocess_data(df):
    """Preprocesses a pandas DataFrame."""
    return process_dataframe(df)
