#  Copyright (c) 2025 Medical Imaging and Data Resource Center (MIDRC).
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
This module contains the JsdViewBase class, which serves as a base class for JSD views.
"""

from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QMainWindow


@dataclass
class GroupBoxData:
    """
    Class: GroupBoxData
    This class represents a group box widget for data selection. It provides functionality for creating labels and
    combo boxes for data files and a category combo box. The class has methods for setting up the layout,
    updating the category combo box, and initializing the widget.
    Attributes:
        _file_infos (list): A list of file information dictionaries.
        _category_info (dict): A dictionary containing information about the selected category.
    Methods:
        __init__(self): Initializes the GroupBoxData object.
        get_file_infos(self): Returns the file information dictionaries.
        append_file_info(self, file_info: dict): Appends a file information dictionary to the list of file information
                                                 dictionaries.
        get_category_info(self): Returns the category information dictionary.
        update_category_list(self, categorylist, categoryindex): Updates the category information dictionary with the
                                                                given category list and index.
        update_category_index(self, categoryindex): Updates the category information dictionary with the given category
                                                    index.
        update_category_text(self, categorytext): Updates the category information dictionary with the given category
                                                  text.
    """
    _file_infos = []
    _category_info = {
        'current_text': None,
        'current_index': None,
        'category_list': [],
    }

    @property
    def file_infos(self):
        """
        Get the file information dictionaries.

        Returns:
            list: A list of file information dictionaries.
        """
        return self._file_infos

    def get_file_infos(self):
        """
        Get the file information dictionaries.

        Returns:
            list: A list of file information dictionaries.
        """
        return self._file_infos

    def append_file_info(self, file_info: dict):
        """Appends a file information dictionary to the list of file information dictionaries."""
        file_info['checked'] = file_info.get('checked', True)
        self._file_infos.append(file_info)
        # TODO: Update the category list too?

    @property
    def category_info(self):
        """
        Get the category information dictionary.

        Returns:
            dict: A dictionary containing information about the selected category.
        """
        return self._category_info

    def get_category_info(self):
        """
        Get the category information dictionary.

        Returns:
            dict: A dictionary containing information about the selected category.
        """
        return self._category_info

    def update_category_list(self, categorylist, categoryindex):
        """Updates the category information dictionary with the given category list and index."""
        self._category_info = {
            'current_text': categorylist[categoryindex],
            'current_index': categoryindex,
            'category_list': categorylist,
        }

    def update_category_index(self, categoryindex):
        """Updates the category information dictionary with the given category index."""
        self._category_info['current_index'] = categoryindex
        self._category_info['current_text'] = self._category_info['category_list'][categoryindex]

    def update_category_text(self, categorytext):
        """Updates the category information dictionary with the given category text."""
        category_list = self._category_info['category_list']
        if categorytext in category_list:
            self._category_info['current_text'] = categorytext
            self._category_info['current_index'] = category_list.index(categorytext)


class JsdViewBase(QObject):
    """
    Class: JsdViewBase
    This class represents a base class for JSD views. It provides functionality for creating a data selection group box,
    updating the category combo box, and initializing the widget.
    Attributes:
        _data_selection_group_box (GroupBoxData): A data selection group box.
        _controller (JSDController): A JSDController object.
        update_view_on_controller_initialization (bool): A flag indicating whether the view should be updated on
                                                         controller initialization.
    Methods:
        __init__(self): Initializes the JsdViewBase object.
        open_excel_file(self, data_source_dict): Opens an Excel file and adds it to the data selection group box.
        update_pie_chart_dock(self, sheet_dict): Updates the pie chart dock with the given sheet dict.
        update_spider_chart(self, spider_plot_values_dict): Updates the spider chart with new values.
        update_jsd_timeline_plot(self, jsd_model): Updates the JSD timeline plot with the specified JSD model.
        update_area_chart(self, sheet_dict): Updates the area chart with new data.
    """
    _data_selection_group_box = GroupBoxData()
    _controller = None
    update_view_on_controller_initialization = True
    add_data_source = Signal(dict)

    def __init__(self):
        """
        Initialize the JsdViewBase.
        """
        if not isinstance(self, QMainWindow):
            super().__init__()
        self.update_view_on_controller_initialization = True
        self._dataselectiongroupbox = GroupBoxData()

    @property
    def dataselectiongroupbox(self):
        """
        Get the data selection group box.

        Returns:
            GroupBoxData: The data selection group box.
        """
        return self._dataselectiongroupbox

    def open_excel_file(self, data_source_dict):
        """
        Opens an Excel file and adds it to the data selection group box.

        Args:
            data_source_dict (dict): The data source dictionary.
        """
        self._dataselectiongroupbox.append_file_info({
            'description': data_source_dict['description'],
            'source_id': data_source_dict['name'],
            'index': len(self._dataselectiongroupbox.file_infos),
            'checked': True,
        })

    def update_pie_chart_dock(self, sheet_dict):
        """
        Updates the pie chart dock with the given sheet dict.

        Args:
            sheet_dict (dict): A dictionary of index keys and sheets.
        """
        pass  # pylint: disable=unnecessary-pass

    def update_spider_chart(self, spider_plot_values_dict):
        """
        Updates the spider chart with new values.

        Args:
            spider_plot_values_dict (dict): A dictionary of dictionaries where each dictionary contains
            the values for one series on the spider chart.
        """
        pass  # pylint: disable=unnecessary-pass

    def update_jsd_timeline_plot(self, jsd_model):
        """
        Updates the JSD timeline plot with the specified JSD model.

        Args:
            jsd_model (JSDTableModel): The JSDTableModel object.
        """
        pass  # pylint: disable=unnecessary-pass

    def update_area_chart(self, category):
        """
        Updates the area chart with new data.

        Args:
            sheet_dict (dict): A dictionary of index keys and sheets containing data for the chart.
        """
        pass  # pylint: disable=unnecessary-pass
