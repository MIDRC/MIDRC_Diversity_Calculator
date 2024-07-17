from typing import Optional
from PySide6.QtWidgets import (QWidget, QMenu, QFileDialog, QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QLayout)
from PySide6.QtGui import QClipboard, QAction, QImage, QPixmap, QPainter
from PySide6.QtCore import QEvent, Qt, QObject, QDir, QStandardPaths, QDateTime
from PySide6.QtCharts import QChartView, QChart


class GrabbableWidgetMixin(QObject):
    """
    Mixin class for adding snapshot (grab) and save functionalities to a QWidget.

    Attributes:
        DEFAULT_SAVE_FILE_PREFIX (str): Default prefix for save file names.
        DATE_TIME_FORMAT (str): The datetime format for appending to default filenames when saving snapshots

    Methods:
        __init__(self, parent: QWidget = None, save_file_prefix: str = DEFAULT_SAVE_FILE_PREFIX):
            Initialize the class instance with optional parent QWidget and a save file prefix.
        eventFilter(self, source, event):
            Filters events for the widget to handle context menu events.
        showContextMenu(self, pos):
            Display a context menu for capturing snapshots of the widget.
        copyToClipboard(self):
            Copy the snapshot of the parent widget to the clipboard.
        default_filename(self, suffix=".png"):
            Generate a default filename for saving snapshots.
        saveToDisk(self):
            Save a snapshot of the parent widget to disk.
        saveHighResToDisk(self):
            Save a high-resolution snapshot of the parent widget to disk.
    """
    DEFAULT_SAVE_FILE_PREFIX = "diversity_plot_"
    DATE_TIME_FORMAT = "yyyyMMddhhmmss"  # Constant for date-time format

    def __init__(self, parent: QWidget = None, save_file_prefix: str = DEFAULT_SAVE_FILE_PREFIX) -> None:
        """
        Initialize the class instance with optional parent QWidget and a save file prefix.
        Set the save dialog status to False by default.

        Attributes:
            save_dialog_open (bool): Indicates if the save dialog is currently open.
        """
        self.save_dialog_open = False # Indicates if the save dialog is currently open
        super().__init__(parent)
        self.save_file_prefix = save_file_prefix
        parent.setContextMenuPolicy(Qt.CustomContextMenu)
        parent.customContextMenuRequested.connect(self.showContextMenu)
        parent.installEventFilter(self)
        self.parent = parent

    def eventFilter(self, source, event):
        """
        Filters events for the widget to handle context menu events.

        Args:
            source: The source of the event.
            event: The event to be filtered.

        Returns:
            bool: True if the event is a context menu event for the parent widget, False otherwise.
        """
        if event.type() == QEvent.ContextMenu and source == self.parent:
            self.showContextMenu(event.pos())
            return True
        return super().eventFilter(source, event)

    def showContextMenu(self, pos):
        """
        Display a context menu for the widget for capturing snapshots of the widget.

        Args:
            pos: The position where the context menu should be displayed.

        Returns:
            None
        """
        contextMenu = QMenu(self.parent)
        copyAction = QAction("Copy", self.parent)
        saveAction = QAction("Save", self.parent)

        copyAction.triggered.connect(self.copy_to_clipboard)
        saveAction.triggered.connect(self.save_to_disk)

        contextMenu.addAction(copyAction)
        contextMenu.addAction(saveAction)

        # Only display this action if we don't have the high res save dialog open for this widget
        if not self.save_dialog_open:
            saveHighResAction = QAction("Save High Resolution", self.parent)
            saveHighResAction.triggered.connect(self.save_high_res_to_disk)
            contextMenu.addAction(saveHighResAction)

        contextMenu.exec(self.parent.mapToGlobal(pos))

    def copy_to_clipboard(self):
        """
        Copy the snapshot of the parent widget to the clipboard.

        Returns:
            None
        """
        clipboard = QApplication.clipboard()
        if clipboard is not None:
            snapshot = self.parent.grab()
            clipboard.setPixmap(snapshot)
            del snapshot

    def create_directory(self):
        """
        Create the directory for saving snapshots if it does not exist.

        Returns:
            QDir: The directory path for saving the snapshot.
        """
        subdir = "Screenshots"
        pictures_location = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        screenshots_dir = QDir(pictures_location)
        screenshots_dir.mkpath(subdir)
        screenshots_dir.cd(subdir)

        return screenshots_dir

    def default_filename(self, suffix: str = ".png") -> str:
        """
        Generate a default filename for saving snapshots.

        Args:
            suffix: The file extension to be appended to the filename. Default is '.png'.

        Returns:
            str: The default file path for saving the snapshot.
        """
        # Get the default save directory
        screenshots_dir = self.create_directory()

        # Set default file name using QDateTime and the constant format
        default_filename = self.save_file_prefix + QDateTime.currentDateTime().toString(self.DATE_TIME_FORMAT) + suffix
        return screenshots_dir.filePath(default_filename)

    def save_to_disk(self):
        """
        Save a snapshot of the parent widget to disk.

        Prompts the user to choose a file location and format for saving the snapshot.
        If a file is selected, the snapshot of the widget is saved to the chosen location.

        Returns:
            None
        """
        options = QFileDialog.Options()
        fileName, _ = QFileDialog.getSaveFileName(self.parent, "Save Snapshot", self.default_filename(".png"),
                                                  "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
                                                  options=options)
        if fileName:
            snapshot = self.parent.grab()
            snapshot.save(fileName)
            del snapshot

    def save_high_res_to_disk(self) -> None:
        """
        Save a high-resolution snapshot of the parent widget to disk.

        Opens a dialog to capture a high-resolution snapshot of the widget and saves it to the chosen file location.
        Resets the save dialog status after saving the snapshot.

        Returns:
            None
        """
        self.save_dialog_open = True
        screenshot_dialog = SaveWidgetAsImageDialog(self.parent)
        screenshot_dialog.exec()
        high_res_snapshot = screenshot_dialog.image

        # QImage.isNull() does not always work properly
        # if (not high_res_snapshot.isNull()) and screenshot_dialog.result() == QDialog.Accepted:
        if screenshot_dialog.result() == QDialog.Accepted:
            options = QFileDialog.Options()
            fileName, _ = QFileDialog.getSaveFileName(self.parent, "Save High Resolution Snapshot",
                                                      self.default_filename("_highres.png"),
                                                      "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
                                                      options=options)
            if fileName:
                high_res_snapshot.save(fileName)

        self.save_dialog_open = False


