#  Copyright (c) 2024 Medical Imaging and Data Resource Center (MIDRC).
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
This module contains classes and functions for building and processing Excel and CSV files.
"""
import importlib.util
import io
import math
import os
from pathlib import Path
import re
import warnings

import pandas as pd

from midrc_react.core.data_preprocessing import bin_dataframe_column


class DataSource:
    """
    Class representing a data source with optional plugin-based preprocessing and numeric column adjustments.
    """

    def __init__(self, data_source, custom_age_ranges=None):
        """
        Initializes the DataSource class.

        Args:
            data_source (dict): The data source configuration.
            custom_age_ranges (dict, optional): A dictionary of custom age ranges.
        """
        self.name = data_source['name']
        self.sheets = {}
        self.datatype = data_source['data type']
        self.filename = data_source['filename']
        self.data_source = data_source
        self.custom_age_ranges = custom_age_ranges
        self._numeric_cols = data_source.get('numeric_cols', {})  # Extract numeric columns from config
        self._columns = data_source.get('columns', [])
        self.raw_data = None

        # Load preprocessing plugin if specified
        self.preprocessor = None
        if 'plugin' in data_source and data_source['plugin']:
            plugin_name = data_source['plugin']
            plugin_path = os.path.join("plugins", f"{plugin_name}.py")
            self.preprocessor = self.load_plugin(plugin_path)

        # Load data
        if self.datatype == 'file' and self.filename:
            if self.filename.endswith(('.csv', '.tsv')):
                self.build_data_frames_from_csv(self.filename)
            else:
                self.build_data_frames_from_file(self.filename)
        if self.datatype == 'content' and 'content' in data_source:
            self.build_data_frames_from_content(data_source['content'])

    def raw_columns_to_use(self):
        """
        Returns a list of the raw columns to use for the analysis.

        Returns:
            list: A list of the raw columns to use for the analysis.
        """
        return self._columns

    @property
    def numeric_cols(self):
        """
        Returns a dictionary of numeric columns to use for the analysis.

        Returns:
            dict: A dictionary of numeric columns to use for the analysis.
        """
        return self._numeric_cols

    def load_plugin(self, plugin_path):
        """
        Dynamically loads a preprocessing plugin from the given path.

        Args:
            plugin_path (str): Path to the plugin Python file.

        Returns:
            A reference to the plugin's preprocess_data function if found, else None.
        """
        if not os.path.exists(plugin_path):
            orig_plugin_path = plugin_path
            plugin_path = os.path.join(Path(__file__).resolve().parent.parent, plugin_path)
            if not os.path.exists(plugin_path):
                print(f"Plugin file {orig_plugin_path} not found. Location {plugin_path} also not found.")
                return None

        module_name = os.path.basename(plugin_path).replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        if hasattr(module, "preprocess_data"):
            return module.preprocess_data
        # else:
        print(f"Plugin {module_name} does not define a 'preprocess_data' function.")
        return None

    def apply_numeric_column_adjustments(self, df: pd.DataFrame):
        """
        Applies numeric column adjustments to a DataFrame using binning.

        Args:
            df (pd.DataFrame): The input DataFrame.

        Returns:
            pd.DataFrame: The DataFrame with numeric column adjustments.
        """
        for str_col, col_dict in self._numeric_cols.items():
            num_col = col_dict['raw column'] if 'raw column' in col_dict else str_col
            bins = col_dict['bins'] if 'bins' in col_dict else None
            labels = col_dict['labels'] if 'labels' in col_dict else None

            if num_col in df.columns:
                df = bin_dataframe_column(df, num_col, str_col, bins=bins, labels=labels)
                # The following code is kept for potential future use.
                # if bins:
                #     # Apply binning if bins are provided
                #     df = bin_dataframe_column(df, num_col, str_col, bins=bins, labels=labels)
                # else:
                #     # Default "N-N" format conversion
                #     df[str_col] = df[num_col].apply(lambda x: f'{int(x)}-{int(x)}' if pd.notna(x) else x)

        return df

    def build_data_frames_from_csv(self, filename: str):
        """
        Loads and preprocesses a CSV or TSV file.

        Args:
            filename (str): The file path.

        Returns:
            None
        """
        delimiter = ',' if filename.endswith('.csv') else '\t'
        df = pd.read_csv(filename, delimiter=delimiter)

        # Apply preprocessing if a plugin is available
        if self.preprocessor:
            df = self.preprocessor(df)

        # Apply numeric column adjustments
        df = self.apply_numeric_column_adjustments(df)

        self.raw_data = df
        self.create_sheets_from_df(df)

    def build_data_frames_from_file(self, filename: str):
        """
        Loads an Excel file.

        Args:
            filename (str): The file path.

        Returns:
            None
        """
        file = pd.ExcelFile(filename)
        self.raw_data = None
        if file is not None:
            self.create_sheets(file)

    def build_data_frames_from_content(self, content: io.BytesIO):
        """
        Loads data from an in-memory content stream.

        Args:
            content (io.BytesIO): Binary Excel file data.

        Returns:
            None
        """
        file = pd.ExcelFile(content)
        if file is not None:
            self.create_sheets(file)

    def create_sheets(self, file: pd.ExcelFile):
        """
        Creates sheets from a given file.

        Parameters:
            file (pd.ExcelFile): The Excel file object.

        Returns:
            None
        """
        for s in file.sheet_names:
            self.sheets[s] = DataSheet(s, self.data_source, self.custom_age_ranges, is_excel=True, file=file)

    def create_sheets_from_df(self, df: pd.DataFrame):
        """
        Creates data sheets from a DataFrame.

        Args:
            df (pd.DataFrame): The processed DataFrame.

        Returns:
            None
        """
        for col in self._columns:
            if col in df.columns:
                df_cumsum = self.calculate_cumulative_sums(df, col)
                if col in self._numeric_cols:
                    labels = self._numeric_cols[col].get('labels', None)
                    if labels:
                        # The first column (e.g., date) remains at index 0.
                        date_column = df_cumsum.columns[0]
                        # Keep only labels that are present in the DataFrame.
                        labels_in_df = [col for col in labels if col in df_cumsum.columns]
                        # The remaining columns are those not in labels_in_df and not the date column.
                        remaining_cols = [col for col in df_cumsum.columns if
                                          col not in labels_in_df and col != date_column]
                        # Build the new column order.
                        new_order = [date_column] + labels_in_df + remaining_cols
                        df_cumsum = df_cumsum[new_order]
                self.sheets[col] = DataSheet(col, self.data_source, self.custom_age_ranges, is_excel=False,
                                             df=df_cumsum)

    def calculate_cumulative_sums(self, df: pd.DataFrame, col: str):
        """
        Calculates cumulative sums for a given column.

        Args:
            df (pd.DataFrame): The input DataFrame.
            col (str): The column to calculate cumulative sums for.

        Returns:
            pd.DataFrame: A DataFrame with cumulative sums.
        """
        unique_dates = sorted(df['date'].unique())
        unique_values = df[col].unique()
        df_cumsum = pd.DataFrame({'date': unique_dates})

        for value in unique_values:
            df_cumsum[value] = [((df['date'] <= date) & (df[col] == value)).sum() for date in unique_dates]

        return df_cumsum


class DataSheet:
    """
    Class representing a data sheet.

    Attributes:
        name (str): The name of the data sheet.
        columns (dict): A dictionary containing the columns of the data sheet.
        data_columns (list): A list of data columns in the data sheet.

    Methods:
        __init__(self, sheet_name, data_source, custom_age_ranges, is_excel=False, file=None):
                    Initializes a new instance of the DataSheet class.
        create_custom_age_columns(self, age_ranges): Scans the column headers in the age category to build consistent
                                                     age columns.
    """
    def __init__(self, sheet_name, data_source, custom_age_ranges, is_excel=False, file: pd.ExcelFile = None,
                 df: pd.DataFrame = None):
        """
        Initialize the DataSheet object.

        Args:
            sheet_name (str): The name of the sheet in the Excel file to parse.
            data_source (dict): The data source object.
            is_excel (bool, optional): Flag indicating whether the data source is an Excel file. Defaults to False.
            file (pd.ExcelFile, optional): The Excel file to read the sheet from

        Returns:
            None
        """
        self.name = sheet_name
        self._columns = {}

        if is_excel and file is not None:
            self._df = file.parse(sheet_name=sheet_name, usecols=lambda x: '(%)' not in str(x), engine='openpyxl')
        elif df is not None:
            self._df = df
        self._load_data_from_df(data_source)

        if custom_age_ranges and self.name in custom_age_ranges:
            self.create_custom_age_columns(custom_age_ranges[self.name])

    def _load_data_from_df(self, data_source: dict):
        """
        Load and process data from a DataFrame in self._df
        Args:
            data_source (dict): The data source object containing additional settings.

        Returns:
            None
        """
        self._df.columns = self._df.columns.astype(str)
        self._process_date_column(data_source)
        self._process_columns(data_source)

    @property
    def df(self):
        """Return the dataframe."""
        return self._df

    @property
    def columns(self):
        """Return the columns."""
        return self._columns

    @property
    def data_columns(self):
        """Return the data columns. This skips the first column, which is the date column."""
        return list(self.columns.keys())[1:]

    def _process_date_column(self, data_source: dict):
        """Process and format the date column."""

        # This assumes that the first column is either the date column or does not have useful data
        if data_source.get('date'):
            self._df.drop(self._df.columns[0], axis=1, inplace=True)
            self._df.insert(0, 'date', data_source['date'], False)

        self._df['date'] = pd.to_datetime(self._df['date'], errors='coerce')

        self._columns['date'] = self._df.columns[0]

    def _process_columns(self, data_source: dict):
        """Process and rename columns according to the data source settings."""
        for col in self._df.columns[1:]:
            col_name = col
            if 'remove column name text' in data_source:
                for txt in data_source['remove column name text']:
                    col_name = col.split(txt)[0]
            col_name = col_name.rstrip()
            self._columns[col_name] = col
            self._df[col_name] = self._df.pop(col)

        # Find all columns matching the pattern (case-insensitive)
        matches = [col for col in self._df.columns if re.search(r'not\s*reported', col, flags=re.IGNORECASE)]

        if len(matches) > 1:
            raise ValueError(f"Expected one match for 'Not Reported', found multiple: {matches}")
        if len(matches) == 1:
            self._df.rename(columns={matches[0]: 'Not Reported'}, inplace=True)
            self._columns['Not Reported'] = self._columns.pop(matches[0])

    def create_custom_age_columns(self, age_ranges: list[tuple]):
        """
        Creates custom age columns by summing values from columns that match each age range.

        Parameters:
            age_ranges (list of tuple): Each tuple is (min_age, max_age).

        Notes:
            - Drops any previously created custom columns.
            - Considers only columns that start with a digit and do not contain '(%)' or '(CUSUM)'.
            - A column is included for an age range if:
                • Its lower bound (the first number in the header) is within the range.
                • If an upper bound exists (a second number), the age range's max is not less than it.
                • If no upper bound exists, the column is only included if max_age is infinite.
            - Warns if any eligible column is unused.
        """

        # Drop previously created custom columns.
        self._df.drop(columns=[col for col in self._df.columns if 'Custom' in col], inplace=True)

        # Filter eligible columns: those starting with a digit and not containing '(%)' or '(CUSUM)'.
        cols = [col for col in self._df.columns if
                col and col[0].isdigit() and '(%)' not in col and '(CUSUM)' not in col]
        cols_used = []

        def should_include(col, age_range):
            """
            Returns True if the column should be included for the given age_range.

            The column is included only if:
              - Its lower bound (first number) is within the age range.
              - If a second number exists (upper bound), then age_range[1] must be at least that value.
              - If no upper bound exists, the column is only included when age_range[1] is infinite.
            """
            nums = re.findall(r'\d+', col)
            lower = int(nums[0])
            if age_range[0] > lower or age_range[1] < lower:
                return False
            if len(nums) == 1:
                return math.isinf(age_range[1])
            # else:
            upper = int(nums[1])
            return not age_range[1] < upper

        # Create custom age columns.
        for age_range in age_ranges:
            cols_to_sum = [col for col in cols if should_include(col, age_range)]
            cols_used.extend(cols_to_sum)
            self._df[f'{age_range[0]}-{age_range[1]} Custom'] = self._df[cols_to_sum].sum(axis=1)

        # Warn if any eligible column was not used.
        for col in cols:
            if col not in cols_used:
                warnings.warn(f"{self.name}: Column '{col}' not used!", stacklevel=2)
