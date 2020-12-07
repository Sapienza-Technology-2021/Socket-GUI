import socket
import time
import threading
import sys

class Server:
    def __init__(self):
        self.ip = ""
        self.port = 22222
        self.data = {}
        self.conns = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.th_flag = 0
        self.ack_server_th()
        self.inizializza_th()

    def inizializza(self):
        try:
            self.socket.bind((self.ip, self.port))
            self.socket.setblocking(0) 
            self.socket.listen()

        except Exception as e:
            time.sleep(1)
            print(e.args[0])
            self.inizializza()

        print("Server in ascolto...")
        while True:
            try:
                conn, addr = self.socket.accept()
                #print(self.socket)
                print("Client connesso. Indirizzo: ",addr)
                if(len(self.conns) <= 16):
                    x = threading.Thread(target = self.client_handler, args = ([conn]))
                    x.start()
                    self.conns[conn] = x
                    print("Numero threads: ",len(self.conns))
                else:
                    print("Numero di threads massimo raggiunto")
                    #send alert
                    #clean()
            
            except BlockingIOError:
                pass

            except Exception as e:
                print(e.args[0])
                time.sleep(1)

            for i in list(self.conns):
                if(not self.conns[i].is_alive()):
                    del self.conns[i]
                    print("Numero Threads: ",len(self.conns))          
            if(self.th_flag):
                self.th_flag = 0
                print("Quitting main server...")
                exit(0)

    def client_handler(self,conn):
        print("Entering Thread")
        th_data = threading.local()
        th_data.isclientalive = 1
        conn.settimeout(10)
        while ((not self.th_flag) and (th_data.isclientalive)):
            try:
                th_data.buffer = conn.recv(4096)
                if(th_data.buffer == b""):
                    raise Exception
                print(th_data.buffer)
            except socket.timeout:
                print("Connection timeout")
                conn.close()
                th_data.isclientalive = 0
            except:
                conn.close()
                th_data.isclientalive = 0
                print("Disconnesso")
        exit(0)


    def ack_server(self):
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ack_socket.settimeout(1.5)
            ack_socket.bind(("", 12345))
            print("ACK SERVER in ascolto")
        except Exception as e:
            print("Errore di inizializzazione ACK SERVER")
            print(e.args[0])
            time.sleep(1)
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

server = Server()

while True:
    try:
        time.sleep(1)
    except KeyboardInterrupt:
        server.disconnetti()
        exit(0)