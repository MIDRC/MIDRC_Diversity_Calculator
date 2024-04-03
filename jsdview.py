from typing import List, Tuple
from PySide6.QtCore import QRect, Qt, QDateTime, QTime, QPointF, Signal
from PySide6.QtGui import QColor, QPainter, QAction
from PySide6.QtWidgets import (QGridLayout, QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox, QMenu,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar, QDockWidget, QSplitter,
                               QLayout)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QVXYModelMapper, QDateTimeAxis, QValueAxis,
                              QPieSeries, QPolarChart, QAreaSeries, QCategoryAxis)
from datetimetools import numpy_datetime64_to_qdate, convert_date_to_milliseconds
from jsdmodel import JSDTableModel


class JsdDataSelectionGroupBox:
    pass


class JsdWindow(QMainWindow):
    WINDOW_TITLE = 'MIDRC Diversity Calculator'

    def __init__(self):
        """
        Initialize the JsdWindow.

        This method sets up the main window and all of the component widgets.
        """
        super().__init__()

        # Set up graphical layout
        self._dataselectiongroupbox = JsdDataSelectionGroupBox()

        self.table_view = QTableView()
        self.addDockWidget(Qt.LeftDockWidgetArea, self.createTableDockWidget(self.table_view, 'JSD Table - ' + JsdWindow.WINDOW_TITLE))

        self.jsd_timeline_chart = JsdChart()
        self.jsd_timeline_chart_view = QChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.createMainLayout())

        self.setMenuBar(self.createMenuBar())

        self.pie_chart_views = {}
        self.pie_chart_hbox = QHBoxLayout()
        self.pie_chart_dock_widget = self.createPieChartDockWidget(self.pie_chart_hbox, 'Pie Charts - ' + JsdWindow.WINDOW_TITLE)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        self.spider_chart = QPolarChart()
        self.area_chart = QChart()
        self.spider_chart_vbox = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget = self.createSpiderChartDockWidget(self.spider_chart_vbox, 'Diversity Charts - ' + JsdWindow.WINDOW_TITLE)
        self.addDockWidget(Qt.RightDockWidgetArea, self.spider_chart_dock_widget)

        self.setWindowTitle(JsdWindow.WINDOW_TITLE)


    def createMainLayout(self) -> QVBoxLayout:
        """
        Create the main layout for the application.
        This layout includes the data selection group box and the JSD timeline chart view.
        """
        main_layout = QVBoxLayout()
        main_layout.addWidget(self._dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        return main_layout

    def get_dataselectiongroupbox(self) -> JsdDataSelectionGroupBox:
        # Get the Data Selection GroupBox object.
        return self._dataselectiongroupbox

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
        assert isinstance(title, str), "The 'title' argument must be a string."
        dock_widget.setWindowTitle(title)
        return dock_widget

    def createSpiderChartDockWidget(self, spider_chart_vbox: QSplitter, title: str) -> QDockWidget:
        """
        Create a dock widget with an area chart and a spider chart.

        Args:
            spider_chart_vbox: The QSplitter containing the spider chart.
            title: The title of the dock widget.

        Returns:
            The created QDockWidget.
        """
        assert isinstance(title, str), "The 'title' argument must be a string."
        spider_chart_dock_widget = QDockWidget()
        spider_chart_dock_widget.setWidget(spider_chart_vbox)
        self.addAreaChartView()
        self.addSpiderChartView()
        spider_chart_dock_widget.setWindowTitle(title)
        return spider_chart_dock_widget

    def addAreaChartView(self):
        """
        Add an area chart view to the spider chart dock widget.

        Returns:
            The created area_chart_view.

        Raises:
            None
        """
        area_chart_view = QChartView(self.area_chart)
        self.spider_chart_vbox.addWidget(area_chart_view)
        return area_chart_view

    def addSpiderChartView(self):
        """
        Add a spider chart view to the spider chart vbox layout.
    
        Returns:
            The spider chart view object that was added.
        """
        spider_chart_view = QChartView(self.spider_chart)
        self.spider_chart_vbox.addWidget(spider_chart_view)
        return spider_chart_view

    def updatePieChartDock(self, sheets):
        """
        Update the pie chart dock with new data.
        """
        # First, get rid of the old stuff just to be safe
        for c, pv in self.pie_chart_views.items():
            self.pie_chart_dock_widget.layout().removeWidget(pv)
            pv.deleteLater()
        self.pie_chart_views = {}
        charts = {}

        # For now, just use the file in the first combobox
        categories = list(sheets)

        # Set the timepoint to the last timepoint in the series for now
        timepoint = -1

        new_pie_chart_views = {}
        for category in categories:
            chart = QChart()
            new_pie_chart_views[category] = QChartView(chart)
            chart.setTitle(category)
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns
            series = QPieSeries(chart)
            for col in cols_to_use:
                if df[col].iloc[timepoint] > 0:
                    slc = series.append(col, df[col].iloc[timepoint])
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            self.pie_chart_hbox.addWidget(new_pie_chart_views[category], stretch=1)
        self.pie_chart_views = new_pie_chart_views

    def updateSpiderChart(self, spider_plot_values):
        """
        Update the spider chart with new data.
        """
        file1_data = self._dataselectiongroupbox.file_comboboxes[0].currentData()
        file2_data = self._dataselectiongroupbox.file_comboboxes[1].currentData()

        self.spider_chart.removeAllSeries()
        for axis in self.spider_chart.axes():
            self.spider_chart.removeAxis(axis)

        self.updateSpiderChartTitle(file1_data, file2_data)

        labels = spider_plot_values.keys()
        series = QLineSeries()
        angular_axis = QCategoryAxis()
        angular_axis.setRange(0, 360)
        angular_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)

        step_size = 360 / len(labels)
        for index, label in enumerate(labels):
            angle = step_size * index
            series.append(angle, spider_plot_values[label])
            angular_axis.append(label, angle)

        series.append(360, series.points()[0].y())
        series.setName(f'{file1_data} vs {file2_data}')

        self.spider_chart.addSeries(series)
        self.spider_chart.addAxis(angular_axis, QPolarChart.PolarOrientationAngular)
        series.attachAxis(angular_axis)

        radial_axis = QValueAxis()
        radial_axis.setRange(0, max(point.y() for point in series.points()))
        radial_axis.setLabelFormat('%.2f')
        self.spider_chart.addAxis(radial_axis, QPolarChart.PolarOrientationRadial)
        series.attachAxis(radial_axis)

        return True

    def updateSpiderChartTitle(self, file1_data: str = 'File 1', file2_data: str = 'File 2'):
        """
        Set the title of the spider chart.

        Args:
            file1_data (str): The data from file 1.
            file2_data (str): The data from file 2.
        """
        title = f"Comparison of {file1_data} and {file2_data} - JSD per category"
        self.spider_chart.setTitle(title)

    def updateAreaChart(self, sheets, filename):
        """
        Update the area chart with new data.
        """
        category = self._dataselectiongroupbox.category_combobox.currentText()

        self.area_chart.removeAllSeries()
        self.area_chart.setTitle(f'{filename} {category} distribution over time')

        df = sheets[category].df
        cols_to_use = sheets[category].data_columns
        total_counts = df[cols_to_use].sum(axis=1)
        upper_counts = df[cols_to_use].cumsum(axis=1)
        upper_counts = upper_counts.apply(lambda x: 100.0 * x / total_counts)
        dates = [QDateTime(numpy_datetime64_to_qdate(date), QTime()) for date in df.date.values]
        lower_series = None
        for index, col in enumerate(cols_to_use):
            if df[col].iloc[-1] == 0:
                continue

            points = [QPointF(dates[j].toMSecsSinceEpoch(), upper_counts.iloc[j][col]) for j in range(len(dates))]
            if len(dates) == 1:
                points.append(QPointF(dates[0].toMSecsSinceEpoch() + 1, upper_counts.iloc[0][col]))

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
        self.area_chart.setProperty("current_data", filename)

        return True

    def updateJsdTimelinePlot(self, jsd_model):
        self.table_view.setModel(jsd_model)
        self.jsd_timeline_chart.removeAllSeries()
        jsd_model.clear_mapping()
        series = QLineSeries()
        series.setName(f"{self._dataselectiongroupbox.file_comboboxes[0].currentData()} vs "
                       f"{self._dataselectiongroupbox.file_comboboxes[1].currentData()} "
                       f"{self._dataselectiongroupbox.category_combobox.currentText()} JSD")
        col = 0
        row_count = jsd_model.rowCount()
        for i in range(row_count):
            timepoint = jsd_model.input_data[i][col]
            if timepoint is not None:
                series.append(convert_date_to_milliseconds(timepoint), jsd_model.input_data[i][col + 1])
        self.jsd_timeline_chart.addSeries(series)
        jsd_model.add_mapping(series.pen().color().name(), QRect(0, 0, 2, row_count))

        self.jsd_timeline_chart.removeAxis(self.jsd_timeline_chart.axisX())
        axisX = QDateTimeAxis()
        axisX.setTickCount(10)
        axisX.setFormat("MMM yyyy")
        axisX.setTitleText("Date")
        self.jsd_timeline_chart.addAxis(axisX, Qt.AlignBottom)
        series.attachAxis(axisX)

        axisY = self.jsd_timeline_chart.axisY()
        if axisY is None:
            axisY = QValueAxis()
            axisY.setTitleText("JSD value")
            axisY.setRange(0, 1)
            axisY.setTickCount(11)
            self.jsd_timeline_chart.addAxis(axisY, Qt.AlignLeft)
        series.attachAxis(axisY)

        self.jsd_timeline_chart_view.setChart(self.jsd_timeline_chart)

        return True

    def setAnimationOptions(self, enable_animations: bool):
        """
        Set the animation options for the JSD timeline chart.

        Args:
            enable_animations (bool): If True, enable all animations. If False, disable all animations.
        """
        if enable_animations:
            self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        else:
            self.jsd_timeline_chart.setAnimationOptions(QChart.NoAnimation)
        return True


