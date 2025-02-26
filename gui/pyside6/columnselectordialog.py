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

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QDialogButtonBox, QHBoxLayout, QCheckBox, QButtonGroup, QDoubleSpinBox
)

class NumericColumnSelectorDialog(QDialog):
    """
    Dialog window for displaying and editing numeric column settings.

    This class represents a dialog window that allows the user to select numeric columns and set binning parameters.
    It inherits from the QDialog class provided by the PySide6.QtWidgets module.

    Attributes:
        columns (list): A list of column names.
        parent (QWidget): The parent widget of the dialog.
        layout (QVBoxLayout): The layout of the dialog.
        column_settings (dict): A dictionary containing the checkbox, min_input, max_input, and step_input widgets.
        button_box (QDialogButtonBox): The button box containing the OK and Cancel buttons.

    Methods:
        __init__(self, columns, parent=None): Initialize the NumericColumnSelectorDialog object.
        toggle_inputs(self, checked, min_input, max_input, step_input): Toggle the visibility of the min, max, and step inputs based on the checkbox state.
        get_selected_columns_with_bins(self): Return a dictionary of selected columns with their bin settings.
    """
    def __init__(self, columns, parent=None):
        """
        Initialize the NumericColumnSelectorDialog object.

        Args:
            columns (list): A list of column names.
            parent (QWidget, optional): The parent widget of the dialog. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Numeric Columns and Binning Parameters")
        self.layout = QVBoxLayout()

        # Add a checkbox and min/max/step input for each column
        self.column_settings = {}
        for column in columns:
            checkbox = QCheckBox(column)
            min_input = QDoubleSpinBox()
            min_input.setPrefix("Min: ")
            min_input.setMaximum(1e6)
            min_input.setValue(0)
            min_input.setVisible(False)  # Hidden by default

            max_input = QDoubleSpinBox()
            max_input.setPrefix("Max: ")
            max_input.setMaximum(1e6)
            max_input.setValue(100)
            max_input.setVisible(False)  # Hidden by default

            step_input = QDoubleSpinBox()
            step_input.setPrefix("Step: ")
            step_input.setMaximum(1e6)
            step_input.setValue(10)
            step_input.setVisible(False)  # Hidden by default

            # Connect the checkbox to show/hide the min, max, and step inputs
            checkbox.toggled.connect(lambda checked, min_in=min_input, max_in=max_input, step_in=step_input: self.toggle_inputs(checked, min_in, max_in, step_in))

            self.column_settings[column] = {
                'checkbox': checkbox,
                'min_input': min_input,
                'max_input': max_input,
                'step_input': step_input
            }

            row_layout = QHBoxLayout()
            row_layout.addWidget(checkbox)
            row_layout.addWidget(min_input)
            row_layout.addWidget(max_input)
            row_layout.addWidget(step_input)
            self.layout.addLayout(row_layout)

        # Add OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def toggle_inputs(self, checked, min_input, max_input, step_input):
        """Toggle the visibility of the min, max, and step inputs based on the checkbox state."""
        min_input.setVisible(checked)
        max_input.setVisible(checked)
        step_input.setVisible(checked)

    def get_selected_columns_with_bins(self):
        """Return a dictionary of selected columns with their bin settings."""
        selected_columns = {}
        for column, settings in self.column_settings.items():
            if settings['checkbox'].isChecked():
                min_value = settings['min_input'].value()
                max_value = settings['max_input'].value()
                step_value = settings['step_input'].value()
                if min_value < max_value and step_value > 0:
                    bins = list(range(int(min_value), int(max_value) + 1, int(step_value)))
                    selected_columns[column] = {'bins': bins}
        return selected_columns


class ColumnSelectorDialog(QDialog):
    """
    Dialog window for displaying and editing column selections.

    This class represents a dialog window that allows the user to select columns and set binning parameters.
    It inherits from the QDialog class provided by the PySide6.QtWidgets module.

    Attributes:
        columns (list): A list of column names.
        parent (QWidget): The parent widget of the dialog.
        layout (QVBoxLayout): The layout of the dialog.
        checkboxes (dict): A dictionary containing the checkbox widgets.
        button_box (QDialogButtonBox): The button box containing the OK and Cancel buttons.

    Methods:
        __init__(self, columns, parent=None, exclusive=False): Initialize the ColumnSelectorDialog object.
        get_selected_columns(self): Return a list of selected columns.
    """
    def __init__(self, columns, parent=None, exclusive=False):
        """
        Initialize the ColumnSelectorDialog object.

        Args:
            columns (list): A list of column names.
            parent (QWidget, optional): The parent widget of the dialog. Defaults to None.
            exclusive (bool, optional): Whether to use exclusive button group. Defaults to False.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Features")
        self.layout = QVBoxLayout()

        button_group = QButtonGroup(self)
        button_group.setExclusive(exclusive)
        # Add a checkbox for each column
        self.checkboxes = {}
        for column in columns:
            checkbox = QCheckBox(column)
            self.checkboxes[column] = checkbox
            self.layout.addWidget(checkbox)
            button_group.addButton(checkbox)

        # Add OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def get_selected_columns(self):
        """Return a list of selected columns."""
        return [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]