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
import csv
from functools import partial
import io
import math
from typing import Iterable

from PySide6.QtCharts import (QAreaSeries, QCategoryAxis, QChart, QDateTimeAxis, QLineSeries, QPieSeries, QPolarChart,
                              QValueAxis)
from PySide6.QtCore import (QDate, QDateTime, QEvent, QFileInfo, QObject, QPointF, QRect, Qt, QTime, Signal)
from PySide6.QtGui import QAction, QGuiApplication, QKeySequence, QPainter
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QDockWidget, QFileDialog, QFormLayout,
                               QHBoxLayout, QHeaderView, QLabel, QLayout, QLineEdit, QMainWindow, QMenu,
                               QMenuBar, QScrollArea, QSpinBox, QSplitter, QTableView, QVBoxLayout, QWidget)

from dataselectiongroupbox import JsdDataSelectionGroupBox
from datetimetools import convert_date_to_milliseconds, numpy_datetime64_to_qdate
from grabbablewidget import GrabbableChartView


class JsdWindow(QMainWindow):
    """
    Class: JsdWindow

    Represents the main window of the MIDRC Diversity Calculator application.

    Attributes:
    - WINDOW_TITLE: str - The title of the window.
    - DOCK_TITLES: dict - A dictionary containing the titles of the dock widgets.
    - add_data_source: Signal - A signal emitted when a new data source is added.

    Methods:
    - None

    """

    # pylint: disable=too-many-instance-attributes
    # The current number of attributes is not a problem for this class because they are necessary for GUI updates

    WINDOW_TITLE: str = 'MIDRC Diversity Calculator'
    DOCK_TITLES: dict = {
        'table_dock': 'JSD Table - ' + WINDOW_TITLE,
        'pie_chart_dock': 'Pie Charts - ' + WINDOW_TITLE,
        'spider_chart_dock': 'Diversity Charts - ' + WINDOW_TITLE,
    }
    add_data_source = Signal(dict)

    def __init__(self, data_sources):
        """
        Initialize the JsdWindow.

        This method sets up the main window and all the component widgets.
        """
        super().__init__()

        # Set up graphical layout
        self._dataselectiongroupbox = JsdDataSelectionGroupBox(data_sources)

        self.widgets = {}

        self.table_view = CopyableTableView()
        self.addDockWidget(Qt.LeftDockWidgetArea,
                           self.create_table_dock_widget(self.table_view, JsdWindow.DOCK_TITLES['table_dock']))

        self.jsd_timeline_chart = JsdChart()
        self.jsd_timeline_chart_view = GrabbableChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)
        # self.jsd_timeline_chart_view.setMinimumSize(640, 480)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.create_main_layout())

        self.setMenuBar(self.create_menu_bar)

        self.pie_chart_layout = QVBoxLayout()
        self.pie_chart_dock_widget = self.create_pie_chart_dock_widget(self.pie_chart_layout,
                                                                       JsdWindow.DOCK_TITLES['pie_chart_dock'])
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        self.spider_chart = QPolarChart()
        self.area_chart_widget = QWidget()
        # self.area_chart_layout = QVBoxLayout()
        self.area_chart_widget.setLayout(QVBoxLayout())
        self.spider_chart_vbox = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget = self.create_spider_chart_dock_widget(self.spider_chart_vbox,
                                                                             JsdWindow.DOCK_TITLES['spider_chart_dock'])
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
        """
        Return an instance of JsdDataSelectionGroupBox.

        This method returns an instance of the JsdDataSelectionGroupBox class, which is a widget used for data
        selection. It takes no arguments and returns an initialized instance of the JsdDataSelectionGroupBox class.

        Returns:
            JsdDataSelectionGroupBox: An instance of the JsdDataSelectionGroupBox class.
        """
        return self._dataselectiongroupbox

    @property
    def create_menu_bar(self) -> QMenuBar:
        """
        Create a menu bar.

        Returns:
            QMenuBar: The created menu bar.
        """
        menu_bar: QMenuBar = QMenuBar()

        # Add the 'File' menu
        file_menu: QMenu = menu_bar.addMenu("File")

        # Create the 'Open Excel File' action
        open_excel_file_action: QAction = QAction("Open Excel File...", self)
        open_excel_file_action.triggered.connect(self.open_excel_file)
        file_menu.addAction(open_excel_file_action)

        # Add the 'Settings' menu
        settings_menu: QMenu = menu_bar.addMenu("Settings")

        # Create the 'Chart Animations' action
        chart_animation_setting: QAction = QAction("Chart Animations", self)
        chart_animation_setting.setCheckable(True)
        chart_animation_setting.setChecked(True)
        chart_animation_setting.toggled.connect(self.set_animation_options)

        num_files_setting: QAction = QAction("Number of Files to Compare", self)
        num_files_setting.triggered.connect(self.adjust_number_of_files_to_compare)

        # Add the 'View' menu
        view_menu: QMenu = menu_bar.addMenu("View")
        dock_widget_menu: QMenu = view_menu.addMenu("Dock Widgets")
        dock_widget_menu.aboutToShow.connect(partial(self.populate_dock_widget_menu, dock_widget_menu))

        # Add the actions to the 'Settings' menu
        settings_menu.addAction(chart_animation_setting)
        settings_menu.addAction(num_files_setting)

        # Return the menu bar
        return menu_bar

    def populate_dock_widget_menu(self, dock_widget_menu: QMenu) -> None:
        """
        Clear the dock widget menu and populate it with actions for each dock widget.

        This method clears the existing menu items in the menu and creates a new action for each dock widget found.
        Each action corresponds to a dock widget and allows the user to toggle the visibility of the dock widget.
        """
        dock_widget_menu.clear()
        dock_widgets: Iterable[QDockWidget] = self.findChildren(QDockWidget)
        for dock in dock_widgets:
            action: QAction = QAction(dock.windowTitle(), dock_widget_menu)
            action.setCheckable(True)
            action.setChecked(dock.isVisible())
            action.toggled.connect(lambda checked, d=dock: d.setVisible(checked))
            dock_widget_menu.addAction(action)

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
        Creates a dock widget with a given layout and title.

        Args:
            layout (QLayout): The layout to be displayed in the dock widget.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        dock_widget = QDockWidget()
        # w = QWidget()
        scroll_content = QWidget()
        scroll_content.setLayout(layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # w.setLayout(layout)
        dock_widget.setWidget(scroll_area)
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
        self.spider_chart_vbox.addWidget(self.area_chart_widget)
        self.add_spider_chart_view()
        spider_chart_dock_widget.setWindowTitle(title)
        return spider_chart_dock_widget

    def add_area_chart_view(self, area_chart):
        """
        Add an area chart view to the spider chart dock widget.

        Returns:
            The created area_chart_view.

        Raises:
            None
        """
        area_chart_view = GrabbableChartView(area_chart, save_file_prefix="diversity_area_chart")
        self.area_chart_widget.layout().addWidget(area_chart_view, stretch=1)
        return area_chart_view

    def add_spider_chart_view(self):
        """
        Add a spider chart view to the spider chart vbox layout.

        Returns:
            The spider chart view object that was added.
        """
        spider_chart_view = GrabbableChartView(self.spider_chart, save_file_prefix="diversity_spider_chart")
        self.spider_chart_vbox.addWidget(spider_chart_view)
        return spider_chart_view

    def update_pie_chart_dock(self, sheet_dict):
        """
        Update the pie chart dock with the given sheet dict.

        Parameters:
        - sheet_dict (dict): A dictionary of index keys and sheets.

        Returns:
        - None
        """

        # Clear any existing charts in the layout
        clear_layout(self.pie_chart_layout)

        # Retrieve categories and timepoint
        categories = [self.dataselectiongroupbox.category_combobox.itemText(i)
                      for i in range(self.dataselectiongroupbox.category_combobox.count())]
        timepoint = -1

        file_comboboxes = self.dataselectiongroupbox.file_comboboxes

        # Create the row labels and set the fixed width
        labels = JsdWindow._create_pie_chart_labels(sheet_dict, file_comboboxes)

        for sheets in sheet_dict.values():
            row_layout = QHBoxLayout()
            # Add the row label
            row_layout.addWidget(labels.pop(0))

            for category in categories:
                df = sheets[category].df
                cols_to_use = sheets[category].data_columns

                # Filter out columns with zero values and create the pie series
                series = QPieSeries()
                for col in cols_to_use:
                    value = df[col].iloc[timepoint]
                    if value > 0:
                        series.append(col, value)

                # Only create and add the chart if there are valid series items
                if not series.isEmpty():
                    row_layout.addWidget(JsdWindow._create_pie_chart_series(series, category), stretch=1)

            self.pie_chart_layout.addLayout(row_layout, stretch=1)

    @staticmethod
    def _create_pie_chart_labels(sheet_dict, file_comboboxes):
        """
        Create a list of labels for the pie chart dock widget.
        """
        labels = [QLabel(file_comboboxes[index].currentText() + ':') for index in sheet_dict]
        max_label_width = max(label.sizeHint().width() for label in labels)
        for label in labels:
            label.setFixedWidth(max_label_width)
        return labels

    @staticmethod
    def _create_pie_chart_series(series, category):
        """
        Create a pie chart series.
        """
        chart = QChart()
        chart_view = GrabbableChartView(chart, save_file_prefix="diversity_pie_chart")
        chart.setTitle(category)
        chart.setMinimumSize(300, 240)
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignRight)
        return chart_view

    def update_spider_chart(self, spider_plot_values_dict):
        """
        Update the spider chart with new values.

        Parameters:
        - spider_plot_values_dict (dict): A dictionary of dictionaries where each dictionary contains
          the values for one series on the spider chart.

        Returns:
        - bool: True if the chart was updated, False if there was no data to update.
        """

        if not spider_plot_values_dict:
            return False  # Early exit if there's no data

        # Clear the existing series and axes from the spider chart
        self.spider_chart.removeAllSeries()
        for axis in self.spider_chart.axes():
            self.spider_chart.removeAxis(axis)

        # Extract the labels and calculate the angular axis parameters
        labels = list(next(iter(spider_plot_values_dict.values())).keys())
        step_size = 360 / len(labels)
        angles = [step_size * i for i in range(len(labels))]

        # Set up the angular axis
        angular_axis = QCategoryAxis()
        angular_axis.setRange(0, 360)
        angular_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
        for angle, label in zip(angles, labels):
            angular_axis.append(label, angle)
        self.spider_chart.addAxis(angular_axis, QPolarChart.PolarOrientationAngular)

        # Calculate the range for the radial axis
        max_value = max(
            value for series_values in spider_plot_values_dict.values() for value in series_values.values()
        )
        radial_axis = QValueAxis()
        radial_axis.setRange(0, max_value)
        radial_axis.setLabelFormat('%.2f')
        self.spider_chart.addAxis(radial_axis, QPolarChart.PolarOrientationRadial)

        self.spider_chart.setTitle("JSD per category")

        # Create and add each series to the chart
        for index_pair, spider_plot_values in spider_plot_values_dict.items():
            series = QLineSeries()

            # Append points for each label
            for angle, label in zip(angles, labels):
                series.append(angle, spider_plot_values[label])

            # Close the loop by connecting the last point back to the first
            series.append(360, series.points()[0].y())

            # Retrieve the filenames for the series name
            file_pair = [self._dataselectiongroupbox.file_comboboxes[index_pair[0]].currentData(),
                         self._dataselectiongroupbox.file_comboboxes[index_pair[1]].currentData()]

            # Update the chart title if there's only one comparison
            if len(spider_plot_values_dict) == 1:
                self.update_spider_chart_title(file_pair[0], file_pair[1])

            series.setName(f'{file_pair[0]} vs {file_pair[1]}')
            self.spider_chart.addSeries(series)
            series.attachAxis(angular_axis)
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

    def update_area_chart(self, sheet_dict):
        """
        Update the area chart with new data.

        Parameters:
        - sheet_dict (dict): A dictionary of index keys and sheets containing data for the chart.

        Returns:
        - None

        This method updates the area chart with new data provided in the sheet_dict.
        The area chart displays the data in a filled area format, allowing for easy visualization of
        trends and patterns. The sheet_dict values should be a list of sheets, where each sheet contains the
        necessary data for the chart. After updating the chart, the method does not return any value.
        """
        # Get the selected category
        category = self._dataselectiongroupbox.category_combobox.currentText()

        # Clear any existing charts in the layout
        clear_layout(self.area_chart_widget.layout())

        for index, sheets in sheet_dict.items():
            # Create a new QChart object for each sheet
            area_chart = QChart()
            filename = self.dataselectiongroupbox.file_comboboxes[index].currentData()
            area_chart.setTitle(f'{filename} {category} distribution over time')

            # Extract data from the sheet
            df = sheets[category].df
            cols_to_use = sheets[category].data_columns

            # Prepare dates for the X-axis
            dates = [QDateTime(numpy_datetime64_to_qdate(date), QTime()) for date in df.date.values]

            JsdWindow._add_area_chart_series(area_chart, df, cols_to_use, dates)
            JsdWindow._attach_axes_to_area_chart(area_chart, dates)

            # Add the configured chart to the display
            self.add_area_chart_view(area_chart)

        return True

    @staticmethod
    def _add_area_chart_series(area_chart, df, cols_to_use, dates):
        """
        Adds multiple series to the given area chart.

        Parameters:
            area_chart (QChart): The area chart to add the series to.
            df (DataFrame): The DataFrame containing the data for the series.
            cols_to_use (list): A list of column names to use for the series.
            dates (list): A list of QDateTime objects representing the dates for the X-axis.

        Returns:
            None
        """
        # Calculate cumulative percentages
        total_counts = df[cols_to_use].sum(axis=1)
        cumulative_percents = 100.0 * df[cols_to_use].cumsum(axis=1).div(total_counts, axis=0)

        # Create series for the area chart
        lower_series = None
        for col in cols_to_use:
            if df[col].iloc[-1] == 0:  # Skip columns with no data
                continue

            # Generate data points for the series
            points = [QPointF(dates[i].toMSecsSinceEpoch(), cumulative_percents.iloc[i][col]) for i in
                      range(len(dates))]
            if len(dates) == 1:
                points.append(QPointF(dates[0].toMSecsSinceEpoch() + 1, cumulative_percents.iloc[0][col]))

            upper_series = QLineSeries(area_chart)
            upper_series.append(points)

            # Create the area series using the current and previous series
            area_series = QAreaSeries(upper_series, lower_series)
            area_series.setName(col)
            area_chart.addSeries(area_series)

            # Update the lower series for the next iteration
            lower_series = upper_series

    @staticmethod
    def _attach_axes_to_area_chart(area_chart, dates):
        """
        Attaches axes to the given area chart.

        Parameters:
            area_chart (QChart): The area chart to attach the axis to.
            dates (list): A list of QDateTime objects representing the dates for the X-axis.

        Returns:
            None
        """

        # Set up X-axis as a datetime axis
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        axis_x.setRange(dates[0], dates[-1] if len(dates) > 1 else dates[0].addMSecs(1))
        area_chart.addAxis(axis_x, Qt.AlignBottom)

        # Set up Y-axis as a percentage axis
        axis_y = QValueAxis()
        axis_y.setTitleText("Percent of total")
        axis_y.setLabelFormat('%.0f%')
        axis_y.setRange(0, 100)
        area_chart.addAxis(axis_y, Qt.AlignLeft)

        # Attach axes to each series in the chart
        for series in area_chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

    def update_jsd_timeline_plot(self, jsd_model):
        """
        Update the JSD timeline plot with the given JSD model.

        Parameters:
        - jsd_model (Type): The JSD model to update the plot with.

        Returns:
        - None

        This method updates the table view model with the provided JSD model, effectively updating the JSD timeline plot
        """
        self.table_view.setModel(jsd_model)
        self.jsd_timeline_chart.removeAllSeries()
        jsd_model.clear_color_mapping()
        series_list = []
        date_min = math.inf
        date_max = -math.inf

        # Use every other column since there are dates in every other column
        for c, column_info in enumerate(jsd_model.column_infos):
            col = c * 2
            series = QLineSeries()
            series.setName(f"{column_info['file1']} vs "
                           f"{column_info['file2']} "
                           f"{column_info['category']} JSD")
            row_count = jsd_model.rowCount(jsd_model.createIndex(0, col))
            for i in range(row_count):
                time_point = convert_date_to_milliseconds(jsd_model.input_data[col][i])
                if time_point is not None:
                    series.append(time_point, jsd_model.input_data[col + 1][i])
                    if i == 0 and time_point < date_min:
                        date_min = time_point
                    if i == row_count - 1 and time_point > date_max:
                        date_max = time_point
            series_list.append(series)
            self.jsd_timeline_chart.addSeries(series)
            jsd_model.add_color_mapping(series.pen().color().name(), QRect(col, 0, 2, row_count))

        self.jsd_timeline_chart.removeAxis(self.jsd_timeline_chart.axisX())
        axis_x = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        self.jsd_timeline_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = self.jsd_timeline_chart.axisY()
        if axis_y is None:
            axis_y = QValueAxis()
            axis_y.setTitleText("JSD value")
            axis_y.setRange(0, 1)
            axis_y.setTickCount(11)
            self.jsd_timeline_chart.addAxis(axis_y, Qt.AlignLeft)

        for series in series_list:
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)
        axis_x.setRange(QDateTime.fromMSecsSinceEpoch(date_min), QDateTime.fromMSecsSinceEpoch(date_max))

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

    def open_excel_file(self):
        """
        Open an Excel file and add it as a data source.

        This method opens a file dialog to allow the user to select an Excel file. Once a file is selected, a dialog is
        displayed to allow the user to enter additional information about the data source. The information includes
        the name, description, data type, filename, and remove column name text. The data source dictionary is then
        created using the entered information and emitted using the add_data_source signal. The file description and
        name are also added to the file_comboboxes in the dataselectiongroupbox.

        Parameters:
        - None

        Returns:
        - None

        Raises:
        - None
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Excel File", "", "Excel Files (*.xls *.xlsx)")
        file_options_dialog = FileOptionsDialog(self, file_name)
        file_options_dialog.exec()
        data_source_dict = {'name': file_options_dialog.name_line_edit.text(),
                            'description': file_options_dialog.description_line_edit.text(),
                            'data type': 'file',
                            'filename': file_name,
                            'remove column name text': file_options_dialog.remove_column_text_line_edit.text()}
        self.add_data_source.emit(data_source_dict)
        self._dataselectiongroupbox.add_file_to_comboboxes(data_source_dict['description'], data_source_dict['name'])

    def adjust_number_of_files_to_compare(self):
        """
        Adjusts the number of files to compare in the JsdWindow.

        This method opens a dialog box that allows the user to adjust the number of files to compare in the JsdWindow.
        The user can select a value between 2 and the number of files currently opened. The selected value is then used
        to update the number of data items in the JsdDataSelectionGroupBox.

        Parameters:
        - None

        Returns:
        - None

        Raises:
        - None
        """
        d = QDialog(self)
        d.setLayout(QVBoxLayout())
        f_l = QFormLayout()
        d.layout().addLayout(f_l)

        spinbox = QSpinBox()
        # The spinbox range should be between 2 and the number of files opened
        spinbox.setMinimum(2)
        spinbox.setMaximum(self.dataselectiongroupbox.file_comboboxes[0].count())
        spinbox.setValue(len(self.dataselectiongroupbox.file_comboboxes))

        f_l.addRow(QLabel("Number of Files to Compare:"), spinbox)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(d.accept)
        button_box.rejected.connect(d.reject)
        d.layout().addWidget(button_box)

        d.resize(400, -1)
        if d.exec():
            self.dataselectiongroupbox.set_num_data_items(spinbox.value())

    def set_default_widget_sizes(self):
        """
        Set the default sizes for the widgets in the JsdWindow.

        This method resizes the main window and sets the default sizes for the pie chart dock widget and the spider
        chart dock widget. It also sets the stretch factors for the spider chart vbox layout to achieve a good default
        size for the widget.

        Parameters:
        - None

        Returns:
        - None

        Raises:
        - None
        """
        # Resize window and widgets to decent defaults
        self.resize(1800, 1000)
        # Setting a minimum size seems to be the only way to set the default size of dock widgets,
        # but we must reset these values after show() using the reset_minimum_sizes() method
        self.pie_chart_dock_widget.setMinimumHeight(250)
        self.spider_chart_dock_widget.setMinimumWidth(600)
        # These stretch factors seem to make a good default size for the East dock widget
        self.spider_chart_vbox.setStretchFactor(0, 2)
        self.spider_chart_vbox.setStretchFactor(1, 7)

    def reset_minimum_sizes(self):
        """
        Reset the minimum sizes of the spider chart dock widget and the pie chart dock widget.

        This method sets the minimum width of the spider chart dock widget to 0 and the minimum height of the pie chart
        dock widget to 0. This effectively removes any minimum size constraints on these widgets, allowing them to
        resize freely.

        Parameters:
        - None

        Returns:
        - None

        Raises:
        - None
        """
        self.spider_chart_dock_widget.setMinimumWidth(0)
        self.pie_chart_dock_widget.setMinimumHeight(0)


class JsdChart (QChart):
    """
    A custom chart class for JSD data visualization.
    """

    def __init__(self, parent=None, animation_options=QChart.AllAnimations):
        """
        Initializes a new instance of the JsdChart class.

        Args:
            animation_options (QChart.AnimationOptions): The animation options for the chart.
        """
        super().__init__(parent)
        self.setAnimationOptions(animation_options)


def clear_layout(layout):
    """
    Recursively clears all widgets and layouts from the given layout.

    Parameters:
        layout (QLayout): The layout to be cleared.

    Returns:
        bool: True if the layout was cleared, False if layout was None.
    """
    if layout is None:
        return False

    while layout.count():
        child = layout.takeAt(0)
        if child.widget() is not None:
            child.widget().deleteLater()
        elif child.layout() is not None:
            clear_layout(child.layout())
        layout.removeItem(child)

    return True


class FileOptionsDialog (QDialog):
    """
    A dialog window for displaying and editing file options.

    This class represents a dialog window that allows the user to view and modify various options related to a file.
    It inherits from the QDialog class provided by the PySide6.QtWidgets module.

    Methods:
        __init__(self, parent, file_name: str): Initializes the FileOptionsDialog object.
    """
    def __init__(self, parent, file_name: str):
        """
        Initialize the JsdDataSelectionGroupBox.

        This method sets up the data selection group box by creating labels and combo boxes for data files and a
        category combo box.

        Parameters:
        parent: The parent widget of the dialog.
        file_name: The name of the file for which the options are being displayed.

        Returns:
        None
        """
        super().__init__(parent)

        self.setLayout(QVBoxLayout())

        self.name_line_edit = QLineEdit()
        self.description_line_edit = QLineEdit()
        self.remove_column_text_line_edit = QLineEdit()

        form_layout = QFormLayout()
        form_layout.addRow("Name (Plot Titles)", self.name_line_edit)
        form_layout.addRow("Description (Drop-Down Menu)", self.description_line_edit)
        form_layout.addRow("Remove Column Text", self.remove_column_text_line_edit)

        self.layout().addLayout(form_layout)

        fi = QFileInfo(file_name)
        self.setWindowTitle(fi.fileName())
        self.name_line_edit.setText(fi.baseName())
        self.description_line_edit.setText(fi.baseName())

        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(self.accept)
        self.layout().addWidget(button_box)

        self.resize(600, -1)


class CopyableTableView(QTableView):
    """
    A custom subclass of QTableView that allows copying selected data to the clipboard.

    Methods:
        __init__(): Initializes the CopyableTableView object.
        eventFilter(source, event): Filters and handles key press events.
        copy_selection(): Copies the selected data to the clipboard.

    """
    def __init__(self):
        super().__init__()
        self.installEventFilter(self)

    def eventFilter(self, source: QObject, event):
        """
        Filters and handles key press events.

        Parameters:
            source (object): The source object that triggered the event.
            event (QEvent): The event object that contains information about the key press event.

        Returns:
            bool: True if the event is handled, False otherwise.
        """
        if event.type() == QEvent.KeyPress:
            if event == QKeySequence.Copy:
                self.copy_selection()
                return True
        return super(QTableView, self).eventFilter(source, event)

    def copy_selection(self):
        """
        Copies the selected data to the clipboard as a tab-delimited table.

        Returns:
            None

        Raises:
            None
        """
        selection = self.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                index_data = index.data()
                if isinstance(index_data, QDate):
                    index_data = index_data.toString(format=Qt.ISODate)
                table[row][column] = index_data
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QGuiApplication.clipboard().setText(stream.getvalue())
