import inspect
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
from interfaces import debug, InterruptableEvent, PORT, checkLoadJson
import traceback
import socket
import random
import time
import threading
import json


class RoverServer:
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
                print("Chiuso")
                self.conn.close()
                self.conn = None

        def getpeername(self):
            return self.conn.getpeername()

        def recv(self, dataLen):
            if self.isAlive:
                return self.conn.recv(dataLen)

    def __init__(self, port):
        super().__init__()
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

    def serverInit(self):
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
                if len(self.conns) <= 16:
                    thread = threading.Thread(target=self.clientHandler, args=([conn]), daemon=True)
                    thread.start()
                    #anche qui l'inserimento di una connessione deve essere thread safe
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
        while True:
            for i in list(self.conns):
                if not i.isAlive:
                    self.conns[i].join()
                    del self.conns[i]
                    debug("Numero connessioni: " + str(len(self.conns)))

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
        except json.JSONDecodeError:
            debug("Corrupted Json dictionary!")
            traceback.print_exc()
        except Exception:
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
        localcopy = self.conns.copy().keys()
        for conn in localcopy:
            try:
                data = json.dumps(rawData)
                conn.send((data + "\n").encode())
            except:
                print("Send error")
                traceback.print_exc()
                conn.close()
#        self.updateConnsList()

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

    def updateBatt(self):
        self.send({"updateBatt": 100})


if __name__ == "__main__":
    server = None
    batt = 100
    acc = [0,0,0]
    event = InterruptableEvent()
    try:
        server = RoverServer(PORT)
        while True:
            acc = [random.gauss(2,3) for i in range(3)]
            batt -= round(random.random(),2) * 0.1
            if batt < 0:
                batt = 0
            server.send({"updateBatt":batt})
            server.send({"updateAccel":acc})
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
