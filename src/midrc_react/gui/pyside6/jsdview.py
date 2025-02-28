#  Copyright (c) 2025 Medical Imaging and Data Resource Center (MIDRC).
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

"""
This module contains the JsdWindow class, which represents the main window of the midrc_react application.
"""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, List, Optional

from PySide6.QtCharts import (
    QAreaSeries, QCategoryAxis, QChart, QDateTimeAxis, QLineSeries, QPieSeries,
    QPolarChart, QValueAxis,
)
from PySide6.QtCore import (
    QDateTime, QPointF, QRect, Qt, QTime, Signal,
)
from PySide6.QtGui import QAction, QPainter
from PySide6.QtWidgets import (
    QDialog, QDialogButtonBox, QDockWidget, QFormLayout, QHBoxLayout, QHeaderView,
    QLabel, QLayout, QMainWindow, QMenu, QMenuBar, QScrollArea, QSpinBox, QSplitter,
    QTableView, QVBoxLayout, QWidget,
)

from midrc_react.core.datetimetools import convert_date_to_milliseconds, numpy_datetime64_to_qdate
from midrc_react.gui.common.jsdview_base import JsdViewBase
from midrc_react.gui.pyside6.copyabletableview import CopyableTableView
from midrc_react.gui.pyside6.dataselectiongroupbox import JsdDataSelectionGroupBox
from midrc_react.gui.pyside6.file_open_dialogs import (
    open_csv_tsv_file_dialog, open_excel_file_dialog, open_yaml_input_dialog,
)
from midrc_react.gui.pyside6.grabbablewidget import GrabbableChartView


