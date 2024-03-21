import ExcelLayout
import excelparse
import jsdview
import jsdmodel
from PySide6.QtCore import Qt, QObject, Signal, QDate
from dateutil.rrule import *
from datetime import date
import numpy as np
import pandas as pd
from scipy.spatial import distance


class JSDController(QObject):
    categoryplotdatachanged = Signal()
    fileselectionchanged = Signal()
    def __init__(self, jsd_view, jsd_model):
        super().__init__()
        self.jsd_view = jsd_view
        self.jsd_model = jsd_model

        self.fileChanged(None, newcategoryindex=2)
        for f_c in self.jsd_view.dataselectiongroupbox.file_comboboxes:
            f_c.currentIndexChanged.connect(self.fileChanged)
        self.jsd_view.dataselectiongroupbox.category_combobox.currentIndexChanged.connect(self.categoryChanged)

    def fileChanged(self, _, newcategoryindex = None):
        categoryindex = self.jsd_view.dataselectiongroupbox.category_combobox.currentIndex()
        if newcategoryindex is not None:
            categoryindex = newcategoryindex

        cbox0 = self.jsd_view.dataselectiongroupbox.file_comboboxes[0]
        categorylist = list(self.jsd_model.raw_data[cbox0.currentData()].sheets.keys())

        for cbox2 in self.jsd_view.dataselectiongroupbox.file_comboboxes[1:]:
            categorylist2 = self.jsd_model.raw_data[cbox2.currentData()].sheets.keys()
            categorylist = [value for value in categorylist if value in categorylist2]

        self.jsd_view.dataselectiongroupbox.category_combobox.blockSignals(True)
        self.jsd_view.dataselectiongroupbox.category_combobox.clear()
        self.jsd_view.dataselectiongroupbox.category_combobox.addItems(categorylist)
        self.jsd_view.dataselectiongroupbox.category_combobox.setCurrentIndex(categoryindex)
        self.jsd_view.dataselectiongroupbox.category_combobox.blockSignals(False)

        self.fileselectionchanged.emit()

        self.categoryChanged()

    def categoryChanged(self):
        cat = self.jsd_view.dataselectiongroupbox.category_combobox.currentText()
        # cbox0 = self.jsd_view.dataselectiongroupbox.file_comboboxes[0]

        # cols = self.jsd_model.raw_data[cbox0.currentData()].sheets[cat].columns.values()
        # We don't really care about the columns themselves, we just need to update the jsd plot
        num_files = len(self.jsd_view.dataselectiongroupbox.file_comboboxes)
        self.jsd_model.input_data.clear()
        self.jsd_model.row_count = int(num_files * (num_files - 1) / 2)
        #self.jsd_model.input_data = [[0 for i in range(2)] for j in range(self.jsd_model.col_count)]
        input_data = [[]]
        # data_vec = [0] * int(num_files * (num_files + 1) / 2)
        # cur_col = 0
        for i in range(0, num_files):
            cbox1 = self.jsd_view.dataselectiongroupbox.file_comboboxes[i]
            df1 = self.jsd_model.raw_data[cbox1.currentData()].sheets[cat].df
            cols_to_use = self.get_cols_to_use_for_jsd_calc(cbox1, cat)

            for j in range(i+1, num_files):
                cbox2 = self.jsd_view.dataselectiongroupbox.file_comboboxes[j]
                df2 = self.jsd_model.raw_data[cbox2.currentData()].sheets[cat].df
                # cols_to_use = df1.columns.intersection(df2.columns.values())
                # cols_to_use = cols_to_use[1:] # First column is date
                first_date = max(df1.date.values[0], df2.date.values[0])
                date_list = list(df1.date.values) + list(df2.date.values)
                # print(date_list)
                date_list = sorted(set(date_list))
                date_list = remove_elements_less_than(date_list, first_date)
                # jsd_vec = []
                # date_vec = []
                for calcdate in date_list:
                    data_vec = [0] * 2
                    jsd = calcjsd(df1, df2, cols_to_use, calcdate)
                    data_vec[0] = pandas_date_to_qdate(calcdate)
                    # data_vec[0] = pandas_date_to_qdate(calcdate).toJulianDay()
                    # Reduce the number of decimal points
                    data_vec[1] = float(jsd)
                    input_data.append(data_vec)

                input_data = input_data[1:]
                #self.jsd_model.input_data.append(input_data)
                self.jsd_model.input_data = input_data
                # self.jsd_model.input_data[cur_col] = date_vec
                # self.jsd_model.input_data[cur_col + 1] = jsd_vec
                # cur_col += 2
                # print(input_data)
                # print(self.jsd_model.input_data)
                self.jsd_model.row_count = len(date_list) # This shouldn't be necessary as column_count isn't used

            # cur_col += 2
        self.categoryplotdatachanged.emit()
        self.jsd_model.layoutChanged.emit()

    def get_cols_to_use_for_jsd_calc(self, cbox, category):
        cols_to_use = self.jsd_model.raw_data[cbox.currentData()].sheets[category].data_columns

        # Use custom age columns for JSD calculation
        if category == 'Age at Index':
            cols_to_use = []
            for agerange in ExcelLayout.WhitneyPaper.CustomAgeColumns:
                cols_to_use.append(f'{agerange[0]}-{agerange[1]} Custom')
            cols_to_use.append('Not reported')

        return cols_to_use

    def get_spider_plot_values(self, calcdate):
        if calcdate is None:
            calcdate = np.datetime64('today')

        categories = [self.jsd_view.dataselectiongroupbox.category_combobox.itemText(i) for i in
                      range(self.jsd_view.dataselectiongroupbox.category_combobox.count())]

        cbox0 = self.jsd_view.dataselectiongroupbox.file_comboboxes[0]
        sheets0 = self.jsd_model.raw_data[cbox0.currentData()].sheets
        cbox1 = self.jsd_view.dataselectiongroupbox.file_comboboxes[1]
        sheets1 = self.jsd_model.raw_data[cbox1.currentData()].sheets

        jsd_values = {}

        for category in categories:
            cols_to_use = self.get_cols_to_use_for_jsd_calc(cbox0, category)
            jsd = calcjsd(sheets0[category].df, sheets1[category].df, cols_to_use, calcdate)
            jsd_values[category] = jsd

        return jsd_values


