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

from bisect import bisect_left

import numpy as np
from PySide6.QtCore import QObject, Signal
from scipy.spatial import distance

from datetimetools import pandas_date_to_qdate
from jsdmodel import JSDTableModel
from jsdview_base import JsdViewBase
from dataselectiongroupbox import JsdDataSelectionGroupBox as JsdDataSelectionGroupBoxPySide
from ipython.jsdview_ipython import DataSelectionGroupBox as DataSelectionGroupBoxIpython


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
    NOT_REPORTED_COLUMN_NAME = 'Not reported'

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
        if jsd_view is None or not isinstance(jsd_view, JsdViewBase):
            raise ValueError("jsd_view must be a valid JsdViewBase instance")
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
        if self.jsd_view.update_view_on_controller_initialization is True:
            self.file_changed(None, newcategoryindex=0)

    def connect_signals(self):
        """
        Connects signals for file and category comboboxes.
        """
        jsd_view = self.jsd_view  # Store the result of jsd_view() in a variable
        jsd_view.add_data_source.connect(self.jsd_model.add_data_source)
        if isinstance(jsd_view.dataselectiongroupbox, JsdDataSelectionGroupBoxPySide):
            for f_c in jsd_view.dataselectiongroupbox.file_comboboxes:
                f_c.currentIndexChanged.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.num_data_items_changed.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.file_checkbox_state_changed.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.category_combobox.currentIndexChanged.connect(self.category_changed)

        elif isinstance(jsd_view.dataselectiongroupbox, DataSelectionGroupBoxIpython):
            jsd_view.dataselectiongroupbox.file_selection_changed.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.category_changed.connect(self.category_changed)

        self.fileChangedSignal.connect(self.update_file_based_charts)
        self.fileChangedSignal.connect(self.category_changed)

    @property
    def jsd_view(self) -> JsdViewBase:
        """
        Get the JSD view object.

        Returns:
            object: The JSD view object.
        """
        return self._jsd_view

    @jsd_view.setter
    def jsd_view(self, jsd_view: JsdViewBase) -> None:
        """
        Set the JSD view object.

        Parameters:
            jsd_view: The JSD view object.
        """
        if jsd_view is None or not isinstance(jsd_view, JsdViewBase):
            raise ValueError("jsd_view must be a valid JsdViewBase instance")
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
        file_infos = dataselectiongroupbox.get_file_infos()
        category_info = dataselectiongroupbox.get_category_info()
        categoryindex = category_info['current_index']
        if newcategoryindex is not None:
            categoryindex = newcategoryindex

        cbox0 = file_infos[0]
        categorylist = self.jsd_model.data_sources[cbox0['source_id']].sheets.keys()

        for cbox2 in file_infos[1:]:
            categorylist2 = self.jsd_model.data_sources[cbox2['source_id']].sheets.keys()
            categorylist = [value for value in categorylist if value in categorylist2]

        dataselectiongroupbox.update_category_list(categorylist, categoryindex)

        self.fileChangedSignal.emit()

    def get_file_sheets_from_index(self, index=0):
        """
        Get the sheets from the selected file combobox.

        Args:
            index (int): The index of the file combobox. Default is 0.

        Returns:
            dict: A dictionary containing the sheets from the selected file.
        """
        try:
            current_data = self.jsd_view.dataselectiongroupbox.get_file_infos()[index]['source_id']
        except IndexError as exc:
            raise IndexError("Index out of range") from exc

        sheets = self.jsd_model.data_sources[current_data].sheets
        return sheets

    def category_changed(self):
        """
        Parses the dates from all files for the current category and updates the data in the model appropriately.

        Returns:
            None
        """
        dataselectiongroupbox = self.jsd_view.dataselectiongroupbox
        file_infos = dataselectiongroupbox.get_file_infos()
        category = dataselectiongroupbox.get_category_info()['current_text']

        model_input_data = []
        column_infos = []

        for i, cbox1 in enumerate(file_infos[:-1]):
            file1 = cbox1['source_id']
            df1 = self.jsd_model.data_sources[file1].sheets[category].df
            cols_to_use = self.get_cols_to_use_for_jsd_calc(file1, category)

            for j, cbox2 in enumerate(file_infos[i + 1:], start=i + 1):
                file2 = cbox2['source_id']
                df2 = self.jsd_model.data_sources[file2].sheets[category].df

                first_date = max(df1.date.values[0], df2.date.values[0])
                date_list = sorted(set(np.concatenate((df1.date.values, df2.date.values))))
                date_list = remove_elements_less_than_from_sorted_list(date_list, first_date)

                input_data = [float(calculate_jsd(df1, df2, cols_to_use, calc_date)) for calc_date in date_list]

                model_input_data.append([pandas_date_to_qdate(calc_date) for calc_date in date_list])
                model_input_data.append(input_data)

                column_infos.append({
                    'category': category,
                    'index1': i,
                    'file1': file1,
                    'index2': j,
                    'file2': file2,
                })

        self.jsd_model.update_input_data(model_input_data, column_infos)

        self.update_category_plots()
        self.jsd_model.layoutChanged.emit()

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
        sheet_dict = {}
        file_infos = self.jsd_view.dataselectiongroupbox.get_file_infos()
        for i in range(len(file_infos)):
            if file_infos[i]['checked']:
                sheet_dict[i] = self.get_file_sheets_from_index(i)

        spider_plot_values = self.get_spider_plot_values(spider_plot_date)
        self.jsd_view.update_spider_chart(spider_plot_values)

        try:
            self.jsd_view.update_pie_chart_dock(sheet_dict)
        except (ValueError, KeyError, TypeError):
            return False

        return True

    def update_category_plots(self):
        """
        Update the category plots.

        This method updates the JSD timeline plot and the area chart.

        Returns:
            True if the update was successful, False otherwise
        """
        sheet_dict = {}
        file_infos = self.jsd_view.dataselectiongroupbox.get_file_infos()
        for i in range(len(file_infos)):
            if file_infos[i]['checked']:
                sheet_dict[i] = self.get_file_sheets_from_index(i)

        try:
            self.jsd_view.update_jsd_timeline_plot(self.jsd_model)
            self.jsd_view.update_area_chart(sheet_dict)
            return True
        except (ValueError, KeyError, TypeError) as e:
            print(f"An error occurred during the update of category plots: {e}")
            return False

    def get_cols_to_use_for_jsd_calc(self, source_id, category):
        """
        Generates a list of columns from a sheet that should be used in the JSD calculation.

        This handles custom categories i.e. for custom age ranges

        Parameters:
            source_id (str): The combobox used to get the data file from.
            category (str): The sheet category to get the columns from.

        Returns:
            List of columns in the current sheet category
        """
        cols_to_use = self.jsd_model.data_sources[source_id].sheets[category].data_columns

        custom_age_ranges = self._config.data.get('custom age ranges', None)
        if custom_age_ranges and category in custom_age_ranges:
            cols_to_use = [f'{age_range[0]}-{age_range[1]} Custom' for
                           age_range in custom_age_ranges[category]] + [JSDController.NOT_REPORTED_COLUMN_NAME]

        return cols_to_use

    def get_spider_plot_values(self, calc_date=None):
        """
        Compiles a dictionary of categories and JSD values for a given date.

        Parameters:
            calc_date (Optional[datetime.date]): The date to use for JSD calculation. Default is None.

        Returns:
            dict: A dictionary of categories and JSD values for a given date.
        """
        if calc_date is None:
            calc_date = np.datetime64('today')

        dataselectiongroupbox = self.jsd_view.dataselectiongroupbox
        categories = dataselectiongroupbox.get_category_info()['category_list']

        # Determine indexes to use based on checked boxes or default to all
        file_infos = dataselectiongroupbox.get_file_infos()
        indexes_to_use = [i for i, file_info in enumerate(file_infos) if file_info['checked']]
        if not indexes_to_use:
            indexes_to_use = list(range(len(file_infos)))
        if len(indexes_to_use) == 1:
            indexes_to_use = indexes_to_use * 2  # Duplicate the single index to ensure comparison

        jsd_dict = {}

        # Loop over the selected indexes and calculate JSD values
        for i, index1 in enumerate(indexes_to_use[:-1]):
            for index2 in indexes_to_use[i + 1:]:
                # Ensure we're not comparing the same file with itself
                if len(indexes_to_use) == 2 and index1 == index2:
                    index2_candidates = [idx for idx in range(len(file_infos)) if idx != index1]
                else:
                    index2_candidates = [index2]

                for idx2 in index2_candidates:
                    source_id0 = file_infos[index1]['source_id']
                    source_id1 = file_infos[idx2]['source_id']

                    sheets0 = self.jsd_model.data_sources[source_id0].sheets
                    sheets1 = self.jsd_model.data_sources[source_id1].sheets

                    jsd_dict[(index1, idx2)] = {
                        category: calculate_jsd(
                            sheets0[category].df,
                            sheets1[category].df,
                            self.get_cols_to_use_for_jsd_calc(source_id0, category),
                            calc_date,
                        )
                        for category in categories
                    }

        return jsd_dict


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