class JsdWindow(QMainWindow, JsdViewBase):
    """
    Main window of the MIDRC-REACT application.

    Attributes:
        add_data_source (Signal): Emitted when a new data source is added.
        WINDOW_TITLE (str): The window title.
        DOCK_TITLES (dict): Titles for various dock widgets.
    """
    add_data_source = Signal(dict)

    WINDOW_TITLE: str = 'MIDRC-REACT Representativeness Exploration and Comparison Tool'
    DOCK_TITLES: Dict[str, str] = {
        'table_dock': 'JSD Table - ' + WINDOW_TITLE,
        'pie_chart_dock': 'Pie Charts - ' + WINDOW_TITLE,
        'spider_chart_dock': 'Distribution Charts - ' + WINDOW_TITLE,
    }

    def __init__(self, data_sources: Any) -> None:
        """
        Initialize the JsdWindow with provided data sources and set up the GUI.

        Args:
            data_sources (Any): Data sources used to initialize the data selection group box.
        """
        super().__init__()
        # Set up the data selection group box
        self._dataselectiongroupbox: JsdDataSelectionGroupBox = JsdDataSelectionGroupBox(data_sources)

        self.widgets: Dict[str, Any] = {}

        # Set up the table view dock
        self.table_view: CopyableTableView = CopyableTableView()
        self.addDockWidget(
            Qt.LeftDockWidgetArea,
            self.create_table_dock_widget(self.table_view, JsdWindow.DOCK_TITLES['table_dock']),
        )

        # Set up the timeline chart and its view
        self.jsd_timeline_chart: JsdChart = JsdChart()
        self.jsd_timeline_chart_view: GrabbableChartView = GrabbableChartView(self.jsd_timeline_chart)
        self.jsd_timeline_chart_view.setRenderHint(QPainter.Antialiasing)

        self.setCentralWidget(QWidget())
        self.centralWidget().setLayout(self.create_main_layout())

        # Set up the menu bar
        self.setMenuBar(self.create_menu_bar)

        # Set up the pie chart dock
        self.pie_chart_layout: QVBoxLayout = QVBoxLayout()
        self.pie_chart_dock_widget: QDockWidget = self.create_pie_chart_dock_widget(
            self.pie_chart_layout, JsdWindow.DOCK_TITLES['pie_chart_dock'],
        )
        self.addDockWidget(Qt.BottomDockWidgetArea, self.pie_chart_dock_widget)

        # Set up the spider chart and area chart
        self.spider_chart: QPolarChart = QPolarChart()
        self.area_chart_widget: QWidget = QWidget()
        self.area_chart_widget.setLayout(QVBoxLayout())
        self.spider_chart_vbox: QSplitter = QSplitter(Qt.Vertical)
        self.spider_chart_dock_widget: QDockWidget = self.create_spider_chart_dock_widget(
            self.spider_chart_vbox, JsdWindow.DOCK_TITLES['spider_chart_dock'],
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.spider_chart_dock_widget)

        self.setWindowTitle(JsdWindow.WINDOW_TITLE)

    # Methods from file_open_dialogs are attached directly
    open_excel_file_dialog = open_excel_file_dialog
    open_yaml_input_dialog = open_yaml_input_dialog
    open_csv_tsv_file_dialog = open_csv_tsv_file_dialog

    def create_main_layout(self) -> QVBoxLayout:
        """
        Create and return the main layout for the application.

        Returns:
            QVBoxLayout: The vertical box layout containing the data selection group box and timeline chart.
        """
        main_layout: QVBoxLayout = QVBoxLayout()
        main_layout.addWidget(self._dataselectiongroupbox)
        main_layout.addWidget(self.jsd_timeline_chart_view)
        return main_layout

    @property
    def dataselectiongroupbox(self) -> JsdDataSelectionGroupBox:
        """
        Return the data selection group box widget.

        Returns:
            JsdDataSelectionGroupBox: The data selection group box.
        """
        return self._dataselectiongroupbox

    @property
    def create_menu_bar(self) -> QMenuBar:
        """
        Create and return the main menu bar with File, Settings, and View menus.

        Returns:
            QMenuBar: The created menu bar.
        """
        menu_bar: QMenuBar = QMenuBar()

        # File Menu
        file_menu: QMenu = menu_bar.addMenu("File")
        open_excel_file_action: QAction = QAction("Open Excel File...", self)
        open_excel_file_action.triggered.connect(self.open_excel_file_dialog)
        file_menu.addAction(open_excel_file_action)

        open_csv_file_action: QAction = QAction("Open CSV/TSV File...", self)
        open_csv_file_action.triggered.connect(self.open_csv_tsv_file_dialog)
        file_menu.addAction(open_csv_file_action)

        open_yaml_file_action: QAction = QAction("Open File From YAML...", self)
        open_yaml_file_action.triggered.connect(self.open_yaml_input_dialog)
        file_menu.addAction(open_yaml_file_action)

        # Settings Menu
        settings_menu: QMenu = menu_bar.addMenu("Settings")
        chart_animation_setting: QAction = QAction("Chart Animations", self)
        chart_animation_setting.setCheckable(True)
        chart_animation_setting.setChecked(True)
        chart_animation_setting.toggled.connect(self.set_animation_options)

        num_files_setting: QAction = QAction("Number of Files to Compare", self)
        num_files_setting.triggered.connect(self.adjust_number_of_files_to_compare)
        settings_menu.addAction(chart_animation_setting)
        settings_menu.addAction(num_files_setting)

        # View Menu
        view_menu: QMenu = menu_bar.addMenu("View")
        dock_widget_menu: QMenu = view_menu.addMenu("Dock Widgets")
        dock_widget_menu.aboutToShow.connect(lambda: self.populate_dock_widget_menu(dock_widget_menu))

        return menu_bar

    def populate_dock_widget_menu(self, dock_widget_menu: QMenu) -> None:
        """
        Clear and repopulate the dock widget menu with toggle actions for each dock widget.

        Args:
            dock_widget_menu (QMenu): The menu to populate.
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
        Create a dock widget that contains a table view.

        Args:
            table_view (QTableView): The table view widget.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        table_dock_widget: QDockWidget = QDockWidget()
        table_view.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        table_view.verticalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table_dock_widget.setWidget(table_view)
        table_dock_widget.setWindowTitle(title)
        return table_dock_widget

    @staticmethod
    def create_pie_chart_dock_widget(layout: QLayout, title: str) -> QDockWidget:
        """
        Create a dock widget for pie charts with a given layout and title.

        Args:
            layout (QLayout): The layout containing pie chart widgets.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        dock_widget: QDockWidget = QDockWidget()
        scroll_content: QWidget = QWidget()
        scroll_content.setLayout(layout)

        scroll_area: QScrollArea = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(scroll_content)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)

        dock_widget.setWidget(scroll_area)
        dock_widget.setWindowTitle(title)
        return dock_widget

    def create_spider_chart_dock_widget(self, spider_chart_vbox: QSplitter, title: str) -> QDockWidget:
        """
        Create a dock widget containing a spider chart and an area chart.

        Args:
            spider_chart_vbox (QSplitter): The container for the spider chart.
            title (str): The title of the dock widget.

        Returns:
            QDockWidget: The created dock widget.
        """
        spider_chart_dock_widget: QDockWidget = QDockWidget()
        spider_chart_dock_widget.setWidget(spider_chart_vbox)
        self.spider_chart_vbox.addWidget(self.area_chart_widget)
        self.add_spider_chart_view()
        spider_chart_dock_widget.setWindowTitle(title)
        return spider_chart_dock_widget

    def add_area_chart_view(self, area_chart: QChart) -> GrabbableChartView:
        """
        Add an area chart view to the area chart widget.

        Args:
            area_chart (QChart): The area chart to add.

        Returns:
            GrabbableChartView: The view that was added.
        """
        area_chart_view: GrabbableChartView = GrabbableChartView(
            area_chart, save_file_prefix="MIDRC-REACT_area_chart",
        )
        self.area_chart_widget.layout().addWidget(area_chart_view, stretch=1)
        return area_chart_view

    def add_spider_chart_view(self) -> GrabbableChartView:
        """
        Add a spider chart view to the spider chart container.

        Returns:
            GrabbableChartView: The spider chart view that was added.
        """
        spider_chart_view: GrabbableChartView = GrabbableChartView(
            self.spider_chart, save_file_prefix="MIDRC-REACT_spider_chart",
        )
        self.spider_chart_vbox.addWidget(spider_chart_view)
        return spider_chart_view

    def update_pie_chart_dock(self, sheet_dict: Dict[Any, Any]) -> None:
        """
        Update the pie chart dock with the provided sheet data.

        Args:
            sheet_dict (dict): A dictionary where each key maps to a set of sheets.

        Returns:
            None
        """
        clear_layout(self.pie_chart_layout)
        categorybox = self.dataselectiongroupbox.category_combobox
        categories: List[str] = [categorybox.itemText(i) for i in range(categorybox.count())]
        timepoint: int = -1
        file_comboboxes = self.dataselectiongroupbox.file_comboboxes
        labels: List[QLabel] = JsdWindow._create_pie_chart_labels(sheet_dict, file_comboboxes)

        for sheets in sheet_dict.values():
            row_layout: QHBoxLayout = QHBoxLayout()
            # Add the row label
            if labels:
                row_layout.addWidget(labels.pop(0))
            for category in categories:
                if category not in sheets:
                    continue
                df = sheets[category].df
                cols_to_use = sheets[category].data_columns
                series = QPieSeries()
                for col in cols_to_use:
                    value = df[col].iloc[timepoint]
                    if value > 0:
                        series.append(col, value)
                if not series.isEmpty():
                    row_layout.addWidget(JsdWindow._create_pie_chart_series(series, category), stretch=1)
            self.pie_chart_layout.addLayout(row_layout, stretch=1)

    @staticmethod
    def _create_pie_chart_labels(sheet_dict: Dict[Any, Any], file_comboboxes: List[Any]) -> List[QLabel]:
        """
        Create and return a list of labels for each sheet based on file combobox selections.

        Args:
            sheet_dict (dict): The dictionary of sheets.
            file_comboboxes (list): List of file combobox widgets.

        Returns:
            List[QLabel]: List of QLabel objects for the pie charts.
        """
        labels = [QLabel(file_comboboxes[index].currentText() + ':') for index in sheet_dict]
        max_label_width = max(label.sizeHint().width() for label in labels)
        for label in labels:
            label.setFixedWidth(max_label_width)
        return labels

    @staticmethod
    def _create_pie_chart_series(series: QPieSeries, category: str) -> GrabbableChartView:
        """
        Create a chart view for the pie chart series.

        Args:
            series (QPieSeries): The pie series data.
            category (str): The category name.

        Returns:
            GrabbableChartView: A view containing the pie chart.
        """
        chart: QChart = QChart()
        chart_view: GrabbableChartView = GrabbableChartView(chart, save_file_prefix="MIDRC-REACT_pie_chart")
        chart.setTitle(category)
        chart.setMinimumSize(300, 240)
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignRight)
        return chart_view

    def update_spider_chart(self, spider_plot_values_dict: Dict[Any, Dict[str, float]]) -> bool:
        """
        Update the spider chart with the provided plot values.

        Args:
            spider_plot_values_dict (dict): Dictionary containing series values keyed by index pairs.

        Returns:
            bool: True if chart updated; False if no data provided.
        """
        if not spider_plot_values_dict:
            return False

        self.spider_chart.removeAllSeries()
        for axis in self.spider_chart.axes():
            self.spider_chart.removeAxis(axis)

        labels: List[str] = list(next(iter(spider_plot_values_dict.values())).keys())
        step_size: float = 360 / len(labels)
        angles: List[float] = [step_size * i for i in range(len(labels))]

        angular_axis: QCategoryAxis = QCategoryAxis()
        angular_axis.setRange(0, 360)
        angular_axis.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
        for angle, label in zip(angles, labels):
            angular_axis.append(label, angle)
        self.spider_chart.addAxis(angular_axis, QPolarChart.PolarOrientationAngular)

        max_value: float = max(
            value for series_values in spider_plot_values_dict.values() for value in series_values.values()
        )
        radial_axis: QValueAxis = QValueAxis()
        radial_axis.setRange(0, max_value)
        radial_axis.setLabelFormat('%.2f')
        self.spider_chart.addAxis(radial_axis, QPolarChart.PolarOrientationRadial)

        self.spider_chart.setTitle("JSD per category")

        for index_pair, spider_plot_values in spider_plot_values_dict.items():
            series: QLineSeries = QLineSeries()
            for angle, label in zip(angles, labels):
                series.append(angle, spider_plot_values[label])
            # Close the loop
            if series.points():
                series.append(360, series.points()[0].y())
            file_pair = [
                self._dataselectiongroupbox.file_comboboxes[index_pair[0]].currentData(),
                self._dataselectiongroupbox.file_comboboxes[index_pair[1]].currentData(),
            ]
            if len(spider_plot_values_dict) == 1:
                self.update_spider_chart_title(file_pair[0], file_pair[1])
            series.setName(f'{file_pair[0]} vs {file_pair[1]}')
            self.spider_chart.addSeries(series)
            series.attachAxis(angular_axis)
            series.attachAxis(radial_axis)

        return True

    def update_spider_chart_title(self, file1_data: str = 'File 1', file2_data: str = 'File 2') -> None:
        """
        Update the title of the spider chart with the provided file names.

        Args:
            file1_data (str): Data label for file 1.
            file2_data (str): Data label for file 2.
        """
        title: str = f"Comparison of {file1_data} and {file2_data} - JSD per category"
        self.spider_chart.setTitle(title)

    def update_area_chart(self, category: Dict[Any, Any]) -> bool:
        """
        Update the area chart with new data from the provided sheets.

        Args:
            category (dict): A dictionary where each key maps to a sheet containing chart data.

        Returns:
            bool: True if area charts were updated.
        """
        category_str: str = self._dataselectiongroupbox.category_combobox.currentText()
        clear_layout(self.area_chart_widget.layout())

        for index, sheets in category.items():
            area_chart: QChart = QChart()
            filename: str = self.dataselectiongroupbox.file_comboboxes[index].currentData()
            area_chart.setTitle(f'{filename} {category_str} distribution over time')

            if category_str.endswith(' (ks2)'):
                category_str = category_str[:-6]
            if category_str not in sheets:
                continue

            df = sheets[category_str].df
            cols_to_use = sheets[category_str].data_columns
            dates: List[QDateTime] = [QDateTime(numpy_datetime64_to_qdate(date), QTime()) for date in df.date.values]

            JsdWindow._add_area_chart_series(area_chart, df, cols_to_use, dates)
            JsdWindow._attach_axes_to_area_chart(area_chart, dates)
            self.add_area_chart_view(area_chart)

        return True

    @staticmethod
    def _add_area_chart_series(area_chart: QChart, df: Any, cols_to_use: List[str], dates: List[QDateTime]) -> None:
        """
        Add series to an area chart based on provided data.

        Args:
            area_chart (QChart): The chart to update.
            df (DataFrame): Data source for the series.
            cols_to_use (List[str]): List of columns to plot.
            dates (List[QDateTime]): X-axis dates for the chart.

        Returns:
            None
        """
        df_cols = df[cols_to_use]
        total_counts = df_cols.sum(axis=1)
        cumulative_percents = 100.0 * df_cols.cumsum(axis=1).div(total_counts, axis=0)
        lower_series = None

        for col in cols_to_use:
            if df_cols[col].iloc[-1] == 0:
                continue
            points: List[QPointF] = [
                QPointF(dates[i].toMSecsSinceEpoch(), cumulative_percents.iloc[i][col])
                for i in range(len(dates))
            ]
            if len(dates) == 1:
                points.append(QPointF(dates[0].toMSecsSinceEpoch() + 1, cumulative_percents.iloc[0][col]))
            upper_series: QLineSeries = QLineSeries(area_chart)
            upper_series.append(points)
            area_series: QAreaSeries = QAreaSeries(upper_series, lower_series)
            area_series.setName(col)
            area_chart.addSeries(area_series)
            lower_series = upper_series

    @staticmethod
    def _attach_axes_to_area_chart(area_chart: QChart, dates: List[QDateTime]) -> None:
        """
        Attach X and Y axes to an area chart.

        Args:
            area_chart (QChart): The chart to attach axes to.
            dates (List[QDateTime]): List of dates for the X-axis.

        Returns:
            None
        """
        axis_x: QDateTimeAxis = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        axis_x.setRange(dates[0], dates[-1] if len(dates) > 1 else dates[0].addMSecs(1))
        area_chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y: QValueAxis = QValueAxis()
        axis_y.setTitleText("Percent of total")
        axis_y.setLabelFormat('%.0f%')
        axis_y.setRange(0, 100)
        area_chart.addAxis(axis_y, Qt.AlignLeft)

        for series in area_chart.series():
            series.attachAxis(axis_x)
            series.attachAxis(axis_y)

    def update_jsd_timeline_plot(self, jsd_model: Any) -> bool:
        """
        Update the JSD timeline plot using the provided model.

        Args:
            jsd_model (Any): The data model containing JSD timeline data.

        Returns:
            bool: True if the timeline plot was updated successfully.
        """
        self.table_view.setModel(jsd_model)
        self.jsd_timeline_chart.removeAllSeries()
        jsd_model.clear_color_mapping()
        series_list: List[QLineSeries] = []
        date_min: float = math.inf
        date_max: float = -math.inf

        for c, column_info in enumerate(jsd_model.column_infos):
            col: int = c * 2
            series: QLineSeries = QLineSeries()
            series.setName(f"{column_info['file1']} vs {column_info['file2']} {column_info['category']} JSD")
            row_count: int = jsd_model.rowCount(jsd_model.createIndex(0, col))
            for i in range(row_count):
                time_point: Optional[float] = convert_date_to_milliseconds(jsd_model.input_data[col][i])
                if time_point is not None:
                    series.append(time_point, jsd_model.input_data[col + 1][i])
                    if i == 0 and time_point < date_min:
                        date_min = time_point
                    if i == row_count - 1 and time_point > date_max:
                        date_max = time_point
            series_list.append(series)
            self.jsd_timeline_chart.addSeries(series)
            jsd_model.add_color_mapping(series.pen().color().name(), QRect(col, 0, 2, row_count))

        # Configure X axis
        self.jsd_timeline_chart.removeAxis(self.jsd_timeline_chart.axisX())
        axis_x: QDateTimeAxis = QDateTimeAxis()
        axis_x.setTickCount(10)
        axis_x.setFormat("MMM yyyy")
        axis_x.setTitleText("Date")
        self.jsd_timeline_chart.addAxis(axis_x, Qt.AlignBottom)

        # Configure Y axis
        axis_y: Optional[QValueAxis] = self.jsd_timeline_chart.axisY()
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

    def set_animation_options(self, enable_animations: bool) -> bool:
        """
        Enable or disable chart animations.

        Args:
            enable_animations (bool): True to enable animations, False to disable.

        Returns:
            bool: True after setting the animation options.
        """
        if enable_animations:
            self.jsd_timeline_chart.setAnimationOptions(QChart.AllAnimations)
        else:
            self.jsd_timeline_chart.setAnimationOptions(QChart.NoAnimation)
        return True

    def adjust_number_of_files_to_compare(self) -> None:
        """
        Open a dialog to adjust the number of files to compare and update the UI accordingly.

        Returns:
            None
        """
        d: QDialog = QDialog(self)
        d.setLayout(QVBoxLayout())
        f_l: QFormLayout = QFormLayout()
        d.layout().addLayout(f_l)

        spinbox: QSpinBox = QSpinBox()
        spinbox.setMinimum(2)
        spinbox.setMaximum(self.dataselectiongroupbox.file_comboboxes[0].count())
        spinbox.setValue(len(self.dataselectiongroupbox.file_comboboxes))
        f_l.addRow(QLabel("Number of Files to Compare:"), spinbox)

        button_box: QDialogButtonBox = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(d.accept)
        button_box.rejected.connect(d.reject)
        d.layout().addWidget(button_box)
        d.resize(400, -1)
        if d.exec():
            self.dataselectiongroupbox.set_num_data_items(spinbox.value())

    def set_default_widget_sizes(self) -> None:
        """
        Set default sizes for main window and dock widgets for an optimal initial layout.

        Returns:
            None
        """
        self.resize(1800, 1000)
        self.pie_chart_dock_widget.setMinimumHeight(250)
        self.spider_chart_dock_widget.setMinimumWidth(600)
        self.spider_chart_vbox.setStretchFactor(0, 2)
        self.spider_chart_vbox.setStretchFactor(1, 7)

    def reset_minimum_sizes(self) -> None:
        """
        Reset the minimum sizes of the spider and pie chart dock widgets to allow free resizing.

        Returns:
            None
        """
        self.spider_chart_dock_widget.setMinimumWidth(0)
        self.pie_chart_dock_widget.setMinimumHeight(0)


class JsdChart(QChart):
    """
    Custom chart class for JSD data visualization.
    """
    def __init__(self, parent: Optional[QWidget] = None, animation_options: int = QChart.AllAnimations) -> None:
        """
        Initialize the JsdChart with optional parent and animation options.

        Args:
            parent (Optional[QWidget]): The parent widget.
            animation_options (int): Chart animation options.
        """
        super().__init__(parent)
        self.setAnimationOptions(animation_options)


def clear_layout(layout: Optional[QLayout]) -> bool:
    """
    Recursively clear all widgets and sub-layouts from a given layout.

    Args:
        layout (Optional[QLayout]): The layout to clear.

    Returns:
        bool: True if layout cleared; False if layout was None.
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
