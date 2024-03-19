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
        self.name = name
        self.sheets = {}
        self.filename = None
        self.file = None
        if self.name in WhitneyPaper.FileNames:
            self.buildwhitneydataframes()

    def buildwhitneydataframes(self):
        if self.name in WhitneyPaper.FileNames:
            self.filename = WhitneyPaper.FileNames[self.name]
            self.file = pd.ExcelFile(self.filename)
            self.createsheets()

    def createsheets(self):
        if self.name in WhitneyPaper.FileNames:
            for s in WhitneyPaper.SheetNames:
                self.sheets[s] = DataSheet(s, self, excel=True)


class DataSheet:
    def __init__(self, sheet_name, datasource, excel=False):
        # name is the name of the sheet in the Excel file to parse
        self.name = sheet_name
        self.columns = {}
        self.data_columns = []
        if excel:
            self.df = pd.read_excel(datasource.file, sheet_name)
            cols = [col for col in self.df.columns if '(%)' not in col]

            if datasource.name == 'Census':
                cols = ['date'] + cols[1:]
                self.df.insert(0, 'date', ['2010-01-01'], False)

            self.df['date'] = pd.to_datetime(self.df['date'])

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

            # These are the raw data columns that should be used for creating graphs and figures
            self.data_columns = list(self.columns.keys())[1:]

        if self.name == 'Age at Index':
            self.createCustomAgeColumns()

    def createCustomAgeColumns(self, age_ranges=WhitneyPaper.CustomAgeColumns):
        # Drop previously created custom columns
        cols_to_drop = [col for col in self.df.columns if 'Custom' in col]
        self.df.drop(cols_to_drop, inplace=True)

        # The 'Age at Index' columns need alteration for JSD calculation
        if self.name == 'Age at Index':
            cols = [col for col in self.df.columns if '(%)' not in col and '(CUSUM)' not in col and col[0].isdigit()]
            print(cols)
            cols_used = []
            for agerange in age_ranges:
                cols_to_sum = []
                # Skip the first column (date) and the last column (Unreported)
                for col in cols:
                    # First pull out the text part of the column name
                    colrange = col.split('years')[0].split('Years')[0].strip(' +')
                    # Now find the start and ending age
                    colrange = colrange.replace('to', '-').replace(' ', '').split('-')
                    # print(colrange)
                    use_col = True
                    if agerange[0] > int(colrange[0]):
                        use_col = False
                    if agerange[1] < int(colrange[0]):
                        use_col = False
                    if len(colrange) == 1 and not math.isinf(agerange[1]):
                        use_col = False
                    if len(colrange) > 1 and agerange[1] < int(colrange[1]):
                        use_col = False

                    if use_col:
                        cols_to_sum.append(col)
                cols_used += cols_to_sum
                self.df[f'{agerange[0]}-{agerange[1]} Custom'] = self.df[cols_to_sum].sum(axis=1)

            # Check to make sure all columns get used
            for col in cols:
                if col not in cols_used:
                    print(f"Warning! Column '{col}' not used!!!")
