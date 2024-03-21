from PySide6.QtCore import QRect, Qt, QDateTime, QTime
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar, QDockWidget)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QVXYModelMapper, QDateTimeAxis, QValueAxis,
                              QPieSeries)

import jsdmodel
import jsdcontroller


class JsdWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up graphical layout
        self.dataselectiongroupbox = JsdDataSelectionGroupBox()

        self.table_view = QTableView()
        self.hbox = QHBoxLayout()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.createTableDockWidget())

        self.jsd_timeline_chart = QChart()
        self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        self.jsd_timeline_chart_view = QChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.createMainLayout())

        self.setMenuBar(self.createMenuBar())

        self.pie_chart_dock_widget = self.createPieChartDockWidget()
        self.pie_chart_views = {}
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        # Connect model and controller to this view
        self.jsd_model = jsdmodel.JSDTableModel()
        self.jsd_controller = jsdcontroller.JSDController(self, self.jsd_model)

        # Update category plots when the category is changed
        self.jsd_controller.categoryplotdatachanged.connect(self.updateCategoryPlots)
        # The plotdatachanged signal emits before we connect it, so call updateplot() once here
        self.updateCategoryPlots()

        # Update the file-based plots when the file selection is changed
        self.jsd_controller.fileselectionchanged.connect(self.updatePieChartDock)
        # The fileselectionchanged signal emits before we connect it, so call updateplot() once here
        self.updatePieChartDock()

        self.setWindowTitle('MIDRC JSD Tool')

    def createMainLayout(self):
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)

        main_layout = QVBoxLayout()
        main_layout.addWidget(self.dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        # table_hbox = QHBoxLayout()
        # table_hbox.addWidget(self.table_view)
        # table_hbox.addWidget(self.jsd_timeline_chart_view, stretch=1)
        # main_layout.addLayout(table_hbox)
        return main_layout

    def createMenuBar(self):
        menu_bar = QMenuBar()
        fileMenu = menu_bar.addMenu("File")
        settingsMenu = menu_bar.addMenu("Settings")
        chartanimationsetting = QAction("Chart Animations", self)
        chartanimationsetting.setCheckable(True)
        chartanimationsetting.setChecked(True)
        chartanimationsetting.toggled.connect(self.setAnimationOptions)
        settingsMenu.addAction(chartanimationsetting)
        return menu_bar

    def createTableDockWidget(self):
        table_dock_widget = QDockWidget()
        table_dock_widget.setWidget(self.table_view)
        table_dock_widget.setWindowTitle('JSD Table')
        return table_dock_widget

    def createPieChartDockWidget(self):
        pie_chart_dock_widget = QDockWidget()
        w = QWidget()
        pie_chart_dock_widget.setWidget(w)
        w.setLayout(self.hbox)
        return pie_chart_dock_widget

    def updatePieChartDock(self):
        # First, get rid of the old stuff just to be safe
        for c, pv in self.pie_chart_views.items():
            print('Deleting chart', pv.chart().title(), ':', c)
            self.pie_chart_dock_widget.layout().removeWidget(pv)
            pv.deleteLater()
        self.pie_chart_views = {}

        # For now, just use the first file
        cbox0 = self.dataselectiongroupbox.file_comboboxes[0]
        sheets = self.jsd_model.raw_data[cbox0.currentData()].sheets
        categories = list(sheets.keys())
        charts = {}
        for index, category in enumerate(categories):
            chart = QChart()
            self.pie_chart_views[category] = QChartView(chart)
            chart.setTitle(category)
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns
            series = QPieSeries(chart)
            for col in cols_to_use:
                print(f"{category} Pie chart - {col} : {df[col].iloc[-1]}")
                if df[col].iloc[-1] > 0:
                    slc = series.append(col, df[col].iloc[-1])
                    # slc.setLabelVisible()
            # series.setPieSize(0.4)
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            self.hbox.addWidget(self.pie_chart_views[category])

    def updateCategoryPlots(self):
        self.updatejsdtimelineplot()

    def updatejsdtimelineplot(self):
        # print("Updating table and plot")
        self.table_view.setModel(self.jsd_model)

        self.jsd_timeline_chart.removeAllSeries()
        series = QLineSeries()
        series.setName('{} vs {} {} JSD'.format(self.dataselectiongroupbox.file_comboboxes[0].currentData(),
                                                     self.dataselectiongroupbox.file_comboboxes[1].currentData(),
                                                     self.dataselectiongroupbox.category_combobox.currentText()))
        col = 0
        for i in range(self.jsd_model.rowCount()):
            if self.jsd_model.input_data[i][col] is not None:
                series.append(QDateTime(self.jsd_model.input_data[i][col], QTime()).toMSecsSinceEpoch(),
                              self.jsd_model.input_data[i][col + 1])
        # self.mapper = QVXYModelMapper(self)
        # self.mapper.setXColumn(0)
        # self.mapper.setYColumn(1)
        # self.mapper.setSeries(series)
        # self.mapper.setModel(self.jsd_model)
        self.jsd_timeline_chart.addSeries(series)


        self.jsd_model.add_mapping(series.pen().color().name(),
                                   QRect(0, 0, 2, self.jsd_model.rowCount()))
        # self.chart.createDefaultAxes()

        for axis in self.jsd_timeline_chart.axes():
            # series.detachAxis(axis)
            self.jsd_timeline_chart.removeAxis(axis)

        axisX = QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        self.jsd_timeline_chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText("JSD value")
        axisY.setRange(0,1)
        axisY.setTickCount(11)
        self.jsd_timeline_chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

    def setAnimationOptions(self, toggle):
        # print(f"Set Chart Animations To {toggle}")
        if toggle:
            self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        else:
            self.jsd_timeline_chart.setAnimationOptions(QChart.NoAnimation)

class JsdDataSelectionGroupBox(QGroupBox):
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