class JsdDataSelectionGroupBox(QGroupBox):
    def __init__(self):
        """
        Initialize the JsdDataSelectionGroupBox.

        This method sets up the data selection group box by creating labels and combo boxes for data files and a category combo box.
        """
        super().__init__()

        self.setTitle('Data Selection')

        FILE_TYPES = {
            'MIDRC': 'MIDRC Excel File',
            'CDC': 'CDC Excel File',
            'Census': 'Census Excel File'
        }

        numDataItems = 2
        self.labels = []
        self.file_comboboxes = []
        grid = QGridLayout()

        for x in range(numDataItems):
            self.labels.append(QLabel(f'Data File {x + 1}'))
            c = QComboBox()
            for k, v in FILE_TYPES.items():
                c.addItem(v, userData=k)
            c.setCurrentIndex(x)
            self.file_comboboxes.append(c)
            grid.addWidget(self.labels[-1], x, 0)
            grid.addWidget(self.file_comboboxes[-1], x, 1)

        num_comboboxes = len(self.file_comboboxes)
        grid.addWidget(QLabel('Category'), num_comboboxes, 0)
        self.category_combobox = QComboBox()
        grid.addWidget(self.category_combobox, num_comboboxes, 1)

        self.setLayout(grid)


class JsdChart (QChart):
    """
    A custom chart class for JSD data visualization.
    """

    def __init__(self, animation_options=QChart.AllAnimations):
        """
        Initializes a new instance of the JsdChart class.

        Args:
            animation_options (QChart.AnimationOptions): The animation options for the chart.
        """
        super().__init__()
        self.setAnimationOptions(animation_options)