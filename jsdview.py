from typing import Type, Union, List, Tuple
from PySide6.QtCore import QRect, Qt, QDateTime, QTime, QPointF, QSignalBlocker
from PySide6.QtGui import QPainter, QAction
from PySide6.QtWidgets import (QHeaderView, QTableView, QWidget, QMainWindow, QGroupBox, QMenu,
                               QVBoxLayout, QComboBox, QLabel, QHBoxLayout, QMenuBar, QDockWidget, QSplitter,
                               QLayout, QFormLayout)
from PySide6.QtCharts import (QChart, QChartView, QLineSeries, QDateTimeAxis, QValueAxis,
                              QPieSeries, QPolarChart, QAreaSeries, QCategoryAxis)
from datetimetools import numpy_datetime64_to_qdate, convert_date_to_milliseconds


class JsdDataSelectionGroupBox(QGroupBox):
    NUM_DATA_ITEMS = 2

    def __init__(self, data_sources):
        """
        Initialize the JsdDataSelectionGroupBox.

        This method sets up the data selection group box by creating labels and combo boxes for data files and a
        category combo box.
        """
        super().__init__()

        self.setTitle('Data Selection')

        self.labels = [QLabel(f'Data File {x + 1}') for x in range(self.NUM_DATA_ITEMS)]
        self.file_comboboxes = [QComboBox() for _ in range(self.NUM_DATA_ITEMS)]
        self.category_label = QLabel('Category')
        self.category_combobox = QComboBox()
        self.set_layout(data_sources)

    def set_layout(self, data_sources):
        """
        Sets the layout for the widget.
        """
        # Create the form layout
        form_layout = QFormLayout()

        # Add the file comboboxes and labels to the form layout
        items = [(d['description'], d['name']) for d in data_sources]
        for combobox_index, combobox in enumerate(self.file_comboboxes):
            for combobox_item in items:
                combobox.addItem(combobox_item[0], userData=combobox_item[1])
            combobox.setCurrentIndex(combobox_index)
            form_layout.addRow(self.labels[combobox_index], combobox)

        # Add the category label and combobox to the form layout
        form_layout.addRow(self.category_label, self.category_combobox)

        # Set the layout for the widget
        self.setLayout(form_layout)

    def update_category_combo_box(self, categorylist, categoryindex):
        with QSignalBlocker(self.category_combobox):
            self.category_combobox.clear()
            self.category_combobox.addItems(categorylist)
            self.category_combobox.setCurrentIndex(categoryindex)


