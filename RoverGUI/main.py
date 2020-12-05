import sys
import time
import random
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox
from clientinterface import ClientInterface


class RoverUi(QtWidgets.QMainWindow, ClientInterface):
    def __init__(self):
        super(RoverUi, self).__init__()
        uic.loadUi('form.ui', self)
        self.show()
        self.connectButton.clicked.connect(self.connectBtnListener)
        self.moveUp.clicked.connect(self.moveUpListener)
        self.moveDown.clicked.connect(self.moveDownListener)
        self.moveLeft.clicked.connect(self.moveLeftListener)
        self.moveRight.clicked.connect(self.moveRightListener)
        self.moveUpRight.clicked.connect(self.moveUpRightListener)
        self.moveUpLeft.clicked.connect(self.moveUpLeftListener)
        self.moveDownLeft.clicked.connect(self.moveDownLeftListener)
        self.moveDownRight.clicked.connect(self.moveDownRightListener)
        self.moveStop.clicked.connect(self.moveStopListener)

    def connectBtnListener(self):
        ip = self.ipField.text()
        if ip == "":
            QMessageBox.warning(self, "Errore", "Nessun IP inserito!")
        else:
            pass
            # Connetti socket
            # QMessageBox.warning(self, "Errore", "Connessione fallita!")

    def updateAccel(self, xyz):
        self.accelXNumber.display("{:.1f}".format(xyz[0]))
        self.accelYNumber.display("{:.1f}".format(xyz[1]))
        self.accelZNumber.display("{:.1f}".format(xyz[2]))

    def moveUpListener(self):
        self.roverSocket.move([0, 1], speedSlider.value())

    def moveDownListener(self):
        self.roverSocket.move([0, -1], speedSlider.value())

    def moveLeftListener(self):
        self.roverSocket.move([-1, 0], speedSlider.value())

    def moveRightListener(self):
        self.roverSocket.move([1, 0], speedSlider.value())

    def moveUpRightListener(self):
        self.roverSocket.move([1, 1], speedSlider.value())

    def moveUpLeftListener(self):
        self.roverSocket.move([1, -1], speedSlider.value())

    def moveDownLeftListener(self):
        self.roverSocket.move([-1, -1], speedSlider.value())

    def moveDownRightListener(self):
        self.roverSocket.move([-1, 1], speedSlider.value())

    def moveStopListener(self):
        self.roverSocket.stop()

    def updateGyro(self, xyz):
        self.gyroXNumber.display("{:.1f}".format(xyz[0]))
        self.gyroYNumber.display("{:.1f}".format(xyz[1]))
        self.gyroZNumber.display("{:.1f}".format(xyz[2]))

    def updateMagn(self, xyz):
        self.magnXNumber.display("{:.1f}".format(xyz[0]))
        self.magnYNumber.display("{:.1f}".format(xyz[1]))
        self.magnZNumber.display("{:.1f}".format(xyz[2]))

    def updateIrDistance(self, dist):
        self.irDistNumber.display("{:.1f}".format(dist))

    def updateBatt(self, val):
        self.batteryNumber.display("{:.1f}".format(val))

    def updateCpuTemp(self, val):
        self.cpuTempNumber.display("{:.1f}".format(val))

if __name__ == "__main__":
    # nuovo thread socket... avvia socket
    app = QtWidgets.QApplication([])
    roverUi = RoverUi()
    roverUi.show()
    sys.exit(app.exec_())
