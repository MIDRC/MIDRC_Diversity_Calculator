import sys
from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QSplashScreen, QWidget
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from jsdcontroller import JSDController
from jsdmodel import JSDTableModel
from jsdview import JsdWindow


class SplashScreen(QSplashScreen):
    @staticmethod
    def _create_pixmap():
        """
        Create a pixmap with the splash screen message centered on it.
        """
        SPLASH_WIDTH = 800
        SPLASH_HEIGHT = 600
        FONT_FAMILY = 'Arial'
        FONT_SIZE = 36
        SPLASH_SCREEN_MESSAGE = 'MIDRC Diversity Calculator\n' \
                                '\n' \
                                'Loading Excel files, please wait...'
        BACKGROUND_COLOR = QColor(Qt.white)

        pixmap = QPixmap(SPLASH_WIDTH, SPLASH_HEIGHT)
        font = QFont(FONT_FAMILY, pointSize=FONT_SIZE)
        with QPainter(pixmap) as painter:
            painter.setRenderHint(QPainter.Antialiasing)
            painter.fillRect(pixmap.rect(), BACKGROUND_COLOR)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignCenter, SPLASH_SCREEN_MESSAGE)
        return pixmap

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        """
        Initialize the object.

        Args:
            parent: The parent widget.
        """
        super().__init__(parent)
        pixmap = self._create_pixmap()
        self.setPixmap(pixmap)


def launch_diversity_calculator():
    q_app = QApplication.instance()
    if q_app is None:
        q_app = QApplication(sys.argv)

    splash = SplashScreen()
    splash.show()
    q_app.processEvents()

    w = JsdWindow()
    RAW_DATA_KEYS = ['MIDRC', 'CDC', 'Census', 'MIDRC COVID+']
    w.jsd_controller = JSDController(w, JSDTableModel(RAW_DATA_KEYS))
    w.show()

    splash.finish(w)
    sys.exit(q_app.exec())


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    launch_diversity_calculator()

