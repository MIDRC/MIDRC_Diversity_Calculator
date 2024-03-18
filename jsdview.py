from PySide6.QtCore import QRect, Qt, QDateTime, QTime
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar)
from PySide6.QtCharts import QChart, QChartView, QLineSeries, QVXYModelMapper, QDateTimeAxis, QValueAxis

import jsdmodel
import jsdcontroller


class JsdWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up graphical layout
        self.groupbox = JsdGroupBox()

        self.table_hbox = QHBoxLayout()
        self.table_view = QTableView()
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        self.chart = QChart()
        self.chart.setAnimationOptions(QChart.AllAnimations)
        self.chart_view = QChartView(self.chart)
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        self.chart_view.setMinimumSize(800, 600)

        self.setCentralWidget(QWidget())
        self.main_layout = QVBoxLayout()
        self.main_layout.addWidget(self.groupbox)
        #self.main_layout.addWidget(self.chart_view)
        self.table_hbox.addWidget(self.table_view)
        self.table_hbox.addWidget(self.chart_view, stretch=1)
        self.main_layout.addLayout(self.table_hbox)
        self.centralWidget().setLayout(self.main_layout)

        self.menu_bar = QMenuBar()
        fileMenu = self.menu_bar.addMenu("File")
        settingsMenu = self.menu_bar.addMenu("Settings")
        self.chartanimationsetting = QAction("Chart Animations", self)
        self.chartanimationsetting.setCheckable(True)
        self.chartanimationsetting.setChecked(True)
        self.chartanimationsetting.toggled.connect(self.setAnimationOptions)
        settingsMenu.addAction(self.chartanimationsetting)
        self.setMenuBar(self.menu_bar)

        # Connect model and controller to this view
        self.jsd_model = jsdmodel.JSDTableModel()
        self.jsd_controller = jsdcontroller.JSDController(self, self.jsd_model)
        self.jsd_controller.plotdatachanged.connect(self.updateplot)
        # The plotdatachanged signal emits before we connect it, so call updateplot() once here
        self.updateplot()


        self.setWindowTitle('MIDRC JSD Tool')

    def updateplot(self):
        # print("Updating table and plot")
        self.table_view.setModel(self.jsd_model)

        self.chart.removeAllSeries()
        self.series = QLineSeries()
        self.series.setName('{} vs {} {} JSD'.format(self.groupbox.file_comboboxes[0].currentData(),
                                                     self.groupbox.file_comboboxes[1].currentData(),
                                                     self.groupbox.category_combobox.currentText()))
        col = 0
        for i in range(self.jsd_model.rowCount()):
            if self.jsd_model.input_data[i][col] is not None:
                self.series.append(QDateTime(self.jsd_model.input_data[i][col], QTime()).toMSecsSinceEpoch(),
                                   self.jsd_model.input_data[i][col + 1])
        # self.mapper = QVXYModelMapper(self)
        # self.mapper.setXColumn(0)
        # self.mapper.setYColumn(1)
        # self.mapper.setSeries(self.series)
        # self.mapper.setModel(self.jsd_model)
        self.chart.addSeries(self.series)


        self.jsd_model.add_mapping(self.series.pen().color().name(),
                               QRect(0, 0, 2, self.jsd_model.rowCount()))
        # self.chart.createDefaultAxes()

        for axis in self.chart.axes():
            # self.series.detachAxis(axis)
            self.chart.removeAxis(axis)

        axisX = QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        self.chart.addAxis(axisX, Qt.AlignBottom)
        self.series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText("JSD value")
        axisY.setRange(0,1)
        axisY.setTickCount(11)
        self.chart.addAxis(axisY, Qt.AlignLeft)
        self.series.attachAxis(axisY)

    def setAnimationOptions(self, toggle):
        print(f"Set Chart Animations To {toggle}")
        if toggle:
            self.chart.setAnimationOptions(QChart.AllAnimations)
        else:
            self.chart.setAnimationOptions(QChart.NoAnimation)

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

