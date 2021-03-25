######################### IMPORT #########################

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from utils import PORT, check_load_json, init_logger
import socket
import random
import time
import threading
import json
import logging
import serial
from serial.tools.list_ports import comports as list_serial_ports

######################### GLOBAL #########################

init_logger()

global lock
# noinspection PyRedeclaration
lock = threading.RLock()


######################### CONNECTION UTILITY CLASS #########################

class ClientConnection:
    def __init__(self, conn):
        self.conn = conn
        self.isAlive = True

    def send(self, x):
        if self.isAlive:
            self.conn.send(x)

    def close(self):
        if self.isAlive:
            self.isAlive = False
            logging.info("Chiuso")
            self.conn.close()
            self.conn = None

    def get_peer_name(self):
        return self.conn.get_peer_name()

    def recv(self, dataLen):
        if self.isAlive:
            return self.conn.recv(dataLen)


######################### SERIAL CONNECTION #########################

class SerialConnection:
    def __init__(self):
        self.serialPort = None
        self.serialConnected = False
        self.start_serial_thread()

    def println(self, message):
        if self.serialPort is not None and self.serialPort.isOpen:
            try:
                self.serialPort.write((message + "\n").encode('utf-8'))
                self.serialPort.flush()
            except:
                logging.error("Could not print serial message!")
        else:
            logging.warning("Serial port not initialized, attempted writing")

    def read(self):
        if self.serialPort is not None and self.serialPort.isOpen:
            try:
                message = self.serialPort.readline().decode("utf-8").replace("\n", "").replace("\r", "")
                if message != "":
                    return message
                else:
                    return "Nothing to read"
            except:
                logging.error("Could not read serial message!")
                return ""
        else:
            logging.warning("Serial port not initialized, attempted reading")
            return ""

    def run_serial_loop(self):
        while not self.serialConnected:
            try:
                logging.info("Scanning serial ports...")
                # logging.info(listSerialPorts())
                # for port in listSerialPorts():
                # logging.info("Trying with " + port.name)
                for port in list_serial_ports():
                    logging.info("Trying with " + port.name)
                    try:
                        self.serialPort = serial.Serial(port=port.device, baudrate=115200,
                                                        timeout=5, rtscts=True, dsrdtr=True, exclusive=True)
                    except:
                        logging.warning(port.name + " unavailable.")
                        continue
                    time.sleep(2)
                    self.println(">C")
                    time.sleep(0.3)
                    response = self.read()
                    logging.info(response)
                    if response == "C4b7caa5d-2634-44f3-ad62-5ffb1e08d73f":
                        logging.info(port.device + " connected.")
                        self.serialConnected = True
                        break
                    else:
                        logging.info("No answer from " + port.name)
                        self.serialPort.close()
                        self.serialPort = None
            except:
                logging.error("Unexpected error, Arduino is now disconnected!")
                if self.serialPort is not None:
                    self.serialPort.close()
                    self.serialPort = None
            time.sleep(1)
        logging.info("Serial loop stopped")

    def start_serial_thread(self):
        threading.Thread(target=self.run_serial_loop, args=(), name="Serial find", daemon=True).start()


######################### SERVER #########################

