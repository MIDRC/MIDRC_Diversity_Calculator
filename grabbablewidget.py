from PySide6.QtWidgets import (QWidget, QMenu, QFileDialog, QApplication, QDialog, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel)
from PySide6.QtGui import QClipboard, QAction, QImage, QPixmap, QPainter
from PySide6.QtCore import QEvent, Qt, QObject, QDir, QStandardPaths
from PySide6.QtCharts import QChartView
from datetime import datetime
import os

class GrabbableWidgetMixin(QObject):
    DEFAULT_SAVE_FILE_PREFIX = "diversity_plot_"

    def __init__(self, parent=None, save_file_prefix=DEFAULT_SAVE_FILE_PREFIX):
        super().__init__(parent)
        self.save_file_prefix = save_file_prefix
        parent.setContextMenuPolicy(Qt.CustomContextMenu)
        parent.customContextMenuRequested.connect(self.showContextMenu)
        parent.installEventFilter(self)
        self.parent = parent
        self.save_dialog_open = False

    def eventFilter(self, source, event):
        if event.type() == QEvent.ContextMenu and source == self.parent and self.save_dialog_open is False:
            self.showContextMenu(event.pos())
            return True
        return super().eventFilter(source, event)

    def showContextMenu(self, pos):
        # Only display the context menu if we don't have the high res save dialog open for this widget
        if not self.save_dialog_open:
            contextMenu = QMenu(self.parent)
            copyAction = QAction("Copy", self.parent)
            saveAction = QAction("Save", self.parent)
            saveHighResAction = QAction("Save High Resolution", self.parent)


            copyAction.triggered.connect(self.copyToClipboard)
            saveAction.triggered.connect(self.saveToDisk)
            saveHighResAction.triggered.connect(self.saveHighResToDisk)

            contextMenu.addAction(copyAction)
            contextMenu.addAction(saveAction)
            contextMenu.addAction(saveHighResAction)

            contextMenu.exec(self.parent.mapToGlobal(pos))

    def copyToClipboard(self):
        snapshot = self.parent.grab()
        clipboard = QApplication.clipboard()
        clipboard.setPixmap(snapshot)

    def default_filename(self, suffix=".png"):
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
        options = QFileDialog.Options()
        default_filename = self.save_file_prefix + datetime.now().strftime("%Y%m%d%H%M%S")
        fileName, _ = QFileDialog.getSaveFileName(self.parent, "Save Snapshot", self.default_filename(".png"),
                                                  "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)",
                                                  options=options)
        if fileName:
            snapshot = self.parent.grab()
            snapshot.save(fileName)

    def saveHighResToDisk(self):
        self.save_dialog_open = True
        screenshot_dialog = SaveWidgetAsImageDialog(None, self.parent)
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
    def __init__(self, parent, widget):
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
        self.layout().removeWidget(self.widget)
        self.widget_parent_layout.replaceWidget(self.temp_widget, self.widget)

    def cancel_save(self):
        self.restore_widget()
        self.reject()

    def save_image(self):
        ratio = 2
        self.image = QImage(round(ratio * self.widget.width()), round(ratio * self.widget.height()), QImage.Format_RGB32)
        # self.image.setDevicePixelRatio(ratio) # The QPainter handles this automatically
        painter = QPainter(self.image)
        self.widget.render(painter)
        painter.end()

        self.restore_widget()
        self.accept()

class GrabbableChartView(QChartView):
    def __init__(self, chart, parent=None, save_file_prefix=GrabbableWidgetMixin.DEFAULT_SAVE_FILE_PREFIX):
        super().__init__(chart, parent)
        self.mixin = GrabbableWidgetMixin(self, save_file_prefix)

