import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from PyQt5 import QtWidgets, QtGui, uic
from PyQt5.QtWidgets import QMessageBox
from interfaces import ControllerInterface, RoverInterface, debug, APP_NAME, PORT
from roverclient import RoverClient


class RoverUi(QtWidgets.QMainWindow, ControllerInterface):
    def __init__(self, roverInt):
        super(RoverUi, self).__init__()
        self.roverInterface = roverInt
        uic.loadUi('GUI/form.ui', self)
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
        self.tabWidget.setCurrentIndex(0)
        self.show()

    # Button listeners

    def connectBtnListener(self):
        if self.roverInterface.isConnected():
            self.roverInterface.disconnect()
        else:
            ip = self.ipField.text()
            if ip == "":
                QMessageBox.warning(self, "Errore", "Nessun IP inserito!")
            else:
                # spezza IP e porta
                if self.roverInterface.connect(ip, PORT):
                    # Successo, abilita componenti
                    pass
                else:
                    QMessageBox.warning(self, "Errore", "Connessione fallita!")

    def moveUpListener(self):
        self.roverInterface.move(self.speedSlider.value())

    def moveDownListener(self):
        self.roverInterface.move(-self.speedSlider.value())

    def rotCCWListener(self):
        self.roverInterface.rotate(-self.degPerClickSlider.value())

    def rotCWListener(self):
        self.roverInterface.rotate(self.degPerClickSlider.value())

    def moveUpRightListener(self):
        self.roverInterface.moveRotate(self.speedSlider.value(), self.rotSpeedSlider.value())

    def moveUpLeftListener(self):
        self.roverInterface.moveRotate(self.speedSlider.value(), -self.rotSpeedSlider.value())

    def moveDownLeftListener(self):
        self.roverInterface.moveRotate(-self.speedSlider.value(), -self.rotSpeedSlider.value())

    def moveDownRightListener(self):
        self.roverInterface.moveRotate(-self.speedSlider.value(), self.rotSpeedSlider.value())

    def moveStopListener(self):
        self.roverInterface.stop()

    # Controller interface methods
    def updateAccel(self, xyz):
        super(RoverUi, self).updateAccel(xyz)
        self.accelXNumber.display("{:.2f}".format(xyz[0]))
        self.accelYNumber.display("{:.2f}".format(xyz[1]))
        self.accelZNumber.display("{:.2f}".format(xyz[2]))
        
    def updateGyro(self, xyz):
        super(RoverUi, self).updateGyro(xyz)
        self.gyroXNumber.display("{:.2f}".format(xyz[0]))
        self.gyroYNumber.display("{:.2f}".format(xyz[1]))
        self.gyroZNumber.display("{:.2f}".format(xyz[2]))

    def updateMagn(self, xyz):
        super(RoverUi, self).updateMagn(xyz)
        self.magnXNumber.display("{:.2f}".format(xyz[0]))
        self.magnYNumber.display("{:.2f}".format(xyz[1]))
        self.magnZNumber.display("{:.2f}".format(xyz[2]))

    def updateIrDistance(self, dist1, dist2):
        super(RoverUi, self).updateIrDistance(dist1, dist2)
        self.irSxDistNumber.display("{:.2f}".format(dist1))
        self.irDxDistNumber.display("{:.2f}".format(dist2))

    def updateBatt(self, val):
        super(RoverUi, self).updateBatt(val)
        self.batteryNumber.display("{:.1f}".format(val))

    def updateCpuTemp(self, val):
        super(RoverUi, self).updateCpuTemp(val)
        self.cpuTempNumber.display("{:.1f}".format(val))

    def updateRPMFeedback(self, val):
        super(RoverUi, self).updateRPMFeedback(val)
        self.motorRPMLabel.setText(val + " RPM")

    def setMLEnabled(self, val):
        super(RoverUi, self).setMLEnabled(val)
        self.enableMLBox.setChecked(val)


# Main
if __name__ == "__main__":
    # nuovo thread socket... avvia socket
    roverInterface = RoverClient()
    app = QtWidgets.QApplication([])
    gui = RoverUi(roverInterface)
    roverInterface.setControllerInterface(gui)
    gui.show()
    sys.exit(app.exec_())
