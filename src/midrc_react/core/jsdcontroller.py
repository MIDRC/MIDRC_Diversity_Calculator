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
This module contains the JSDController class, which manages the JSD view and model.
"""

from bisect import bisect_left
import itertools

import numpy as np
import pandas as pd
from PySide6.QtCore import QObject, Signal
from scipy.spatial import distance

from midrc_react.core.aggregate_jsd_calc import calc_aggregate_jsd_at_date
from midrc_react.core.data_preprocessing import combine_datasets_from_list
from midrc_react.core.datetimetools import pandas_date_to_qdate
from midrc_react.core.famd_calc import calc_famd_ks2_at_date, calc_famd_ks2_at_dates
from midrc_react.core.jsdmodel import JSDTableModel
from midrc_react.core.numeric_distances import calc_ks2_samp_by_feature
from midrc_react.gui.common.jsdview_base import JsdViewBase


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
    NOT_REPORTED_COLUMN_NAME = 'Not Reported'

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
        self._num_categories = 0
        self._raw_data_available = False

        self.initialize()

    def initialize(self):
        """
        Initialize the JSDController.

        Returns:
            None
        """
        self.connect_signals()
        if self.jsd_view.update_view_on_controller_initialization is True:
            self.file_changed(None, new_category_index=0)

    def connect_signals(self):
        """
        Connects signals for file and category comboboxes.
        """
        jsd_view = self.jsd_view  # Store the result of jsd_view() in a variable
        jsd_view.add_data_source.connect(self.jsd_model.add_data_source)

        dataselectiongroupbox_class_name = type(jsd_view.dataselectiongroupbox).__name__

        if dataselectiongroupbox_class_name == 'JsdDataSelectionGroupBox':
            for f_c in jsd_view.dataselectiongroupbox.file_comboboxes:
                f_c.currentIndexChanged.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.num_data_items_changed.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.file_checkbox_state_changed.connect(self.file_changed)
            jsd_view.dataselectiongroupbox.category_combobox.currentIndexChanged.connect(self.category_changed)

        elif dataselectiongroupbox_class_name == 'DataSelectionGroupBox':
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

    @property
    def num_categories(self) -> int:
        """
        Get the number of categories.

        Returns:
            int: The number of categories.
        """
        return self._num_categories

    def file_changed(self, _, new_category_index=None):
        """
        Parses the categories from the files selected in the comboboxes and updates the category box appropriately.
        Emits the fileChangedSignal signal upon completion.

        Args:
            new_category_index Optional(int): The index of the category to set, if None then use previous index.
        """
        dataselectiongroupbox = self.jsd_view.dataselectiongroupbox
        file_infos = dataselectiongroupbox.get_file_infos()
        if not file_infos:
            print("No files available.")
            return

        category_info = dataselectiongroupbox.get_category_info()
        category_index = category_info['current_index']
        if new_category_index is not None:
            category_index = new_category_index

        # Compute the intersection of category keys across all file_infos.
        category_set = None
        for cbox in file_infos:
            ds = self.jsd_model.data_sources[cbox['source_id']]
            if category_set is None:
                category_set = set(ds.sheets.keys())
            else:
                category_set.intersection_update(ds.sheets.keys())

        category_list = list(category_set)

        # Compute has_raw_data using all() with a generator expression.
        has_raw_data = all(
            self.jsd_model.data_sources[cbox['source_id']].raw_data is not None
            for cbox in file_infos
        )

        self._num_categories = len(category_list)
        self._raw_data_available = has_raw_data
        if self._raw_data_available:
            category_list.append('Aggregate')
            category_list.append('FAMD')
            for category in category_list:
                if category in self.jsd_model.data_sources[file_infos[0]['source_id']].numeric_cols:
                    category_list.append(f'{category} (ks2)')

        dataselectiongroupbox.update_category_list(category_list, category_index)

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

    def get_categories(self):
        """
        Get the list of categories from the data sources.

        Returns:
            list: A list of categories.
        """
        categories = set()
        for data_source in self._jsd_model.data_sources.values():
            categories.update(data_source.sheets.keys())
        return list(categories)

    def category_changed(self):
        """
        Parses the dates from all files for the current category and updates the data in the model appropriately.

        Returns:
            None
        """
        dataselectiongroupbox = self.jsd_view.dataselectiongroupbox
        file_infos = dataselectiongroupbox.get_file_infos()
        category = dataselectiongroupbox.get_category_info()['current_text']

        # Try to avoid a race condition where the category is changed before the file is changed
        if not category:
            return

        def build_date_list(df1, df2):
            first_date = max(min(df1.date.values), min(df2.date.values))
            date_list = sorted(set(np.concatenate((df1.date.values, df2.date.values))))
            return remove_elements_less_than_from_sorted_list(date_list, first_date)

        model_input_data = []
        column_infos = []

        for (i, cbox1), (j, cbox2) in itertools.combinations(enumerate(file_infos), 2):
            file1 = cbox1['source_id']
            file2 = cbox2['source_id']
            data_source_1 = self.jsd_model.data_sources[file1]
            data_source_2 = self.jsd_model.data_sources[file2]

            input_data = None

            if all(category in ds.sheets for ds in (data_source_1, data_source_2)):
                df1 = data_source_1.sheets[category].df
                df2 = data_source_2.sheets[category].df
                date_list = build_date_list(df1, df2)
                cols_to_use = self.get_cols_to_use_for_jsd_calc(file1, category)

                input_data = [float(calculate_jsd(df1, df2, cols_to_use, calc_date)) for calc_date in date_list]

            elif category == 'Aggregate':
                raw_df1 = data_source_1.raw_data
                raw_df2 = data_source_2.raw_data
                date_list = build_date_list(raw_df1, raw_df2)
                cols_to_use = set(data_source_1.raw_columns_to_use())
                cols_to_use = list(cols_to_use.intersection(data_source_2.raw_columns_to_use()))
                if 'Race and Ethnicity' in cols_to_use:
                    cols_to_use.remove('Race and Ethnicity')

                input_data = [float(calc_aggregate_jsd_at_date(raw_df1, raw_df2, cols_to_use, calc_date))
                              for calc_date in date_list]

            elif category == 'FAMD':
                raw_df1 = data_source_1.raw_data
                raw_df2 = data_source_2.raw_data
                date_list = build_date_list(raw_df1, raw_df2)
                cols_to_use = set(data_source_1.raw_columns_to_use())
                cols_to_use = list(cols_to_use.intersection(data_source_2.raw_columns_to_use()))
                if 'Race and Ethnicity' in cols_to_use:
                    cols_to_use.remove('Race and Ethnicity')
                numeric_cols = []
                for str_col, col_info in data_source_1.numeric_cols.items():
                    cols_to_use.remove(str_col)
                    num_col = col_info['raw column']
                    cols_to_use.append(num_col)
                    numeric_cols.append(num_col)
                input_data = calc_famd_ks2_at_dates(
                    data_source_1.raw_data,
                    data_source_2.raw_data,
                    cols_to_use,
                    numeric_cols,
                    date_list,
                )
            elif category.endswith(' (ks2)'):
                raw_df1 = data_source_1.raw_data
                raw_df2 = data_source_2.raw_data
                combined_df = combine_datasets_from_list([raw_df1, raw_df2])
                date_list = build_date_list(raw_df1, raw_df2)
                str_col = category[:-6]
                num_col = data_source_1.numeric_cols[str_col]['raw column']

                input_data = [float(calc_ks2_samp_by_feature(combined_df[combined_df['date'] <= date],
                                                             num_col)['Dataset 0 vs Dataset 1']) for date in date_list]

            if input_data is not None:
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

    def get_timeline_data(self, category: str):
        """
        Get the timeline data for the specified category.

        Args:
            category (str): The category for which to get the timeline data.

        Returns:
            pd.DataFrame: A DataFrame containing the timeline data.
        """
        data_frames = []
        for ds1, ds2 in itertools.combinations(self.jsd_model.data_sources.values(), 2):
            # Ensure both data sources contain the category.
            if not all(category in ds.sheets for ds in (ds1, ds2)):
                continue

            # Copy ds1's dataframe for modifications.
            df = ds1.sheets[category].df.copy()
            df['label'] = f"{ds1.name} vs {ds2.name}"

            cols_to_use = self.get_cols_to_use_for_jsd_calc(ds1.name, category)
            df['value'] = df['date'].apply(
                lambda calc_date, ds1, ds2, category, cols_to_use=cols_to_use:
                calculate_jsd(
                    df1=ds1.sheets[category].df,
                    df2=ds2.sheets[category].df,
                    cols_to_use=cols_to_use,
                    calc_date=calc_date,
                )
            )
            data_frames.append(df)

        return pd.concat(data_frames, ignore_index=True) if data_frames else pd.DataFrame()

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
        for i, file_info in enumerate(file_infos):
            if file_info['checked']:
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
        for i, file_info in enumerate(file_infos):
            if file_info['checked']:
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
        for index1, index2 in itertools.combinations(indexes_to_use, 2):
            # Ensure we're not comparing the same file with itself
            if len(indexes_to_use) == 2 and index1 == index2:
                index2_candidates = [idx for idx in range(len(file_infos)) if idx != index1]
            else:
                index2_candidates = [index2]

            for idx2 in index2_candidates:
                source_id1 = file_infos[index1]['source_id']
                source_id2 = file_infos[idx2]['source_id']

                data_source_1 = self.jsd_model.data_sources[source_id1]
                data_source_2 = self.jsd_model.data_sources[source_id2]

                jsd_dict[(index1, idx2)] = {
                    category: calculate_jsd(
                        data_source_1.sheets[category].df,
                        data_source_2.sheets[category].df,
                        self.get_cols_to_use_for_jsd_calc(source_id1, category),
                        calc_date,
                    )
                    for category in categories[:self._num_categories]
                }
                for category in categories[self._num_categories:]:
                    if category == 'Aggregate':
                        cols_to_use = set(data_source_1.raw_columns_to_use())
                        cols_to_use = list(cols_to_use.intersection(data_source_2.raw_columns_to_use()))
                        if 'Race and Ethnicity' in cols_to_use:
                            cols_to_use.remove('Race and Ethnicity')
                        jsd_dict[(index1, idx2)][category] = calc_aggregate_jsd_at_date(
                            data_source_1.raw_data,
                            data_source_2.raw_data,
                            cols_to_use,
                            calc_date,
                        )
                    elif category == 'FAMD':
                        cols_to_use = set(data_source_1.raw_columns_to_use())
                        cols_to_use = list(cols_to_use.intersection(data_source_2.raw_columns_to_use()))
                        if 'Race and Ethnicity' in cols_to_use:
                            cols_to_use.remove('Race and Ethnicity')
                        numeric_cols = []
                        for str_col, col_info in data_source_1.numeric_cols.items():
                            cols_to_use.remove(str_col)
                            num_col = col_info['raw column']
                            cols_to_use.append(num_col)
                            numeric_cols.append(num_col)
                        jsd_dict[(index1, idx2)][category] = calc_famd_ks2_at_date(
                            data_source_1.raw_data,
                            data_source_2.raw_data,
                            cols_to_use,
                            numeric_cols,
                            calc_date,
                        )
                    elif category.endswith(' (ks2)'):
                        raw_df1 = data_source_1.raw_data
                        raw_df2 = data_source_2.raw_data
                        combined_df = combine_datasets_from_list([raw_df1, raw_df2])
                        str_col = category[:-6]
                        num_col = data_source_1.numeric_cols[str_col]['raw column']
                        jsd_dict[(index1, idx2)][category] = calc_ks2_samp_by_feature(
                            combined_df[combined_df['date'] <= calc_date],
                            num_col,
                        )['Dataset 0 vs Dataset 1']

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

    # Create a temporary dataframe with missing columns filled with zeros
    df1_temp = df1.reindex(columns=cols_to_use, fill_value=0)
    df2_temp = df2.reindex(columns=cols_to_use, fill_value=0)

    # Extract data without modifying df2
    df1_data = df1_temp.iloc[df1_row].values.astype(float)
    df2_data = df2_temp.iloc[df2_row].values.astype(float)

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
