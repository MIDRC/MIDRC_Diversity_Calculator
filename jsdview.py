from PySide6.QtCore import QRect
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox,
                               QVBoxLayout, QComboBox, QLabel)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QVXYModelMapper

import jsdmodel

class JsdWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        #cw = QWidget()
        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout()
        self.jsd_groupbox = JsdGroupBox()
        self.main_layout.addWidget(self.jsd_groupbox)
        self.centralWidget().setLayout(self.main_layout)

class JsdGroupBox(QGroupBox):
    def __init__(self):
        super().__init__()

        self.setTitle('Data Selection')

        numDataItems = 2
        self.labels = []
        self.comboboxes = []
        grid = QGridLayout()

        for x in range(numDataItems):
            self.labels.append(QLabel(f'Data {x + 1}'))
            self.comboboxes.append(QComboBox())
            grid.addWidget(self.labels[-1], x, 0)
            grid.addWidget(self.comboboxes[-1], x, 1)

        self.setLayout(grid)