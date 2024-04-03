import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QSplashScreen
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
from jsdcontroller import JSDController
from jsdmodel import JSDTableModel
from jsdview import JsdWindow

def launch_diversity_calculator():
    """
    Creates and launches the diversity calculator application.

    Returns:
        int: The QApplication instance's return value.
    """
    q_app = QApplication(sys.argv)

    # Create the splash screen
    pixmap = QPixmap(800, 600)  # Specify the size of the splashscreen pixmap
    painter = QPainter(pixmap)
    painter.fillRect(pixmap.rect(), Qt.white)
    font = QFont()
    font.setPointSize(36)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, 'MIDRC Diversity Calculator\n'
                                                    '\n'
                                                    'Loading Excel files, please wait...')
    painter.end()
    splash = QSplashScreen(pixmap)
    splash.show()
    q_app.processEvents()

    # Create the diversity calculator window
    w = JsdWindow()
    RAW_DATA_KEYS = ['MIDRC', 'CDC', 'Census']
    w.jsd_controller = JSDController(w, JSDTableModel(RAW_DATA_KEYS))
    w.show()

    # Close the splash screen and wait for the window to be closed
    splash.finish(w)
    return q_app.exec()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    status = launch_diversity_calculator()
    sys.exit(status)

