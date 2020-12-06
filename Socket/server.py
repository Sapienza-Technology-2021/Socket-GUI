import socket
import time
import threading
import sys

class Server:
    def __init__(self):
        self.ip = ""
        self.port = 22222
        self.data = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.th_flag = 0
        self.ack_server_th()
        self.inizializza_th()

    def inizializza(self):
        self.socket.bind((self.ip, self.port))
        self.socket.listen() 
        print("Server in ascolto...")
        while not self.th_flag:
            conn, addr = self.socket.accept()
            print(self.socket)
            print("Client connesso. Indirizzo: ",addr)
            #Verificare eccezioni client non connesso
            #provare con timeout messaggi e risposte per verificare se il client riceve
            #self.socket.accept usa un socket bloccante quindi non verificherà se th_flag è cambiata e se il socket è chiuso
                 
    def ack_server(self):
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.settimeout(1.5)
            ack_socket.bind(("", 12345))
            print("ACK SERVER in ascolto")

        except:
            print("Errore di inizializzazione ACK SERVER")
            time.sleep(0.5)
            self.ack_server()

        while True:
            try:
                response, addr = ack_socket.recvfrom(1024)
                if(response == b"discover"):
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((addr[0], 12346))
                    s.send(b"ack")
                    s.close()
            
            except socket.timeout:
                pass

            except:
                time.sleep(1)
                print("Errore riscontrato in ACK SERVER")
                print("Unexpected error:", sys.exc_info()[0])

            if(self.ack_th_flag):
                self.ack_th_flag = 0
                print("Quitting ACK SERVER...")
                exit(0)

    def inizializza_th(self):
        th_server = threading.Thread(target = self.inizializza, args = ())
        th_server.start()

    def ack_server_th(self):
        self.ack_th_flag = 0
        ack_th = threading.Thread(target = self.ack_server, args = ())
        ack_th.start()

    def disconnetti(self):
        print("Quitting...")
        self.th_flag = 1
        self.ack_th_flag = 1
        self.socket.close()

    def send(self,data):
        pass

    def recv(self):
        pass

server = Server()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        server.disconnetti()
        exit(0)