from typing import List, Tuple
from jsdmodel import JSDTableModel
from jsdcontroller import JSDController
from PySide6.QtCore import QRect, Qt, QDateTime, QTime, QPointF
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox, QMenu,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar, QDockWidget, QSplitter,
                               QLayout)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QVXYModelMapper, QDateTimeAxis, QValueAxis,
                              QPieSeries, QPolarChart, QAreaSeries, QCategoryAxis)

import jsdmodel
import jsdcontroller


class JsdWindow(QMainWindow):
    def __init__(self):
        super(JsdWindow, self).__init__()

        # Set up graphical layout
        self.dataselectiongroupbox = JsdDataSelectionGroupBox()

        self.table_view = QTableView()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.createTableDockWidget(self.table_view, 'JSD Table - MIDRC Diversity Calculator'))

        self.jsd_timeline_chart = JsdChart()
        self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        self.jsd_timeline_chart_view = QChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.createMainLayout())

        self.setMenuBar(self.createMenuBar())

        self.pie_chart_views = {}
        self.pie_chart_hbox = QHBoxLayout()
        self.pie_chart_dock_widget = self.createPieChartDockWidget(self.pie_chart_hbox, 'Pie Charts - MIDRC Diversity Calculator')
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        self.spider_chart = QPolarChart()
        self.area_chart = QChart()
        self.spider_chart_vbox = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget = self.createSpiderChartDockWidget()
        self.addDockWidget(Qt.RightDockWidgetArea, self.spider_chart_dock_widget)

        # Connect model and controller to this view
        self.jsd_model = JSDTableModel()
        self.jsd_controller = JSDController(self, self.jsd_model)

        # Update category plots when the category is changed
        self.jsd_controller.categoryplotdatachanged.connect(self.updateCategoryPlots)
        self.jsd_controller.categoryplotdatachanged.emit()
        # Update the file-based plots when the file selection is changed
        self.jsd_controller.fileselectionchanged.connect(self.updateFileBasedCharts)
        self.jsd_controller.fileselectionchanged.emit()

        self.setWindowTitle('MIDRC Diversity Calculator')

    def createMainLayout(self) -> QVBoxLayout:
        """
        Create the main layout for the application.
        This layout includes the data selection group box and the JSD timeline chart view.
        """
        main_layout = QVBoxLayout()
        main_layout.addWidget(self.dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        return main_layout

    def createMenuBar(self) -> QMenuBar:
        """
        Create the menu bar.
        """
        menu_bar: QMenuBar = QMenuBar()

        # Add the 'File' menu
        fileMenu: QMenu = menu_bar.addMenu("File")

        # Add the 'Settings' menu
        settingsMenu: QMenu = menu_bar.addMenu("Settings")

        # Create the 'Chart Animations' action
        chartanimationsetting: QAction = QAction("Chart Animations", self)
        chartanimationsetting.setCheckable(True)
        chartanimationsetting.setChecked(True)
        chartanimationsetting.toggled.connect(lambda checked: self.setAnimationOptions(checked))

        # Add the 'Chart Animations' action to the 'Settings' menu
        settingsMenu.addAction(chartanimationsetting)

        # Return the menu bar
        return menu_bar

    def createTableDockWidget(self, table_view: QTableView, title: str) -> QDockWidget:
        """
        Creates a dock widget with a table view.

        Args:
            table_view (QTableView): The table view to be displayed in the dock widget.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        table_dock_widget = QDockWidget()
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table_view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_dock_widget.setWidget(table_view)
        table_dock_widget.setWindowTitle(title)
        return table_dock_widget

    def createPieChartDockWidget(self, layout: QLayout, title: str) -> QDockWidget:
        """
        Creates a dock widget with a given widget.

        Args:
            layout (QLayout): The layout to be displayed in the dock widget.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        dock_widget = QDockWidget()
        w = QWidget()
        w.setLayout(layout)
        dock_widget.setWidget(w)
        if isinstance(title, str):
            dock_widget.setWindowTitle(title)
        else:
            raise TypeError("The 'title' argument must be a string.")
        return dock_widget

    def createSpiderChartDockWidget(self) -> QDockWidget:
        spider_chart_dock_widget = QDockWidget()
        spider_chart_dock_widget.setWidget(self.spider_chart_vbox)
        area_chart_view = QChartView(self.area_chart)
        self.spider_chart_vbox.addWidget(area_chart_view)
        spider_chart_view = QChartView(self.spider_chart)
        self.spider_chart_vbox.addWidget(spider_chart_view)
        spider_chart_dock_widget.setWindowTitle('Diversity Charts - MIDRC Diversity Calculator')
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
                if df[col].iloc[timepoint] > 0:
                    slc = series.append(col, df[col].iloc[timepoint])
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            self.pie_chart_hbox.addWidget(self.pie_chart_views[category], stretch=1)

    def updateSpiderChart(self, date=None):
        spider_plot_values = self.jsd_controller.get_spider_plot_values(date)
        self.spider_chart.removeAllSeries()
        for axis in self.spider_chart.axes():
            self.spider_chart.removeAxis(axis)

        self.spider_chart.setTitle(f'{self.dataselectiongroupbox.file_comboboxes[0].currentData()} vs '
                                   f'{self.dataselectiongroupbox.file_comboboxes[1].currentData()} - ')
        self.spider_chart.setTitle('JSD per category')

        labels = list(spider_plot_values.keys())
        series = QLineSeries()
        angular_axis = QCategoryAxis()
        angular_axis.setRange(0, 360)
        angular_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
        for index, label in enumerate(labels):
            angle = 360 * index / len(labels)
            series.append(angle, spider_plot_values[label])
            angular_axis.append(label, angle)
        series.append(360, spider_plot_values[labels[0]])
        series.setName(f'{self.dataselectiongroupbox.file_comboboxes[0].currentData()} vs '
                       f'{self.dataselectiongroupbox.file_comboboxes[1].currentData()}')

        self.spider_chart.addSeries(series)
        self.spider_chart.addAxis(angular_axis, QPolarChart.PolarOrientationAngular)
        series.attachAxis(angular_axis)

        radial_axis = QValueAxis()
        radial_axis.setRange(0, max(map(QPointF.y, series.points())))
        radial_axis.setLabelFormat('%.2f')
        self.spider_chart.addAxis(radial_axis, QPolarChart.PolarOrientationRadial)
        series.attachAxis(radial_axis)

    def updateAreaChart(self):
        file_cbox_index = 0
        sheets = self.get_file_sheets_from_combobox(file_cbox_index)
        category = self.dataselectiongroupbox.category_combobox.currentText()
        self.area_chart.removeAllSeries()
        self.area_chart.setTitle(f'{self.dataselectiongroupbox.file_comboboxes[file_cbox_index].currentData()} '
                                 f'{category} distribution over time')

        df = sheets[category].df
        cols_to_use = sheets[category].data_columns
        total_counts = df[cols_to_use].sum(axis=1)
        dates = [QDateTime(jsdcontroller.numpy_datetime64_to_qdate(date), QTime()) for date in df.date.values]
        lower_series = None
        for index, col in enumerate(cols_to_use):
            if df[col].iloc[-1] == 0:
                continue

            upper_counts = df[cols_to_use[:index+1]].sum(axis=1)
            points = [QPointF(dates[j].toMSecsSinceEpoch(), 100.0 * upper_counts[j] / total_counts[j]) for j in range(len(dates))]

            if len(dates) == 1:
                points.append(QPointF(dates[0].toMSecsSinceEpoch() + 1, 100.0 * upper_counts[0] / total_counts[0]))

            upper_series = QLineSeries(self.area_chart)
            upper_series.append(points)

            area = QAreaSeries(upper_series, lower_series)
            area.setName(col)
            self.area_chart.addSeries(area)
            lower_series = upper_series

        for axis in self.area_chart.axes():
            self.area_chart.removeAxis(axis)
        self.area_chart.createDefaultAxes()

        self.area_chart.removeAxis(self.area_chart.axisX())
        axisX = QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        axisX.setRange(dates[0], dates[-1] if len(dates) > 1 else dates[0].addMSecs(1))
        self.area_chart.addAxis(axisX, Qt.AlignBottom)

        axisY = self.area_chart.axisY()
        axisY.setTitleText("Percent of total")
        axisY.setLabelFormat('%.0f%')
        axisY.setRange(0, 100)

    def updateCategoryPlots(self):
        self.updatejsdtimelineplot()
        self.updateAreaChart()

    def updatejsdtimelineplot(self):
        self.table_view.setModel(self.jsd_model)
        new_chart = QChart()
        new_chart.removeAllSeries()
        series = QLineSeries()
        series.setName('{} vs {} {} JSD'.format(self.dataselectiongroupbox.file_comboboxes[0].currentData(),
                                                self.dataselectiongroupbox.file_comboboxes[1].currentData(),
                                                self.dataselectiongroupbox.category_combobox.currentText()))
        col = 0
        for i in range(self.jsd_model.rowCount()):
            if self.jsd_model.input_data[i][col] is not None:
                series.append(QDateTime(self.jsd_model.input_data[i][col], QTime()).toMSecsSinceEpoch(),
                              self.jsd_model.input_data[i][col + 1])
        new_chart.addSeries(series)
        self.jsd_model.add_mapping(series.pen().color().name(),
                                   QRect(0, 0, 2, self.jsd_model.rowCount()))

        for axis in new_chart.axes():
            new_chart.removeAxis(axis)

        axisX = QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        new_chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = QValueAxis()
        axisY.setTitleText("JSD value")
        axisY.setRange(0, 1)
        axisY.setTickCount(11)
        new_chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

        self.jsd_timeline_chart = new_chart
        self.jsd_timeline_chart_view.setChart(new_chart)

    def setAnimationOptions(self, toggle):
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