def calcjsd(df1, df2, cols_to_use, calcdate):
    # Because we want to search for less than or equal, we add one second to the datetime to use
    calcdate += np.timedelta64(1, 's')
    # find the row with the highest date below the date specified above
    df1_row = (np.searchsorted(df1.date.values, calcdate) - 1).clip(0)
    df2_row = (np.searchsorted(df2.date.values, calcdate) - 1).clip(0)

    # get the data for the rows and columns determined above
    df1_data = np.asarray(df1[cols_to_use].iloc[df1_row].values, dtype=float)
    df2_data = np.asarray(df2[cols_to_use].iloc[df2_row].values, dtype=float)

    return distance.jensenshannon(df1_data, df2_data, base=2.0)


def pandas_date_to_qdate(pandas_date):
    """
    Convert a pandas Timestamp or datetime object to a PySide2 QDate object.

    Parameters:
        pandas_date (pd.Timestamp or datetime): Pandas Timestamp or datetime object.

    Returns:
        QDate: PySide2 QDate object representing the same date.
    """
    if isinstance(pandas_date, pd.Timestamp):
        return QDate(pandas_date.year, pandas_date.month, pandas_date.day)
    elif isinstance(pandas_date, np.datetime64):
        return numpy_datetime64_to_qdate(pandas_date)
    else:
        raise ValueError("Input must be a Pandas Timestamp or datetime object")


def numpy_datetime64_to_qdate(numpy_datetime):
    """
    Convert a NumPy datetime64 object to a PySide2 QDate object.

    Parameters:
        numpy_datetime (numpy.datetime64): NumPy datetime64 object.

    Returns:
        QDate: PySide2 QDate object representing the same date.
    """
    # Extract year, month, and day from numpy datetime64
    # year = np.datetime64(numpy_datetime, 'Y').astype(int)
    # month = np.datetime64(numpy_datetime, 'M').astype(int)
    # day = np.datetime64(numpy_datetime, 'D').astype(int)

    # Convert numpy datetime64 to Python datetime
    python_datetime = np.datetime64(numpy_datetime).astype('M8[D]').astype('O')

    # Extract year, month, and day from Python datetime
    year = python_datetime.year
    month = python_datetime.month
    day = python_datetime.day

    return QDate(year, month, day)


def remove_elements_less_than(sorted_list, value):
    # Find the index of the first element greater than or equal to the value
    index = 0
    while index < len(sorted_list) and sorted_list[index] < value:
        index += 1

    # Slice the list to keep only elements greater than or equal to the value
    return sorted_list[index:]
