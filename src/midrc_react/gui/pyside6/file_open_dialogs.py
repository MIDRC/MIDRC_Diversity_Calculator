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
Module for file open dialogs using PySide6.

This module provides dialogs for opening Excel and CSV/TSV files along with
options dialogs. The dialogs support file-specific persistence via QSettings,
plugin processing, and column selection.
"""

import csv
import importlib.util
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
from PySide6.QtCore import QFileInfo, QSettings
from PySide6.QtWidgets import (
    QComboBox, QDialog, QDialogButtonBox, QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox,
    QPushButton, QSizePolicy, QTextEdit, QVBoxLayout, QWidget,
)
import yaml

from midrc_react.gui.pyside6.columnselectordialog import ColumnSelectorDialog, NumericColumnSelectorDialog


class BaseFileOptionsDialog(QDialog):
    """
    Base dialog window for displaying and editing file options.

    Provides common functionality such as setting the default window title
    and base name from the file.
    """
    def __init__(self, parent: Optional[QWidget], file_name: str) -> None:
        """
        Initialize the base file options dialog.

        Args:
            parent (Optional[QWidget]): The parent widget.
            file_name (str): The full path of the file.
        """
        super().__init__(parent)
        self.settings = QSettings("MIDRC", "REACH")
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

        # Add dialog buttons (OK only)
        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        self.layout().addWidget(button_box)

        self.resize(600, -1)


def represent_list(dumper, data):
    """
    Represent lists in flow style (inline with square brackets)

    Args:
        dumper: The YAML dumper.
        data: The list to represent.
    """
    return dumper.represent_sequence('tag:yaml.org,2002:seq', data, flow_style=True)


# pylint: disable=too-many-ancestors
class FlowStyleListDumper(yaml.Dumper):
    """ YAML dumper that represents lists in flow style. """
    pass  # pylint: disable=unnecessary-pass


FlowStyleListDumper.add_representer(list, represent_list)


# pylint: disable=too-many-ancestors,too-many-instance-attributes,too-many-locals,too-many-statements
class CSVTSVOptionsDialog(BaseFileOptionsDialog):
    """
    Dialog for editing CSV/TSV file options with plugin processing.

    Provides file-specific persistence and a fallback to last used settings.
    """
    def __init__(self, parent: Optional[QWidget], file_name: str,
                 available_columns: Optional[List[str]] = None) -> None:
        """
        Initialize the CSV/TSV options dialog.

        Args:
            parent (Optional[QWidget]): The parent widget.
            file_name (str): The file path.
            available_columns (Optional[List[str]]): The list of available columns.
        """
        super().__init__(parent, file_name)
        self.available_columns = available_columns or []
        self.processed_df = None
        self.file_name = file_name

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ----- Plugin Processing Section -----
        top_widget = QWidget()
        top_layout = QVBoxLayout()
        top_widget.setLayout(top_layout)

        # Row 1: File path display using a conditional relative or full path
        file_layout = QHBoxLayout()
        file_label = QLabel("File:")
        relative_path = os.path.relpath(file_name)
        display_path = file_name if relative_path.count('..') > 2 else relative_path
        self.file_path_line_edit = QLineEdit(display_path)
        self.file_path_line_edit.setReadOnly(True)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_path_line_edit)
        top_layout.addLayout(file_layout)

        form_layout = QFormLayout()
        self.name_line_edit = QLineEdit()
        self.description_line_edit = QLineEdit()
        form_layout.addRow("Name (Plot Titles):", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu):", self.description_line_edit)
        top_layout.addLayout(form_layout)

        # Step 2: Plugin dropdown and Process Plugin button
        plugin_layout = QHBoxLayout()
        plugin_label = QLabel("Plugin:")
        self.plugin_combo = QComboBox()
        self.plugin_combo.addItem("(None)")
        plugin_folder = "plugins"
        if os.path.isdir(plugin_folder):
            for file in os.listdir(plugin_folder):
                if file.endswith(".py"):
                    plugin_name = file[:-3]
                    self.plugin_combo.addItem(plugin_name)
        plugin_folder = os.path.join(Path(__file__).resolve().parent.parent.parent, plugin_folder)
        if os.path.isdir(plugin_folder):
            for file in os.listdir(plugin_folder):
                if file.endswith(".py"):
                    plugin_name = file[:-3]
                    self.plugin_combo.addItem(plugin_name)
        # Set the default selection to the first plugin if available
        if self.plugin_combo.count() > 0:
            self.plugin_combo.setCurrentIndex(1)
        self.process_button = QPushButton("Process Plugin")
        self.process_button.clicked.connect(self.process_plugin)
        plugin_layout.addWidget(plugin_label)
        plugin_layout.addWidget(self.plugin_combo)
        plugin_layout.addWidget(self.process_button)
        # Add status label for notifications below the button
        self.plugin_status_label = QLabel("")
        plugin_layout.addWidget(self.plugin_status_label)
        top_layout.addLayout(plugin_layout)

        main_layout.addWidget(top_widget)

        # ----- Main Options Section (Initially Disabled) -----
        self.rest_widget = QWidget()
        self.rest_widget.setMinimumHeight(200)
        rest_layout = QFormLayout()

        # Column selector row
        columns_layout = QHBoxLayout()
        self.columns_line_edit = QLineEdit()
        self.columns_line_edit.setReadOnly(True)
        # Set the size policy to expanding horizontally
        self.columns_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.select_columns_button = QDialogButtonBox()
        select_columns_btn = self.select_columns_button.addButton("Select Columns", QDialogButtonBox.ActionRole)
        select_columns_btn.clicked.connect(self.open_column_selector)
        columns_layout.addWidget(self.columns_line_edit)
        columns_layout.addWidget(self.select_columns_button)
        # Set stretch so the line edit uses all available space
        columns_layout.setStretchFactor(self.columns_line_edit, 1)
        rest_layout.addRow("Columns to Use:", columns_layout)

        # Numeric column selector row
        numeric_layout = QHBoxLayout()
        self.numeric_cols_text_edit = QTextEdit()
        # Set the size policy to expanding horizontally
        self.numeric_cols_text_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.numeric_cols_text_edit.setMinimumWidth(380)
        self.select_numeric_cols_button = QDialogButtonBox()
        select_numeric_btn = self.select_numeric_cols_button.addButton("Select Numeric Columns",
                                                                       QDialogButtonBox.ActionRole)
        select_numeric_btn.clicked.connect(self.open_numeric_column_selector)
        numeric_layout.addWidget(self.numeric_cols_text_edit)
        numeric_layout.addWidget(self.select_numeric_cols_button)
        # Set stretch so the text edit uses all available space
        numeric_layout.setStretchFactor(self.numeric_cols_text_edit, 1)
        rest_layout.addRow("Numeric Column Options:", numeric_layout)

        self.rest_widget.setLayout(rest_layout)
        self.rest_widget.setEnabled(False)
        main_layout.addWidget(self.rest_widget)

        # Final OK/Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self.setLayout(main_layout)
        self.resize(600, 400)

        self.name_line_edit.setText(self.default_base)
        self.description_line_edit.setText(self.default_base)

        # Load saved defaults
        self.load_defaults()

    def _load_values_from_group(self, settings, group: str) -> Dict[str, Any]:
        """
        Helper to load common QSettings values from a given group.

        Args:
            settings: QSettings object.
            group (str): The group name to load values from.
        """
        settings.beginGroup(group)
        values = {
            "plugin": settings.value("plugin", ""),
            "name": settings.value("name", ""),
            "description": settings.value("description", ""),
            "columns": settings.value("columns", ""),
            "numeric_cols": settings.value("numeric_cols", ""),
        }
        settings.endGroup()
        return values

    def load_defaults(self) -> None:
        """
        Load saved options for this file from QSettings.

        If no file-specific settings are found, load the last used settings.
        """
        settings = self.settings
        file_group = f"csvtsv/{self.file_name}"
        file_values = self._load_values_from_group(settings, file_group)

        # If all file-specific values are empty, fallback to last used settings.
        if not any(file_values.values()):
            last_values = self._load_values_from_group(settings, "csvtsv/last")
        else:
            last_values = {}

        saved_plugin = file_values.get("plugin") or last_values.get("plugin", "")
        saved_name = file_values.get("name") or last_values.get("name", self.default_base)
        saved_description = (
            file_values.get("description") or last_values.get("description", self.default_base)
        )
        saved_columns = file_values.get("columns") or last_values.get("columns", "")
        saved_numeric = file_values.get("numeric_cols") or last_values.get("numeric_cols", "")

        if saved_plugin:
            idx = self.plugin_combo.findText(saved_plugin)
            if idx != -1:
                self.plugin_combo.setCurrentIndex(idx)
        self.name_line_edit.setText(saved_name)
        self.description_line_edit.setText(saved_description)
        if saved_columns:
            self.columns_line_edit.setText(saved_columns)
        if saved_numeric:
            self.numeric_cols_text_edit.setText(saved_numeric)

    def _set_settings_values_to_group(self, settings, group):
        """
        Helper to set common QSettings values.

        Args:
            settings: QSettings object.
            group (str): The group name to set values for.
        """
        settings.beginGroup(group)
        settings.setValue("plugin", self.plugin_combo.currentText().strip())
        settings.setValue("name", self.name_line_edit.text())
        settings.setValue("description", self.description_line_edit.text())
        settings.setValue("columns", self.columns_line_edit.text())
        settings.setValue("numeric_cols", self.numeric_cols_text_edit.toPlainText())
        settings.endGroup()

    def save_defaults(self) -> None:
        """
        Save current dialog options to QSettings for both file-specific and last used settings.
        """
        settings = self.settings
        # Save file-specific defaults.
        self._set_settings_values_to_group(settings, f"csvtsv/{self.file_name}")

        # Also update last used settings.
        self._set_settings_values_to_group(settings, "csvtsv/last")

    def accept(self) -> None:
        """Override accept to save defaults before closing the dialog."""
        self.save_defaults()
        super().accept()

    def process_plugin(self) -> None:
        """
        Process the file with the selected plugin (if any) and update available columns.
        The plugin selection controls are locked after processing.
        Instead of popups, text is displayed in the plugin status label.
        """
        selected_plugin = self.plugin_combo.currentText().strip()
        if selected_plugin == "(None)":
            self.plugin_status_label.setText("plugin bypassed")
        else:
            delimiter = ',' if self.file_name.lower().endswith('.csv') else '\t'
            try:
                df = pd.read_csv(self.file_name, delimiter=delimiter)
            except pd.errors.ParserError as pe:
                self.plugin_status_label.setText(f"CSV parsing failed: {pe}")
                return
            except FileNotFoundError as fnfe:
                self.plugin_status_label.setText(f"File not found: {fnfe}")
                return
            except Exception as e:  # pylint: disable=W0718
                self.plugin_status_label.setText(f"Processing failed: {e}")
                return
            plugin_path = os.path.join("plugins", f"{selected_plugin}.py")
            if not os.path.exists(plugin_path):
                plugin_path = os.path.join(Path(__file__).resolve().parent.parent.parent, plugin_path)
                if not os.path.exists(plugin_path):
                    self.plugin_status_label.setText("Plugin file not found.")
                    return
            spec = importlib.util.spec_from_file_location(selected_plugin, plugin_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            if not hasattr(module, "preprocess_data"):
                self.plugin_status_label.setText("Plugin does not define preprocess_data.")
                return
            preprocess_data = module.preprocess_data
            try:
                df = preprocess_data(df)
            except Exception as e:  # pylint: disable=W0718
                self.plugin_status_label.setText(f"Plugin processing failed: {str(e)}")
                return
            self.processed_df = df
            self.available_columns = list(df.columns)

            # Check selected cols and numeric cols
            selected_cols = [col.strip() for col in self.columns_line_edit.text().split(',') if col.strip()]
            cols = [col for col in selected_cols if col in self.available_columns]
            self.columns_line_edit.setText(",".join(cols))
            numeric_dict = yaml.safe_load(self.numeric_cols_text_edit.toPlainText())
            if numeric_dict:
                valid_numeric = {}
                for key, val in numeric_dict.items():
                    if "raw column" in val.keys() and val["raw column"] in self.available_columns:
                        valid_numeric[key] = val
                # Use FlowStyleListDumper to maintain inline lists
                self.numeric_cols_text_edit.setText(
                    yaml.dump(valid_numeric, Dumper=FlowStyleListDumper, default_flow_style=None),
                )

            self.plugin_status_label.setText("plugin processed successfully")
        # Disable plugin selection controls
        self.plugin_combo.setEnabled(False)
        self.process_button.setEnabled(False)
        self.rest_widget.setEnabled(True)

    def open_column_selector(self) -> None:
        """
        Open a dialog for selecting columns to use and pre-select items based on the text edit.
        """
        if self.available_columns:
            dialog = ColumnSelectorDialog(self.available_columns, self, exclusive=False)
            # Pre-select columns extracted from the current text edit.
            preselected = [col.strip() for col in self.columns_line_edit.text().split(',') if col.strip()]
            for col, checkbox in dialog.checkboxes.items():
                if col in preselected:
                    checkbox.setChecked(True)
            if dialog.exec():
                selected_columns = dialog.get_selected_columns()
                self.columns_line_edit.setText(','.join(selected_columns))
        else:
            QMessageBox.warning(self, "No Columns", "No available columns found after processing.")

    def open_numeric_column_selector(self) -> None:
        """
        Open a dialog for selecting numeric columns and binning parameters.
        Pre-select items based on either the YAML config or the current columns text.
        """
        selected_cols = [col.strip() for col in self.columns_line_edit.text().split(',') if col.strip()]
        if selected_cols:
            dialog = NumericColumnSelectorDialog(selected_cols, self)
            # Attempt to load YAML configuration; if invalid or empty, fallback to selected columns.
            try:
                numeric_config = yaml.safe_load(self.numeric_cols_text_edit.toPlainText()) or {}
            except yaml.YAMLError:
                numeric_config = {}
            if numeric_config and isinstance(numeric_config, dict) and numeric_config.keys():
                preselected = {}
                for k, v in numeric_config.items():
                    if "raw column" in v.keys() and v["raw column"] in selected_cols:
                        preselected[v["raw column"]] = k
                # Pre-check dialog checkboxes based on preselected names.
                for col, settings in dialog.column_settings.items():
                    if col in preselected:
                        settings['checkbox'].setChecked(True)
                        settings['label_edit'].setText(preselected[col])
            if dialog.exec():
                selected_numeric = dialog.get_selected_columns_with_bins()
                numeric_cols_dict = {}
                for col_name, (raw_col, bins, labels) in selected_numeric.items():
                    numeric_cols_dict[col_name] = {
                        'raw column': raw_col,
                        'bins': bins,
                        'labels': labels if labels else None,
                    }
                yaml_str = yaml.dump(numeric_cols_dict, Dumper=FlowStyleListDumper, default_flow_style=None)
                self.numeric_cols_text_edit.setText(yaml_str)
        else:
            QMessageBox.warning(self, "No Columns", "Select at least one column to process.")

    def get_data(self) -> Dict[str, Any]:
        """
        Retrieve all user selections from the dialog.

        Returns:
            Dict[str, Any]: A dictionary containing file metadata and user selections.
        """
        # If the raw column appears in the columns list, replace it with the key (col_name)
        selected_cols = [col.strip() for col in self.columns_line_edit.text().split(",") if col.strip()]
        numeric_cols = yaml.safe_load(self.numeric_cols_text_edit.toPlainText())
        for str_col, val in numeric_cols.items():
            raw_col = val["raw column"]
            selected_cols = [str_col if col == raw_col else col for col in selected_cols]
        return {
            "name": self.name_line_edit.text(),
            "description": self.description_line_edit.text(),
            "columns": selected_cols,
            "numeric_cols": numeric_cols,
            "plugin": self.plugin_combo.currentText().strip(),
        }


def get_csv_tsv_columns(file_name: str) -> List[str]:
    """
    Extract and return the header row (column names) from a CSV or TSV file.

    Args:
        file_name (str): The path to the CSV/TSV file.

    Returns:
        List[str]: A list of column names. Returns an empty list if reading fails.
    """
    delimiter = ',' if file_name.lower().endswith('.csv') else '\t'
    try:
        with open(file_name, newline='', encoding='utf-8') as f:
            reader = csv.reader(f, delimiter=delimiter)
            return next(reader)
    except csv.Error:
        return []


def open_excel_file_dialog(self: Any) -> None:
    """
    Open a file dialog to select an Excel file and show its options dialog.

    Emits a data source dictionary via self.add_data_source and updates UI elements via self._dataselectiongroupbox.
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
        'remove column name text': dialog.remove_column_text_line_edit.text(),
    }
    self.add_data_source.emit(data_source_dict)
    self.dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict['description'],
        data_source_dict['name'],
    )


