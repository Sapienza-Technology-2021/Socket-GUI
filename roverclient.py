import json
import socket
import threading
import time
import traceback

from utils import checkLoadJson, debug, PORT, InterruptableEvent


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

    def setControllerInterface(self, interface):
        self.interface = interface

    def registerFunctions(self, cmds):
        self.commands = cmds

    def ensureConnection(self):
        if self.connected:
            return True
        else:
            if self.interface is not None:
                self.interface.onDisconnect()
            return False

    def scan(self):
        # da implementare la perdita e il reset della connessione
        try:
            self.discover_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.discover_socket.bind(("", 12346))
            self.discover_socket.settimeout(1)
            print("ACK SERVER in ascolto")
        except:
            traceback.print_exc()
            print("Errore di inizializzazione acknowledgment server")
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
                    print("Server trovato: ", self.server_ip)
                    self.connect(self.server_ip, PORT)
            except socket.timeout:
                pass
            except:
                traceback.print_exc()
                print("Errore riscontrato nell'invio di pacchetti broadcast")
                time.sleep(1)
        print("Scan stopped")

    def send(self, data):
        if self.ensureConnection():
            try:
                data = json.dumps(data)
                self.sock.send((data + "\n").encode())
            except:
                print("Send error")
                traceback.print_exc()
                self.disconnect()

    def stopScan(self):
        print("Stopping thread...")
        self.scan_run = False
        if self.discover_socket is not None:
            self.discover_socket.close()
        if self.discover_client_sock is not None:
            self.discover_client_sock.close()

    def parse(self, data):
        try:
            loaded = checkLoadJson(data)
            if loaded is None:
                return
            for item in self.commands:
                if item in loaded:
                    debug(item + " " + str(loaded[item]))
                    if self.interface is not None:
                        getattr(self.interface, item)(loaded[item])
        except json.JSONDecodeError:
            debug("Corrupted Json dictionary!")
            traceback.print_exc()
        except Exception as e:
            traceback.print_exc()

    def serverHandler(self):
        debug("Handler thread start")
        message = ""
        count = 0
        try:
            while self.connected:
                buffer = self.sock.recv(1024).decode()
                marker = buffer.find("\n")
                if marker >= 0:
                    message += buffer[:marker]
                    debug("Client receive")
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
        except (ConnectionResetError, ConnectionAbortedError, socket.timeout):
            debug("Connection reset")
            self.disconnect()
        except BlockingIOError:
            debug("Blocking IO error")
        except:
            debug("Disconnesso")
            traceback.print_exc()
            self.disconnect()
        debug("Server handler stopped.")

    def connect(self, ip, port):
        try:
            self.sock.connect((ip, port))
            print("Connesso al server: ", ip)
            self.connected = True
            threading.Thread(target=self.serverHandler, args=(), daemon=True).start()
            self.sock.send(b"<PING>\n")
            return True
        except:
            traceback.print_exc()
            print("Errore riscontrato in fase di connessione")
            self.connected = False
            return False

    def isConnected(self):
        return self.connected

    def disconnect(self):
        self.connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.stopScan()
        if self.interface is not None:
            self.interface.onDisconnect()

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


# Debug
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
        traceback.print_exc()
        client.disconnect()
        exit(1)
