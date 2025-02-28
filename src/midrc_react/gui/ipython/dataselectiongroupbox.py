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
This module contains classes and functions for creating a data selection group box.
"""

import io

import ipywidgets as widgets
from PySide6.QtCore import QObject, Signal

from midrc_react.gui.common.jsdview_base import GroupBoxData
from midrc_react.gui.common.utils import create_data_source_dict, create_file_info, get_common_categories


# Define the data selection group box
class DataSelectionGroupBox(QObject, GroupBoxData):
    """
    Class: DataSelectionGroupBox
    This class represents a group box widget for data selection. It provides functionality for creating labels and
    combo boxes for data files and a category combo box. The class has methods for setting up the layout,
    updating the category combo box, and initializing the widget.
    Attributes:
        _file_comboboxes (list): A list of file comboboxes.
        _category_combobox (widgets.Dropdown): A category combo box.
        _num_fileboxes_combobox (widgets.Dropdown): A number of fileboxes combo box.
        _file_upload (widgets.FileUpload): A file upload component.
        _layout (widgets.VBox): The layout of the group box.
        _jsd_model (JSDTableModel): The JSDTableModel object.
        _num_fileboxes (int): The number of file boxes.
        _raw_data_available (bool): A flag indicating whether raw data is available.
    Methods:
        __init__(self, jsd_model): Initializes the DataSelectionGroupBox object.
        on_num_fileboxes_changed(self, change): Handles the number of file boxes changing.
        update_filebox_layout(self, num_fileboxes): Updates the filebox layout based on the number of file boxes.
        update_file_comboboxes(self): Updates the file comboboxes based on the data sources.
        on_category_changed(self, change): Handles the category changing.
        on_file_selection_changed(self, change=None): Handles the file selection changing.
        display(self): Returns the layout of the group box.
    """
    category_changed = Signal()
    file_selection_changed = Signal(str)
    excel_file_uploaded = Signal(object)  # Signal to emit the uploaded file content

    def __init__(self, jsd_model):
        """
        Initialize the DataSelectionGroupBox.

        Args:
            jsd_model (JSDTableModel): The JSDTableModel object.
        """
        super().__init__()
        self.jsd_model = jsd_model
        self._file_comboboxes = []
        self._category_combobox = widgets.Dropdown(
            options=[],
            value=None,
            description='Attribute:',
            disabled=True,
        )
        self._num_fileboxes_combobox = widgets.Dropdown(
            options=[2],  # Adjust the range as needed
            value=2,
            description='Number of Fileboxes:',
            disabled=False,
            style={'description_width': 'initial'},
        )
        self._file_upload = widgets.FileUpload(
            accept='.xlsx',
            multiple=False,
            description='Upload Excel File',
            layout=widgets.Layout(width='180px'),
        )
        self._file_upload.observe(self._on_file_upload, names='value')
        self.layout = widgets.VBox()
        self._setup_layout()

        self.num_fileboxes = 5  # Set the default number of fileboxes
        self._initialize_data_sources()

        # Connect signals
        self._category_combobox.observe(self.on_category_changed, names='value')
        self._num_fileboxes_combobox.observe(self.on_num_fileboxes_changed, names='value')
        for combobox in self.file_comboboxes:
            combobox.observe(self.on_file_selection_changed, names='value')

    def _setup_layout(self):
        """
        Sets up the layout of the group box.
        """
        spacer = widgets.Box(layout=widgets.Layout(flex='1 1 auto', width='auto'))
        self.layout.children = [widgets.HBox([self._category_combobox, spacer, self._num_fileboxes_combobox,
                                              self._file_upload])]

    def _initialize_data_sources(self):
        """
        Initialize the file comboboxes based on the data sources.
        """
        data_sources = self.jsd_model.data_sources
        for index, data_source_key in enumerate(list(data_sources.keys())[len(self.file_comboboxes):self.num_fileboxes],
                                                start=len(self.file_comboboxes)):
            combobox = widgets.Dropdown(
                options=list(data_sources.keys()),
                value=data_source_key,
                description=f'Data Source {index + 1}:',
                disabled=False,
                layout=widgets.Layout(width='300px'),
                style={'description_width': 'initial'},
            )
            self.file_comboboxes.append(combobox)
            self.layout.children += (combobox,)
            combobox.observe(self.on_file_selection_changed, names='value')

        self._num_fileboxes_combobox.options = list(range(2, len(data_sources) + 1))
        if len(data_sources) > 1:
            self._num_fileboxes_combobox.value = min(self.num_fileboxes, len(data_sources))

        # Initialize category combobox based on the current data selection
        if self.file_comboboxes:
            self.on_file_selection_changed()

    def on_num_fileboxes_changed(self, change):
        """
        Handles the number of file boxes changing.

        Args:
            change (dict): The change dictionary.
        """
        self.change_number_of_fileboxes(change['new'])

    def update_file_comboboxes(self):
        """
        Update the file comboboxes based on the data sources.
        """
        data_sources = self.jsd_model.data_sources
        for combobox in self._file_comboboxes:
            combobox.options = list(data_sources.keys())
        if self.num_fileboxes > len(self._file_comboboxes):
            self._initialize_data_sources()

    @property
    def file_comboboxes(self):
        """
        Get the file comboboxes.

        Returns:
            list: A list of file comboboxes.
        """
        return self._file_comboboxes

    def change_number_of_fileboxes(self, num_fileboxes):
        """
        Change the number of file boxes.

        Args:
            num_fileboxes (int): The new number of file boxes.
        """
        self.num_fileboxes = num_fileboxes

        # Add file comboboxes if num_fileboxes is greater than the current number
        if self.num_fileboxes > len(self.file_comboboxes):
            self.update_file_comboboxes()

        # Remove file comboboxes if num_fileboxes is less than the current number
        elif self.num_fileboxes < len(self.file_comboboxes):
            # Remove excess comboboxes from the layout and list
            excess_comboboxes = len(self.file_comboboxes) - self.num_fileboxes
            for _ in range(excess_comboboxes):
                combobox_to_remove = self._file_comboboxes.pop()
                self.layout.children = tuple(child for child in self.layout.children if child != combobox_to_remove)
            self.on_file_selection_changed()

    def _on_file_upload(self, change):
        """
        Handles the file upload.

        Args:
            change (dict): The change dictionary.
        """
        for filename, file_info in change['new'].items():
            content = file_info['content']
            file_content = io.BytesIO(content)
            data_source_dict = create_data_source_dict(filename, file_content)
            self.excel_file_uploaded.emit(data_source_dict)

    def update_category_combobox(self):
        """
        Update the category combobox based on the selected data sources.
        """
        previous_value = self.get_category_info()['current_text']

        file_infos = self.get_file_infos()

        # Use the helper to retrieve common categories.
        common_categories = get_common_categories(file_infos, self.jsd_model)

        self._category_combobox.options = common_categories
        if previous_value not in common_categories:
            self.update_category_list(common_categories, 0)
            self._category_combobox.index = 0
        else:
            self.update_category_list(common_categories, common_categories.index(previous_value))
            self._category_combobox.value = previous_value
        self._category_combobox.disabled = False

    def on_category_changed(self, change):
        """
        Handles the category changing.

        Args:
            change (dict): The change dictionary.
        """
        self.update_category_text(change['new'])
        self.category_changed.emit()

    def on_file_selection_changed(self, change=None):
        """
        Handles the file selection changing.

        Args:
            change (dict, optional): The change dictionary. Defaults to None.
        """
        data_sources = self.jsd_model.data_sources
        file_infos = []
        for index, file_combobox in enumerate(self.file_comboboxes):
            data_source_dict = data_sources[file_combobox.value].data_source
            file_infos.append(create_file_info(data_source_dict, index))
        self._file_infos = file_infos
        self.update_category_combobox()
        self.file_selection_changed.emit(change)

    def display(self):
        """
        Returns the layout of the group box.

        Returns:
            widgets.VBox: The layout of the group box.
        """
        return self.layout
