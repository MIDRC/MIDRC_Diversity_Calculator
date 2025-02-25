import yaml
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QDialogButtonBox, QFileDialog,
    QMessageBox, QLineEdit, QFormLayout
)
from PySide6.QtCore import QFileInfo

class FileOptionsDialog(QDialog):
    """
    A dialog window for displaying and editing Excel file options.
    """
    def __init__(self, parent, file_name: str):
        """
        Initialize the FileOptionsDialog for an Excel file.
        """
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        self.name_line_edit = QLineEdit()
        self.description_line_edit = QLineEdit()
        self.remove_column_text_line_edit = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Name (Plot Titles)", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu)", self.description_line_edit)
        form_layout.addRow("Remove Column Text", self.remove_column_text_line_edit)
        self.layout().addLayout(form_layout)

        fi = QFileInfo(file_name)
        self.setWindowTitle(fi.fileName())
        self.name_line_edit.setText(fi.baseName())
        self.description_line_edit.setText(fi.baseName())

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        self.layout().addWidget(button_box)

        self.resize(600, -1)

class CSVTSVOptionsDialog(QDialog):
    """
    A dialog window for displaying and editing CSV/TSV file options.
    """
    def __init__(self, parent, file_name: str):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())

        # Create input fields for additional CSV/TSV metadata
        self.name_line_edit = QLineEdit()
        self.description_line_edit = QLineEdit()
        self.columns_text_edit = QTextEdit()
        self.numeric_cols_text_edit = QTextEdit()
        self.plugin_line_edit = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Name (Plot Titles):", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu):", self.description_line_edit)
        form_layout.addRow("Columns (comma-separated or YAML list):", self.columns_text_edit)
        form_layout.addRow("Numeric Column Options (YAML):", self.numeric_cols_text_edit)
        form_layout.addRow("Plugin:", self.plugin_line_edit)
        self.layout().addLayout(form_layout)

        # Set default values based on the filename
        fi = QFileInfo(file_name)
        self.setWindowTitle(fi.fileName())
        default_base = fi.baseName()
        self.name_line_edit.setText(default_base)
        self.description_line_edit.setText(default_base)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.layout().addWidget(button_box)

        self.resize(600, -1)

def open_excel_file_dialog(self):
    """
    Open a file dialog to select an Excel file and then show its options dialog.
    """
    file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xls *.xlsx)")
    if not file_name:
        return

    file_options_dialog = FileOptionsDialog(self, file_name)
    if file_options_dialog.exec() != QDialog.Accepted:
        return

    data_source_dict = {
        'name': file_options_dialog.name_line_edit.text(),
        'description': file_options_dialog.description_line_edit.text(),
        'data type': 'file',
        'filename': file_name,
        'remove column name text': file_options_dialog.remove_column_text_line_edit.text()
    }
    self.add_data_source.emit(data_source_dict)
    self._dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict['description'],
        data_source_dict['name']
    )

def open_yaml_input_dialog(self):
    """
    Open a dialog to paste YAML content and add it as a data source.
    """
    dialog = QDialog(self)
    dialog.setWindowTitle("Paste YAML Content")
    layout = QVBoxLayout(dialog)
    label = QLabel("Paste YAML content below:")
    layout.addWidget(label)
    text_edit = QTextEdit()
    layout.addWidget(text_edit)
    button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
    layout.addWidget(button_box)
    button_box.accepted.connect(dialog.accept)
    button_box.rejected.connect(dialog.reject)

    if dialog.exec() == QDialog.Accepted:
        yaml_content = text_edit.toPlainText()
        try:
            data_source_dict = yaml.safe_load(yaml_content)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse YAML content: {e}")
            return
        self.add_data_source.emit(data_source_dict)
        self._dataselectiongroupbox.add_file_to_comboboxes(
            data_source_dict.get('description', ''),
            data_source_dict.get('name', '')
        )

def open_csv_tsv_file_dialog(self):
    """
    Open a file dialog to select a CSV or TSV file and then show its options dialog.
    """
    file_name, _ = QFileDialog.getOpenFileName(self, "Open CSV/TSV File", "", "CSV/TSV Files (*.csv *.tsv)")
    if not file_name:
        return

    file_options_dialog = CSVTSVOptionsDialog(self, file_name)
    if file_options_dialog.exec() != QDialog.Accepted:
        return

    # Parse numeric column options from YAML input
    try:
        numeric_cols = yaml.safe_load(file_options_dialog.numeric_cols_text_edit.toPlainText())
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to parse Numeric Column Options YAML: {e}")
        return

    # Process the columns input; support both comma-separated and YAML list formats
    columns_input = file_options_dialog.columns_text_edit.toPlainText().strip()
    if columns_input.startswith('['):
        try:
            columns = yaml.safe_load(columns_input)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to parse Columns YAML: {e}")
            return
    else:
        columns = [col.strip() for col in columns_input.split(',') if col.strip()]

    data_source_dict = {
        'name': file_options_dialog.name_line_edit.text(),
        'description': file_options_dialog.description_line_edit.text(),
        'data type': 'file',
        'filename': file_name,
        'columns': columns,
        'numeric_cols': numeric_cols,
        'plugin': file_options_dialog.plugin_line_edit.text(),
    }
    print('Data source dict:')
    print(data_source_dict)
    self.add_data_source.emit(data_source_dict)
    self._dataselectiongroupbox.add_file_to_comboboxes(
        data_source_dict.get('description', ''),
        data_source_dict.get('name', '')
    )
