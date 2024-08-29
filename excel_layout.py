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

import math
import re
import warnings

import pandas as pd


class DataSource:
    """
    Class representing a data source.

    Attributes:
        name (str): The name of the data source.
        sheets (dict): A dictionary containing the sheets of the data source.
        datatype (str): The type of the data source.
        filename (str): The filename of the data source.
        data_source (dict): The data source object.
        custom_age_ranges (dict, optional): A dictionary containing custom age ranges.

    Methods:
        __init__(self, data_source, custom_age_ranges=None): Initializes a new instance of the DataSource class.
        build_data_frames(self, filename: str): Builds dataframes.
        create_sheets(self, file: pd.ExcelFile): Creates sheets from a given file.
    """
    def __init__(self, data_source, custom_age_ranges=None):
        """
        Initializes a new instance of the DataSource class.

        Args:
            data_source (dict): The data source object.
            custom_age_ranges (dict, optional): A dictionary containing custom age ranges.

        Returns:
            None
        """
        self.name = data_source['name']
        self.sheets = {}
        self.datatype = data_source['data type']
        self.filename = data_source['filename']
        self.data_source = data_source
        self.custom_age_ranges = custom_age_ranges
        if self.datatype == 'file' and self.filename:
            self.build_data_frames(self.filename)

    def build_data_frames(self, filename: str):
        """
        Builds dataframes.

        Parameters:
            filename (str): The filename of the Excel file.

        Returns:
            None
        """
        file = pd.ExcelFile(filename)
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
    def __init__(self, sheet_name, data_source, custom_age_ranges, is_excel=False, file: pd.ExcelFile = None):
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
        self.columns = {}
        self.data_columns = []

        if is_excel and file is not None:
            self._load_excel_data(file, sheet_name, data_source)

        if custom_age_ranges and self.name in custom_age_ranges:
            self.create_custom_age_columns(custom_age_ranges[self.name])

    def _load_excel_data(self, file: pd.ExcelFile, sheet_name: str, data_source: dict):
        """
        Load and process data from an Excel file.

        Args:
            file (pd.ExcelFile): The Excel file to read the sheet from.
            sheet_name (str): The name of the sheet to parse.
            data_source (dict): The data source object containing additional settings.

        Returns:
            None
        """
        self._df = file.parse(sheet_name=sheet_name, usecols=lambda x: '(%)' not in str(x), engine='openpyxl')
        self._df.columns = self._df.columns.astype(str)
        self._process_date_column(data_source)
        self._process_columns(data_source)

    @property
    def df(self):
        """Return the dataframe."""
        return self._df

    def _process_date_column(self, data_source: dict):
        """Process and format the date column."""

        # This assumes that the first column is either the date column or does not have useful data
        if data_source.get('date'):
            self._df.drop(self._df.columns[0], axis=1, inplace=True)
            self._df.insert(0, 'date', data_source['date'], False)

        self._df['date'] = pd.to_datetime(self._df['date'], errors='coerce')

        if 'Not reported' not in self._df.columns:
            self._df['Not reported'] = 0

        self.columns['date'] = self._df.columns[0]

    def _process_columns(self, data_source: dict):
        """Process and rename columns according to the data source settings."""
        for col in self._df.columns[1:]:
            col_name = col
            if 'remove column name text' in data_source:
                for txt in data_source['remove column name text']:
                    col_name = col.split(txt)[0]
            col_name = col_name.rstrip()
            self.columns[col_name] = col
            self._df[col_name] = self._df.pop(col)

        self.data_columns = list(self.columns.keys())[1:]

    def create_custom_age_columns(self, age_ranges):
        """
        Scans the column headers in the age category to build consistent age columns.

        Parameters:
            age_ranges (list): A list of age ranges to be used for creating custom age columns.

        Returns:
            None

        Raises:
            None

        Notes:
            - This method drops any previously created custom age columns.
            - It identifies the columns that need to be altered for JSD calculation.
            - It sums the values of the identified columns for each age range and creates a new custom age column.
            - It checks if all columns have been used and raises a warning if any column is not used.
        """
        # Drop previously created custom columns
        cols_to_drop = [col for col in self._df.columns if 'Custom' in col]
        self._df.drop(columns=cols_to_drop, inplace=True)

        # The 'Age at Index' columns need alteration for JSD calculation
        cols = [col for col in self._df.columns if '(%)' not in col and '(CUSUM)' not in col and col[0].isdigit()]
        cols_used = []
        for agerange in age_ranges:
            cols_to_sum = []
            for col in cols:
                colrange = re.findall(r'\d+', col)
                skip_col = (agerange[0] > int(colrange[0]) or
                            agerange[1] < int(colrange[0]) or
                            (len(colrange) == 1 and not math.isinf(agerange[1])) or
                            (len(colrange) > 1 and agerange[1] < int(colrange[1])))

                if not skip_col:
                    cols_to_sum.append(col)
            cols_used.extend(cols_to_sum)
            self._df[f'{agerange[0]}-{agerange[1]} Custom'] = self._df[cols_to_sum].sum(axis=1)

        # Check to make sure all columns get used
        for col in cols:
            if col not in cols_used:
                warnings.warn(f"Column '{col}' not used!!!", stacklevel=2)