class JsdWindow(QMainWindow):
    WINDOW_TITLE: str = 'MIDRC Diversity Calculator'

    def __init__(self, data_sources):
        """
        Initialize the JsdWindow.

        This method sets up the main window and all the component widgets.
        """
        super().__init__()

        # Set up graphical layout
        self._dataselectiongroupbox = JsdDataSelectionGroupBox(data_sources)

        self.table_view = QTableView()
        self.addDockWidget(Qt.LeftDockWidgetArea,
                           self.create_table_dock_widget(self.table_view, 'JSD Table - ' + JsdWindow.WINDOW_TITLE))

        self.jsd_timeline_chart = JsdChart()
        self.jsd_timeline_chart_view = QChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.create_main_layout())

        self.setMenuBar(self.create_menu_bar())

        self.pie_chart_views = {}
        self.pie_chart_hbox = QHBoxLayout()
        self.pie_chart_dock_widget = self.create_pie_chart_dock_widget(self.pie_chart_hbox,
                                                                   'Pie Charts - ' + JsdWindow.WINDOW_TITLE)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        self.spider_chart = QPolarChart()
        self.area_chart = QChart()
        self.spider_chart_vbox = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget = self.create_spider_chart_dock_widget(self.spider_chart_vbox,
                                                                         'Diversity Charts - ' + JsdWindow.WINDOW_TITLE)
        self.addDockWidget(Qt.RightDockWidgetArea, self.spider_chart_dock_widget)

        self.setWindowTitle(JsdWindow.WINDOW_TITLE)

    def create_main_layout(self) -> QVBoxLayout:
        """
        Create the main layout for the application.
        This layout includes the data selection group box and the JSD timeline chart view.
        """
        main_layout = QVBoxLayout()
        main_layout.addWidget(self._dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        return main_layout

    @property
    def dataselectiongroupbox(self) -> JsdDataSelectionGroupBox:
        # Get the Data Selection GroupBox object.
        return self._dataselectiongroupbox

    def create_menu_bar(self) -> QMenuBar:
        """
        Create the menu bar.
        """
        menu_bar: QMenuBar = QMenuBar()

        # Add the 'File' menu
        file_menu: QMenu = menu_bar.addMenu("File")

        # Add the 'Settings' menu
        settings_menu: QMenu = menu_bar.addMenu("Settings")

        # Create the 'Chart Animations' action
        chartanimationsetting: QAction = QAction("Chart Animations", self)
        chartanimationsetting.setCheckable(True)
        chartanimationsetting.setChecked(True)
        chartanimationsetting.toggled.connect(lambda checked: self.set_animation_options(checked))

        # Add the 'Chart Animations' action to the 'Settings' menu
        settings_menu.addAction(chartanimationsetting)

        # Return the menu bar
        return menu_bar

    @staticmethod
    def create_table_dock_widget(table_view: QTableView, title: str) -> QDockWidget:
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

    @staticmethod
    def create_pie_chart_dock_widget(layout: QLayout, title: str) -> QDockWidget:
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
        assert isinstance(title, str), f"The 'title' argument must be a string. Got {type(title).__name__} instead."
        dock_widget.setWindowTitle(title)
        return dock_widget

    def create_spider_chart_dock_widget(self, spider_chart_vbox: QSplitter, title: str) -> QDockWidget:
        """
        Create a dock widget with an area chart and a spider chart.

        Args:
            spider_chart_vbox: The QSplitter containing the spider chart.
            title: The title of the dock widget.

        Returns:
            The created QDockWidget.
        """
        assert isinstance(title, str), f"The 'title' argument must be a string. Got {type(title).__name__} instead."
        spider_chart_dock_widget = QDockWidget()
        spider_chart_dock_widget.setWidget(spider_chart_vbox)
        self.add_area_chart_view()
        self.add_spider_chart_view()
        spider_chart_dock_widget.setWindowTitle(title)
        return spider_chart_dock_widget

    def add_area_chart_view(self):
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

    def add_spider_chart_view(self):
        """
        Add a spider chart view to the spider chart vbox layout.
    
        Returns:
            The spider chart view object that was added.
        """
        spider_chart_view = QChartView(self.spider_chart)
        self.spider_chart_vbox.addWidget(spider_chart_view)
        return spider_chart_view

    def update_pie_chart_dock(self, sheets):
        """
        Update the pie chart dock with new data.
        """
        # First, get rid of the old stuff just to be safe
        for c, pv in self.pie_chart_views.items():
            self.pie_chart_dock_widget.layout().removeWidget(pv)
            pv.deleteLater()
        self.pie_chart_views = {}

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
                    series.append(col, df[col].iloc[timepoint])
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            self.pie_chart_hbox.addWidget(new_pie_chart_views[category], stretch=1)
        self.pie_chart_views = new_pie_chart_views

    def update_spider_chart(self, spider_plot_values):
        """
        Update the spider chart with new data.
        """
        file1_data = self._dataselectiongroupbox.file_comboboxes[0].currentData()
        file2_data = self._dataselectiongroupbox.file_comboboxes[1].currentData()

        self.spider_chart.removeAllSeries()
        for axis in self.spider_chart.axes():
            self.spider_chart.removeAxis(axis)

        self.update_spider_chart_title(file1_data, file2_data)

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

    def update_spider_chart_title(self, file1_data: str = 'File 1', file2_data: str = 'File 2'):
        """
        Set the title of the spider chart.

        Args:
            file1_data (str): The data from file 1.
            file2_data (str): The data from file 2.
        """
        title = f"Comparison of {file1_data} and {file2_data} - JSD per category"
        self.spider_chart.setTitle(title)

    def update_area_chart(self, sheets, filename):
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
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        axis_x.setRange(dates[0], dates[-1] if len(dates) > 1 else dates[0].addMSecs(1))
        self.area_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = self.area_chart.axisY()
        axis_y.setTitleText("Percent of total")
        axis_y.setLabelFormat('%.0f%')
        axis_y.setRange(0, 100)
        self.area_chart.setProperty("current_data", filename)

        return True

    def update_jsd_timeline_plot(self, jsd_model):
        self.table_view.setModel(jsd_model)
        self.jsd_timeline_chart.removeAllSeries()
        jsd_model.clear_color_mapping()
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
        jsd_model.add_color_mapping(series.pen().color().name(), QRect(0, 0, 2, row_count))

        self.jsd_timeline_chart.removeAxis(self.jsd_timeline_chart.axisX())
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        self.jsd_timeline_chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)

        axis_y = self.jsd_timeline_chart.axisY()
        if axis_y is None:
            axis_y = QValueAxis()
            axis_y.setTitleText("JSD value")
            axis_y.setRange(0, 1)
            axis_y.setTickCount(11)
            self.jsd_timeline_chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)

        self.jsd_timeline_chart_view.setChart(self.jsd_timeline_chart)

        return True

    def set_animation_options(self, enable_animations: bool):
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
