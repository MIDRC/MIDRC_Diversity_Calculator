import re
import warnings
import pandas as pd
import math


class DataSource:
    def __init__(self, data_source, custom_age_ranges=None):
        """
        Initializes a new instance of the DataSource class.

        Args:
            name (str): The name for this DataSource.
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
        """
        file = pd.ExcelFile(filename)
        if file is not None:
            self.create_sheets(file)

    def create_sheets(self, file: pd.ExcelFile):
        """
        Creates sheets from a given file.
        """
        for s in file.sheet_names:
            self.sheets[s] = DataSheet(s, self.data_source, self.custom_age_ranges, is_excel=True, file=file)


class DataSheet:
    def __init__(self, sheet_name, data_source, custom_age_ranges, is_excel=False, file=None):
        """
        Initialize the DataSheet object.

        Args:
            sheet_name (str): The name of the sheet in the Excel file to parse.
            datasource_name (str): The name of the data source object.
            is_excel (bool, optional): Flag indicating whether the data source is an Excel file. Defaults to False.
            file (pd.ExcelFile, optional): The excel file to read the sheet from
        """
        self.name = sheet_name
        self.columns = {}
        self.data_columns = []

        if is_excel:
            self.df = pd.read_excel(file, sheet_name, usecols=lambda x: '(%)' not in x, engine='openpyxl')
            cols = [col for col in self.df.columns]

            if data_source.get('date', None):
                cols = ['date'] + cols[1:]
                self.df.insert(0, 'date', data_source['date'], False)

            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')

            if cols[-1].find('Not reported') == -1:
                cols = cols + ['Not reported']
                self.df['Not reported'] = 0

            self.columns['date'] = cols[0]
            for col in cols[1:]:
                colname = col
                if data_source.get('remove column name text', None):
                    for txt in data_source['remove column name text']:
                        colname = str(col).split(txt)[0]
                        self.df[colname.rstrip()] = self.df[col]
                self.columns[colname.rstrip()] = col

            self.data_columns = list(self.columns.keys())[1:]

        if custom_age_ranges and self.name in custom_age_ranges:
            self.create_custom_age_columns(custom_age_ranges[self.name])

    def create_custom_age_columns(self, age_ranges):
        """
        Scans the column headers in the age category to build consistent age columns.
        """
        # Drop previously created custom columns
        cols_to_drop = [col for col in self.df.columns if 'Custom' in col]
        self.df.drop(columns=cols_to_drop, inplace=True)

        # The 'Age at Index' columns need alteration for JSD calculation
        cols = [col for col in self.df.columns if '(%)' not in col and '(CUSUM)' not in col and col[0].isdigit()]
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
            self.df[f'{agerange[0]}-{agerange[1]} Custom'] = self.df[cols_to_sum].sum(axis=1)

        # Check to make sure all columns get used
        for col in cols:
            if col not in cols_used:
                warnings.warn(f"Column '{col}' not used!!!")
