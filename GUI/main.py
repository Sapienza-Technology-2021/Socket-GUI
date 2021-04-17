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
             "updateRPMFeedback", "setMLEnabled", "setMotorsPowered", "updateCompass"])
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
        self.accel_time_axis = []
        self.compass_time_axis = []
        self.accel_data = [[], [], []]
        self.compass_data = [[], []]
        self.accel_graph.setBackground('w')
        self.accel_graph.showGrid(x=True, y=True)
        self.accel_graph.setYRange(-12, 12, padding=0)
        self.accel_graph.addLegend()
        self.compass_graph.setBackground('w')
        self.compass_graph.showGrid(x=True, y=True)
        self.compass_graph.setYRange(-180, 180, padding=0)
        self.compass_graph.addLegend()
        self.accel_X = self.accel_graph.plot(self.accel_time_axis, self.accel_data[0],
                                             pen=mkPen(color=(213, 0, 0), width=2), name="Accel. X")
        self.accel_Y = self.accel_graph.plot(self.accel_time_axis, self.accel_data[1],
                                             pen=mkPen(color=(41, 98, 255), width=2), name="Accel. Y")
        self.accel_Z = self.accel_graph.plot(self.accel_time_axis, self.accel_data[2],
                                             pen=mkPen(color=(255, 171, 0), width=2), name="Accel. Z")
        self.compass_current = self.compass_graph.plot(self.compass_time_axis, self.compass_data[0],
                                                       pen=mkPen(color=(213, 0, 0), width=3), name="Compass")
        self.compass_target = self.compass_graph.plot(self.compass_time_axis, self.compass_data[1],
                                                      pen=mkPen(color=(41, 98, 255), width=3), name="Target")
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
                QMessageBox.warning(self, "Error", "Please, write an IP address!")
            else:
                if self.roverClient.connect(ip, PORT):
                    self.enableComponents(True)
                    self.ipField.setEnabled(False)
                    self.connectButton.setText("Disconnetti")
                else:
                    QMessageBox.warning(self, "Error", "Connection failed!")

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

    ######################### CONTROLLER INTERFACE CLASS #########################

    def updateAccel(self, xyz):
        accel_count = len(self.accel_time_axis)
        # Add a new value on the t axis
        if accel_count > 0:
            self.accel_time_axis.append(self.accel_time_axis[-1] + 1)
            if accel_count > 40:
                self.accel_time_axis = self.accel_time_axis[1:]
                self.accel_data = [self.accel_data[0][1:], self.accel_data[1][1:], self.accel_data[2][1:]]
        else:
            self.accel_time_axis.append(0)
        self.accel_data[0].append(xyz[0])
        self.accel_data[1].append(xyz[1])
        self.accel_data[2].append(xyz[2])
        self.accel_X.setData(self.accel_time_axis, self.accel_data[0])
        self.accel_Y.setData(self.accel_time_axis, self.accel_data[1])
        self.accel_Z.setData(self.accel_time_axis, self.accel_data[2])

    def updateCompass(self, data):
        compass_count = len(self.compass_time_axis)
        # Add a new value on the t axis
        if compass_count > 0:
            self.compass_time_axis.append(self.accel_time_axis[-1] + 1)
            if compass_count > 30:
                self.compass_time_axis = self.accel_time_axis[1:]
                self.compass_data = [self.compass_data[0][1:], self.compass_data[1][1:], self.compass_data[2][1:]]
        else:
            self.compass_time_axis.append(0)
        self.compass_data[0].append(data[0])
        self.compass_data[1].append(data[1])
        self.compass_current.setData(self.compass_time_axis, self.compass_data[0])
        self.compass_target.setData(self.compass_time_axis, self.compass_data[1])

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
