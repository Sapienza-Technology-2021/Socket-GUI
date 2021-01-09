import sys
import time
import socket
import threading
import traceback
import json
from interfaces import checkLoadJson, ControllerInterface, RoverInterface, debug, APP_NAME, PORT, InterruptableEvent


class RoverClient(RoverInterface):
    def __init__(self):
        super(RoverClient, self).__init__()
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_ip = ""
        self.scan_run = False
        self.discover_socket = None
        self.discover_client_sock = None
        #threading.Thread(target = self.scan, args=(), daemon=True).start()

    def scan(self):
        #da implementare la perdita e il reset della connessione
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
                print("Unexpected error:", sys.exc_info()[0])
                time.sleep(1)
        print("Scan stopped")

    def send(self, data):
        self.ensureConnection()
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
            if "updateAccel" in loaded:
                debug("updateAccel " + str(loaded["updateAccel"]))
            if "updateGyro" in loaded:
                debug("updateGyro " + str(loaded["updateGyro"]))
            if "updateMagn" in loaded:
                debug("updateMagn " + str(loaded["updateMagn"]))
            if "updateIrDistance" in loaded:
                debug("updateIrDistance " + str(loaded["updateIrDistance"]))
            if "updateBatt" in loaded:
                debug("updateBatt " + str(loaded["updateBatt"]))
            if "updateCpuTemp" in loaded:
                debug("updateCpuTemp " + str(loaded["updateCpuTemp"]))
            if "updateRPMFeedback" in loaded:
                debug("updateRPMFeedback " + str(loaded["updateRPMFeedback"]))
            if "setMLEnabled" in loaded:
                debug("Set ML " + str(loaded["setMLEnabled"]))
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
        except Exception as e:
            debug("Disconnesso")
            traceback.print_exc()
            self.disconnect()
        debug("Server handler stopped.")

    def connect(self, ip, port):
        super(RoverClient, self).connect(ip, port)
        try:
            self.sock.connect((ip, port))
            print("Connesso al server: ", ip)
            self.connected = True
            threading.Thread(target = self.serverHandler, args=()).start()
            self.sock.send(b"<PING>\n")
            return True
        except:
            traceback.print_exc()
            print("Errore riscontrato in fase di connessione")
            self.connected = False
            return False

    def disconnect(self):
        super(RoverClient, self).disconnect()
        self.connected = False
        self.stopScan()
        if self.sock is not None:
            self.sock.close()

    def move(self, speed):
        super(RoverClient, self).move(speed)
        self.send({"move": speed})

    def moveRotate(self, speed, degPerMin):
        super(RoverClient, self).moveRotate(speed, degPerMin)
        self.send({"moveRotate": [speed, degPerMin]})

    def rotate(self, angle):
        super(RoverClient, self).rotate(angle)
        self.send({"rotate": angle})

    def stop(self):
        super(RoverClient, self).stop()
        self.send({"stop": True})

    def setMLEnabled(self, val):
        super(RoverClient, self).setMLEnabled(val)
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
    except Exception as e:
        traceback.print_exc()
        client.disconnect()
        exit(1)
