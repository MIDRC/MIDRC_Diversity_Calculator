import sys
import jsdview
from PySide6.QtWidgets import QApplication

# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = jsdview.JsdWindow()
    w.show()
    sys.exit(app.exec())

# See PyCharm help at https://www.jetbrains.com/help/pycharm/
