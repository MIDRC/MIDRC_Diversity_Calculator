from ExcelLayout import DataSource
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
from PySide6.QtGui import QColor
from typing import Optional, Any, List


class JSDTableModel(QAbstractTableModel):
    """
    A class representing a table model for JSD data.

    This class inherits from the QAbstractTableModel class and provides the necessary methods to interact with the
    JSD data in a table format. It handles the display of data, editing of data, and mapping of colors to specific
    areas of the table.

    Attributes:
        HEADER_MAPPING (List[str]): A list of header labels for the table columns.

    Methods:
        __init__(self, data_source_list=None, custom_age_ranges=None): Initializes the JSDTableModel with the given data
            sources and custom age ranges.
        rowCount(self, parent: QModelIndex = None) -> int: Returns the number of rows in the model.
        columnCount(self, parent: QModelIndex = QModelIndex()) -> int: Returns the number of columns in the model.
        headerData(self, section: int, orientation: int, role: int, *args, **kwargs) -> Any: Returns the header data for
            the specified section, orientation, and role.
        data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[Any]: Returns the data for the given
            index and role.
        setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool: Sets the data for the given
            index.
        flags(self, index: QModelIndex) -> Qt.ItemFlags: Returns the flags for the given index.
        add_color_mapping(self, color: str, mapping_area: Any): Adds a color mapping to the JSDTableModel.
        clear_color_mapping(self): Clears the color mapping in the JSDTableModel.

    """
    HEADER_MAPPING = [
        "Date",
        "JSD"
    ]

    def __init__(self, data_source_list=None, custom_age_ranges=None):
        """
        Initialize the JSDTableModel.

        This method initializes the JSDTableModel by setting up the input data, mapping, and raw data sources.

        Args:
            data_source_list (List[dict], optional): A list of data sources. Each data source is a dictionary with the
                                                     following keys:
                - 'name' (str): The name of the data source.
                - 'data type' (str): The type of the data source.
                - 'filename' (str): The filename of the data source.
            custom_age_ranges (Any, optional): Custom age ranges for the data sources.

        Returns:
            None
        """
        super().__init__()
        self.input_data = []
        self.column_infos = []  # This is a list of dicts containing column metadata
        self._color_mapping = {}
        self._color_cache = {}
        self.custom_age_ranges = custom_age_ranges

        if data_source_list is not None:
            self.data_sources = {}
            for data_source_dict in data_source_list:
                self.add_data_source(data_source_dict)

    def add_data_source(self, data_source_dict):
        self.data_sources[data_source_dict['name']] = DataSource(data_source_dict, self.custom_age_ranges)

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        This method returns the number of rows in the model based on the length of the input data.

        Args:
            parent (QModelIndex): The parent index. Row count should be the same regardless of column.

        Returns:
            int: The number of rows in the model.
        """
        # return len(self.input_data)
        return len(self.input_data[parent.column()])

    def columnCount(self, parent: QModelIndex = None) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index. Defaults to QModelIndex().

        Returns:
            int: The number of columns in the model.
        """
        # return len(self.input_data[parent.row()])
        return len(self.input_data)

    def headerData(self, section: int, orientation: int, role: int, *args, **kwargs) -> Any:
        """
        Returns the header data for the specified section, orientation, and role.

        Args:
            section (int): The section index.
            orientation (int): The orientation of the header (Qt.Horizontal or Qt.Vertical).
            role (int): The role of the header data.
            *args: Additional positional arguments.
            **kwargs: Additional keyword arguments.

        Returns:
            Any: The header data for the specified section, orientation, and role.
        """
        if role != Qt.DisplayRole:
            return None

        if orientation == Qt.Horizontal:
            return JSDTableModel.HEADER_MAPPING[section % 2]
        else:
            return str(section + 1)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Optional[Any]:
        """
        Returns the data for the given index and role.

        Args:
            index (QModelIndex): The index of the data.
            role (int): The role of the data. Defaults to Qt.DisplayRole.

        Returns:
            Optional[Any]: The data for the given index and role. If the role is Qt.DisplayRole or Qt.EditRole,
            it returns the corresponding data from the input_data list. If the role is Qt.BackgroundRole, it
            checks if the index is within any of the mapping areas defined in the _color_mapping dictionary.
            If it is, it returns the corresponding color from the _color_cache dictionary. If it is not within
            any mapping area, it returns the color white from the _color_cache dictionary. If the role is not
            any of the above, it returns None.
        """
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self.input_data[index.column()][index.row()]
        elif role == Qt.BackgroundRole:
            row = index.row()
            column = index.column()
            for color, rects in self._color_mapping.items():
                if rects is not None:
                    for rect in rects:
                        if rect.contains(column, row):
                            return self._color_cache.setdefault(color, QColor(color))
            return self._color_cache.setdefault(Qt.white, QColor(Qt.white))
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
            self.input_data[index.column()][index.row()] = float(value)
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

    def add_color_mapping(self, color: str, mapping_area: Any):
        """
        Add a color mapping to the JSDTableModel.

        Args:
            color (str): The color to be mapped.
            mapping_area (Any): The area to be mapped to the color.

        Returns:
            None
        """
        self._color_mapping.setdefault(color, [])
        self._color_mapping[color].append(mapping_area)

    def clear_color_mapping(self):
        """
        Clear the color mapping in the JSDTableModel.

        This method clears the color mapping, removing all color mappings from the
        JSDTableModel.

        Returns:
            None
        """
        self._color_mapping.clear()
        self._color_cache.clear()
