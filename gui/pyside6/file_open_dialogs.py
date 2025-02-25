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

import yaml
from typing import Any, Dict, Optional, Union
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QFileDialog,
    QMessageBox, QLineEdit, QFormLayout, QWidget
)
from PySide6.QtCore import QFileInfo

class BaseFileOptionsDialog(QDialog):
    """
    Base dialog window for displaying and editing file options.

    This class provides common functionality for dialogs that capture file metadata,
    such as setting the default window title and default values based on the selected file.
    """
    def __init__(self, parent: Optional[QWidget], file_name: str) -> None:
        """
        Initialize the base file options dialog.

        Args:
            parent (Optional[QWidget]): The parent widget.
            file_name (str): The full path of the file.
        """
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        fi: QFileInfo = QFileInfo(file_name)
        self.setWindowTitle(fi.fileName())
        self.default_base: str = fi.baseName()


class FileOptionsDialog(BaseFileOptionsDialog):
    """
    Dialog window for displaying and editing Excel file options.
    """
    def __init__(self, parent: Optional[QWidget], file_name: str) -> None:
        """
        Initialize the FileOptionsDialog for an Excel file.

        Args:
            parent (Optional[QWidget]): The parent widget.
            file_name (str): The Excel file path.
        """
        super().__init__(parent, file_name)

        # Create input fields for file metadata
        self.name_line_edit: QLineEdit = QLineEdit()
        self.description_line_edit: QLineEdit = QLineEdit()
        self.remove_column_text_line_edit: QLineEdit = QLineEdit()

        # Setup form layout
        form_layout: QFormLayout = QFormLayout()
        form_layout.addRow("Name (Plot Titles):", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu):", self.description_line_edit)
        form_layout.addRow("Remove Column Text:", self.remove_column_text_line_edit)
        self.layout().addLayout(form_layout)

        # Set default values based on the file name
        self.name_line_edit.setText(self.default_base)
        self.description_line_edit.setText(self.default_base)

        # Add dialog buttons (OK only, no Cancel option)
        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        self.layout().addWidget(button_box)

        self.resize(600, -1)


class CSVTSVOptionsDialog(BaseFileOptionsDialog):
    """
    Dialog window for displaying and editing CSV/TSV file options.
    """
    def __init__(self, parent: Optional[QWidget], file_name: str) -> None:
        """
        Initialize the CSVTSVOptionsDialog for a CSV/TSV file.

        Args:
            parent (Optional[QWidget]): The parent widget.
            file_name (str): The CSV/TSV file path.
        """
        super().__init__(parent, file_name)

        # Create input fields for additional CSV/TSV metadata
        self.name_line_edit: QLineEdit = QLineEdit()
        self.description_line_edit: QLineEdit = QLineEdit()
        self.columns_text_edit: QTextEdit = QTextEdit()
        self.numeric_cols_text_edit: QTextEdit = QTextEdit()
        self.plugin_line_edit: QLineEdit = QLineEdit()

        # Setup form layout
        form_layout: QFormLayout = QFormLayout()
        form_layout.addRow("Name (Plot Titles):", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu):", self.description_line_edit)
        form_layout.addRow("Columns (comma-separated or YAML list):", self.columns_text_edit)
        form_layout.addRow("Numeric Column Options (YAML):", self.numeric_cols_text_edit)
        form_layout.addRow("Plugin:", self.plugin_line_edit)
        self.layout().addLayout(form_layout)

        # Set default values based on the file name
        self.name_line_edit.setText(self.default_base)
        self.description_line_edit.setText(self.default_base)

        # Add dialog buttons with OK and Cancel options
        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

        self.resize(600, -1)


