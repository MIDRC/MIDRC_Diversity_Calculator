import base64
import io

from dash import Dash, dcc, html, callback_context
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from PySide6.QtCore import Signal, QObject
from gui.jsdview_base import GroupBoxData

class DataSelectionGroupBox(QObject, GroupBoxData):
    category_changed = Signal()
    file_selection_changed = Signal(str)
    excel_file_uploaded = Signal(object)  # Signal to emit the uploaded file content

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
                'margin': '10px'
            },
            multiple=False
        )
        self.layout = html.Div()
        self._setup_layout()

        self.num_fileboxes = 5  # Set the default number of fileboxes
        self._initialize_data_sources()

        # Callback for category combobox
        self.app.callback(
            Output(self._category_combobox, 'value'),
            [Input(self._category_combobox, 'value')],
            [State(self._category_combobox, 'value')]
        )(self.on_category_changed)

        # Callback for num_fileboxes dropdown
        self.app.callback(
            Output(self._num_fileboxes_combobox, 'value'),
            [Input(self._num_fileboxes_combobox, 'value')],
            [State(self._num_fileboxes_combobox, 'value')]
        )(self.on_num_fileboxes_changed)

        # Callback for file selection dropdowns
        for combobox in self.file_comboboxes:
            self.app.callback(
                Output(combobox, 'value'),
                [Input(combobox, 'value')],
                [State(combobox, 'value')]
            )(self.on_file_selection_changed)

        # Callback for file upload
        self.app.callback(
            Output('output-data-upload', 'children'),
            [Input('upload-data', 'contents')],
            [State('upload-data', 'filename')]
        )(self._on_file_upload)

        # Callback to update filebox layout dynamically
        self.app.callback(
            Output('filebox-container', 'children'),
            Input(self._num_fileboxes_combobox, 'value')
        )(self.update_filebox_layout)

    def _setup_layout(self):
        self.layout.children = [
            html.Div([
                self._category_combobox,
                self._num_fileboxes_combobox,
                self._file_upload,
                html.Div(id='output-data-upload'),
                html.Div(id='filebox-container')  # This will hold the fileboxes dynamically
            ])
        ]

    def _initialize_data_sources(self):
        # Initialize file comboboxes based on data sources from JSDController
        data_sources = self.jsd_model.data_sources
        for index, data_source_key in enumerate(list(data_sources.keys())[len(self.file_comboboxes):self.num_fileboxes], start=len(self.file_comboboxes)):
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
        if value is None:
            return previous_value
        self.change_number_of_fileboxes(value)
        return value

    def update_filebox_layout(self, num_fileboxes):
        """Dynamically updates the displayed fileboxes when the number changes."""
        self.num_fileboxes = num_fileboxes
        data_sources = self.jsd_model.data_sources

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
        # Update file comboboxes based on data sources
        data_sources = self.jsd_model.data_sources
        for combobox in self._file_comboboxes:
            combobox.options = [{'label': ds_key, 'value': ds_key} for ds_key in data_sources.keys()]
        if self.num_fileboxes > len(self._file_comboboxes):
            self._initialize_data_sources()

    @property
    def file_comboboxes(self):
        return self._file_comboboxes

    @property
    def category_combobox(self):
        return self._category_combobox

    def change_number_of_fileboxes(self, num_fileboxes):
        self.num_fileboxes = num_fileboxes

        # Add file comboboxes if num_fileboxes is greater than the current number
        if self.num_fileboxes > len(self.file_comboboxes):
            self.update_file_comboboxes()

        # Remove file comboboxes if num_fileboxes is less than the current number
        elif self.num_fileboxes < len(self.file_comboboxes):
            # Remove excess comboboxes from the layout and list
            excess_comboboxes = len(self.file_comboboxes) - self.num_fileboxes
            self.on_file_selection_changed()

    def _on_file_upload(self, contents, filename):
        if contents is not None:
            content_type, content_string = contents.split(',')
            decoded = base64.b64decode(content_string)
            file_content = io.BytesIO(decoded)
            data_source_dict = {
                'description': filename,
                'name': filename,
                'content': file_content,
                'data type': 'content',
            }
            self.excel_file_uploaded.emit(data_source_dict)

    def update_category_combobox(self):
        # Update category combobox based on selected data sources
        previous_value = self.get_category_info()['current_text']

        file_infos = self.get_file_infos()
        cbox0 = file_infos[0]
        common_categories = self.jsd_model.data_sources[cbox0['source_id']].sheets.keys()

        for cbox2 in file_infos[1:]:
            categorylist2 = self.jsd_model.data_sources[cbox2['source_id']].sheets.keys()
            common_categories = [value for value in common_categories if value in categorylist2]
        self._category_combobox.options = [{'label': cat, 'value': cat} for cat in common_categories]
        if previous_value not in common_categories:
            self.update_category_list(common_categories, 0)
            self._category_combobox.value = common_categories[0]
        else:
            self.update_category_list(common_categories, common_categories.index(previous_value))
            self._category_combobox.value = previous_value
        self._category_combobox.disabled = False

    def on_category_changed(self, value, previous_value=None):
        if value is None:
            return previous_value
        self.update_category_text(value)
        self.category_changed.emit()
        return value

    def on_file_selection_changed(self, value=None, previous_value=None):
        data_sources = self.jsd_model.data_sources
        file_infos = []

        for index, file_combobox in enumerate(self.file_comboboxes):
            if file_combobox.value is None:
                continue  # Skip unselected dropdowns

            data_source_dict = data_sources[file_combobox.value].data_source
            file_infos.append({
                'description': data_source_dict['description'],
                'source_id': data_source_dict['name'],
                'index': index,
                'checked': True,
            })

        self._file_infos = file_infos
        self.update_category_combobox()  # Ensure category dropdown is updated properly

        if value is not None:
            return previous_value

        self.file_selection_changed.emit(value)

        return value

    def display(self):
        return self.layout