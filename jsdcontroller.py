from bisect import bisect_left
from PySide6.QtCore import Qt, QObject, Signal
import numpy as np
from scipy.spatial import distance
from datetimetools import pandas_date_to_qdate
from jsdmodel import JSDTableModel
from jsdview import JsdWindow


class JSDController(QObject):
    """
    Class JSDController

    This class represents a JSD Controller. It emits a signal when the model changes.

    Attributes:
    - modelChanged: A Signal that is emitted when the model changes.

    Methods:
    - None

    """
    modelChanged = Signal()
    fileChangedSignal = Signal()
    
    def __init__(self, jsd_view, jsd_model, config):
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
        self._config = config

        self.initialize()

    def initialize(self):
        """
        Initialize the JSDController.

        Returns:
            None
        """
        self.connect_signals()
        self.file_changed(None, newcategoryindex=0)

    def connect_signals(self):
        """
        Connects signals for file and category comboboxes.
        """
        jsd_view = self.jsd_view  # Store the result of jsd_view() in a variable
        jsd_view.add_data_source.connect(self.jsd_model.add_data_source)
        for f_c in jsd_view.dataselectiongroupbox.file_comboboxes:
            f_c.currentIndexChanged.connect(self.file_changed)
        jsd_view.dataselectiongroupbox.num_data_items_changed.connect(self.file_changed)
        jsd_view.dataselectiongroupbox.file_checkbox_state_changed.connect(self.file_changed)
        jsd_view.dataselectiongroupbox.category_combobox.currentIndexChanged.connect(self.category_changed)

        self.fileChangedSignal.connect(self.update_file_based_charts)
        self.fileChangedSignal.connect(self.category_changed)

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

    def file_changed(self, _, newcategoryindex=None):
        """
        Parses the categories from the files selected in the comboboxes and updates the category box appropriately.
        Emits the fileChangedSignal signal upon completion.

        Args:
            newcategoryindex Optional(int): The index of the category to set, if None then use previous index.
        """
        dataselectiongroupbox = self.jsd_view.dataselectiongroupbox
        category_combobox = dataselectiongroupbox.category_combobox
        categoryindex = category_combobox.currentIndex()
        if newcategoryindex is not None:
            categoryindex = newcategoryindex

        cbox0 = dataselectiongroupbox.file_comboboxes[0]
        categorylist = self.jsd_model.data_sources[cbox0.currentData()].sheets.keys()

        for cbox2 in dataselectiongroupbox.file_comboboxes[1:]:
            categorylist2 = self.jsd_model.data_sources[cbox2.currentData()].sheets.keys()
            categorylist = [value for value in categorylist if value in categorylist2]

        dataselectiongroupbox.update_category_combo_box(categorylist, categoryindex)

        self.fileChangedSignal.emit()

    def get_file_sheets_from_combobox(self, index=0):
        """
        Get the sheets from the selected file combobox.

        Args:
            index (int): The index of the file combobox. Default is 0.

        Returns:
            dict: A dictionary containing the sheets from the selected file.
        """
        try:
            current_data = self.jsd_view.dataselectiongroupbox.file_comboboxes[index].currentData()
        except IndexError:
            raise IndexError("Index out of range")

        sheets = self.jsd_model.data_sources[current_data].sheets
        return sheets

    def category_changed(self):
        """
        Parses the dates from all files for the current category, and updates the data in the model appropriately.

        Returns:
            None

        Raises:
            None
        """
        jsd_view = self.jsd_view
        jsd_model = self.jsd_model
        dataselectiongroupbox = jsd_view.dataselectiongroupbox
        cat = dataselectiongroupbox.category_combobox.currentText()

        model_input_data = []
        column_infos = []

        column_info = {'category': cat}

        for i, cbox1 in enumerate(dataselectiongroupbox.file_comboboxes):
            column_info['index1'] = i
            column_info['file1'] = cbox1.currentData()
            df1 = jsd_model.data_sources[column_info['file1']].sheets[cat].df
            cols_to_use = self.get_cols_to_use_for_jsd_calc(cbox1, cat)

            for j, cbox2 in enumerate(dataselectiongroupbox.file_comboboxes[i+1:], start=i+1):
                column_info['index2'] = j
                column_info['file2'] = cbox2.currentData()
                df2 = jsd_model.data_sources[column_info['file2']].sheets[cat].df
                first_date = max(df1.date.values[0], df2.date.values[0])
                date_list = np.concatenate((df1.date.values, df2.date.values))
                date_list = sorted(set(date_list))
                date_list = remove_elements_less_than_from_sorted_list(date_list, first_date)

                # input_data = [[pandas_date_to_qdate(calcdate),
                #                float(calculate_jsd(df1, df2, cols_to_use, calcdate))] for calcdate in date_list]
                # jsd_model.input_data.extend(input_data)

                input_data = [float(calculate_jsd(df1, df2, cols_to_use, calc_date)) for calc_date in date_list]
                model_input_data.append([pandas_date_to_qdate(calc_date) for calc_date in date_list])
                model_input_data.append(input_data)
                # jsd_model.column_infos.append(copy.deepcopy(column_info)) # We shouldn't need to recursively copy
                column_infos.append(column_info.copy())

        jsd_model.update_input_data(model_input_data, column_infos)
        # print(len(jsd_model.input_data))
        # print([len(data) for data in jsd_model.input_data])

        self.update_category_plots()
        jsd_model.layoutChanged.emit()

    def update_file_based_charts(self):
        """
        Update the file-based charts.

        This method updates the pie chart dock and the spider chart.

        Returns:
            True if the update was successful, False otherwise

        Raises:
            None
        """
        # file_cbox_index = 0
        spider_plot_date = None
        sheet_list = []
        for i in range(len(self.jsd_view.dataselectiongroupbox.file_comboboxes)):
            if self.jsd_view.dataselectiongroupbox.file_checkboxes[i].isChecked():
                sheet_list.append(self.get_file_sheets_from_combobox(i))

        spider_plot_values = self.get_spider_plot_values(spider_plot_date)
        self.jsd_view.update_spider_chart(spider_plot_values)

        try:
            self.jsd_view.update_pie_chart_dock(sheet_list)
        except Exception:
            return False

        return True

    def update_category_plots(self):
        """
        Update the category plots.

        This method updates the JSD timeline plot and the area chart.

        Returns:
            True if the update was successful, False otherwise
        """
        sheet_list = []
        for i in range(len(self.jsd_view.dataselectiongroupbox.file_comboboxes)):
            if self.jsd_view.dataselectiongroupbox.file_checkboxes[i].isChecked():
                sheet_list.append(self.get_file_sheets_from_combobox(i))

        try:
            self.jsd_view.update_jsd_timeline_plot(self.jsd_model)
            self.jsd_view.update_area_chart(sheet_list)
            return True
        except Exception as e:
            print(f"An error occurred during the update of category plots: {e}")
            return False

    def get_cols_to_use_for_jsd_calc(self, cbox, category):
        """
        Generates a list of columns from a sheet that should be used in the JSD calculation.

        This handles custom categories i.e. for custom age ranges

        Parameters:
            cbox (QComboBox): The combobox used to get the data file from.
            category (str): The sheet category to get the columns from.

        Returns:
            List of columns in the current sheet category
        """
        NOT_REPORTED = 'Not reported'

        cols_to_use = self.jsd_model.data_sources[cbox.currentData()].sheets[category].data_columns

        custom_age_ranges = self._config.data.get('custom age ranges', None)
        if custom_age_ranges and category in custom_age_ranges:
            cols_to_use = [f'{age_range[0]}-{age_range[1]} Custom' for
                           age_range in custom_age_ranges[category]] + [NOT_REPORTED]

        return cols_to_use

    def get_spider_plot_values(self, calc_date):
        """
        Compiles a dictionary of categories and JSD values for a given date.

        Parameters:
            calc_date (Optional[datetime.date]): The date to use for JSD calculation. Default is None.

        Returns:
            A dictionary of categories and JSD values for a given date.
        """
        if calc_date is None:
            calc_date = np.datetime64('today')

        jsd_view = self.jsd_view
        dataselectiongroupbox = jsd_view.dataselectiongroupbox
        categories = [dataselectiongroupbox.category_combobox.itemText(i) for i in
                      range(dataselectiongroupbox.category_combobox.count())]

        cbox0 = dataselectiongroupbox.file_comboboxes[0]
        sheets0 = self.jsd_model.data_sources[cbox0.currentData()].sheets
        cbox1 = dataselectiongroupbox.file_comboboxes[1]
        sheets1 = self.jsd_model.data_sources[cbox1.currentData()].sheets

        jsd_values = {category: calculate_jsd(sheets0[category].df,
                                              sheets1[category].df,
                                              self.get_cols_to_use_for_jsd_calc(cbox0, category),
                                              calc_date) for category in categories}

        return jsd_values


