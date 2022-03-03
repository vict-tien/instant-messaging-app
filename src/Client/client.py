"""
    Python 3
    Usage: python3 TCPClient3.py localhost 12000
    coding: utf-8
    
"""
from socket import *
from threading import Thread
import sys
import threading
import readline
import time

# This function takes the message which needs to be print, and safely prints out
# the message without breaking other threads such as the input and p2p connections
# Reference: https://stackoverflow.com/a/4653306/12208789
def safe_print(*args):
    sys.stdout.write('\r' + ' ' * (len(readline.get_line_buffer()) + 2) + '\r')
    print(*args, end="")
    sys.stdout.flush()
    time.sleep(0.1)

# This function creates a private messaging receiver which is listening to incoming 
# messages at the given socket and will act correspondingly to the user.
def getPrivateMessageReceiver(p2pSocket):
    def privateMessageReceiver():
        while True:
            data = p2pSocket.recv(1024).decode()
            if "['EXIT']" in data:
                if "['END']" not in data:
                    message = data.split()
                    message = message[0] + " " + message[2] + " ['END']" 
                    peerSocketList[data.split()[1]].send(message.encode())
                    time.sleep(0.1)
                peerSocketList[data.split()[1]].close()
                peerSocketList.pop(data.split()[1])
                p2pSocket.close()
                peerListeningList.pop(data.split()[1])
                clientName = data.split()[1]
                if len(data.split()) > 3 and data.split()[3] == 'True':
                    safe_print(f"Private messaging with {clientName} closed due to inactivity\n")
                else:
                    safe_print(f"Private messaging with {clientName} closed\n")
                break
            else: 
                safe_print(data + '\n')
    
    return privateMessageReceiver

# This function listens to port which designated to P2P connections for incoming 
# network. If a peer is trying to connect to this port to initiate private messaging,
# the function will accept the connection, start a thread with the private socket for
# communication, and add the thread to the peerListeningList for future utilisation.
def privateReceiveConnector():
    while True:
        p2pSocket, p2pAddress = p2pMessagingSocket.accept()
        privateReceiver = getPrivateMessageReceiver(p2pSocket)
        privateSocketThread = threading.Thread(target=privateReceiver)
        privateSocketThread.daemon = True
        privateSocketThread.start()
        peerListeningList[p2pClient] = p2pSocket

# This function handles the start of a private messaging connection if requested 
# by the client. The function starts a p2p connection correspondingly and possibly 
# ask if the user is willing to start p2p and act correspondingly.
def startNewPrivateConnection(userName, targetIp, targetPort, flag):
    global allowPrivate
    newPeerSocket = socket(AF_INET, SOCK_STREAM)
    newPeerSocket.connect((targetIp, int(targetPort)))
    if (flag == 'False'): 
        safe_print(f"{userName} would like to private message, enter y or n: ")
        allowPrivate = True
    peerSocketList[userName] = newPeerSocket
    
# This function handles the message being sent to the client. The function will 
# decode the message, understand the command, and act correspondingly. 
def messageReceiver():
    global terminate, userName, p2pClient
    while True:
        data = clientSocket.recv(1024).decode()
        if "['EXIT']" in data:
            safe_print(data[:-8])
            clientSocket.send("".encode())
            for peer in peerSocketList:
                peerSocketList[peer].send(f"['EXIT'] {userName} {peer} True".encode())
            terminate = True
        elif  "['TARGET']" in data:
            data = data.split()
            p2pClient = data[1]
            userName = data[4]
            startNewPrivateConnection(p2pClient, data[2], data[3], data[5])
        else: 
            safe_print(data)

