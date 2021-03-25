######################### IMPORT #########################

import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from utils import debug, PORT, checkLoadJson
import traceback
import socket
import random
import time
import threading
import json
import serial
from serial.tools.list_ports import comports as listSerialPorts

######################### GLOBAL #########################

global lock
lock = threading.RLock()


######################### CODE #########################

class RoverServer:
    ######################### CONNECTION-CLASS #########################
    class Connection:
        def __init__(self, conn):
            self.conn = conn
            self.isAlive = True

        def send(self, x):
            if self.isAlive:
                self.conn.send(x)

        def close(self):
            if self.isAlive:
                self.isAlive = False
                debug("Chiuso")
                self.conn.close()
                self.conn = None

        def getpeername(self):
            return self.conn.getpeername()

        def recv(self, dataLen):
            if self.isAlive:
                return self.conn.recv(dataLen)

    ######################### PYSERIAL-CLASS #########################
    class serialConnection:
        def __init__(self):
            self.serialPort = None
            self.serialConnected = False
            self.startSerialConnection_th()

        def serialPrint(self, message):
            if self.serialPort is not None and self.serialPort.isOpen:
                try:
                    message += "\n"
                    self.serialPort.write(message.encode('utf-8'))
                    self.serialPort.flush()
                except:
                    debug("Could not print serial message!")
            else:
                debug("Serial port not initialized, attempted writing")

        def serialRead(self):
            if self.serialPort is not None and self.serialPort.isOpen:
                try:
                    message = self.serialPort.readline().decode("utf-8").replace("\n", "").replace("\r", "")
                    if (message != ""):
                        return message
                    else:
                        return "Nothing to read"
                except:
                    debug("Could not read serial message!")
                    return ""
            else:
                debug("Serial port not initialized, attempted reading")
                return ""

        def runSerialConnection(self):
            while not self.serialConnected:
                try:
                    debug("Scanning serial ports...")
                    # debug(listSerialPorts())
                    # for port in listSerialPorts():
                    # debug("Trying with " + port.name)
                    for port in listSerialPorts():
                        debug("Trying with " + port.name)
                        try:
                            self.serialPort = serial.Serial(port=port.device, baudrate=9600, timeout=5)
                            # rtscts=True, dsrdtr=True, exclusive=True) chiedere a Marco :)
                        except:
                            debug(port.name + " unavailable.")
                            continue
                        time.sleep(2)
                        self.serialPrint(">C")
                        time.sleep(0.3)
                        response = self.serialRead()
                        debug(response)
                        if response == "C4b7caa5d-2634-44f3-ad62-5ffb1e08d73f":
                            debug(port.device + " connected.")
                            self.serialConnected = True
                            break
                        else:
                            debug("No answer from " + port.name)
                            self.serialPort.close()
                            self.serialPort = None
                except:
                    debug("Unexpected error:", sys.exc_info())
                    debug("Unexpected error, Arduino and the sensors are now disconnected!")
                    # addUserMessage("Server", "Errore inaspettato, sensori e Arduino si sono disconnessi!", MessageType.ERROR)
                    if self.serialPort is not None:
                        self.serialPort.close()
                        self.serialPort = None
                time.sleep(1)
            debug("Sensors-refresh thread stopped")

        def startSerialConnection_th(self):
            th_serialConn = threading.Thread(target=self.runSerialConnection, args=(), daemon=True)
            th_serialConn.start()

        ######################### INIT-SERVER #########################

    def __init__(self, port):
        super().__init__()
        self.serial = self.serialConnection()
        self.ip = ""
        self.port = port
        self.data = {}
        self.conns = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.th_flag = True
        th_server = threading.Thread(target=self.serverInit, args=(), daemon=True)
        th_server.start()
        self.ack_th_flag = True
        ack_th = threading.Thread(target=self.ackServer, args=(), daemon=True)
        ack_th.start()
        threading.Thread(target=self.connectionPool, args=(), daemon=True).start()
        self.mlenabled = False
        threading.Thread(target=self.serialLoopReceive, args=(), daemon=True).start()
        threading.Thread(target=self.updateRequest, args=(), daemon=True).start()

    ######################### DEF-SERIAL #########################

    def serialLoopReceive(self):
        while True:
            if not self.serial.serialConnected:
                time.sleep(2)
            else:
                message = self.serial.serialRead()
                if (message == ""):
                    # avvisa client
                    self.serial.serialConnected = None
                    self.serial.startSerialConnection_th()
                elif (message == "Nothing to read"):
                    pass
                elif (message[0] == ">"):
                    debug(message)
                else:
                    # spacchetta e invia con self.send()
                    if message[0] == "A":
                        x, y, z = message[1:-1].split("%")
                        acc = [float(x) / 100, float(y) / 100, float(z) / 100]
                        debug(acc)
                        self.send({"updateAccel": acc})
                    elif message[0] == "G":
                        x, y, z = message[1:-1].split("%")
                        gir = [float(x) / 100, float(y) / 100, float(z) / 100]
                        debug(gir)
                        self.send({"updateGyro": gir})
                    elif message[0] == "M":
                        x, y, z = message[1:-1].split("%")
                        magn = [float(x) / 100, float(y) / 100, float(z) / 100]
                        debug(magn)
                        self.send({"updateMagn": magn})
                    elif message[0] == "B":
                        batt = float(message[1:-1]) / 100
                        debug(batt)
                        self.send({"updateBatt": batt})
                    elif message[0] == "T":
                        temp = float(message[1:-1]) / 100
                        self.send({"updateCpuTemp": temp})
                    else:
                        debug("Non so come risponderti :(")
                # for command in ["B205%", "A201%451%456%", "M153%454%1332%", "G1522%1234%4355%"]: # riga di test, non serve il for
                #     self.serial.serialPrint(command) ######## RIGA DI TEST

    def updateRequest(self):
        while True:
            if not self.serial.serialConnected:
                time.sleep(2)
            else:
                batt = 100
                acc = [random.randint(0, 100) for i in range(3)]
                magn = [random.randint(0, 100) for i in range(3)]
                gir = [random.randint(0, 100) for i in range(3)]
                batt -= random.randint(0, 101)
                if batt < 0:
                    batt = 0
                for command in [f"B{batt * 100}%", f"A{acc[0] * 100}%{acc[1] * 100}%{acc[2] * 100}%",
                                f"M{magn[0] * 100}%{magn[1] * 100}%{magn[2] * 100}%",
                                f"G{gir[0] * 100}%{gir[1] * 100}%{gir[2] * 100}%"]:  # riga di test
                    # debug(command)
                    self.serial.serialPrint(command)
            time.sleep(2)

    ######################### DEF-SERVER #########################

    def serverInit(self):
        global lock
        debug("Server init...")
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
        except Exception:
            debug("Init error!")
            traceback.print_exc()
            time.sleep(5)
            if self.th_flag is True:
                debug("Init retry...")
                self.serverInit()
        debug("Server in ascolto...")
        try:
            while self.th_flag:
                sock, addr = self.socket.accept()
                conn = self.Connection(sock)
                debug("Client connesso. Indirizzo: " + str(addr[0]))
                with lock:
                    if len(self.conns) <= 16:
                        thread = threading.Thread(target=self.clientHandler, args=([conn]), daemon=True)
                        thread.start()
                        self.conns[conn] = thread
                        conn.send(b"<PING>\n")
                        debug("Numero threads: " + str(len(self.conns)))
                    else:
                        debug("Numero di threads massimo raggiunto!")
                        conn.close()
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            debug("Connection reset")
        except BlockingIOError:
            debug("Blocking IO error")
        except Exception:
            debug("Init error!")
            traceback.print_exc()
        debug("Closing server...")

    def connectionPool(self):
        global lock
        while True:
            with lock:
                for i in list(self.conns):
                    if not i.isAlive:
                        self.conns[i].join()
                        del self.conns[i]
                        debug("Numero connessioni: " + str(len(self.conns)))
            time.sleep(1)

    def disconnect(self):
        debug("Stopping server...")
        self.th_flag = False
        self.ack_th_flag = False
        self.socket.close()

    def parse(self, data):
        try:
            loaded = checkLoadJson(data)
            commands = ["move", "moveRotate", "rotate", "stop", "setMLEnabled"]
            if loaded is None:
                return
            for item in commands:
                if item in loaded:
                    debug(item + " " + str(loaded[item]))
                    getattr(self, item)(loaded[item])
        except json.JSONDecodeError:
            debug("Corrupted Json dictionary!")
            traceback.print_exc()
        except:
            traceback.print_exc()

    def clientHandler(self, conn):
        debug("Handler thread start")
        info = conn.getpeername()[0]
        message = ""
        count = 0
        try:
            while self.th_flag:
                buffer = conn.recv(1024).decode()
                marker = buffer.find("\n")
                if marker >= 0:
                    message += buffer[:marker]
                    debug("Server received: " + message)
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
                # debug(th_data.buffer)
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            debug("Connection reset: " + info)
            conn.close()
        except BlockingIOError:
            debug("Blocking IO error")
        except Exception:
            debug("Disconnesso " + info)
            traceback.print_exc()
            conn.close()
        debug("Client handler stopped.")

    def send(self, rawData):
        global lock
        with lock:
            for conn in self.conns.keys():
                try:
                    data = json.dumps(rawData)
                    conn.send((data + "\n").encode())
                except:
                    debug("Send error")
                    traceback.print_exc()
                    conn.close()

    def ackServer(self):
        try:
            self.ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # ack_socket.settimeout(1.5)
            self.ack_socket.bind(("", 12345))
            debug("ACK server in ascolto")
        except Exception:
            debug("Errore di inizializzazione ACK server")
            traceback.print_exc()
            time.sleep(5)
            if self.ack_th_flag is True:
                debug("ACK init retry...")
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
            debug("ACK timeout.")
        except Exception:
            debug("Errore riscontrato in ACK server")
            traceback.print_exc()
        debug("Quitting ACK server...")

    ######################### DEF-ROVER #########################

    def setMLEnabled(self, val):
        self.mlenabled = val
        self.send({"setMLEnabled": self.mlenabled})

    # funzioni motori

    def move(self, speed):
        debug(f"Movimento con velocità: {str(speed)}")
        self.serial.serialPrint(f">M{str(int(speed * 100))}%")
        # self.send({"move": speed})

    def moveRotate(self, moveRotateVect):
        speed = moveRotateVect[0]  # Cambiare speed (ovunque) con metri
        degPerMin = moveRotateVect[1]
        debug(f"Movimento con velocità {str(speed)} e rotazione {str(degPerMin)}")
        self.serial.serialPrint(f">W{str(int(speed * 100))}%{str(int(degPerMin * 100))}%")
        # self.send({"moveRotate": [speed, degPerMin]})

    def moveToStop(self):
        debug("Movimento fino a stop")
        self.serial.serialPrint(">m%")
        # da implementare nell' interfaccia un pulsante di movimento senza parametri (da aggiungere poi ai commands del parse qui nel server)

    def setSpeed(self, speed):
        debug(f"Velocità massima impostata a: {str(int(speed * 100))}")
        self.serial.serialPrint(f">V{str(int(speed * 100))}%")
        # da implementare nell' interfaccia un pulsante di movimento senza parametri (da aggiungere poi ai commands del parse qui nel server)

    def setSpeedPWM(self, speedPWM):
        debug(f"Movimento con velocità: {str(speedPWM)} PWM")
        self.serial.serialPrint(f">v{str(int(speedPWM * 100))}%")
        # da implementare nell' interfaccia un pulsante di movimento senza parametri (da aggiungere poi ai commands del parse qui nel server)

    def rotate(self, angle):
        debug(f"Rotazione di {str(angle)}")
        self.serial.serialPrint(f">A{str(int(angle * 100))}%")
        # self.send({"rotate": angle})

    def stop(self, value):
        debug("Stop rover")
        self.serial.serialPrint(">S")
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
        traceback.print_exc()
        if server is not None:
            server.disconnect()
        exit(1)
