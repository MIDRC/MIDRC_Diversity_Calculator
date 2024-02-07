# Class structures for Excel spreadsheets

import pandas as pd


class WhitneyPaper:
    FileNames = {'MIDRC': 'MIDRC Open A1 and R1 - cumulative by batch.xlsx',
                 'CDC': 'CDC_COVIDpos - cumulative by month.xlsx',
                 'Census': 'Census_all.xlsx'}

    SheetNames = ['Age at Index',
                  'Sex',
                  'Race',
                  'Ethnicity',
                  'Race and Ethnicity']


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
    def __init__(self, name, datasource, excel=False):
        self.name = name
        self.columns = {}
        if excel:
            self.df = pd.read_excel(datasource.file, self.name)
            cols = [col for col in self.df.columns if '(%)' not in col]
            if datasource.name == 'Census':
                cols = ['date'] + cols[1:] + ['Not reported']
                self.df.insert(0, 'date', ['2010-01-01'], False)
                self.df['Not reported'] = [0]
            self.columns['date'] = cols[0]
            for col in cols[1:]:
                colname = col
                if datasource.name == 'MIDRC':
                    colname = str(col).split('(CUSUM)')[0]
                self.columns[colname.rstrip()] = col
