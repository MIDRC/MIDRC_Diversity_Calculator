from PySide6.QtCore import QRect, Qt, QDateTime, QTime, QPointF
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar, QDockWidget, QSplitter)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QVXYModelMapper, QDateTimeAxis, QValueAxis,
                              QPieSeries, QPolarChart, QAreaSeries)

import jsdmodel
import jsdcontroller


class JsdWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up graphical layout
        self.dataselectiongroupbox = JsdDataSelectionGroupBox()

        self.table_view = QTableView()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.createTableDockWidget())

        self.jsd_timeline_chart = QChart()
        self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        self.jsd_timeline_chart_view = QChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.createMainLayout())

        self.setMenuBar(self.createMenuBar())

        self.pie_chart_views = {}
        self.pie_chart_hbox = QHBoxLayout()  # If this is a local variable, only 1 plot shows up ¯\_(ツ)_/¯
        self.pie_chart_dock_widget = self.createPieChartDockWidget()
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        self.spider_chart = QPolarChart()
        self.area_chart = QChart()
        self.spider_chart_vbox = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget = self.createSpiderChartDockWidget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.spider_chart_dock_widget)

        # Connect model and controller to this view
        self.jsd_model = jsdmodel.JSDTableModel()
        self.jsd_controller = jsdcontroller.JSDController(self, self.jsd_model)

        # Update category plots when the category is changed
        self.jsd_controller.categoryplotdatachanged.connect(self.updateCategoryPlots)
        # The plotdatachanged signal emits before we connect it, so call receiver once here
        self.updateCategoryPlots()

        # Update the file-based plots when the file selection is changed
        self.jsd_controller.fileselectionchanged.connect(self.updateFileBasedCharts)
        # The fileselectionchanged signal emits before we connect it, so call receiver once here
        self.updateFileBasedCharts()

        self.setWindowTitle('MIDRC JSD Tool')

    def createMainLayout(self):
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        # The table used to not be a dock widget, the following section can probably be removed now
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
        self.table_view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_dock_widget.setWidget(self.table_view)
        table_dock_widget.setWindowTitle('JSD Table')
        return table_dock_widget

    def createPieChartDockWidget(self):
        pie_chart_dock_widget = QDockWidget()
        w = QWidget()
        pie_chart_dock_widget.setWidget(w)
        w.setLayout(self.pie_chart_hbox)
        return pie_chart_dock_widget

    def createSpiderChartDockWidget(self):
        spider_chart_dock_widget = QDockWidget()
        # w = QWidget()
        # spider_chart_dock_widget.setWidget(w)
        # w.setLayout(self.spider_chart_vbox)
        spider_chart_dock_widget.setWidget(self.spider_chart_vbox)
        area_chart_view = QChartView(self.area_chart)
        self.spider_chart_vbox.addWidget(area_chart_view)
        spider_chart_view = QChartView(self.spider_chart)
        self.spider_chart_vbox.addWidget(spider_chart_view)
        return spider_chart_dock_widget

    def updateFileBasedCharts(self):
        self.updatePieChartDock()
        self.updateSpiderChart()

    def get_file_sheets_from_combobox(self, index=0):
        cbox = self.dataselectiongroupbox.file_comboboxes[index]
        sheets = self.jsd_model.raw_data[cbox.currentData()].sheets
        return sheets

    def updatePieChartDock(self):
        # First, get rid of the old stuff just to be safe
        for c, pv in self.pie_chart_views.items():
            # print('Deleting chart', pv.chart().title(), ':', c)
            self.pie_chart_dock_widget.layout().removeWidget(pv)
            pv.deleteLater()
        self.pie_chart_views = {}
        charts = {}

        # For now, just use the file in the first combobox
        sheets = self.get_file_sheets_from_combobox(0)
        categories = list(sheets.keys())

        # Set the timepoint to the last timepoint in the series for now
        timepoint = -1

        for index, category in enumerate(categories):
            chart = QChart()
            self.pie_chart_views[category] = QChartView(chart)
            chart.setTitle(category)
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns
            series = QPieSeries(chart)
            for col in cols_to_use:
                # print(f"{category} Pie chart - {col} : {df[col].iloc[timepoint]}")
                if df[col].iloc[timepoint] > 0:
                    slc = series.append(col, df[col].iloc[timepoint])
                    # slc.setLabelVisible()
            # series.setPieSize(0.4)
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            self.pie_chart_hbox.addWidget(self.pie_chart_views[category], stretch=1)

    def updateSpiderChart(self):
        self.spider_chart.setTitle('Spider Chart')

    def updateAreaChart(self):
        # For now, just use the file in the first combobox
        file_cbox_index = 0
        sheets = self.get_file_sheets_from_combobox(file_cbox_index)
        category = self.dataselectiongroupbox.category_combobox.currentText()
        self.area_chart.removeAllSeries()
        self.area_chart.setTitle(f'{category} distribution over time')

        df = sheets[category].df
        cols_to_use = sheets[category].data_columns
        total_counts = df[cols_to_use].sum(axis=1)
        dates = [QDateTime(jsdcontroller.numpy_datetime64_to_qdate(date), QTime()) for date in df.date.values]
        # lower_series = [QPointF(dates[j], 0.0) for j in range(len(dates))]  # This is an option instead of None
        lower_series = None
        for index, col in enumerate(cols_to_use):
            if df[col].iloc[-1] == 0:  # Cumulative sum is zero, so skip category
                # print(f"Skipping column '{col}' for category '{category}' and file "
                #       f"'{self.dataselectiongroupbox.file_comboboxes[file_cbox_index].currentData()}'")
                continue

            upper_counts = df[cols_to_use[:index+1]].sum(axis=1)
            points = [QPointF(dates[j].toMSecsSinceEpoch(), 100.0 * upper_counts[j] / total_counts[j]) for j in range(len(dates))]

            if len(dates) == 1:  # Only a single date in this file
                points.append(QPointF(dates[0].toMSecsSinceEpoch() + 1, 100.0 * upper_counts[0] / total_counts[0]))

            upper_series = QLineSeries(self.area_chart)
            upper_series.append(points)

            area = QAreaSeries(upper_series, lower_series)
            area.setName(col)
            self.area_chart.addSeries(area)
            lower_series = upper_series

        for axis in self.area_chart.axes():
            self.area_chart.removeAxis(axis)
        self.area_chart.createDefaultAxes()  # We have to use createDefaultAxes() or each line uses its own set of axes

        self.area_chart.removeAxis(self.area_chart.axisX())
        axisX = QDateTimeAxis()
        # axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        # We assume that the dates are sorted, so don't need the following
        # dates_s = sorted(dates)
        # axisX.setRange(dates_s[0], dates_s[-1])
        axisX.setRange(dates[0], dates[-1] if len(dates) > 1 else dates[0].addMSecs(1))
        self.area_chart.addAxis(axisX, Qt.AlignBottom)

        axisY = self.area_chart.axisY()
        axisY.setTitleText("Percent of total")
        axisY.setLabelFormat('%.0f%')
        axisY.setRange(0, 100)
        # axisY.setTickCount(11)

    def updateCategoryPlots(self):
        self.updatejsdtimelineplot()
        self.updateAreaChart()

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

