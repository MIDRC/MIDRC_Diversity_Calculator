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
This module contains the DataSelectionGroupBox class, which represents a group box widget for data selection.
"""

import base64
import io

from dash import Dash, dcc, html
from dash.dependencies import Input, Output, State

from midrc_react.gui.common.file_upload import process_file_upload
from midrc_react.gui.common.jsdview_base import GroupBoxData
from midrc_react.gui.common.utils import create_data_source_dict, create_file_info, get_common_categories


class DataSelectionGroupBox(GroupBoxData):
    """
    Class: DataSelectionGroupBox
    This class represents a group box widget for data selection. It provides functionality for creating labels and
    combo boxes for data files and a category combo box. The class has methods for setting up the layout,
    updating the category combo box, and initializing the widget.
    Attributes:
        _file_comboboxes (list): A list of file comboboxes.
        _category_combobox (dcc.Dropdown): A category combo box.
        _num_fileboxes_combobox (dcc.Dropdown): A number of fileboxes combo box.
        _file_upload (dcc.Upload): A file upload component.
        _layout (html.Div): The layout of the group box.
        _jsd_model (JSDTableModel): The JSDTableModel object.
        _num_fileboxes (int): The number of file boxes.
        _raw_data_available (bool): A flag indicating whether raw data is available.
    Methods:
        __init__(self, jsd_model, app: Dash): Initializes the DataSelectionGroupBox object.
        on_num_fileboxes_changed(self, value, previous_value=None): Handles the number of file boxes changing.
        update_filebox_layout(self, num_fileboxes): Updates the filebox layout based on the number of file boxes.
        update_file_comboboxes(self): Updates the file comboboxes based on the data sources.
        on_category_changed(self, value, previous_value=None): Handles the category changing.
        on_file_selection_changed(self, value=None, previous_value=None): Handles the file selection changing.
        display(self): Returns the layout of the group box.
    """

    def __init__(self, jsd_model, app: Dash):
        super().__init__()
        self.app = app
        self.app.config.suppress_callback_exceptions = True  # Allow dynamically generated components

        self.jsd_model = jsd_model
        self._file_comboboxes = []
        self._category_combobox = dcc.Dropdown(
            options=[],
            value=None,
            placeholder='Select Attribute',
            disabled=True,
        )
        self._num_fileboxes_combobox = dcc.Dropdown(
            options=[{'label': str(i), 'value': i} for i in range(2, 6)],  # Adjust the range as needed
            value=2,
            placeholder='Number of Fileboxes',
            disabled=False,
        )
        self._file_upload = dcc.Upload(
            id='upload-data',
            children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
            style={
                'width': '100%',
                'height': '60px',
                'lineHeight': '60px',
                'borderWidth': '1px',
                'borderStyle': 'dashed',
                'borderRadius': '5px',
                'textAlign': 'center',
                'margin': '10px',
            },
            multiple=False,
        )
        self.layout = html.Div()
        self._setup_layout()

        self.num_fileboxes = 5  # Set the default number of fileboxes
        self._initialize_data_sources()

        # Callback for category combobox
        self.app.callback(
            Output(self._category_combobox, 'value'),
            [Input(self._category_combobox, 'value')],
            [State(self._category_combobox, 'value')],
        )(self.on_category_changed)

        # Callback for num_fileboxes dropdown
        self.app.callback(
            Output(self._num_fileboxes_combobox, 'value'),
            [Input(self._num_fileboxes_combobox, 'value')],
            [State(self._num_fileboxes_combobox, 'value')],
        )(self.on_num_fileboxes_changed)

        # Callback for file selection dropdowns
        for combobox in self.file_comboboxes:
            self.app.callback(
                Output(combobox, 'value'),
                [Input(combobox, 'value')],
                [State(combobox, 'value')],
            )(self.on_file_selection_changed)

        # Callback for file upload
        self.app.callback(
            Output('output-data-upload', 'children'),
            [Input('upload-data', 'contents')],
            [State('upload-data', 'filename')],
        )(self._on_file_upload)

        # Callback to update filebox layout dynamically
        self.app.callback(
            Output('filebox-container', 'children'),
            Input(self._num_fileboxes_combobox, 'value'),
        )(self.update_filebox_layout)

    def _setup_layout(self):
        self.layout.children = [
            html.Div([
                self._category_combobox,
                self._num_fileboxes_combobox,
                self._file_upload,
                html.Div(id='output-data-upload'),
                html.Div(id='filebox-container'),  # This will hold the fileboxes dynamically
            ])
        ]

    def _initialize_data_sources(self):
        # Initialize file comboboxes based on data sources from JSDController
        data_sources = self.jsd_model.data_sources
        for index, data_source_key in enumerate(list(data_sources.keys())[len(self.file_comboboxes):self.num_fileboxes],
                                                start=len(self.file_comboboxes)):
            combobox = dcc.Dropdown(
                options=[{'label': ds_key, 'value': ds_key} for ds_key in data_sources.keys()],
                value=data_source_key,
                placeholder=f'Data Source {index + 1}',
                disabled=False,
            )
            self.file_comboboxes.append(combobox)
            # self.layout.children.append(combobox)

        self._num_fileboxes_combobox.options = [{'label': str(i), 'value': i} for i in range(2, len(data_sources) + 1)]
        if len(data_sources) > 1:
            self._num_fileboxes_combobox.value = min(self.num_fileboxes, len(data_sources))

        # Initialize category combobox based on the current data selection
        if self.file_comboboxes:
            self.on_file_selection_changed()

    def on_num_fileboxes_changed(self, value, previous_value=None):
        """
        Handles the number of file boxes changing.

        Args:
            value (int): The new number of file boxes.
            previous_value (int, optional): The previous number of file boxes. Defaults to None.

        Returns:
            int: The new number of file boxes.
        """
        if value is None:
            return previous_value
        self.change_number_of_fileboxes(value)
        return value

    def update_filebox_layout(self, num_fileboxes):
        """Dynamically updates the displayed fileboxes when the number changes."""
        self.num_fileboxes = num_fileboxes
        data_sources = self.jsd_model.data_sources
        print(f"Updating fileboxes to {num_fileboxes} using data sources: {data_sources.keys()}")

        # Generate new dropdowns
        filebox_dropdowns = []
        for i in range(self.num_fileboxes):
            combobox = dcc.Dropdown(
                id=f'filebox-{i}',
                options=[{'label': key, 'value': key} for key in data_sources.keys()],
                value=self._file_comboboxes[i].value if i < len(self._file_comboboxes) else None,
                placeholder=f'Data Source {i + 1}',
                disabled=False,
            )
            filebox_dropdowns.append(combobox)

        # Update the internal list of comboboxes
        self._file_comboboxes = filebox_dropdowns

        return filebox_dropdowns

    def update_file_comboboxes(self):
        """
        Update the file comboboxes based on the data sources.
        """
        data_sources = self.jsd_model.data_sources
        for combobox in self._file_comboboxes:
            combobox.options = [{'label': ds_key, 'value': ds_key} for ds_key in data_sources.keys()]
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

    @property
    def category_combobox(self):
        """
        Get the category combobox.

        Returns:
            dcc.Dropdown: The category combobox.
        """
        return self._category_combobox

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
            # excess_comboboxes = len(self.file_comboboxes) - self.num_fileboxes
            self.on_file_selection_changed()

    def _on_file_upload(self, contents, filename):
        """
        Handles the file upload.

        Args:
            contents (str): The contents of the file.
            filename (str): The name of the file.

        Returns:
            html.Div: A div containing the file name.
        """
        if contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file_content = io.BytesIO(decoded)
            data_source_dict = create_data_source_dict(filename, file_content, content_type=content_type)

            print("⚠️ Manually calling file upload handler")
            # Retrieve the JSDViewDash instance from the app configuration.
            jsd_view = self.app.config.get('jsd_view')
            if jsd_view is not None:
                process_file_upload(jsd_view, data_source_dict)
            else:
                print("JSDViewDash instance not found in app.config.")
            return html.Div([f'File uploaded: {filename}'])
        return html.Div(['No file uploaded yet.'])

    def update_category_combobox(self):
        """
        Update the category combobox based on the selected data sources.
        """
        previous_value = self.get_category_info()['current_text']

        file_infos = self.get_file_infos()

        # Use the helper to retrieve common categories.
        common_categories = get_common_categories(file_infos, self.jsd_model)
        self._category_combobox.options = [{'label': cat, 'value': cat} for cat in common_categories]
        if previous_value not in common_categories:
            self.update_category_list(common_categories, 0)
            self._category_combobox.value = common_categories[0]
        else:
            self.update_category_list(common_categories, common_categories.index(previous_value))
            self._category_combobox.value = previous_value
        self._category_combobox.disabled = False

    def on_category_changed(self, value, previous_value=None):
        """
        Handles the category changing.

        Args:
            value (str): The new category.
            previous_value (str, optional): The previous category. Defaults to None.

        Returns:
            str: The new category.
        """
        if value is None:
            return previous_value
        self.update_category_text(value)
        return value

    def on_file_selection_changed(self, value=None, previous_value=None):
        """
        Handles the file selection changing.

        Args:
            value (str, optional): The new file selection. Defaults to None.
            previous_value (str, optional): The previous file selection. Defaults to None.

        Returns:
            str: The new file selection.
        """
        data_sources = self.jsd_model.data_sources
        file_infos = []

        for index, file_combobox in enumerate(self.file_comboboxes):
            if file_combobox.value is None:
                continue  # Skip unselected dropdowns

            data_source_dict = data_sources[file_combobox.value].data_source
            file_infos.append(create_file_info(data_source_dict, index))

        self._file_infos = file_infos
        self.update_category_combobox()  # Ensure category dropdown is updated properly

        if value is not None:
            return previous_value

        return value

    def display(self):
        """
        Returns the layout of the group box.

        Returns:
            html.Div: The layout of the group box.
        """
        return self.layout
