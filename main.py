import sys
import jsdview
from PySide6.QtWidgets import QApplication, QLabel, QSplashScreen
from PySide6.QtGui import QPixmap, QPainter

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)

    pixmap = QPixmap()
    painter = QPainter(pixmap)
    painter.drawText(0, 0, 'Loading Excel files, please wait...')
    splash = QSplashScreen(pixmap)
    splash.show()
    app.processEvents()
    w = jsdview.JsdWindow()
    w.show()
    splash.finish(w)
    sys.exit(app.exec())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