def calculate_jsd(df1, df2, cols_to_use, calc_date):
    """
    Calculate the Jensen-Shannon distance between two dataframes for a given date.

    There is an assumption that the date column of the dataframes are sorted from smallest to largest.

    Note: The Jensen-Shannon distance returned is the square root of the Jensen-Shannon divergence.

    Parameters:
    df1 (pd.DataFrame): First dataframe.
    df2 (pd.DataFrame): Second dataframe.
    cols_to_use (list): List of columns to use for the calculation.
    calc_date (pd.Timestamp): Date for which the calculation is performed.

    Returns:
    float: Jensen-Shannon distance between the two dataframes.
    """
    if df1.empty or df2.empty:
        return None

    df1_row = df1.date.searchsorted(calc_date, side='right') - 1
    df2_row = df2.date.searchsorted(calc_date, side='right') - 1

    df1_data = df1[cols_to_use].iloc[df1_row].values.astype(float)
    df2_data = df2[cols_to_use].iloc[df2_row].values.astype(float)

    return distance.jensenshannon(df1_data, df2_data, base=2.0)


def remove_elements_less_than_from_sorted_list(sorted_list, value):
    """
    Remove elements less than the given value from a sorted list.

    Args:
        sorted_list (list): A sorted list of elements.
        value: The value to compare against.

    Returns:
        list: A new list containing only elements greater than or equal to the value.
    """
    # Find the index of the first element greater than or equal to the value
    index = bisect_left(sorted_list, value)

    # Slice the list to keep only elements greater than or equal to the value
    return sorted_list[index:]
