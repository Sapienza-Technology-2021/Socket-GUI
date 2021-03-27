import json
import logging
import socket
import threading
import time

from utils import check_load_json, PORT, InterruptableEvent, init_logger

init_logger()


######################### CLIENT CLASS #########################

class RoverClient:

    def __init__(self):
        self.connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_ip = ""
        self.scan_run = False
        self.discover_socket = None
        self.discover_client_sock = None
        self.commands = []
        self.interface = None
        # threading.Thread(target = self.scan, args=(), daemon=True).start()

    def set_client_controller(self, interface):
        self.interface = interface

    def register_functions(self, commands):
        self.commands = commands

    def ensure_connection(self):
        if self.connected:
            return True
        else:
            if self.interface is not None:
                self.interface.on_disconnection()
            return False

    def scan(self):
        # da implementare la perdita e il reset della connessione
        try:
            self.discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discover_socket.bind(("", 12346))
            self.discover_socket.settimeout(1)
            logging.info("Ack server init")
        except:
            logging.error("Ack server init error")
            time.sleep(0.2)
            self.scan()
        while self.scan_run and not self.connected:
            try:
                self.discover_client_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self.discover_client_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                self.discover_client_sock.sendto(b"<ROVER_DISCOVER>", ("<broadcast>", 12345))
                response, addr = self.discover_socket.recvfrom(1024)
                if response == b"ack":
                    self.server_ip = addr[0]
                    logging.info("Server found: " + self.server_ip)
                    self.connect(self.server_ip, PORT)
            except socket.timeout:
                pass
            except:
                logging.error("Broadcast send error")
                time.sleep(1)
        logging.info("Scan stopped")

    def send(self, data):
        if self.ensure_connection():
            try:
                data = json.dumps(data)
                self.sock.send((data + "\n").encode())
            except:
                logging.error("Send error!")
                self.disconnect()

    def stop_scan(self):
        logging.info("Stopping thread...")
        self.scan_run = False
        if self.discover_socket is not None:
            self.discover_socket.close()
        if self.discover_client_sock is not None:
            self.discover_client_sock.close()

    def parse(self, data):
        try:
            loaded = check_load_json(data)
            if loaded is None:
                return
            for item in self.commands:
                if item in loaded:
                    logging.info(item + " " + str(loaded[item]))
                    if self.interface is not None:
                        getattr(self.interface, item)(loaded[item])
        except json.JSONDecodeError:
            logging.warning("Corrupted Json dictionary!")
        except:
            logging.error("Parsing error!")

    def serverHandler(self):
        logging.info("Handler thread start")
        message = ""
        count = 0
        try:
            while self.connected:
                buffer = self.sock.recv(1024).decode()
                marker = buffer.find("\n")
                if marker >= 0:
                    message += buffer[:marker]
                    logging.info("Client receive")
                    logging.info(message)
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
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            logging.warning("Connection reset")
            self.disconnect()
        except BlockingIOError:
            logging.warning("Blocking IO error")
        except:
            logging.warning("Disconnected")
            self.disconnect()
        logging.info("Server handler stopped.")

    def connect(self, ip, port):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((ip, port))
            logging.info("Connected to server " + ip)
            self.connected = True
            threading.Thread(target=self.serverHandler, args=(), name="Client thread", daemon=True).start()
            self.sock.send(b"<PING>\n")
            return True
        except:
            logging.error("Connection error")
            self.connected = False
            return False

    def isConnected(self):
        return self.connected

    def disconnect(self):
        self.connected = False
        self.sock.close()
        self.stop_scan()
        if self.interface is not None:
            self.interface.on_disconnection()

    ######################### DEF-ROVER #########################

    def move(self, speed):
        self.send({"move": speed})

    def moveRotate(self, speed, degPerMin):
        self.send({"moveRotate": [speed, degPerMin]})

    def rotate(self, angle):
        self.send({"rotate": angle})

    def stop(self):
        self.send({"stop": True})

    def setMLEnabled(self, val):
        self.send({"setMLEnabled": val})

    def setMotorsPowered(self, val):
        self.send({"setMotorsPowered": val})


######################### MAIN #########################

if __name__ == "__main__":
    client = RoverClient()
    event = InterruptableEvent()
    try:
        client.connect("localhost", PORT)
        event.wait()
    except KeyboardInterrupt:
        client.disconnect()
        exit(0)
    except:
        logging.error("Error in main")
        client.disconnect()
        exit(1)
