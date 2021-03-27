import inspect
import os
import sys

from PyQt5.QtCore import Qt

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtWidgets import QMessageBox
from utils import APP_NAME, PORT
from roverclient import RoverClient
from pyqtgraph import mkPen


######################### USER INTERFACE CLASS #########################

class RoverUi(QtWidgets.QMainWindow):
    def __init__(self):
        super(RoverUi, self).__init__()
        uic.loadUi('form.ui', self)
        self.roverClient = RoverClient()
        self.roverClient.set_client_controller(self)
        self.roverClient.register_functions(
            ["updateAccel", "updateDistance", "updateBattery", "updateCpuTemp",
             "updateRPMFeedback", "setMLEnabled", "setMotorsPowered"])
        self.setWindowIcon(QtGui.QIcon('res/icon.png'))
        self.setWindowTitle(APP_NAME)
        self.connectButton.clicked.connect(self.connectBtnListener)
        self.moveUp.clicked.connect(self.moveUpListener)
        self.moveDown.clicked.connect(self.moveDownListener)
        self.rotCCWBtn.clicked.connect(self.rotCCWListener)
        self.rotCWBtn.clicked.connect(self.rotCWListener)
        self.moveUpRight.clicked.connect(self.moveUpRightListener)
        self.moveUpLeft.clicked.connect(self.moveUpLeftListener)
        self.moveDownLeft.clicked.connect(self.moveDownLeftListener)
        self.moveDownRight.clicked.connect(self.moveDownRightListener)
        self.moveStop.clicked.connect(self.moveStopListener)
        self.enableMLBox.stateChanged.connect(self.sendSetMLEnabled)
        self.motorPowerBox.stateChanged.connect(self.motorPowerBoxListener)
        self.tabWidget.setCurrentIndex(0)
        hour = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        temperature = [30, 32, 34, 32, 33, 31, 29, 32, 35, 45]
        self.accel_graph.setBackground('w')
        self.accel_graph.plot(hour, temperature, pen=mkPen(color=(255, 0, 0)))
        self.enableComponents(False)
        self.show()

    def on_disconnection(self):
        self.enableComponents(False)
        self.ipField.setEnabled(True)
        self.connectButton.setText("Connetti")

    def closeEvent(self, event):
        if self.roverClient.isConnected():
            reply = QMessageBox.question(self, APP_NAME, "Are you sure you want to quit?",
                                         QMessageBox.Close | QMessageBox.Cancel)
            if reply == QMessageBox.Close:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()

    # Button listeners

    def connectBtnListener(self):
        if self.roverClient.isConnected():
            self.roverClient.disconnect()
            self.on_disconnection()
        else:
            ip = self.ipField.text()
            if ip == "":
                QMessageBox.warning(self, "Errore", "Nessun IP inserito!")
            else:
                if self.roverClient.connect(ip, PORT):
                    self.enableComponents(True)
                    self.ipField.setEnabled(False)
                    self.connectButton.setText("Disconnetti")
                else:
                    QMessageBox.warning(self, "Errore", "Connessione fallita!")

    def enableComponents(self, b):
        self.moveUp.setEnabled(b)
        self.moveDown.setEnabled(b)
        self.rotCCWBtn.setEnabled(b)
        self.rotCWBtn.setEnabled(b)
        self.moveUpRight.setEnabled(b)
        self.moveUpLeft.setEnabled(b)
        self.moveDownLeft.setEnabled(b)
        self.moveDownRight.setEnabled(b)
        self.moveStop.setEnabled(b)
        self.speedSlider.setEnabled(b)
        self.rotSpeedSlider.setEnabled(b)
        self.degPerClickSlider.setEnabled(b)
        self.motorPowerBox.setEnabled(b)

    def motorPowerBoxListener(self):
        self.roverClient.setMotorsPowered(self.motorPowerBox.isChecked())

    def moveUpListener(self):
        self.roverClient.moveTime(3000)

    def moveDownListener(self):
        self.roverClient.moveTime(-3000)

    def rotCCWListener(self):
        self.roverClient.rotate(-self.degPerClickSlider.value())

    def rotCWListener(self):
        self.roverClient.rotate(self.degPerClickSlider.value())

    def moveUpRightListener(self):
        self.roverClient.moveRotate(self.speedSlider.value(), self.rotSpeedSlider.value())

    def moveUpLeftListener(self):
        self.roverClient.moveRotate(self.speedSlider.value(), -self.rotSpeedSlider.value())

    def moveDownLeftListener(self):
        self.roverClient.moveRotate(-self.speedSlider.value(), -self.rotSpeedSlider.value())

    def moveDownRightListener(self):
        self.roverClient.moveRotate(-self.speedSlider.value(), self.rotSpeedSlider.value())

    def moveStopListener(self):
        self.roverClient.stop()

    def sendSetMLEnabled(self, val):
        if self.enableMLBox.isChecked():
            self.roverClient.setMLEnabled(True)
        else:
            self.roverClient.setMLEnabled(False)

    # Controller interface methods
    def updateAccel(self, xyz):
        self.accelXNumber.display("{:.2f}".format(xyz[0]))
        self.accelYNumber.display("{:.2f}".format(xyz[1]))
        self.accelZNumber.display("{:.2f}".format(xyz[2]))

    def updateDistance(self, dist1):
        self.irSxDistNumber.display("{:.2f}".format(dist1))
        # self.irDxDistNumber.display("{:.2f}".format(dist2))

    def updateBattery(self, val):
        self.batteryNumber.display("{:.1f}".format(val))

    def updateCpuTemp(self, val):
        self.cpuTempNumber.display("{:.1f}".format(val))

    def updateRPMFeedback(self, val):
        self.motorRPMLabel.setText(val + " RPM")

    def setMLEnabled(self, val):
        self.enableMLBox.setChecked(val)

    def setMotorsPowered(self, val):
        self.motorPowerBox.setChecked(val)


######################### MAIN #########################

if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    gui = RoverUi()
    gui.show()
    sys.exit(app.exec_())
