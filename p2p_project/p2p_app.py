#!/usr/bin/python3
# Python program to implement a strict decentralized P2P 
import socket
import sys
import socketserver
import threading
import selectors
import types

REQUEST_PEER_LIST_COMMAND = b'qwerty'
RECEIVE_PEER_LIST_COMMAND = b'qwerty'

class NewPeerHandler(socketserver.StreamRequestHandler):
    """
    This handler acts to field new peer connections
    """

    def handle(self):
        message = self.rfile.readline().strip()
        if (message == REQUEST_PEER_LIST_COMMAND):
            self.wfile.writelines([bytes("Sent Peer List\n",'utf-8')])
            # TODO: add handling so we can exchange peer lists.
        else:
            print("{} wrote:".format(self.client_address[0]))
            print(message.decode('utf-8'))


class ThreadedP2PServer(socketserver.ThreadingMixIn,socketserver.TCPServer):

    def server_activate(self) -> None:
        super().server_activate()
        print("Started self server")
        self.peer_list = [self.server_address]
    

def client(ip, port, message):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((ip, port))
        sock.sendall(bytes(message, 'ascii'))
        response = str(sock.recv(1024), 'ascii')
        print("Received: {}".format(response))

class MainClient:
    def __init__(self):
        self.open_sockets = []
        self.sel = selectors.DefaultSelector()
        self.service_thread = threading.Thread(target=self.check_reads)
        self.service_thread.daemon = True
        
    def service_connection(self,key,mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)
            if recv_data:
                print(f"{data.connid} wrote: {recv_data!r}")
            if not recv_data:
                print(f"Closing connection to {data.connid}")
                self.sel.unregister(sock)
                sock.close()


    def check_reads(self):
        while True:
            events = self.sel.select(timeout=1)
            if events:
                for key, mask in events:
                    self.service_connection(key, mask)
            # Check for a socket being monitored to continue.
            if not self.sel.get_map():
                pass
                #break

    def open_chat(self,hostIP,hostPort) -> socket.socket:
        sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        sock.setblocking(False)
        sock.connect_ex((hostIP,hostPort))
        events = selectors.EVENT_READ
        data = types.SimpleNamespace(
            connid=hostIP,
            messages=[],
            outb=b""
        )
        self.sel.register(sock,events,data=data)
        self.open_sockets.append(sock)
        return sock
        
    def chat_pm(self,sock):
        termsel = selectors.DefaultSelector()
        termsel.register(sock,selectors.EVENT_WRITE)
        while True:
            events = termsel.select(timeout=1)
            if events:
                message = input('(someone)>')
                sock.sendall(bytes(message,'utf-8'))


    def run(self):
        self.service_thread.start()
        while True:
            inp = input('>')

            if (inp.split(" ")[0] == "connect"):
                command = inp.split(" ")
                sock = self.open_chat(command[1],int(command[2]))
                self.chat_pm(sock)
            



if __name__ == "__main__":
    if len(sys.argv) == 3:
        HOST, PORT = str(sys.argv[1]) , int(sys.argv[2])
    else:
        HOST, PORT = "localhost", 0

    server = ThreadedP2PServer((HOST,PORT), NewPeerHandler) 
    with server:
        ip, port = server.server_address

        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        #client(ip, port, REQUEST_PEER_LIST_COMMAND.decode('utf-8') + "\n")
        #client(ip, port, "Hello World 2\n")
        #client(ip, port, "Hello World 3\n")
        terminal = MainClient()
        terminal.run()
        server.shutdown()



