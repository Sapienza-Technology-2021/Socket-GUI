#Client
import sys
import time
import socket
import threading
class Socket:
    def __init__(self,UI): #usare UI = None?
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.ui = UI
        self.is_connected = 0
        self.server_ip = ""
        self.server_port = 22222
        self.scanth_flag = 0
        self.scan_th()

    def scan(self):
        #da implementare la perdita e il reset della connessione
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.bind(("",12346))
            ack_socket.settimeout(1)
            print("ACK SERVER in ascolto")
        except:
            print("Errore di inizializzazione acknowledgment server")
            time.sleep(0.2)
            self.scan()
        while True:
            if not self.is_connected:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    s.sendto(b"discover",("<broadcast>",12345))
                    response, addr = ack_socket.recvfrom(1024)
                    if(response == b"ack"):
                        self.server_ip = addr[0]
                        print("Server trovato: ",self.server_ip)
                        self.connect(self.server_ip, self.server_port)
                        
                except socket.timeout:
                    pass
                
                except:
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
        if(self.is_connected):
            try:
                pass
            except:
                pass
            #ricevi dati

    def send(self,data):
        #funzione per inviare dati
        if(self.is_connected):
            try:
                #invia dati
                pass
            except:
                #connessione caduta?
                self.is_connected = 0

    def stopscan(self):
        print("Stopping thread...")
        self.scanth_flag = 1

    def scan_th(self):
        th = threading.Thread(target = self.scan, args=())
        th.start()

    def manual_scan(self):
        #itera tutta la subnet sulla porta desiderata
        pass

    def connect(self, ip, port):
        try:
            self.sock.connect((ip,port))
            self.is_connected = 1
            self.sock.send(b"first data")
            print("Connesso al server: ",ip)
        except:
            print("Errore riscontrato in fase di connessione")
            self.is_connected = 0

class Qt:
    def __init__(self):
        connection = Socket(self)
        while True:
            try:
                time.sleep(1)
            except KeyboardInterrupt:
                connection.stopscan()
                exit(0)
    def ext(self):
        print("BUM!")

app = Qt()