class RoverServer:

    def __init__(self, port):
        self.serial = SerialConnection()
        self.ip = ""
        self.port = port
        self.data = {}
        self.conns = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.th_flag = True
        th_server = threading.Thread(target=self.serverInit, name="Server", args=(), daemon=True)
        th_server.start()
        self.ack_th_flag = True
        ack_th = threading.Thread(target=self.ackServer, name="Ack server", args=(), daemon=True)
        ack_th.start()
        threading.Thread(target=self.connectionPool, name="Connect pool", args=(), daemon=True).start()
        self.machine_learning_en = False
        threading.Thread(target=self.serialLoopReceive, name="Serial loop", args=(), daemon=True).start()
        threading.Thread(target=self.updateRequest, args=(), name="Update request", daemon=True).start()

    ######################### DEF-SERIAL #########################

    def serialLoopReceive(self):
        while True:
            if not self.serial.serialConnected:
                time.sleep(2)
            else:
                message = self.serial.read()
                if message == "":
                    # avvisa client
                    self.serial.serialConnected = None
                    self.serial.start_serial_thread()
                elif message == "Nothing to read":
                    pass
                elif message[0] == ">":
                    logging.info(message)
                else:
                    # spacchetta e invia con self.send()
                    if message[0] == "A":
                        x, y, z = message[1:-1].split("%")
                        acc = [float(x) / 100, float(y) / 100, float(z) / 100]
                        logging.info(acc)
                        self.send({"updateAccel": acc})
                    elif message[0] == "G":
                        x, y, z = message[1:-1].split("%")
                        gir = [float(x) / 100, float(y) / 100, float(z) / 100]
                        logging.info(gir)
                        self.send({"updateGyro": gir})
                    elif message[0] == "M":
                        x, y, z = message[1:-1].split("%")
                        magn = [float(x) / 100, float(y) / 100, float(z) / 100]
                        logging.info(magn)
                        self.send({"updateMagn": magn})
                    elif message[0] == "B":
                        batt = float(message[1:-1]) / 100
                        logging.info(batt)
                        self.send({"updateBatt": batt})
                    elif message[0] == "T":
                        temp = float(message[1:-1]) / 100
                        self.send({"updateCpuTemp": temp})
                    else:
                        logging.info("Non so come risponderti :(")
                # for command in ["B205%", "A201%451%456%", "M153%454%1332%", "G1522%1234%4355%"]: # riga di test, non serve il for
                #     self.serial.serialPrint(command) ######## RIGA DI TEST

    def updateRequest(self):
        while True:
            if not self.serial.serialConnected:
                time.sleep(2)
            else:
                batt = 100
                acc = [random.randint(0, 100) for _ in range(3)]
                magn = [random.randint(0, 100) for _ in range(3)]
                gir = [random.randint(0, 100) for _ in range(3)]
                batt -= random.randint(0, 101)
                if batt < 0:
                    batt = 0
                for command in [f"B{batt * 100}%", f"A{acc[0] * 100}%{acc[1] * 100}%{acc[2] * 100}%",
                                f"M{magn[0] * 100}%{magn[1] * 100}%{magn[2] * 100}%",
                                f"G{gir[0] * 100}%{gir[1] * 100}%{gir[2] * 100}%"]:  # riga di test
                    # logging.info(command)
                    self.serial.println(command)
            time.sleep(2)

    ######################### DEF-SERVER #########################

    def serverInit(self):
        global lock
        logging.info("Server init...")
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
        except Exception:
            logging.error("Init error!")
            time.sleep(5)
            if self.th_flag is True:
                logging.info("Init retry...")
                self.serverInit()
        logging.info("Server in ascolto...")
        try:
            while self.th_flag:
                sock, addr = self.socket.accept()
                conn = ClientConnection(sock)
                logging.info("Client connesso. Indirizzo: " + str(addr[0]))
                with lock:
                    if len(self.conns) <= 16:
                        thread = threading.Thread(target=self.clientHandler,
                                                  name="Client handler", args=([conn]), daemon=True)
                        thread.start()
                        self.conns[conn] = thread
                        conn.send(b"<PING>\n")
                        logging.info("Numero threads: " + str(len(self.conns)))
                    else:
                        logging.info("Numero di threads massimo raggiunto!")
                        conn.close()
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            logging.warning("Connection reset")
        except BlockingIOError:
            logging.warning("Blocking IO error")
        except:
            logging.error("Init error!")
        logging.info("Closing server...")

    def connectionPool(self):
        global lock
        while True:
            with lock:
                for i in list(self.conns):
                    if not i.isAlive:
                        self.conns[i].join()
                        del self.conns[i]
                        logging.info("Numero connessioni: " + str(len(self.conns)))
            time.sleep(1)

    def disconnect(self):
        logging.info("Stopping server...")
        self.th_flag = False
        self.ack_th_flag = False
        self.socket.close()

    def parse(self, data):
        try:
            loaded = check_load_json(data)
            commands = ["move", "moveRotate", "rotate", "stop", "setMLEnabled"]
            if loaded is None:
                return
            for item in commands:
                if item in loaded:
                    logging.info(item + " " + str(loaded[item]))
                    getattr(self, item)(loaded[item])
        except json.JSONDecodeError:
            logging.warning("Corrupted Json dictionary!")
        except:
            logging.error("Parsing error!")

    def clientHandler(self, conn):
        logging.info("Handler thread start")
        info = conn.get_peer_name()[0]
        message = ""
        count = 0
        try:
            while self.th_flag:
                buffer = conn.recv(1024).decode()
                marker = buffer.find("\n")
                if marker >= 0:
                    message += buffer[:marker]
                    logging.info("Server received: " + message)
                    self.parse(message)
                    message = ""
                    count = 0
                else:
                    count += 1
                    if count > 1000:
                        raise socket.timeout
                    message += buffer
                if buffer == b"":
                    raise Exception
                # logging.info(th_data.buffer)
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            logging.warning("Connection reset: " + info)
            conn.close()
        except BlockingIOError:
            logging.warning("Blocking IO error")
        except:
            logging.error("Disconnesso " + info)
            conn.close()
        logging.info("Client handler stopped.")

    def send(self, rawData):
        global lock
        with lock:
            for conn in self.conns.keys():
                try:
                    data = json.dumps(rawData)
                    conn.send((data + "\n").encode())
                except:
                    logging.error("Send error")
                    conn.close()

    def ackServer(self):
        try:
            self.ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # ack_socket.settimeout(1.5)
            self.ack_socket.bind(("", 12345))
            logging.info("ACK server in ascolto")
        except:
            logging.error("Errore di inizializzazione ACK server")
            time.sleep(5)
            if self.ack_th_flag is True:
                logging.info("ACK init retry...")
                self.ackServer()
        try:
            while self.ack_th_flag:
                response, addr = self.ack_socket.recvfrom(1024)
                if response == b"<ROVER_DISCOVER>":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((addr[0], 12346))
                    s.send(b"ack")
                    s.close()
        except socket.timeout:
            logging.info("ACK timeout.")
        except:
            logging.error("Errore riscontrato in ACK server")
        logging.info("Quitting ACK server...")

    ######################### DEF-ROVER #########################

    def setMLEnabled(self, val):
        self.machine_learning_en = val
        self.send({"setMLEnabled": self.machine_learning_en})

    # funzioni motori

    def move(self, speed):
        logging.info(f"Movimento con velocità: {str(speed)}")
        self.serial.println(f">M{str(int(speed * 100))}%")
        # self.send({"move": speed})

    def moveRotate(self, moveRotateVect):
        speed = moveRotateVect[0]  # Cambiare speed (ovunque) con metri
        deg_per_min = moveRotateVect[1]
        logging.info(f"Movimento con velocità {str(speed)} e rotazione {str(deg_per_min)}")
        self.serial.println(f">W{str(int(speed * 100))}%{str(int(deg_per_min * 100))}%")
        # self.send({"moveRotate": [speed, deg_per_min]})

    def moveToStop(self):
        logging.info("Movimento fino a stop")
        self.serial.println(">m%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def setSpeed(self, speed):
        logging.info(f"Velocità massima impostata a: {str(int(speed * 100))}")
        self.serial.println(f">V{str(int(speed * 100))}%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def setSpeedPWM(self, speedPWM):
        logging.info(f"Movimento con velocità: {str(speedPWM)} PWM")
        self.serial.println(f">v{str(int(speedPWM * 100))}%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def rotate(self, angle):
        logging.info(f"Rotazione di {str(angle)}")
        self.serial.println(f">A{str(int(angle * 100))}%")
        # self.send({"rotate": angle})

    def stop(self):
        logging.info("Stop rover")
        self.serial.println(">S")
        # self.send({"stop": True})


# thread di aggiornamento sensori

# def updateAll(self):
#     batt = 100
#     acc = [0, 0, 0]
#     while True:
#         acc = [random.gauss(2, 3) for i in range(3)]
#         batt -= round(random.random(), 2) * 0.1
#         if batt < 0:
#             batt = 0
#         self.send({"updateBatt": batt})
#         self.send({"updateAccel": acc})
#         time.sleep(0.2)

######################### MAIN #########################

if __name__ == "__main__":
    server = None
    try:
        server = RoverServer(PORT)
        # threading.Thread(target = server.updateAll, args=(), daemon=True).start()
        while True:
            time.sleep(0.2)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        if server is not None:
            server.disconnect()
        exit(0)
    except:
        logging.error("Error in main")
        if server is not None:
            server.disconnect()
        exit(1)
