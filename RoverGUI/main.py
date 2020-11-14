from PyQt5 import QtWidgets, uic
import sys


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('form.ui', self)
        self.show()


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = Ui()
    widget.show()
    sys.exit(app.exec_())
