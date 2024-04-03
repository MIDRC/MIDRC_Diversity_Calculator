import sys
import jsdview
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QLabel, QSplashScreen
from PySide6.QtGui import QPixmap, QPainter, QColor, QFont


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
    w = jsdview.JsdWindow()
    w.show()

    # Close the splash screen and wait for the window to be closed
    splash.finish(w)
    return q_app.exec()


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    status = launch_diversity_calculator()
    sys.exit(status)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
