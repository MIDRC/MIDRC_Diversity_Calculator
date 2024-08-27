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

import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPixmap
from PySide6.QtWidgets import QApplication, QSplashScreen

from jsdconfig import JSDConfig
from jsdcontroller import JSDController
from jsdmodel import JSDTableModel
from jsdview import JsdWindow


class SplashScreen(QSplashScreen):
    """
    Class: SplashScreen

    This class is a subclass of QSplashScreen and represents a splash screen for a GUI application.
    It provides a static method _create_pixmap() to create a pixmap with a centered splash screen message.
    The __init__() method initializes the object and sets the pixmap.
    """
    SPLASH_WIDTH = 800
    SPLASH_HEIGHT = 600
    FONT_FAMILY = 'Arial'
    FONT_SIZE = 36
    SPLASH_SCREEN_MESSAGE = 'MIDRC Diversity Calculator\n' \
                            '\n' \
                            'Loading Excel files, please wait...'
    BACKGROUND_COLOR = QColor(Qt.white)

    @staticmethod
    def _create_pixmap():
        """
        Function: _create_pixmap

        Create a pixmap with the splash screen message centered on it.

        Returns:
            QPixmap: The created QPixmap object.
        """

        pixmap = QPixmap(SplashScreen.SPLASH_WIDTH, SplashScreen.SPLASH_HEIGHT)
        font = QFont(SplashScreen.FONT_FAMILY, pointSize=SplashScreen.FONT_SIZE)
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(pixmap.rect(), SplashScreen.BACKGROUND_COLOR)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, SplashScreen.SPLASH_SCREEN_MESSAGE)
        return pixmap

    def __init__(self) -> None:
        """
        Initialize the object.
        """
        super().__init__()
        pixmap = self._create_pixmap()
        self.setPixmap(pixmap)


def launch_diversity_calculator():
    """
    Function: launch_diversity_calculator

    This function launches the diversity calculator application.
    * It checks if a QApplication instance already exists, and if not, creates one.
    * It then creates a SplashScreen object and displays it.
    * Next, it initializes a JSDConfig object and retrieves the data source list from the configuration.
    * It creates a JsdWindow object with the data source list and sets the JSDController with a JSDTableModel and the
    configuration.
    * Finally, it shows the JsdWindow, finishes the SplashScreen, and exits the application.

    Returns:
        None
    """
    q_app = QApplication.instance()
    if q_app is None:
        q_app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    q_app.processEvents()

    config = JSDConfig()
    data_source_list = config.data['data sources']
    w = JsdWindow(data_source_list)  # Note: We should have the controller populate this once the tablemodel is loaded
    w.jsd_controller = JSDController(w,
                                     JSDTableModel(data_source_list, config.data.get('custom age ranges', None)),
                                     config)

    # Set the default widget sizes, show the window, then reset the minimum sizes
    w.set_default_widget_sizes()
    w.show()
    q_app.processEvents()
    w.reset_minimum_sizes()

    splash.finish(w)
    sys.exit(q_app.exec())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    launch_diversity_calculator()
