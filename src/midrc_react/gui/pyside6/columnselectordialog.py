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
This module contains the ColumnSelectorDialog and NumericColumnSelectorDialog classes for selecting columns in a GUI.
"""

from PySide6.QtWidgets import (
    QButtonGroup, QCheckBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QGridLayout, QHBoxLayout, QLineEdit,
    QScrollArea, QVBoxLayout, QWidget,
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
        toggle_inputs(self, checked, min_input, max_input, step_input): Toggle the visibility of the min, max, and step
                                                                        inputs based on the checkbox state.
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

        # Add a checkbox, a textedit for string column name, and min/max/step inputs for each column
        self.column_settings = {}
        for column in columns:
            checkbox = QCheckBox(column)

            # New QLineEdit for the target string column name
            label_edit = QLineEdit()
            label_edit.setPlaceholderText("Target String Column")
            label_edit.setMinimumWidth(150)
            label_edit.setVisible(False)  # Hidden by default

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
            checkbox.toggled.connect(
                lambda checked, label_ed=label_edit, min_in=min_input, max_in=max_input, step_in=step_input:
                self.toggle_inputs(checked, label_ed, min_in, max_in, step_in)
            )

            row_layout = QHBoxLayout()
            row_layout.addWidget(checkbox)
            row_layout.addWidget(label_edit)
            row_layout.addWidget(min_input)
            row_layout.addWidget(max_input)
            row_layout.addWidget(step_input)
            self.layout.addLayout(row_layout)

            self.column_settings[column] = {
                'checkbox': checkbox,
                'label_edit': label_edit,
                'min_input': min_input,
                'max_input': max_input,
                'step_input': step_input,
            }

        # Add OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

        self.setLayout(self.layout)

    def toggle_inputs(self, checked, label_ed, min_input, max_input, step_input):
        """Toggle the visibility of the min, max, and step inputs based on the checkbox state."""
        label_ed.setVisible(checked)
        min_input.setVisible(checked)
        max_input.setVisible(checked)
        step_input.setVisible(checked)

    def get_selected_columns_with_bins(self):
        """
        Return a dictionary of selected columns with their bin settings.
        Returns:
            dict: keys are the target string column names; values are tuples
                  (raw column, bins, labels) where labels is None.
        """
        selected_columns = {}
        for column, settings in self.column_settings.items():
            if settings['checkbox'].isChecked():
                # Use provided target name or default to the original column name
                target_col = settings['label_edit'].text().strip() or column
                min_val = settings['min_input'].value()
                max_val = settings['max_input'].value()
                step_val = settings['step_input'].value()
                if min_val < max_val and step_val > 0:
                    bins = list(range(int(min_val), int(max_val) + 1, int(step_val)))
                    selected_columns[target_col] = (column, bins, None)
        # print('selected_columns:\n', selected_columns)
        return selected_columns


class ColumnSelectorDialog(QDialog):
    """
    Dialog window for displaying and editing column selections.

    The checkboxes are displayed in a grid layout inside a scroll area to support
    a large number of columns. If a column name is longer than max_length characters,
    a shortened version is displayed with a tooltip showing the full column name.
    """
    def __init__(self, columns, parent=None, exclusive=False, max_length=25, rows_per_column=10):
        """
        Initialize the ColumnSelectorDialog object.

        Args:
            columns (list): A list of column names.
            parent (QWidget, optional): The parent widget. Defaults to None.
            exclusive (bool, optional): Whether to use an exclusive button group. Defaults to False.
            max_length (int, optional): Maximum characters to display before shortening the label.
            rows_per_column (int, optional): Number of checkboxes per column.
        """
        super().__init__(parent)
        self.setWindowTitle("Select Features")
        layout = QVBoxLayout(self)

        # Create a scroll area for the checkboxes
        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        grid_layout = QGridLayout(scroll_content)
        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        # Button group to optionally handle exclusive selection
        button_group = QButtonGroup(self)
        button_group.setExclusive(exclusive)
        self.checkboxes = {}

        # Add checkboxes in a grid layout using rows per column
        for idx, column in enumerate(columns):
            display_text = column
            if len(column) > max_length:
                display_text = column[:max_length] + "..."
            checkbox = QCheckBox(display_text)
            if len(column) > max_length:
                checkbox.setToolTip(column)
            self.checkboxes[column] = checkbox
            row = idx % rows_per_column
            col = idx // rows_per_column
            grid_layout.addWidget(checkbox, row, col)
            button_group.addButton(checkbox)

        # Add OK and Cancel buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def get_selected_columns(self):
        """Return a list of selected columns."""
        return [col for col, checkbox in self.checkboxes.items() if checkbox.isChecked()]
