#Client
import sys
import time
import socket
import threading
import traceback
import json
from interfaces import ControllerInterface, RoverInterface, debug, APP_NAME, PORT


class RoverClient(RoverInterface):
    def __init__(self):
        super(RoverClient, self).__init__()
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.server_ip = ""
        self.scanth_flag = 0
        self.client_th_flag = 0
        th = threading.Thread(target = self.client, args=())
        th.start()
        #self.scan_th()

    def scan(self):
        #da implementare la perdita e il reset della connessione
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.bind(("", 12346))
            ack_socket.settimeout(1)
            print("ACK SERVER in ascolto")
        except:
            traceback.print_exc()
            print("Errore di inizializzazione acknowledgment server")
            time.sleep(0.2)
            self.scan()
        while True:
            if not self.connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.sendto(b"discover", ("<broadcast>",12345))
                    response, addr = ack_socket.recvfrom(1024)
                    if response == b"ack":
                        self.server_ip = addr[0]
                        print("Server trovato: ",self.server_ip)
                        self.connect(self.server_ip, PORT)
                except socket.timeout:
                    pass
                except:
                    traceback.print_exc()
                    print("Errore riscontrato nell'invio di pacchetti broadcast")
                    print("Unexpected error:", sys.exc_info()[0])
                    time.sleep(1)
                    
            else:
                #possibile implementare qui un check a cadenza regolare per verificare la presenza del server
                #oltre al riconoscimento tramite eccezioni sui metodi recv e send
                time.sleep(1)

            if(self.scanth_flag==1):
                self.scanth_flag = 0
                print("Quitting...")
                exit(0)
    
    def recv(self):
        if self.connected:
            try:
                pass
            except:
                pass
            #ricevi dati

    def send(self, data):
        self.ensureConnection()
        try:
            data = json.dumps(data)
            self.sock.send((data + "\n").encode())
        except:
            print("Send error")
            traceback.print_exc()
            self.disconnect()

    def stopscan(self):
        print("Stopping thread...")
        self.scanth_flag = 1

    def scan_th(self):
        th = threading.Thread(target = self.scan, args=())
        th.start()
    
    def client(self):
        try:
            while self.connected:
                data = self.sock.recv(1024)
                if data != b"":
                    print(data)
                else:
                    self.disconnect()
        except:
            self.disconnect()

    def manual_scan(self):
        #itera tutta la subnet sulla porta desiderata
        pass

    def connect(self, ip, port):
        super(RoverClient, self).connect(ip, port)
        try:
            self.sock.connect((ip, port))
            self.sock.send(b"first data")
            print("Connesso al server: ", ip)
            self.connected = True
        except:
            traceback.print_exc()
            print("Errore riscontrato in fase di connessione")
            self.connected = False
        return self.connected

    def disconnect(self):
        super(RoverClient, self).disconnect()
        # Disconnetti socket

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
    class Qt:
        def __init__(self):
            connection = RoverClient(self)
            while True:
                try:
                    time.sleep(1)
                except KeyboardInterrupt:
                    connection.stopscan()
                    exit(0)
        def ext(self):
            print("BUM!")

    app = Qt()