def open_yaml_input_dialog(self: Any) -> None:
    """
    Open a dialog to paste YAML content and add it as a data source.

    The dialog loads previously saved YAML content (if available) and saves
    the current input upon acceptance.
    """
    settings = QSettings("MIDRC", "REACH")
    default_yaml = settings.value("yaml_input/default_yaml", "")

    dialog: QDialog = QDialog(self)
    dialog.setWindowTitle("Paste YAML Content")
    layout: QVBoxLayout = QVBoxLayout(dialog)
    label: QLabel = QLabel("Paste YAML content below:")
    layout.addWidget(label)

    text_edit: QTextEdit = QTextEdit()
    text_edit.setText(default_yaml)  # Load previously saved YAML input
    layout.addWidget(text_edit)

    button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec() == QDialog.Accepted:
        yaml_content: str = text_edit.toPlainText()
        try:
            data_source_dict: Dict[str, Any] = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            QMessageBox.critical(self, "Error", f"Failed to parse YAML content: {e}")
            return

        if not isinstance(data_source_dict, dict):
            QMessageBox.critical(self, "Error", "Parsed YAML content is not a valid dictionary.")
            return

        # Save the current YAML content as default
        settings.setValue("yaml_input/default_yaml", yaml_content)
        self.add_data_source.emit(data_source_dict)
        self.dataselectiongroupbox.add_file_to_comboboxes(
            data_source_dict.get("description", ""),
            data_source_dict.get("name", ""),
        )


def open_csv_tsv_file_dialog(self: Any) -> None:
    """
    Open a file dialog to select a CSV or TSV file and show its options dialog.

    This function reads the header row to obtain available columns, then opens the CSVTSVOptionsDialog.
    It then validates and collects user selections and emits a data source dictionary.
    """
    file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV/TSV File", "", "CSV/TSV Files (*.csv *.tsv)")
    if not file_name:
        return  # No file selected

    # Extract available columns from the file header
    available_columns: List[str] = get_csv_tsv_columns(file_name)

    dialog: CSVTSVOptionsDialog = CSVTSVOptionsDialog(self, file_name, available_columns=available_columns)
    if dialog.exec() != QDialog.Accepted:
        return  # User cancelled the dialog

    data = dialog.get_data()
    data_source_dict: Dict[str, Any] = {
        'name': data['name'],
        'description': data['description'],
        'data type': 'file',
        'filename': file_name,
        'columns': data['columns'],
        'numeric_cols': data['numeric_cols'],  # Caller can later parse this as YAML if desired
        'plugin': data['plugin'],
    }
    self.add_data_source.emit(data_source_dict)
    self.dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict.get('description', ''),
        data_source_dict.get('name', ''),
    )
