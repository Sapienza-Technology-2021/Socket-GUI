import os, sys, inspect
currentdir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parentdir = os.path.dirname(currentdir)
sys.path.insert(0, parentdir) 
from interfaces import debug, InterruptableEvent, PORT, checkLoadJson
from threading import Event
import traceback
import socket
import time
import threading
import sys
import json


class RoverServer():
    class Connection:
        def __init__(self,conn):
            self.conn = conn
            self.isAlive = True
        def send(self,x):
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
        def recv(self,len):
            if self.isAlive:
                return self.conn.recv(len)
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

    def serverInit(self):
        debug("Server init...")
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.listen()
        except Exception as e:
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
                    self.conns[conn] = thread
                    conn.send(b"<PING>\n")
                    debug("Numero threads: " + str(len(self.conns)))
                else:
                    debug("Numero di threads massimo raggiunto!")
                    conn.close()
                for i in list(self.conns):
                    if not i.isAlive:
                        self.conns[i].join()
                        del self.conns[i]
                        debug("Numero connessioni: " + str(len(self.conns)))
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            debug("Connection reset")
        except BlockingIOError:
            debug("Blocking IO error")
        except Exception as e:
            debug("Init error!")
            traceback.print_exc()
        debug("Closing server...")

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
                if(item in loaded):
                    debug(item + " " + str(loaded[item]))

        except json.JSONDecodeError:
            debug("Corrupted Json dictionary!")
            traceback.print_exc()
        except Exception as e:
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
                    debug("Server receive")
                    debug(message)
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
                #debug(th_data.buffer)
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            debug("Connection reset: " + info)
            conn.close()
        except BlockingIOError:
            debug("Blocking IO error")
        except Exception as e:
            debug("Disconnesso " + info)
            traceback.print_exc()
            conn.close()
        debug("Client handler stopped.")

    def send(self, rawData):
        for conn in self.conns.keys():
            try:
                data = json.dumps(rawData)
                conn.send((data + "\n").encode())
            except:
                print("Send error")
                traceback.print_exc()
                conn.close()

    def ackServer(self):
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            #ack_socket.settimeout(1.5)
            ack_socket.bind(("", 12345))
            debug("ACK server in ascolto")
        except Exception as e:
            debug("Errore di inizializzazione ACK server")
            traceback.print_exc()
            time.sleep(5)
            if self.ack_th_flag is True:
                debug("ACK init retry...")
                self.ack_server()
        try:
            while self.ack_th_flag:
                response, addr = ack_socket.recvfrom(1024)
                if response == b"<ROVER_DISCOVER>":
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((addr[0], 12346))
                    s.send(b"ack")
                    s.close()
        except socket.timeout:
            debug("ACK timeout.")
        except Exception as e:
            debug("Errore riscontrato in ACK server")
            traceback.print_exc()
        debug("Quitting ACK server...")

    def updateBatt(self):
        #quando una connessione si chiude il server non modifica il pool delle connessioni e tenta di inviare su socket già chiusi
        if len(self.conns) > 0:
            print(len(self.conns))
            self.send({"updateBatt": 100})

if __name__ == "__main__":
    server = None
    event = InterruptableEvent()
    try:
        server = RoverServer(PORT)
        while True:
            server.updateBatt()
            time.sleep(5)
    except KeyboardInterrupt:
        print("KeyboardInterrupt")
        if server is not None:
            server.disconnect()
        exit(0)
    except Exception as e:
        traceback.print_exc()
        if server is not None:
            server.disconnect()
        exit(1)
