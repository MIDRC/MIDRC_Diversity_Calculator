from PySide6.QtCore import Signal, QObject
import ipywidgets as widgets
from ipywidgets import VBox, HBox

from jsdview_base import GroupBoxData

# Define the data selection group box
class DataSelectionGroupBox(QObject, GroupBoxData):
    category_changed = Signal()
    file_selection_changed = Signal(str)

    def __init__(self, jsd_model):
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
            style = {'description_width': 'initial'}
        )
        self.layout = VBox()
        self._setup_layout()

        self.num_fileboxes = 2
        self._initialize_data_sources()

        # Connect signals
        self._category_combobox.observe(self.on_category_changed, names='value')
        self._num_fileboxes_combobox.observe(self.on_num_fileboxes_changed, names='value')
        for combobox in self.file_comboboxes:
            combobox.observe(self.on_file_selection_changed, names='value')

    def _setup_layout(self):
        spacer = widgets.Box(layout=widgets.Layout(flex='1 1 auto', width='auto'))
        self.layout.children = [HBox([self._category_combobox, spacer, self._num_fileboxes_combobox])]

    def _initialize_data_sources(self):
        # Initialize file comboboxes based on data sources from JSDController
        data_sources = self.jsd_model.data_sources
        for index, data_source_key in enumerate(list(data_sources.keys())[len(self.file_comboboxes):self.num_fileboxes], start=len(self.file_comboboxes)):
            combobox = widgets.Dropdown(
                options=list([ds_key for ds_key in data_sources.keys()]),
                value=data_source_key,
                description=f'Data Source {index + 1}:',
                disabled=False,
                layout=widgets.Layout(width='300px'),
                style = {'description_width': 'initial'}
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
        self.change_number_of_fileboxes(change['new'])

    def update_file_comboboxes(self):
        # Update file comboboxes based on data sources
        data_sources = self.jsd_model.data_sources
        for combobox in self._file_comboboxes:
            combobox.options = list(data_sources.keys())
        if self.num_fileboxes > len(self._file_comboboxes):
            self._initialize_data_sources()

    @property
    def file_comboboxes(self):
        return self._file_comboboxes

    def change_number_of_fileboxes(self, num_fileboxes):
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

    def update_category_combobox(self):
        # Update category combobox based on selected data sources
        previous_value = self.get_category_info()['current_text']

        file_infos = self.get_file_infos()
        cbox0 = file_infos[0]
        common_categories = self.jsd_model.data_sources[cbox0['source_id']].sheets.keys()

        for cbox2 in file_infos[1:]:
            categorylist2 = self.jsd_model.data_sources[cbox2['source_id']].sheets.keys()
            common_categories = [value for value in common_categories if value in categorylist2]
        self._category_combobox.options = common_categories
        if previous_value not in common_categories:
            self.update_category_list(common_categories, 0)
            self._category_combobox.index = 0
        else:
            self.update_category_list(common_categories, common_categories.index(previous_value))
            self._category_combobox.value = previous_value
        self._category_combobox.disabled = False

    def on_category_changed(self, change):
        self.update_category_text(change['new'])
        self.category_changed.emit()

    def on_file_selection_changed(self, change=None):
        data_sources = self.jsd_model.data_sources
        file_infos = []
        for index, file_combobox in enumerate(self.file_comboboxes):
            data_source_dict = data_sources[file_combobox.value].data_source
            file_infos.append({
                'description': data_source_dict['description'],
                'source_id': data_source_dict['name'],
                'index': index,
                'checked': True,
            })
        self._file_infos = file_infos
        self.update_category_combobox()
        self.file_selection_changed.emit(change)

    def display(self):
        return self.layout