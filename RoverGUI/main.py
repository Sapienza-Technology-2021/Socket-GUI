from PyQt5 import QtWidgets, uic, QtCore, QtGui
import sys


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('form.ui', self)
        self.show()
        self.connectButton.clicked.connect(self.clicked)
    def clicked(self):
        print("Mi hai premuto")

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = Ui()
    widget.show()
    # connectButton = QPushButton()
    # connectButton.setTect("Connetti")
    # connectButton.clicked.connect()
    sys.exit(app.exec_())
