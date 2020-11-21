import sys
import time
import random
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox


class Ui(QtWidgets.QMainWindow):
    def __init__(self):
        super(Ui, self).__init__()
        uic.loadUi('form.ui', self)
        self.show()
        self.connectButton.clicked.connect(self.clicked)  # listener

    def clicked(self):  # funzione eseguita dal bottone
        ip = self.ipField.text()
        # da fare in modo che possa essere inserito solo un indirizzo ip valido
        if ip == "":
            print("Errore: nessun indirizzo ip inserito")

        else:
            print("Mi sto connettendo a... " + ip)
            time.sleep(2)  # da sostituire con gestione dell'errore
            connectionOutput = random.randint(0, 100)
            if connectionOutput in range(0, 50):
                print("Connessione fallita!")
                QMessageBox.about(self, "Errore", "Connessione fallita")

            else:
                print("Connessione riuscita!")
                # questa parte andrà modificata con i valori ricevuti dalla socket
                randAccel = random.randint(100, 1000)/10
                self.xAccelNumber.display("{:.1f}".format(randAccel))
                self.yAccelNumber.display("{:.1f}".format(randAccel * 0.1 + 30))
                self.zAccelNumber.display("{:.1f}".format(randAccel * 0.15 + 45))
                self.batteryNumber.display(100)
                self.cpuTempNumber.display(random.randint(0, 100))


if __name__ == "__main__":
    app = QtWidgets.QApplication([])
    widget = Ui()
    widget.show()
    sys.exit(app.exec_())
