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

from PySide6.QtCore import QSignalBlocker, Signal
from PySide6.QtWidgets import QCheckBox, QComboBox, QFormLayout, QGroupBox, QHBoxLayout, QLabel


class JsdDataSelectionGroupBox(QGroupBox):
    """
    Class: JsdDataSelectionGroupBox

    This class represents a group box widget for data selection. It provides functionality for creating labels and
    combo boxes for data files and a category combo box. The class has methods for setting up the layout,
    updating the category combo box, and initializing the widget.

    Attributes:
        num_data_items_changed (Signal): A signal emitted when the number of data items in the JsdDataSelectionGroupBox
                                         changes.
        NUM_DEFAULT_DATA_ITEMS (int): The default number of data items.

    Methods:
        __init__(self, data_sources): Initializes the JsdDataSelectionGroupBox object.
        set_layout(self, data_sources): Sets the layout for the given data sources.
        add_file_combobox_to_layout(self, auto_populate: bool = True): Adds a file combobox to the layout.
        remove_file_combobox_from_layout(self): Removes a file combobox from the layout.
        set_num_data_items(self, count: int): Sets the number of data items in the JsdDataSelectionGroupBox.
        add_file_to_comboboxes(self, description: str, name: str): Adds a file to the file comboboxes.
        update_category_combo_box(self, categorylist, categoryindex): Updates the category combo box with the given
                                                                      category list and selected index.
    """
    num_data_items_changed = Signal(int)
    file_checkbox_state_changed = Signal(bool)
    NUM_DEFAULT_DATA_ITEMS = 2

    def __init__(self, data_sources):
        """
        Initialize the JsdDataSelectionGroupBox.

        This method sets up the data selection group box by creating labels and combo boxes for data files and a
        category combo box.
        """
        super().__init__()

        self.setTitle('Data Selection')

        self.form_layout = QFormLayout()
        self.file_comboboxes = []
        self.file_checkboxes = []
        self.category_label = QLabel('Attribute')
        self.category_combobox = QComboBox()
        self.set_layout(data_sources)

    def set_layout(self, data_sources):
        """
        Set the layout for the given data sources.

        Parameters:
        - data_sources: A list of data sources.

        Returns:
        None
        """
        # Create the form layout
        form_layout = self.form_layout

        # Set the layout for the widget
        self.setLayout(form_layout)

        # Add the category label and combobox to the form layout
        form_layout.addRow(self.category_label, self.category_combobox)

        # First, add the first combobox
        self.add_file_combobox_to_layout(auto_populate=False)

        # Add the file comboboxes and labels to the form layout
        items = [(d['description'], d['name']) for d in data_sources]
        for combobox_item in items:
            self.add_file_to_comboboxes(combobox_item[0], combobox_item[1])
        self.file_comboboxes[0].setCurrentIndex(0)
        self.file_checkboxes[0].setChecked(True)

        # Now we can copy the data from the first combobox to the rest of them
        self.set_num_data_items(self.NUM_DEFAULT_DATA_ITEMS)

    def add_file_combobox_to_layout(self, auto_populate: bool = True):
        """
        Add a file combobox to the layout.

        Parameters:
        - auto_populate (bool): If True, the combobox will be populated with items from the first combobox.

        Returns:
        None
        """
        new_hbox = QHBoxLayout()
        new_combobox = QComboBox()
        new_checkbox = QCheckBox()
        new_hbox.addWidget(new_combobox, stretch=1)
        new_hbox.addWidget(new_checkbox, stretch=0)

        index = self.form_layout.rowCount()
        new_label = QLabel(f'Data File {index}')
        self.form_layout.insertRow(index - 1, new_label, new_hbox)

        self.file_comboboxes.append(new_combobox)
        self.file_checkboxes.append(new_checkbox)
        new_checkbox.toggled.connect(self.file_checkbox_state_changed.emit)

        if auto_populate:
            cbox: QComboBox = self.file_comboboxes[0]
            for i in range(cbox.count()):
                new_combobox.addItem(cbox.itemText(i), userData=cbox.itemData(i))
            new_combobox.setCurrentIndex(index - 1)

    def remove_file_combobox_from_layout(self):
        """
        Remove a file combobox from the layout.

        This method removes the last file combobox from the layout, including its corresponding label. It updates the
        form layout by removing the row at the specified index. It also removes the label and combobox from the
        respective lists.

        Parameters:
        - None

        Returns:
        - None
        """
        index = len(self.file_comboboxes) - 1
        self.form_layout.removeRow(index)
        self.file_comboboxes.pop(index)
        self.file_checkboxes.pop(index)

    def set_num_data_items(self, count: int):
        """
        Set the number of data items in the JsdDataSelectionGroupBox.

        This method adjusts the number of file comboboxes in the layout based on the given count.
        * If the current number of file comboboxes is equal to the count, the method returns without making any changes.
        * If the current number of file comboboxes is less than the count, the method adds file comboboxes to the layout
          using the add_file_combobox_to_layout method.
        * If the current number of file comboboxes is greater than the count, the method removes file comboboxes from
          the layout using the remove_file_combobox_from_layout method.
        * Finally, the method emits the num_data_items_changed signal with the updated count.

        Parameters:
        - count (int): The desired number of data items.

        Returns:
        None
        """
        if len(self.file_comboboxes) == count:
            return
        while len(self.file_comboboxes) < count:
            self.add_file_combobox_to_layout()
        while len(self.file_comboboxes) > count:
            self.remove_file_combobox_from_layout()
        self.num_data_items_changed.emit(count)

    def add_file_to_comboboxes(self, description: str, name: str):
        """
        Add a file to the file comboboxes.

        This method adds a file to each of the file comboboxes in the JsdDataSelectionGroupBox.
        The file is represented by a description and a name.
        The description is displayed in the combobox as the item text, and the name is stored as the item data.

        Parameters:
        - description (str): The description of the file.
        - name (str): The name of the file.

        Returns:
        None
        """
        for combobox in self.file_comboboxes:
            combobox.addItem(description, userData=name)

    def update_category_combo_box(self, categorylist, categoryindex):
        """
        Update the category combo box with the given category list and set the selected index to the specified
        category index.

        Parameters:
        - categorylist (list): The list of categories to populate the combo box.
        - categoryindex (int): The index of the category to select in the combo box.

        Returns:
        None
        """
        with QSignalBlocker(self.category_combobox):
            self.category_combobox.clear()
            self.category_combobox.addItems(categorylist)
            self.category_combobox.setCurrentIndex(categoryindex)
