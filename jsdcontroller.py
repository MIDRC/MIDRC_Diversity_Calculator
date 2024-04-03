import ExcelLayout
import excelparse
from PySide6.QtCore import Qt, QObject, Signal, QDate
from dateutil.rrule import *
from datetime import date
import numpy as np
import pandas as pd
from scipy.spatial import distance
from datetimetools import pandas_date_to_qdate
from jsdmodel import JSDTableModel
from jsdview import JsdWindow


class JSDController(QObject):
    modelChanged = Signal()
    
    def __init__(self, jsd_view, jsd_model):
        """
        Initialize the JSDController.

        Parameters:
            jsd_view (object): The JSD view object.
            jsd_model (object): The JSD model object.

        Returns:
            None
        """
        super().__init__()
        if jsd_view is None or not isinstance(jsd_view, JsdWindow):
            raise ValueError("jsd_view must be a valid JsdWindow instance")
        if jsd_model is None or not isinstance(jsd_model, JSDTableModel):
            raise ValueError("jsd_model must be a valid JSDTableModel instance")
        self._jsd_view = jsd_view
        self._jsd_model = jsd_model

        self.initialize()

    def initialize(self):
        """
        Initialize the JSDController.

        Parameters:
            None

        Returns:
            None
        """
        self.fileChanged(None, newcategoryindex=0)
        self.connect_signals()

    def connect_signals(self):
        """
        Connects signals for file and category comboboxes.
        """
        jsd_view = self.jsd_view  # Store the result of jsd_view() in a variable
        for f_c in jsd_view.get_dataselectiongroupbox().file_comboboxes:
            f_c.currentIndexChanged.connect(self.fileChanged)
        jsd_view.get_dataselectiongroupbox().category_combobox.currentIndexChanged.connect(self.categoryChanged)

    @property
    def jsd_view(self) -> JsdWindow:
        """
        Get the JSD view object.

        Returns:
            object: The JSD view object.
        """
        return self._jsd_view

    @jsd_view.setter
    def jsd_view(self, jsd_view: JsdWindow) -> None:
        """
        Set the JSD view object.

        Parameters:
            jsd_view: The JSD view object.
        """
        if jsd_view is None:
            raise ValueError("jsd_view must be a valid JsdWindow instance")
        self._jsd_view = jsd_view

    @property
    def jsd_model(self) -> JSDTableModel:
        """
        Get the JSD model object.

        Returns:
            object: The JSD model object.
        """
        return self._jsd_model

    @jsd_model.setter
    def jsd_model(self, jsd_model: JSDTableModel) -> None:
        """
        Set the JSD model object.

        Parameters:
            jsd_model: The JSD model object of type JSDTableModel.
        """
        if not isinstance(jsd_model, JSDTableModel):
            raise ValueError("jsd_model must be a valid JSDTableModel instance")
        if self._jsd_model != jsd_model:
            self._jsd_model = jsd_model
            self.modelChanged.emit()

    def fileChanged(self, _, newcategoryindex = None):
        jsd_view = self.jsd_view
        jsd_model = self.jsd_model
        dataselectiongroupbox = jsd_view.get_dataselectiongroupbox()
        categoryindex = dataselectiongroupbox.category_combobox.currentIndex()
        if newcategoryindex is not None:
            categoryindex = newcategoryindex

        cbox0 = dataselectiongroupbox.file_comboboxes[0]
        categorylist = list(jsd_model.data_sources[cbox0.currentData()].sheets.keys())

        for cbox2 in dataselectiongroupbox.file_comboboxes[1:]:
            categorylist2 = jsd_model.data_sources[cbox2.currentData()].sheets.keys()
            categorylist = [value for value in categorylist if value in categorylist2]

        dataselectiongroupbox.category_combobox.blockSignals(True)
        dataselectiongroupbox.category_combobox.clear()
        dataselectiongroupbox.category_combobox.addItems(categorylist)
        dataselectiongroupbox.category_combobox.setCurrentIndex(categoryindex)
        dataselectiongroupbox.category_combobox.blockSignals(False)

        self.updateFileBasedCharts()
        self.categoryChanged()

    def get_file_sheets_from_combobox(self, index=0):
        """
        Get the sheets from the selected file combobox.

        Args:
            index (int): The index of the file combobox. Default is 0.

        Returns:
            dict: A dictionary containing the sheets from the selected file.
        """
        if index < 0 or index >= len(self.jsd_view.get_dataselectiongroupbox().file_comboboxes):
            raise IndexError("Index out of range")

        cbox = self.jsd_view.get_dataselectiongroupbox().file_comboboxes[index]
        current_data = cbox.currentData()

        jsd_model = self.jsd_model
        if current_data in jsd_model.data_sources:
            sheets = jsd_model.data_sources[current_data].sheets
            return sheets
        else:
            return None

    def categoryChanged(self):
        jsd_view = self.jsd_view
        jsd_model = self.jsd_model
        dataselectiongroupbox = jsd_view.get_dataselectiongroupbox()
        cat = dataselectiongroupbox.category_combobox.currentText()
        # cbox0 = dataselectiongroupbox.file_comboboxes[0]

        # cols = self.jsd_model.data_sources[cbox0.currentData()].sheets[cat].columns.values()
        # We don't really care about the columns themselves, we just need to update the jsd plot
        num_files = len(dataselectiongroupbox.file_comboboxes)
        jsd_model.input_data.clear()
        jsd_model.row_count = int(num_files * (num_files - 1) / 2)
        #self.jsd_model.input_data = [[0 for i in range(2)] for j in range(self.jsd_model.col_count)]
        input_data = [[]]
        # data_vec = [0] * int(num_files * (num_files + 1) / 2)
        # cur_col = 0
        for i in range(0, num_files):
            cbox1 = dataselectiongroupbox.file_comboboxes[i]
            df1 = jsd_model.data_sources[cbox1.currentData()].sheets[cat].df
            cols_to_use = self.get_cols_to_use_for_jsd_calc(cbox1, cat)

            for j in range(i+1, num_files):
                cbox2 = dataselectiongroupbox.file_comboboxes[j]
                df2 = jsd_model.data_sources[cbox2.currentData()].sheets[cat].df
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
                jsd_model.input_data = input_data
                # self.jsd_model.input_data[cur_col] = date_vec
                # self.jsd_model.input_data[cur_col + 1] = jsd_vec
                # cur_col += 2
                # print(input_data)
                # print(self.jsd_model.input_data)
                jsd_model.row_count = len(date_list) # This shouldn't be necessary as column_count isn't used

            # cur_col += 2
        self.updateCategoryPlots()
        jsd_model.layoutChanged.emit()

    def updateFileBasedCharts(self):
        """
        Update the file-based charts.

        This method updates the pie chart dock and the spider chart.

        Parameters:
            None

        Returns:
            True if the update was successful, False otherwise

        Raises:
            None
        """
        file_cbox_index = 0
        sheets = self.get_file_sheets_from_combobox(file_cbox_index)
        self.jsd_view.updatePieChartDock(sheets)

        spider_plot_date = None
        spider_plot_values = self.get_spider_plot_values(spider_plot_date)
        self.jsd_view.updateSpiderChart(spider_plot_values)

        return True

    def updateCategoryPlots(self):
        """
        Update the category plots.

        This method updates the JSD timeline plot and the area chart.

        Parameters:
            None

        Returns:
            True
        """
        self.jsd_view.updateJsdTimelinePlot(self.jsd_model)

        file_cbox_index = 0
        sheets = self.get_file_sheets_from_combobox(file_cbox_index)
        filename = self.jsd_view.get_dataselectiongroupbox().file_comboboxes[file_cbox_index].currentData()
        self.jsd_view.updateAreaChart(sheets, filename)
        return True

    def get_cols_to_use_for_jsd_calc(self, cbox, category):
        cols_to_use = self.jsd_model.data_sources[cbox.currentData()].sheets[category].data_columns

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

        jsd_view = self.jsd_view
        dataselectiongroupbox = jsd_view.get_dataselectiongroupbox()
        categories = [dataselectiongroupbox.category_combobox.itemText(i) for i in
                      range(dataselectiongroupbox.category_combobox.count())]

        cbox0 = dataselectiongroupbox.file_comboboxes[0]
        sheets0 = self.jsd_model.data_sources[cbox0.currentData()].sheets
        cbox1 = dataselectiongroupbox.file_comboboxes[1]
        sheets1 = self.jsd_model.data_sources[cbox1.currentData()].sheets

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


def remove_elements_less_than(sorted_list, value):
    # Find the index of the first element greater than or equal to the value
    index = 0
    while index < len(sorted_list) and sorted_list[index] < value:
        index += 1

    # Slice the list to keep only elements greater than or equal to the value
    return sorted_list[index:]
