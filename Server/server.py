from threading import Event
import traceback
import socket
import time
import threading
import sys
import json

class Parser:
    def __init__(self):
        self.comandi = {"comando":self.elabora}
        pass
    def elabora(self,data):
        lb = data.count("{")
        rb = data.count("}")
        if(lb != rb or lb == 0 or data[0]!="{" or data[len(data)-1]!="}"):
            print("Messaggio corrotto")
            return
        count = 0
        for i in range(len(data)):
            if(data[i] == "{"):
                count += 1
            elif(data[i] == "}"):
                count -= 1
            if(count == 0 and ((i+1) != len(data)) and i != 0):
                print("Messaggio corrotto ",i)
                return
        self.parse(data)

    def parse(self,dict):
        try:
            loaded = json.loads(dict)
            print(loaded)
            self.load_data(loaded)
        except json.JSONDecodeError:
            print("Dizionario corrotto")
        except Exception as e:
            print("Codice errore: ", e.args[0])

    def load_data(self,data):
        try:
            command = data["comando"]
            # if-elif per ogni chiave
            if command == "update":
                print("Mi sto aggiornando") # eseguire funzione relativa al comando
            elif command == "move":
                print("Mi sto muovendo")
            else:
                if command == "":
                    print("Campo comando vuoto")
                else:
                    print("Comando non trovato: ", command)
        except Exception:
            traceback.print_exc()

class Server(Parser): 
    def __init__(self, port):
        super().__init__()
        self.ip = ""
        self.port = port
        self.data = {}
        self.conns = {}
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.th_flag = True
        th_server = threading.Thread(target = self.inizializza, args = ())
        th_server.start()
        self.ack_th_flag = True
        ack_th = threading.Thread(target = self.ack_server, args = ())
        ack_th.start()

    def inizializza(self):
        print("Server init...")
        try:
            self.socket.bind((self.ip, self.port))
            #self.socket.setblocking(0)
            self.socket.listen()
        except Exception as e:
            print("Init error!")
            traceback.print_exc()
            time.sleep(5)
            if self.th_flag is True:
                print("Init retry...")
                self.inizializza()
        print("Server in ascolto...")
        while self.th_flag:
            try:
                conn, addr = self.socket.accept()
                print("Client connesso. Indirizzo: ",addr)
                if len(self.conns) <= 16:
                    x = threading.Thread(target = self.client_handler, args = ([conn]))
                    x.start()
                    self.conns[conn] = x
                    print("Numero threads: ",len(self.conns))
                else:
                    print("Numero di threads massimo raggiunto!")
                    conn.close()
            except BlockingIOError:
                print("Blocking IO error")
            except Exception as e:
                print("Init error!")
                traceback.print_exc()
            for i in list(self.conns):
                if (not self.conns[i].is_alive()):
                    del self.conns[i]
                    print("Numero connessioni: ", len(self.conns))
        print("Closing server...")

    def client_handler(self,conn):
        print("Handler thread start")
        info = conn.getpeername()
        #conn.setblocking(0)
        message = ""
        count = 0
        try:
            while self.th_flag:
                buffer = conn.recv(1024).decode()
                marker = buffer.find("\n")
                if(marker >= 0):
                    message += buffer[:marker]
                    self.elabora(message)
                    message = ""
                    count = 0
                else:
                    count += 1
                    if count > 1000:
                        raise socket.timeout
                    message += buffer
                if buffer == b"":
                    raise Exception
                #print(th_data.buffer)
        except socket.timeout:
            print("Connection timeout: ", info)
            conn.close()
        except BlockingIOError:
            print("Blocking IO error")
        except Exception as e:
            print("Disconnesso ", info)
            conn.close()
            traceback.print_exc()
        print("Client handler stopped.")

    def ack_server(self):
        try:
            ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            ack_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            ack_socket.settimeout(1.5)
            ack_socket.bind(("", 12345))
            print("ACK server in ascolto")
        except Exception as e:
            print("Errore di inizializzazione ACK server")
            traceback.print_exc()
            time.sleep(5)
            if self.ack_th_flag is True:
                print("ACK init retry...")
                self.ack_server()
        while self.ack_th_flag:
            try:
                response, addr = ack_socket.recvfrom(1024)
                if(response == b"discover"):
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    s.connect((addr[0], 12346))
                    s.send(b"ack")
                    s.close()
            except socket.timeout:
                print("ACK timeout.")
            except Exception as e:
                print("Errore riscontrato in ACK SERVER")
                traceback.print_exc()
        print("Quitting ACK SERVER...")

    def disconnetti(self):
        print("Stopping server...")
        self.th_flag = False
        self.ack_th_flag = False
        self.socket.close()

if __name__ == "__main__":
    server = None
    event = Event()
    try:
        server = Server(12345)
        event.wait()
    except KeyboardInterrupt:
        event.clear()
        if server is not None:
            server.disconnetti()
        exit(0)
    except Exception as e:
        traceback.print_exc()
        if server is not None:
            server.disconnetti()
        exit(1)
