from PySide6.QtWidgets import (QWidget, QMenu, QFileDialog, QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel)
from PySide6.QtGui import QClipboard, QAction, QImage, QPixmap, QPainter
from PySide6.QtCore import QEvent, Qt, QObject, QDir, QStandardPaths
from PySide6.QtCharts import QChartView
from datetime import datetime
import os

class GrabbableWidgetMixin(QObject):
    """
    Mixin class for adding snapshot (grab) and save functionalities to a QWidget.

    Attributes:
        DEFAULT_SAVE_FILE_PREFIX (str): Default prefix for save file names.

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

    def __init__(self, parent: QWidget = None, save_file_prefix: str = DEFAULT_SAVE_FILE_PREFIX):
        """
        Initialize the class instance with optional parent QWidget and a save file prefix.
        Set the save dialog status to False by default.
        """
        self.save_dialog_open = False
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


        copyAction.triggered.connect(self.copyToClipboard)
        saveAction.triggered.connect(self.saveToDisk)

        contextMenu.addAction(copyAction)
        contextMenu.addAction(saveAction)

        # Only display this action if we don't have the high res save dialog open for this widget
        if not self.save_dialog_open:
            saveHighResAction = QAction("Save High Resolution", self.parent)
            saveHighResAction.triggered.connect(self.saveHighResToDisk)
            contextMenu.addAction(saveHighResAction)

        contextMenu.exec(self.parent.mapToGlobal(pos))

    def copyToClipboard(self):
        """
        Copy the snapshot of the parent widget to the clipboard.

        Returns:
            None
        """
        snapshot = self.parent.grab()
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(snapshot)

    def default_filename(self, suffix=".png"):
        """
        Generate a default filename for saving snapshots.

        Args:
            suffix (str): The file extension to be appended to the filename. Default is '.png'.

        Returns:
            str: The default file path for saving the snapshot.
        """
        # Get the default save directory
        pictures_location = QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        screenshots_dir = QDir(os.path.join(pictures_location, "Screenshots"))

        # Create the directory if it does not exist
        if not screenshots_dir.exists():
            screenshots_dir.mkpath(".")

        # Set default file name
        default_filename = self.save_file_prefix + datetime.now().strftime("%Y%m%d%H%M%S") + suffix
        return os.path.join(screenshots_dir.path(), default_filename)

    def saveToDisk(self):
        """
        Save a snapshot of the parent widget to disk.

        Prompts the user to choose a file location and format for saving the snapshot.
        If a file is selected, the snapshot of the widget is saved to the chosen location.

        Returns:
            None
        """
        options = QFileDialog.Options()
        default_filename = self.save_file_prefix + datetime.now().strftime("%Y%m%d%H%M%S")
        fileName, _ = QFileDialog.getSaveFileName(self.parent, "Save Snapshot", self.default_filename(".png"),
                                                  "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
                                                  options=options)
        if fileName:
            snapshot = self.parent.grab()
            snapshot.save(fileName)

    def saveHighResToDisk(self):
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
    Initialize the SaveWidgetAsImageDialog instance with optional parent QWidget and a save file prefix.

    Set the save dialog status to False by default.
    Connects context menu signals for the parent widget to show the context menu and handle events.

    Attributes:
        widget: The widget to be saved as an image.
        parent: Optional parent QWidget for the dialog.

    Methods:
        restore_widget: Restore the original widget by removing the temporary widget.
        cancel_save: Restore the original widget and reject the save operation.
        save_image: Save the image of the widget with a specified ratio.
    """
    def __init__(self, widget, parent=None):
        """
        Initialize the SaveWidgetAsImageDialog instance with optional parent QWidget and a save file prefix.

        Set the save dialog status to False by default.
        Connects context menu signals for the parent widget to show the context menu and handle events.
        """
        super().__init__(parent)

        self.setWindowTitle("Save High Resolution Image")
        self.resize(400, 300)

        self.image = None
        self.widget = widget
        self.temp_widget = QLabel()
        self.temp_widget.setPixmap(widget.grab())
        self.widget_parent_layout = widget.parentWidget().layout()
        self.widget_parent_layout.replaceWidget(self.widget, self.temp_widget)

        # Create a layout for the dialog and add the widget to the layout
        layout = QVBoxLayout(self)
        layout.addWidget(self.widget)

        # Create a horizontal layout for the buttons
        button_layout = QHBoxLayout()

        # Create Save and Cancel buttons
        self.save_button = QPushButton("Save", self)
        self.cancel_button = QPushButton("Cancel", self)

        # Connect the buttons to their respective slots
        self.save_button.clicked.connect(self.save_image)
        self.cancel_button.clicked.connect(self.cancel_save)

        # Add buttons to the button layout
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        # Add the button layout to the main layout
        layout.addLayout(button_layout)

    def restore_widget(self):
        """
        Restore the original widget by removing the temporary widget and replacing it with the original widget.

        This method reverts the changes made for displaying the temporary widget.
        """
        self.layout().removeWidget(self.widget)
        self.widget_parent_layout.replaceWidget(self.temp_widget, self.widget)

    def cancel_save(self):
        """
        Restore the original widget and reject the save operation.

        This method restores the original widget by removing the temporary widget and replaces it with the original widget.
        Then, it rejects the save operation.
        """
        self.restore_widget()
        self.reject()

    def save_image(self):
        """
        Save the image of the widget with a specified ratio.

        Creates an image of the widget with a given ratio, renders it using a QPainter, and then restores the original widget.
        Finally, accepts the save operation.
        """
        ratio = 2
        self.image = QImage(round(ratio * self.widget.width()), round(ratio * self.widget.height()), QImage.Format_RGB32)
        # self.image.setDevicePixelRatio(ratio) # The QPainter handles this automatically
        painter = QPainter(self.image)
        self.widget.render(painter)
        painter.end()

        self.restore_widget()
        self.accept()

class GrabbableChartView(QChartView):
    """
    Subclass of QChartView for creating a chart view that can be grabbed and saved as an image.

    Inherits functionality from QChartView and adds the ability to save the chart as an image.
    """
    def __init__(self, chart, parent=None, save_file_prefix=GrabbableWidgetMixin.DEFAULT_SAVE_FILE_PREFIX):
        """
        Initialize the class instance with an optional parent QWidget and a save file prefix.

        Connect context menu signals for the parent widget to show the context menu and handle events.
        """
        super().__init__(chart, parent)
        self.mixin = GrabbableWidgetMixin(self, save_file_prefix)