class SaveWidgetAsImageDialog(QDialog):
    """
    Dialog for saving a widget as an image with options to restore, cancel, and save the image with a specified ratio.

    Attributes:
        widget: The widget to be saved as an image.
        parent: Optional parent QWidget for the dialog.

    Methods:
        restore_widget: Restore the original widget by removing the temporary widget.
        cancel_save: Restore the original widget and reject the save operation.
        save_image: Save the image of the widget with a specified ratio.
    """
    WINDOW_TITLE = "Save High Resolution Image"
    WINDOW_WIDTH = 400
    WINDOW_HEIGHT = 300

    def __init__(self, widget: QWidget, parent: Optional[QWidget] = None):
        """
        Initialize the SaveWidgetAsImageDialog with the specified widget and optional parent.

        Parameters:
            widget (QWidget): The widget to be saved as an image.
            parent (Optional[QWidget]): The optional parent widget for the dialog.
        """
        super().__init__(parent)

        self.setWindowTitle(self.WINDOW_TITLE)
        self.resize(self.WINDOW_WIDTH, self.WINDOW_HEIGHT)

        self._image: QImage = QImage()
        self.widget: QWidget = widget
        self.temp_widget: Optional[QLabel] = None
        self.widget_parent_layout: Optional[QLayout] = None

        self._create_temp_widget()
        self._setup_layout()

    @property
    def image(self) -> QImage:
        """
        Get the image generated from the widget.

        Returns:
            QImage: The image generated from the widget.
        """
        return self._image

    def _create_temp_widget(self):
        """
        Create a temporary widget to display the image before saving.

        Parameters:
            None

        Returns:
            None
        """
        self.temp_widget = QLabel()
        self.temp_widget.setPixmap(self.widget.grab())
        self.widget_parent_layout = self.widget.parentWidget().layout()
        if self.widget_parent_layout is None:  # This means the parent handles the layout instead of having a layout
            self.widget_parent_index = self.widget.parentWidget().indexOf(self.widget)
            self.widget.parentWidget().insertWidget(self.widget_parent_index, self.temp_widget)
        else:
            self.widget_parent_layout.replaceWidget(self.widget, self.temp_widget)

    def _setup_layout(self) -> None:
        """
        Set up the layout for the dialog including the main widget and buttons.
        """
        layout = QVBoxLayout(self)
        layout.addWidget(self.widget)

        self._setup_buttons(layout)

    def _setup_buttons(self, layout):
        """
        Create and configure the Save and Cancel buttons.

        Parameters:
            layout: The layout to add the buttons to.
        """
        button_layout = QHBoxLayout()

        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)

        self.save_button.clicked.connect(self.save_image)
        self.cancel_button.clicked.connect(self.cancel_save)

        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def _restore_widget(self):
        """
        Restore the original widget by removing the temporary widget and replacing it with the original widget.

        This method reverts the changes made for displaying the temporary widget.
        """
        self.layout().removeWidget(self.widget)
        if self.widget_parent_layout is None:  # The parent handles the layout instead of having a layout
            self.temp_widget.parentWidget().replaceWidget(self.widget_parent_index, self.widget)
        else:
            self.widget_parent_layout.replaceWidget(self.temp_widget, self.widget)
        self.temp_widget.deleteLater()

    def cancel_save(self):
        """
        Restore the original widget and reject the save operation.

        This method restores the original widget by removing the temporary widget and replaces it with the original widget.
        Then, it rejects the save operation.
        """
        self._restore_widget()
        self.reject()

    def save_image(self, _, ratio: int = 2):
        """
        Save the image of the widget with a specified ratio.

        Creates an image of the widget with a given ratio, renders it using a QPainter, and then restores the original widget.
        Finally, accepts the save operation.

        Parameters:
            _ : Signals can send a parameter, so ignore it
            ratio (int): The ratio to scale the image.
        """
        image = QImage(round(ratio * self.widget.width()), round(ratio * self.widget.height()), QImage.Format_RGB32)
        # self.image.setDevicePixelRatio(ratio) # The QPainter handles this automatically
        painter = QPainter(self.image)
        self.widget.render(painter)
        painter.end()

        self._image.swap(image)

        self._restore_widget()
        self.accept()


class GrabbableChartView(QChartView):
    """
    Subclass of QChartView for creating a chart view that can be grabbed and saved as an image.

    Inherits functionality from QChartView and adds the ability to save the chart as an image.
    """
    def __init__(self, chart: QChart, parent: Optional[QWidget] = None, save_file_prefix: str = GrabbableWidgetMixin.DEFAULT_SAVE_FILE_PREFIX) -> None:
        """
        Initialize the class instance with an optional parent QWidget, a save file prefix, and a GrabbableWidgetMixin.

        Args:
            chart (QChart): The chart to be displayed in the view.
            parent (Optional[QWidget]): The optional parent QWidget for the chart view.
            save_file_prefix (str): The prefix for save file names.

        Connect context menu signals for the parent widget to show the context menu and handle events.
        """
        super().__init__(chart, parent)
        self.grabbable_mixin = GrabbableWidgetMixin(self, save_file_prefix)

    def save_chart_to_disk(self):
        """
        Save the chart view to disk using the `save_to_disk` functionality from `GrabbableWidgetMixin`.

        Returns:
            None
        """
        self.grabbable_mixin.save_to_disk()

