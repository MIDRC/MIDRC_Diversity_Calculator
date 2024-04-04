import re
import warnings
# Class structures for Excel spreadsheets

import pandas as pd
import math

class WhitneyPaper:
    FileNames = {'MIDRC': 'MIDRC Open A1 and R1 - cumulative by batch.xlsx',
                 'CDC': 'CDC_COVIDpos - cumulative by month.xlsx',
                 'Census': 'Census_all.xlsx'}

    SheetNames = ['Age at Index',
                  'Sex',
                  'Race',
                  'Ethnicity',
                  'Race and Ethnicity']

    CustomAgeColumns = [[0, 17], [18, 49], [50, 64], [65, math.inf]]


class DataSource:
    def __init__(self, name):
        """
        Initializes a new instance of the DataSource class.

        Args:
            name (str): The name for this DataSource.
        """
        self.name = name
        self.sheets = {}
        self.filename = None
        self.file = None
        if self.name in WhitneyPaper.FileNames:
            self.buildwhitneydataframes()

    def buildwhitneydataframes(self):
        """
        Builds Whitney dataframes.
        """
        if self.name in WhitneyPaper.FileNames:
            self.filename = WhitneyPaper.FileNames[self.name]
            self.file = pd.ExcelFile(self.filename)
            if self.file is not None:
                self.createsheets()

    def createsheets(self):
        """
        Creates sheets for Whitney dataframes.
        """
        if self.name in WhitneyPaper.FileNames:
            for s in WhitneyPaper.SheetNames:
                self.sheets[s] = DataSheet(s, self, is_excel=True)


class DataSheet:
    def __init__(self, sheet_name, datasource, is_excel=False):
        """
        Initialize the DataSheet object.

        Args:
            sheet_name (str): The name of the sheet in the Excel file to parse.
            datasource (DataSource): The data source object.
            is_excel (bool, optional): Flag indicating whether the data source is an Excel file. Defaults to False.
        """
        self.name = sheet_name
        self.columns = {}
        self.data_columns = []

        if is_excel:
            self.df = pd.read_excel(datasource.file, sheet_name, usecols=lambda x: '(%)' not in x, engine='openpyxl')
            cols = [col for col in self.df.columns]

            if datasource.name == 'Census':
                cols = ['date'] + cols[1:]
                self.df.insert(0, 'date', ['2010-01-01'], False)

            self.df['date'] = pd.to_datetime(self.df['date'], errors='coerce')

            if cols[-1].find('Not reported') == -1:
                cols = cols + ['Not reported']
                self.df['Not reported'] = 0

            self.columns['date'] = cols[0]
            for col in cols[1:]:
                colname = col
                if datasource.name == 'MIDRC':
                    colname = str(col).split('(CUSUM)')[0]
                    self.df[colname.rstrip()] = self.df[col]
                self.columns[colname.rstrip()] = col

            self.data_columns = list(self.columns.keys())[1:]

        if self.name == 'Age at Index':
            self.createCustomAgeColumns()

    def createCustomAgeColumns(self, age_ranges=WhitneyPaper.CustomAgeColumns):
        """
        Scans the column headers in the age category to build consistent age columns.
        """
        # Drop previously created custom columns
        cols_to_drop = [col for col in self.df.columns if 'Custom' in col]
        self.df.drop(columns=cols_to_drop, inplace=True)

        # The 'Age at Index' columns need alteration for JSD calculation
        if self.name == 'Age at Index':
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
