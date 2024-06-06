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

from ExcelLayout import DataSource
from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal
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
    data_source_added = Signal()

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
        self._input_data = []
        self._column_infos = []  # This is a list of dicts containing column metadata
        self._color_mapping = {}
        self._color_cache = {}
        self.custom_age_ranges = custom_age_ranges
        self.max_row_count = 0

        if data_source_list is not None:
            self.data_sources = {}
            for data_source_dict in data_source_list:
                self.add_data_source(data_source_dict)

    def add_data_source(self, data_source_dict):
        """
        Add a data source to the JSDTableModel.

        This method adds a data source to the JSDTableModel by creating a new instance of the DataSource class and
        storing it in the data_sources dictionary. The data source is identified by its name, which is obtained from the
        'name' key in the data_source_dict parameter. The DataSource object is initialized with the data_source_dict
        and the custom_age_ranges, if provided.

        Args:
            data_source_dict (dict): A dictionary containing the information about the data source.
                                     It should have the following keys:
                - 'name' (str): The name of the data source.
                - 'data type' (str): The type of the data source.
                - 'filename' (str): The filename of the data source.

        Returns:
            None
        """
        self.data_sources[data_source_dict['name']] = DataSource(data_source_dict, self.custom_age_ranges)
        self.data_source_added.emit()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """
        Get the number of rows in the model.

        This method returns the number of rows in the model based on the length of the input data.
        If the parent index is invalid, this method returns the largest number of rows in a column.

        Args:
            parent (QModelIndex): The parent index.

        Returns:
            int: The number of rows in the model.
        """
        if parent.isValid():
            return len(self._input_data[parent.column()])
        else:
            return self.max_row_count

    def update_input_data(self, new_input_data, new_column_infos):
        """
        Update the input data and column information in the JSDTableModel.

        This method updates the input data and column information in the JSDTableModel. It clears the existing input
        data and column information, and then sets them to the new values provided as arguments. It also updates the
        maximum row count based on the new input data.

        Args:
            new_input_data (List[List[Any]]): The new input data to be set in the model. It should be a list of lists,
                                              where each inner list represents a column and contains the data for that
                                              column.
            new_column_infos (List[dict]): The new column information to be set in the model. It should be a list of
                                           dictionaries, where each dictionary represents the metadata for a column.

        Returns:
            None
        """
        self._input_data.clear()
        self._column_infos.clear()

        self._input_data = new_input_data
        self._column_infos = new_column_infos

        # Update the max row count
        self.max_row_count = 0
        for c in range(self.columnCount()):
            self.max_row_count = max(self.max_row_count, len(self._input_data[c]))

    def columnCount(self, parent: QModelIndex = None) -> int:
        """
        Returns the number of columns in the model.

        Args:
            parent (QModelIndex): The parent index. Defaults to QModelIndex().

        Returns:
            int: The number of columns in the model.
        """
        # return len(self.input_data[parent.row()])
        return len(self._input_data)

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
            try:
                return self._input_data[index.column()][index.row()]
            except IndexError:
                return None
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
            self._input_data[index.column()][index.row()] = float(value)
            self.dataChanged.emit(index, index)
            return True
        return False

    @property
    def input_data(self):
        """
        Returns the input data of the JSDTableModel.

        This method returns the input data of the JSDTableModel, which is a list of lists representing the data for each
        column in the model. Each inner list represents a column and contains the data for that column.

        Returns:
            List[List[Any]]: The input data of the JSDTableModel.
        """
        return self._input_data

    @property
    def column_infos(self):
        """
        Returns the column information of the JSDTableModel.

        This method returns the column information of the JSDTableModel, which is a list of dictionaries representing
        the metadata for each set of two columns in the model (one column for date, one column for the JSD value).
        Each dictionary contains the following keys:
        - 'index1' (int): The index of the first file used
        - 'file1' (str): The file name of the first file used.
        - 'index2' (int): The index of the second file used.
        - 'file2' (str): The file name of the second file used.

        Returns:
            List[dict]: The column information of the JSDTableModel.
        """
        return self._column_infos

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
