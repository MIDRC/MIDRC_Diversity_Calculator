from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt
import ExcelLayout

class JSDTableModel(QAbstractTableModel):
    def __init__(self):
        super().__init__()
        self.input_data = []
        self.mapping = {}
        self.column_count = 0
        self.row_count = 0

        self.raw_data = {}
        self.raw_data['MIDRC'] = ExcelLayout.DataSource('MIDRC')
        self.raw_data['CDC'] = ExcelLayout.DataSource('CDC')
        self.raw_data['Census'] = ExcelLayout.DataSource('Census')

    def rowCount(self, parent=QModelIndex()):
        return len(self.input_data)

    def columnCount(self, parent = QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != Qt.DisplayRole:
            return None

        #if orientation == Qt.Horizontal:
        #    if section % 2 == 0:
        #        return "x"
        #    else:
        #        return "y"
        #else:
        #    return str(section + 1)
        return None

    def data(self, index, role=Qt.DisplayRole):
        #if role == Qt.DisplayRole:
        #    return self.input_data[index.row()][index.column()]
        #elif role == Qt.EditRole:
        #    return self.input_data[index.row()][index.column()]
        #elif role == Qt.BackgroundRole:
        #    for color, rect in self.mapping.items():
        #        if rect.contains(index.column(), index.row()):
        #            return QColor(color)
        #    # cell not mapped return white color
        #    return QColor(Qt.white)
        return None

    def setData(self, index, value, role=Qt.EditRole):
        #if index.isValid() and role == Qt.EditRole:
        #    self.input_data[index.row()][index.column()] = float(value)
        #    self.dataChanged.emit(index, index)
        #    return True
        return False

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable | Qt.ItemIsSelectable

    def add_mapping(self, color, area):
        self.mapping[color] = area

    def clear_mapping(self):
        self.mapping = {}

