import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from utils import PORT, ROVER_UUID, check_load_json, init_logger, InterruptableEvent
import socket
import time
import threading
import json
import logging
import serial
from serial.tools.list_ports import comports as list_serial_ports

init_logger()


def get_array_from_message(msg):
    x, y, z = msg[1:-1].split("%")
    return [float(x), float(y), float(z)]


######################### CONNECTION UTILITY CLASS #########################

class ClientConnection:
    def __init__(self, conn):
        self.conn = conn
        self.alive = True

    def send(self, x):
        if self.alive:
            self.conn.send(x)

    def close(self):
        if self.alive:
            self.alive = False
            logging.info("Closed client")
            self.conn.close()
            self.conn = None

    def get_peer_name(self):
        return self.conn.getpeername()

    def recv(self, dataLen):
        if self.alive:
            return self.conn.recv(dataLen)


######################### SERVER #########################

class RoverServer:

    def __init__(self, port):
        self.running = True
        self.serialPort = None
        self.serialConnected = False
        self.machine_learning_en = False
        self.motor_power_on = False
        self.port = port
        self.data = {}
        self.conns = {}
        self.ack_socket = None
        self.lock = threading.Lock()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        threading.Thread(target=self.server_loop, name="Server", args=(), daemon=True).start()
        threading.Thread(target=self.ack_server_loop, name="Ack server", args=(), daemon=True).start()
        threading.Thread(target=self.clients_garbage_collector, name="Garbage collector", args=(), daemon=True).start()
        threading.Thread(target=self.serial_loop, name="Serial loop", args=(), daemon=True).start()

    ######################### SERIAL PORT #########################

    def serial_read_line(self):
        if self.serialPort is not None and self.serialPort.isOpen:
            message = self.serialPort.readline().decode("utf-8").replace("\n", "").replace("\r", "")
            if message == "":
                return None
            else:
                return message
        else:
            logging.warning("Serial port not initialized, attempted reading")
            return None

    def serial_println(self, message):
        if self.serialPort is not None and self.serialPort.isOpen:
            try:
                self.serialPort.write((message + "\n").encode('utf-8'))
                self.serialPort.flush()
            except:
                logging.error("Could not print serial message!")
        else:
            logging.warning("Serial port not initialized, attempted writing")

    def serial_loop(self):
        while self.running:
            try:
                logging.info("Scanning serial ports...")
                for port in list_serial_ports():
                    logging.info("Attempting connection with " + port.name)
                    try:
                        self.serialPort = serial.Serial(port=port.device, baudrate=115200,
                                                        timeout=4, rtscts=True, dsrdtr=True, exclusive=True)
                    except:
                        logging.warning(port.name + " unavailable.")
                        continue
                    time.sleep(1)
                    self.serial_println(">C")
                    time.sleep(0.3)
                    start_time = time.time()
                    while self.serialPort is not None and self.running and self.serialPort.in_waiting:
                        response = self.serial_read_line()
                        if response is None:
                            self.serial_println(">C")
                        else:
                            logging.info("Board replied \"" + response + "\"")
                        if response[1:] == ROVER_UUID:
                            logging.info(port.device + " connected.")
                            self.serial_println(">E0")  # Motors OFF
                            self.motor_power_on = False
                            self.socket_broadcast({"setMotorsPowered": self.motor_power_on})
                            # TODO(Marco): velocità solo per provare
                            self.serial_println(">V200")
                            self.serialConnected = True
                            while self.running:
                                msg = self.serial_read_line()
                                if msg is None:
                                    time.sleep(0.3)
                                elif msg[0] == "L":
                                    logging.info("Serial log: " + msg)
                                elif msg[0] == "A":
                                    array = get_array_from_message(msg)
                                    logging.info("Accelerometer data " + str(array))
                                    self.socket_broadcast({"updateAccel": array})
                                elif msg[0] == "G":
                                    array = get_array_from_message(msg)
                                    logging.info("Gyroscope data " + str(array))
                                    self.socket_broadcast({"updateGyro": array})
                                elif msg[0] == "M":
                                    current, target = msg[1:-1].split("%")
                                    array = [float(current), float(target)]
                                    logging.info("Compass data " + str(array))
                                    self.socket_broadcast({"updateCompass": array})
                                elif msg[0] == "B":
                                    battery = float(msg[1:-1])
                                    logging.info("Battery level: " + str(battery))
                                    self.socket_broadcast({"updateBattery": battery})
                                elif msg[0] == "T":
                                    temp = float(msg[1:-1])
                                    logging.info("IMU temperature: " + str(temp))
                                    self.socket_broadcast({"updateIMUTemp": temp})
                                elif msg[0] == "D":
                                    dist = float(msg[1:-1])
                                    logging.info("Distance: " + str(dist))
                                    self.socket_broadcast({"updateDistance": dist})
                                else:
                                    logging.warning("Unknown message: " + msg)
                        elif (time.time() - start_time) >= 5000:
                            logging.info("No answer from " + port.name)
                            self.serialPort.close()
                            self.serialPort = None
            except:
                logging.error("Unexpected error, Arduino is now disconnected!")
                if self.serialPort is not None:
                    self.serialPort.close()
                    self.serialPort = None
            time.sleep(2)
        logging.info("Serial loop stopped")

    ######################### SOCKET CONNECTION #########################

    def server_loop(self):
        logging.info("Server init...")
        try:
            # socket.gethostname()
            self.socket.bind(("", self.port))
            self.socket.listen()
        except Exception:
            logging.error("Init error!")
            time.sleep(5)
            if self.running is True:
                logging.info("Init retry...")
                self.server_loop()
        logging.info("Server listening...")
        try:
            while self.running:
                sock, addr = self.socket.accept()
                conn = ClientConnection(sock)
                logging.info("Client connected: " + str(addr[0]))
                with self.lock:
                    if len(self.conns) <= 16:
                        thread = threading.Thread(target=self.client_handler,
                                                  name="Client handler", args=([conn]), daemon=True)
                        thread.start()
                        self.conns[conn] = thread
                        conn.send(b"<PING>\n")
                        conn.send((json.dumps({"setMotorsPowered": self.motor_power_on}) + "\n").encode())
                        logging.info("Threads count: " + str(len(self.conns)))
                    else:
                        logging.warning("Max clients count!")
                        conn.close()
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            logging.warning("Connection reset")
        except BlockingIOError:
            logging.warning("Blocking IO error")
        except:
            logging.error("Init error!")
        logging.info("Closing server...")

    def clients_garbage_collector(self):
        while self.running:
            with self.lock:
                for conn in list(self.conns):
                    if not conn.alive:
                        self.conns[conn].join()
                        del self.conns[conn]
                        logging.info("Connections count: " + str(len(self.conns)))
            time.sleep(1)

    def disconnect(self):
        logging.info("Stopping server...")
        self.running = False
        self.socket.close()

    def parse(self, data):
        logging.info("Socket message received: " + data)
        try:
            loaded = check_load_json(data)
            commands = ["move", "setSpeed", "moveRotate", "rotate", "stop", "setMLEnabled",
                        "setMotorsPowered", "moveTime"]
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

    def client_handler(self, conn):
        logging.info("Handler thread start")
        info = conn.get_peer_name()[0]
        message = ""
        count = 0
        try:
            while self.running:
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

    def socket_broadcast(self, rawData):
        with self.lock:
            for conn in self.conns.keys():
                try:
                    data = json.dumps(rawData)
                    conn.send((data + "\n").encode())
                except:
                    logging.error("Send error")
                    conn.close()

    def ack_server_loop(self):
        try:
            self.ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # ack_socket.settimeout(1.5)
            self.ack_socket.bind(("", 12345))
            logging.info("Ack server listening")
        except:
            logging.error("Ack server init error")
            time.sleep(5)
            if self.running is True:
                logging.info("ACK init retry...")
                self.ack_server_loop()
        try:
            while self.running:
                response, addr = self.ack_socket.recvfrom(1024)
                if response == b"<ROVER_DISCOVER>":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((addr[0], 12346))
                    s.send(b"ack")
                    s.close()
        except socket.timeout:
            logging.info("Ack timeout.")
        except:
            logging.error("Ack server error")
        logging.info("Quitting Ack server...")

    ######################### ROVER METHODS #########################

    def setMLEnabled(self, val):
        self.machine_learning_en = val
        self.socket_broadcast({"setMLEnabled": self.machine_learning_en})

    def moveTime(self, time):
        logging.info(f"Movimento sostenuto per: {str(time)} secondi")
        self.serial_println(f">T{str(int(time))}%")

    def move(self, dist):
        logging.info(f"Movimento per {str(dist)} metri")
        self.serial_println(f">M{str(int(dist))}%")

    def moveRotate(self, moveRotateVect):
        speed = moveRotateVect[0]  # Cambiare speed (ovunque) con metri
        deg_per_min = moveRotateVect[1]
        logging.info(f"Movimento con velocità {str(speed)} e rotazione {str(deg_per_min)}")
        self.serial_println(f">W{str(int(speed * 100))}%{str(int(deg_per_min * 100))}%")

    def moveToStop(self):
        logging.info("Movimento fino a stop")
        self.serial_println(">m%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def setSpeed(self, speed):
        logging.info(f"Velocità massima impostata a: {str(int(speed * 100))}")
        self.serial_println(f">V{str(int(speed * 100))}%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def setSpeedPWM(self, speedPWM):
        logging.info(f"Movimento con velocità: {str(speedPWM)} PWM")
        self.serial_println(f">v{str(int(speedPWM * 100))}%")
        # Da implementare nell' interfaccia un pulsante di movimento senza parametri
        # (da aggiungere poi ai commands del parse qui nel server)

    def rotate(self, angle):
        logging.info(f"Rotazione di {str(angle)}")
        self.serial_println(f">A{str(int(angle * 100))}%")

    def stop(self):
        logging.info("Stop rover")
        self.serial_println(">S")

    def setMotorsPowered(self, val):
        self.motor_power_on = val
        if self.motor_power_on:
            logging.info("Motors powered up")
        else:
            logging.info("Motors powered down")
        self.serial_println(">E" + str(int(val)))
        self.socket_broadcast({"setMotorsPowered": self.motor_power_on})


######################### MAIN #########################

if __name__ == "__main__":
    server = None
    event = InterruptableEvent()
    try:
        server = RoverServer(PORT)
        event.wait()
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