# This function handles the messages being send from the user. All messages will be 
# directed to the server unless the user wishes to privately message a peer or stop 
# a private messaging session.
def messageSender():
    global terminate, allowPrivate, userName
    while True:
        message = input()
        if message.lower() == "logout":
            for peer in peerSocketList:
                peerSocketList[peer].send(f"['EXIT'] {userName} {peer}".encode())
            clientSocket.send("".encode())
            terminate = True
        elif allowPrivate == True:
            clientSocket.send("['0']".encode())
            if message == 'y':
                peerSocketList[p2pClient].send(f"{userName} accepts private messaging".encode())
            else:
                peerSocketList[p2pClient].send(f"{userName} declines private messaging".encode())
                time.sleep(0.1)
                peerSocketList[message[1]].send(f"['EXIT'] {userName} {p2pClient}".encode())
            allowPrivate = False
        else:
            message = message.split()
            if len(message) >= 2 and message[0] == "private":
                messageToSend = ' '.join(message[2:])
                messageToSend = f"{userName}(private): " + messageToSend
                if message[1] in peerSocketList:
                    clientSocket.send("['0']".encode())
                    peerSocketList[message[1]].send(messageToSend.encode())
                else: 
                    safe_print(f"Error. Private messaging to {message[1]} not enabled\n")
            elif len(message) == 2 and message[0] == "stopprivate":
                if message[1] in peerSocketList:
                    clientSocket.send("['0']".encode())
                    peerSocketList[message[1]].send(f"['EXIT'] {userName} {message[1]}".encode())
                else:
                    safe_print(f"Error. Cannot stop an inexist private session with {message[1]}\n")
            else:
                clientSocket.send(' '.join(message).encode())

"""
    Main execution code of the client
"""

# Verify if sufficient information have been provided by the command line. Proceed 
# if sufficient. Print out error and stop execution otherwise.
if len(sys.argv) != 2:
    print("\n===== Error usage, python3 TCPClient3.py SERVER_PORT ======\n");
    exit(0);

# Acquire serverPort from command line parameter. serverHost have been set to 
# localhost, 127.0.0.1, by default. This may be changed for later usage.

# ### Change this line of code if you wish to communicate between different computers. 
serverHost = 'localhost'

serverPort = int(sys.argv[1])
serverAddress = (serverHost, serverPort)
  
# Initialise tracking variables to default. terminate determines if the program needs
# to be terminated, userName keeps track of the userName of the current client. 
# p2pClient keeps track of the userName of the p2pClient, and allowPrivate is a flag 
# signaling the messageSender if the input is a proper user command or a p2p connection
# decision.  
terminate = False
userName = None
p2pClient = ''
allowPrivate = False

# Define socket for the client side and connect the socket to the server.
clientSocket = socket(AF_INET, SOCK_STREAM)
clientSocket.connect(serverAddress)

# Define socket for private messaging, bind the address, and listen to the port for 
# connectivity purposes. Additionally, the private messaging port would be obtained 
# to notify the server and allow peers have correct port number for private messaging 
# connection.
p2pMessagingSocket = socket(AF_INET, SOCK_STREAM)
p2pMessagingSocket.bind(("localhost", 0))
p2pMessagingSocket.listen(1)
p2pMessagingPort = p2pMessagingSocket.getsockname()[1]
clientSocket.send(f"['p2pPort'] {p2pMessagingPort}".encode())

'''
    Definition of client side data structure
'''

# The peerSocketList keeps track of the users who have initiated private messaging 
# with the client and their corresponding sockets, which would be used to send private
# messages to the user. The peerSocketList is a dictionary in the following format: 
# {userNameA: socketA, userNameB: socketB, ...}
peerSocketList = {}

# The peerListeningList keeps track of the users who have initiated private messaging
# with the client and their corresponding listening sockets, which would be responsible
# for receving privates messages from the user. The peerListeningList is a dictionary 
# in the following format: {userNameA: socketA, userNameB: socketB, ...}
peerListeningList = {}

# Creates a new thread to handle messages send to the client from the server.
receiverHandler = Thread(name="receiver", target = messageReceiver)
receiverHandler.daemon = True
receiverHandler.start()

# Creates a new thread to handle messages send from the client, including messages 
# send to the server and peer via private messaging.
sendHandler = Thread(name="sender", target = messageSender)
sendHandler.daemon = True
sendHandler.start()

# Creates a new thread to listen for private messaging connection, connect if another
# user wishes to start p2p connection with the client.
privateReceiver = Thread(name="privateReceiver", target = privateReceiveConnector)
privateReceiver.daemon = True
privateReceiver.start()

# Main execution loop to keep the code working. If the client needs to be terminated, 
# terminate will be set to true and the function exits.
while True:
    if terminate:
        exit(0)
