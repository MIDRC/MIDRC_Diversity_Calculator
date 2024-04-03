from ExcelLayout import DataSource
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from typing import Optional, Any

class JSDTableModel(QAbstractTableModel):
    def __init__(self):
        """
        Initialize the JSDTableModel.

        This method initializes the JSDTableModel by setting up the input data, mapping, and raw data sources.
        """
        super().__init__()
        self.input_data = []
        self.color_mapping = {}
        self.color_cache = {}

        RAW_DATA_KEYS = ['MIDRC', 'CDC', 'Census']
        self.data_sources = {}
        for key in RAW_DATA_KEYS:
            self.data_sources[key] = DataSource(key)

    def rowCount(self, parent: QModelIndex = None) -> int:
        """
        Get the number of rows in the model.

        This method returns the number of rows in the model based on the length of the input data.

        Args:
            parent (QModelIndex): The parent index. Row count should be the same regardless of column.

        Returns:
            int: The number of rows in the model.
        """
        return len(self.input_data)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index. Defaults to QModelIndex().

        Returns:
            int: The number of columns in the model.
        """
        return len(self.input_data[parent.row()])

    HEADER_MAPPING = {
        0: "Date",
        1: "JSD"
    }

    def headerData(self, section: int, orientation: int, role: int) -> Optional[str]:
        """
        Returns the header data for the specified section, orientation, and role.
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return JSDTableModel.HEADER_MAPPING.get(section % 2, None)
        else:
            return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[Any]:
        """
        Returns the data for the given index and role.
        """
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.input_data[index.row()][index.column()]
        elif role == Qt.BackgroundRole:
            row = index.row()
            column = index.column()
            for color, rect in self.color_mapping.items():
                if rect.contains(column, row):
                    return self.color_cache.setdefault(color, QColor(color))
            return self.color_cache.setdefault(Qt.white, QColor(Qt.white))
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:
        """
        Set the data for the given index.

        Args:
            index (QModelIndex): The index of the data to be set.
            value (Any): The new value to be set.
            role (int): The role of the data. Defaults to Qt.EditRole.

        Returns:
            bool: True if the data was successfully set, False otherwise.
        """
        if index.isValid() and role == Qt.EditRole:
            self.input_data[index.row()][index.column()] = float(value)
            self.dataChanged.emit(index, index)
            return True
        return False

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:
        """
        Get the flags for the given index.

        Args:
            index (QModelIndex): The index of the item.

        Returns:
            int: The flags for the item.
        """
        if not index.isValid():
            return Qt.NoItemFlags
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def add_mapping(self, color: str, mapping_area: Any):
        """
        Add a color mapping to the JSDTableModel.

        Args:
            color (str): The color to be mapped.
            mapping_area (Any): The area to be mapped to the color.

        Returns:
            None
        """
        self.color_mapping[color] = mapping_area

    def clear_mapping(self):
        """
        Clear the color mapping in the JSDTableModel.

        This method clears the color mapping, removing all color mappings from the
        JSDTableModel.

        Returns:
            None
        """
        self.color_mapping.clear()
        self.color_cache.clear()

