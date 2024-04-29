#!/usr/bin/python3
'''Python program to implement a strict decentralized P2P'''
import socket
import sys
import socketserver
import threading
import selectors
import types
import sqlite3

HANDSHAKE_PEER_COMMAND = b'__hello__'

REQUEST_PEER_LIST_COMMAND = b'qwerty'
RECEIVE_PEER_LIST_COMMAND = b'qwerty'

SQL_DATABASE = "p2p_app.db"


# Acknoledging this is a bad way to handle the database, globals are not good.
# TODO: Refactor to reduce dependency on globals.
global_con = sqlite3.connect(SQL_DATABASE)
global_cur = global_con.cursor()

try:
    global_res = global_cur.execute("SELECT name FROM sqlite_master WHERE name='userlist'")
    table_exists = global_res.fetchone() is not None
except:
    table_exists = False

if (not table_exists):
    global_cur.execute("CREATE TABLE userlist(userid,ipaddr,serverport,clientport,username,email)")

def addUserToDatabase(IPAddr,Port,*,userid="?",username="?",clientport="",email=""):
    con = sqlite3.connect(SQL_DATABASE)
    cur = con.cursor()
    newuser = {
        "id":userid,
        "newip":IPAddr,
        "newserver":Port,
        "newuser":username,
        "newclient":clientport,
        "newemail":email
    }
    res = cur.execute("SELECT * FROM userlist WHERE ipaddr=:newip AND serverport=:newserver",(newuser))
    if res.fetchone() is None:
        cur.execute("INSERT INTO userlist VALUES" +
                    "(:id, :newip, :newserver, :newclient, :newuser, :newemail)",(newuser))
    else:
        cur.execute("UPDATE userlist SET VALUES" +
                    "(:id, :newip, :newserver, :newclient, :newuser, :newemail) " + 
                    "WHERE ipaddr=:newip AND serverport=:newserver",(newuser))
    con.commit()
    return

class NewPeerHandler(socketserver.StreamRequestHandler):
    """
    This handler acts to field new peer connections
    """

    def handle(self):
        message = self.rfile.readline().strip()
        print("{} wrote:".format(self.client_address[0]))
        print(message.decode('utf-8'))

        command = message.split(b' ')[0] 
        messagestr = message.decode('utf-8').split(' ')
        if (command== REQUEST_PEER_LIST_COMMAND):
            self.wfile.writelines([bytes("Sent Peer List\n",'utf-8')])
            # TODO: add handling so we can exchange peer lists.
            return
        if (command == HANDSHAKE_PEER_COMMAND):
            # TODO: add some identification or authentication before we add users to 
            # our database.
            addUserToDatabase(self.client_address[0],self.client_address[1],userid=messagestr[2],username=messagestr[3],clientport=messagestr[1],email=messagestr[4])
            return



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
        self.con = sqlite3.connect(SQL_DATABASE)
        self.cur = self.con.cursor()
        
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
                if (message == "exit"):
                    return
                sock.sendall(bytes(message,'utf-8'))


    def run(self):
        self.service_thread.start()
        while True:
            inp = input('>')

            if (inp.split(" ")[0] == "connect"):
                command = inp.split(" ")
                sock = self.open_chat(command[1],int(command[2]))
                self.chat_pm(sock)
            elif (inp.split(" ")[0] == "listusers"):
                res = self.cur.execute("SELECT * FROM userlist")
                print(res.fetchall())

            



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

        # Test by sending a connection creating new user entry from a bad actor
        client(ip, port, HANDSHAKE_PEER_COMMAND.decode('utf-8') + " -1 \\n 'bad_will :blackhat@agency.com\n")
        #client(ip, port, "Hello World 2\n")
        #client(ip, port, "Hello World 3\n")
        terminal = MainClient()
        terminal.run()
        server.shutdown()



