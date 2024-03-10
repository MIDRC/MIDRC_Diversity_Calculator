from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox,
                               QVBoxLayout, QComboBox, QLabel)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QVXYModelMapper

import jsdmodel
import jsdcontroller


class JsdWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up graphical layout
        self.groupbox = JsdGroupBox()

        self.chart = JsdChart()
        self.chart.createDefaultAxes()
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.groupbox)
        self.main_layout.addWidget(self.chart_view)
        self.centralWidget().setLayout(self.main_layout)

        # Connect model and controller to this view
        self.jsd_model = jsdmodel.JSDTableModel()
        self.jsd_controller = jsdcontroller.JSDController(self, self.jsd_model)

        self.setWindowTitle('MIDRC JSD Tool')


class JsdGroupBox(QGroupBox):
    def __init__(self):
        super().__init__()

        self.setTitle('Data Selection')

        numDataItems = 2
        self.labels = []
        self.file_comboboxes = []
        grid = QGridLayout()

        for x in range(numDataItems):
            self.labels.append(QLabel(f'Data File {x + 1}'))
            c = QComboBox()
            c.addItem('MIDRC Excel File', userData='MIDRC')
            c.addItem('CDC Excel File', userData='CDC')
            c.addItem('Census Excel File', userData='Census')
            c.setCurrentIndex(x)
            self.file_comboboxes.append(c)
            grid.addWidget(self.labels[-1], x, 0)
            grid.addWidget(self.file_comboboxes[-1], x, 1)

        grid.addWidget(QLabel('Category'), len(self.file_comboboxes), 0)
        self.category_combobox = QComboBox()
        grid.addWidget(self.category_combobox, len(self.file_comboboxes), 1)

        self.setLayout(grid)


class JsdChart (QChart):
    def __init__(self):
        super().__init__()