def open_excel_file_dialog(self: Any) -> None:
    """
    Open a file dialog to select an Excel file and show its options dialog.

    This function handles edge cases such as no file selected or dialog cancellation.
    It emits a data source dictionary via self.add_data_source and updates UI elements via self._dataselectiongroupbox.

    Args:
        self (Any): The calling object, expected to have an add_data_source signal and a _dataselectiongroupbox attribute.

    Returns:
        None
    """
    file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xls *.xlsx)")
    if not file_name:
        return  # No file selected

    dialog: FileOptionsDialog = FileOptionsDialog(self, file_name)
    if dialog.exec() != QDialog.Accepted:
        return  # User cancelled the dialog

    data_source_dict: Dict[str, Union[str, Any]] = {
        'name': dialog.name_line_edit.text(),
        'description': dialog.description_line_edit.text(),
        'data type': 'file',
        'filename': file_name,
        'remove column name text': dialog.remove_column_text_line_edit.text()
    }
    self.add_data_source.emit(data_source_dict)
    self._dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict['description'],
        data_source_dict['name']
    )


def open_yaml_input_dialog(self: Any) -> None:
    """
    Open a dialog to paste YAML content and add it as a data source.

    The dialog allows users to input YAML text. The function validates the YAML content and handles errors,
    notifying the user if parsing fails.

    Args:
        self (Any): The calling object, expected to have an add_data_source signal and a _dataselectiongroupbox attribute.

    Returns:
        None
    """
    dialog: QDialog = QDialog(self)
    dialog.setWindowTitle("Paste YAML Content")
    layout: QVBoxLayout = QVBoxLayout(dialog)
    label: QLabel = QLabel("Paste YAML content below:")
    layout.addWidget(label)
    text_edit: QTextEdit = QTextEdit()
    layout.addWidget(text_edit)
    button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec() == QDialog.Accepted:
        yaml_content: str = text_edit.toPlainText()
        try:
            data_source_dict: Dict[str, Any] = yaml.safe_load(yaml_content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse YAML content: {e}")
            return

        if not isinstance(data_source_dict, dict):
            QMessageBox.critical(self, "Error", "Parsed YAML content is not a valid dictionary.")
            return

        self.add_data_source.emit(data_source_dict)
        self._dataselectiongroupbox.add_file_to_comboboxes(
            data_source_dict.get('description', ''),
            data_source_dict.get('name', '')
        )


def open_csv_tsv_file_dialog(self: Any) -> None:
    """
    Open a file dialog to select a CSV or TSV file and show its options dialog.

    This function handles edge cases and user cancellations. It validates and parses the user inputs,
    including YAML parsing for numeric columns and columns fields, and emits a data source dictionary.

    Args:
        self (Any): The calling object, expected to have an add_data_source signal and a _dataselectiongroupbox attribute.

    Returns:
        None
    """
    file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV/TSV File", "", "CSV/TSV Files (*.csv *.tsv)")
    if not file_name:
        return  # No file selected

    dialog: CSVTSVOptionsDialog = CSVTSVOptionsDialog(self, file_name)
    if dialog.exec() != QDialog.Accepted:
        return  # User cancelled the dialog

    # Validate and parse numeric columns YAML input
    try:
        numeric_cols: Any = yaml.safe_load(dialog.numeric_cols_text_edit.toPlainText())
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to parse Numeric Column Options YAML: {e}")
        return

    # Process the columns input; support both comma-separated and YAML list formats
    columns_input: str = dialog.columns_text_edit.toPlainText().strip()
    if columns_input.startswith('['):
        try:
            columns: Any = yaml.safe_load(columns_input)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse Columns YAML: {e}")
            return
    else:
        columns = [col.strip() for col in columns_input.split(',') if col.strip()]

    data_source_dict: Dict[str, Any] = {
        'name': dialog.name_line_edit.text(),
        'description': dialog.description_line_edit.text(),
        'data type': 'file',
        'filename': file_name,
        'columns': columns,
        'numeric_cols': numeric_cols,
        'plugin': dialog.plugin_line_edit.text(),
    }
    self.add_data_source.emit(data_source_dict)
    self._dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict.get('description', ''),
        data_source_dict.get('name', '')
    )
