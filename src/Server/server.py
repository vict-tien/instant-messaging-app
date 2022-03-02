"""
    Python 3
    Usage: python3 server.py localhost 12000
"""
from socket import *
from threading import Thread
import sys
from datetime import datetime
import threading
import time
from signal import signal, SIGPIPE, SIG_DFL, SIG_IGN

"""
    Define multi-thread class for client including the main thread and all 
    corresponding functionalities of the program on the server side
"""
class ClientThread(Thread):
    
    # This is the constructor of a thread and will be used to initialise
    # a thread every time a user connects to the server
    def __init__(self, clientAddress, clientSocket):
        Thread.__init__(self)
        self.clientAddress = clientAddress
        self.clientSocket = clientSocket
        self.clientAlive = False
        
        #print("===== New connection created for: ", clientAddress)
        self.userName = 'userName'
        self.p2pPort = 0
        
    # This function takes care of the main functionality of the server. 
    # It will keep running since a client logs onto the system and until 
    # the client logs out from the server or timed out by the server.
    def run(self):
        self.p2pPort = self.clientSocket.recv(1024).decode().split()[1]
        self.processLogin()
        message = ''
        while self.clientAlive:
            timer = threading.Timer(serverTimeout, self.systemTimeOut)
            timer.start()
            data = self.clientSocket.recv(1024)
            message = data.decode()
            
            # if the message from client is empty, the client would be off-line 
            # then set the client as offline (alive=Flase)
            if message == '':
                timer.cancel()
                self.clientAlive = False
                #print("===== the user disconnected - ", clientAddress)
                self.selectAndRemove(peerList, self.userName)
                self.updateActivityListLogout(self.userName, datetime.now())
                self.broadcast(f"{self.userName} logged out\n", appendix=False)
                self.clientSocket.close()
                break
            
            message = message.split()
            if message[0] == 'message':
                self.message(message, timer)
            elif message[0] == 'broadcast':
                timer.cancel()
                self.broadcast(message)
            elif message[0] == 'whoelse':
                timer.cancel()
                self.clientSocket.send(self.listAllCurrentUsers().encode())
            elif message[0] == 'whoelsesince' and len(message) == 2:
                timePeriod = int(message[1])
                timer.cancel()
                self.clientSocket.send(self.listAllUserSince(timePeriod).encode())
            elif message[0] == 'block' and len(message) == 2:
                self.blockUser(message[1], timer)
            elif message[0] == 'unblock' and len(message) == 2:
                self.unblockUser(message[1], timer)
            elif message[0] == 'startprivate' and len(message) == 2:
                self.startPrivateMessaging(message[1], timer)
            elif message[0] == "['0']":
                timer.cancel()
            else:
                self.clientSocket.send("Error. Invalid command\n".encode())
    
    """
        Customized APIs for the server to utilise for different operations.
    """
    
    # This function takes in the user name of a user and tries to start p2p 
    # messaging between the user and the client by sending user connection info
    # and signal to the client to initiate p2p session. If the client is trying 
    # to start a p2p session with himself or the user is not registered with the 
    # system or the user is not online or the client have been blocked by the user,
    # an error would occur and the client will be notified by the server.
    def startPrivateMessaging(self, user, timer):
        if user == self.userName:
            self.clientSocket.send("Error. Cannot privately message self\n".encode())
        elif self.checkUsers(user):
            timer.cancel()
            for peer in peerList:
                if peer[0] == user:
                    if self.checkIfUserBeenBlocked(peer[0], self.userName):
                        self.clientSocket.send(f"Error. You can not privately message {user} as the recipient has blocked you\n".encode())
                    else:
                        self.clientSocket.send(f"Start private messaging with {user}\n".encode())
                        time.sleep(0.1)
                        self.clientSocket.send(f"['TARGET'] {peer[0]} {peer[1]} {peer[4]} {self.userName} {True}\n".encode())
                        peer[3].clientSocket.send(f"['TARGET'] {self.userName} {self.clientAddress[0]} {self.p2pPort} {peer[0]} {False}\n".encode())
                    break
            else:
                self.clientSocket.send("Error. User is not online\n".encode())        
        else:
            self.clientSocket.send("Error. Invaid user\n".encode())        
    
    # This function takes in the user name of a user and unblocks the user 
    # from not being able to send message to the client or receive notification 
    # from the client. If the client tries to unblock himself or a user that has
    # not been registered with the system, an error would return to the client. 
    # If the given user have not been blocked, an error would raise and the client 
    # woud be notified.
    def unblockUser(self, user, timer):
        if user == self.userName:
            self.clientSocket.send("Error. Cannot unblock self\n".encode())
        elif (self.checkUsers(user)):
            timer.cancel()
            if user in userBlockedList:
                if self.userName in userBlockedList[user]:
                    userBlockedList[user].remove(self.userName)
                    self.clientSocket.send(f"{user} is unblocked\n".encode())
                else:
                    self.clientSocket.send(f"Error. {user} was not blocked\n".encode())
            else:
                self.clientSocket.send(f"Error. {user} was not blocked\n".encode())
        else:
            self.clientSocket.send("Error. Invalid user\n".encode())
    
    # This function takes in the user name of a user and blocks the user from 
    # being able to send messages to the client or receive notification from 
    # client. If the client tries to block himself or a user that has not been 
    # registered with the system, an error message would return to the client. 
    # If the user has already been blocked, the user would be notified.
    def blockUser(self, user, timer):
        if user == self.userName:
            self.clientSocket.send("Error. Cannot block self\n".encode())
        elif (self.checkUsers(user)):
            timer.cancel()
            if user in userBlockedList:
                if self.userName in userBlockedList[user]:
                    self.clientSocket.send(f"Error. {user} has already been blocked\n".encode())
                else:
                    userBlockedList[user].append(self.userName)
                    self.clientSocket.send(f"{user} is blocked\n".encode())
            else:
                userBlockedList[user] = [self.userName]
                self.clientSocket.send(f"{user} is blocked\n".encode())
        else:
            self.clientSocket.send("Error. Invalid user\n".encode())
    
    # This function takes in the message itself and the user who the message
    # would be sent to as a whole, processes the command, and sends the message
    # to the corresponding user if the user is online. If the user has blocked 
    # the client or the user does not exist, an error occurs. If the user is not 
    # currently online, the message will be cached in the server and be sent to 
    # the user once the user logs onto the system
    def message(self, message, timer):
        toUser = message[1]
        message = self.userName + ': ' + ' '.join(message[2:]) + '\n'
        if toUser == self.userName:
            self.clientSocket.send("Error. Cannot send message to your self\n".encode())
        elif (self.checkUsers(toUser)):
            timer.cancel()
            if (self.checkIfUserBeenBlocked(toUser, self.userName)):
                self.clientSocket.send("Your message could not be delivered as the recipient has blocked you\n".encode())
            else:
                for peer in peerList:
                    if (peer[0] == toUser):
                        peer[3].clientSocket.send(message.encode())
                        break;
                else:
                    messageToSend.append([toUser, message])
        else:
            self.clientSocket.send("Error. Invalid user\n".encode())
    
    # This function lists all the users who has logged into the system since
    # the given time, excluding those who have blocked the client for the 
    # whoelsesince functionality
    def listAllUserSince(self, time):
        message = ''
        currentTime = datetime.now()
        for peer in activityList:
            if (self.checkIfUserBeenBlocked(peer[0], self.userName) or peer[0] == self.userName):
                pass
            else:
                if (peer[2] == None and peer[0] not in message):
                    message = message + peer[0] + '\n'
                elif (peer[0] not in message and (currentTime - peer[2]).total_seconds() < time):
                    message = message + peer[0] + '\n'
                else:
                    pass
        return message

    # This function lists all the currently active user who has not currently
    # blocked the client for the whoelse functionality
    def listAllCurrentUsers(self):
        message = ''
        for peer in peerList:
            if (self.checkIfUserBeenBlocked(peer[0], self.userName)):
                pass
            else:
                if (peer[3] != self):
                    message = message + peer[0] + '\n'
        return message
    
    # This function processes the timeout functionality of the server, sends the
    # timeout signal to the client to initiate an active logout by the client
    def systemTimeOut(self):
        self.clientSocket.send("You have been timed out due to inactivity for a long period of time. Please re-login later\n['EXIT']".encode())
        self.selectAndRemove(peerList, clientAddress[1])
    
    # This function processes the broadcase operation of the server, broadcasting 
    # the user's message to all the currently active users
    def broadcast(self, message, appendix=True):
        ifBeingBlocked = False
        if appendix:
            message = self.userName + ': ' + ' '.join(message[1:]) + "\n"
            for peer in peerList:
                if self.checkIfUserBeenBlocked(peer[0], self.userName):
                    ifBeingBlocked = True
                elif (peer[3] != self):
                    peer[3].clientSocket.send(message.encode())
        else:
            for peer in peerList:
                if self.checkIfUserBeenBlocked(self.userName, peer[0]):
                    pass
                elif (peer[3] != self):
                    peer[3].clientSocket.send(message.encode())
        if ifBeingBlocked:
            self.clientSocket.send("Your message could not be delivered to some recipients\n".encode())

    # This function processes the user authentication operation, inlcuding both
    # existing user login and new user registration for the server
    def processLogin(self):
        loginAttempts = 0;
        loginStatus = False;
        self.clientSocket.sendall("Username: ".encode()) 
        userName = self.clientSocket.recv(1024).decode()
        while self.checkIfAlreadyLoggedIn(userName):
            self.clientSocket.send("This user is currently active. Please login with another user\nUsername: ".encode())
            userName = self.clientSocket.recv(1024).decode()

        if (self.checkUsers(userName)):
            self.clientSocket.sendall("Password: ".encode()) 
            while (loginStatus != True):
                if (loginAttempts == 3):
                    self.clientSocket.sendall("Invalid Password. Your account has been blocked. Please try again later\n['EXIT']".encode())
                    loginBlockedList.append([userName, datetime.now()])
                    self.clientSocket.close()
                    break;
                password = self.clientSocket.recv(1024).decode()
                loginAttempts += 1
                if (self.checkIfBeenBlocked(loginBlockedList, userName)):
                    if (datetime.now() - self.getBlockedTime(loginBlockedList, userName)).total_seconds() >serverBlockDuration:
                        self.unblockUserLogin(loginBlockedList, userName)
                    else:
                        self.clientSocket.sendall("Your account is blocked due to multiple login failures. Please try again later\n['EXIT']".encode())
                        self.clientSocket.close()
                        break;
                if (self.verifyPassword(userName, password)):
                    peerList.append([userName, self.clientSocket.getpeername()[0], self.clientSocket.getpeername()[1], self, self.p2pPort])
                    self.userName = userName
                    self.clientSocket.sendall("Welcome to the greatest messaging application ever!\n".encode())
                    self.broadcast(f"{userName} logged in\n", appendix=False)
                    self.updateActivityList(self.userName)
                    loginStatus = True;
                    self.clientAlive = True
                    self.loadCachedMessage()
                elif loginAttempts < 3: 
                    self.clientSocket.sendall("Invalid Password. Please try again\nPassword: ".encode())
                else:
                    pass
        else:
            self.clientSocket.sendall("This is a new user. Enter a password: ".encode()) 
            newPassword = self.clientSocket.recv(1024).decode()
            self.addNewCredentials(userName, newPassword)
            peerList.append([userName, self.clientSocket.getpeername()[0], self.clientSocket.getpeername()[1], self, self.p2pPort])
            self.userName = userName
            self.updateActivityList(self.userName)
            self.broadcast(f"{userName} logged in\n", False)
            self.clientSocket.sendall("Welcome to the greatest messaging application ever!\n".encode())
            self.clientAlive = True
    
    """
        Helper Functions utilised on the server.
    """
    
    # This functions iterates through the safed message list and send all the
    # unread message (messages being sent to the user when the user is not 
    # currently active on the system) to the client 
    def loadCachedMessage(self):
        for i in range(0, len(messageToSend)):
            if messageToSend[i][0] == self.userName:
                self.clientSocket.send(messageToSend[i][1].encode())
                messageToSend.remove(messageToSend[i])
    
    # This function takes in two users, userA and userB and verifies if userB 
    # has been blocked by userA.
    def checkIfUserBeenBlocked(self, userA, userB):
        if userB in userBlockedList:
            if userA in userBlockedList[userB]:
                return True
        return False
    
    # This function updates the activity list, which keeps track of the time 
    # when a user has logged into the system, by including logout timestamps 
    # of a user for listing users who have logged in since a particular time 
    # functionality
    def updateActivityListLogout(self, userName, time):
        for peer in activityList:
            if userName == peer[0]:
                peer[2] = time

    # This function updates the activity list, which keeps track of the time 
    # when a user has logged into the system, by creating logged in information 
    # (user name and logged in time stamp) for listing users who have logged in 
    # since a particular time functionality
    def updateActivityList(self, userName):
        for peer in activityList:
            if userName == peer[0]:
                peer[1] = datetime.now()
                peer[2] = None
        else:
            activityList.append([userName, datetime.now(), None])
    
    # This function iterates through the credentials file and check if the
    # user is a valid user/ has been registered in the system
    def checkUsers(self, userName):
        c = open('credentials.txt', 'r')
        f = c.readlines()
        for line in f:
            detail = line.split()
            if (detail[0] == userName):
                c.close()
                return True;
        c.close()
        return False;
    
    # This function iterates through the peerList, which keeps track of the active
    # users, and checks if a users has been succfully logged into the application
    def checkIfAlreadyLoggedIn(self, userName):
        for peer in peerList:
            if userName == peer[0]:
                return True
        return False

    # This function iterates through the credentials file and check if the
    # user name & password matches the record stored in the credentials.txt
    def verifyPassword(self, userName, password):
        c = open('credentials.txt', 'r')
        f = c.readlines()
        for line in f:
            detail = line.split()
            if (detail[0] == userName):
                if (detail[1] == password):
                    c.close()
                    return True;
        c.close
        return False; 
    
    # This function adds the user name and password of a newly registered user
    # into the end of the credentials file
    def addNewCredentials(self, userName, password):
        c = open('credentials.txt', 'a')
        c.write('\n')
        newCredentials = userName + ' ' + password
        c.write(newCredentials)
        c.close()   
        
    # This function iterates through the peerList, which keeps track of the active
    # users, and logs a user out by removing the corresponding data from the list
    def selectAndRemove(self, peerList, data):
        for i in range(0, len(peerList)):
            if peerList[i][0] == data:
                peerList.remove(peerList[i])
                break;

    # This function iterates through the blockedList, which keeps track of the user 
    # information of users who have multiple unsuccessful login attemps, and 
    # determine whether a user have been blocked by the system
    def checkIfBeenBlocked(self, blockedList, userName):
        for i in blockedList:
            if (i[0] == userName):
                return True;
        return False;
    
    # This function iterates through the blockedList, which keeps track of the user 
    # information of users who have multiple unsuccessful login attemps, and unblock
    # the given user from the system
    def unblockUserLogin(self, blockedList, userName):
        for i in range(0, len(blockedList)):
            if blockedList[i][0] == userName:
                blockedList.remove(blockedList[i])
               
    # This function iterates through the blockedList, which keeps track of the user
    # information of users who have multiple unsuccessful login attemps, and returns
    # the time when a user have been blocked by the system
    def getBlockedTime(self, blockedList, userName):
        for i in blockedList:
            if (i[0] == userName):
                return i[1];

"""
    Main execution of the server function
"""

# Verify if sufficient information have been provided by the command line
# Proceed if sufficient. Print out error and stop execution otherwise.
if len(sys.argv) != 4:
    print("\n===== Error usage, python3 TCPServer3.py SERVER_PORT ======\n");
    exit(0);
    
# Acquire serverPort, serverBlockDuration, and serverTimeout from command line
# parameter. serverHost have been set to localhost, 127.0.0.1, by default. This
# may change under different usages.
serverHost = "127.0.0.1"
serverPort = int(sys.argv[1])
serverBlockDuration = int(sys.argv[2])
serverTimeout = int(sys.argv[3])
serverAddress = (serverHost, serverPort)

# Define socket for the server side and bind address for connectivity purposes
serverSocket = socket(AF_INET, SOCK_STREAM)
serverSocket.bind(serverAddress)

'''
    The Definition of server side data structure
'''

# The loginBlockedList keeps track of the list of users who have been blocked by
# the server due to multiple unsuccessful logins. Each element of the 
# loginBlockedList would be a list in the following data structure: 
# [userName, timestampWhenUserHadBeenBlocked]
loginBlockedList = []

# The peerList keeps track of the currently logged in users and their corresponding
# information. Each element of the peerList would be a list in the following data 
# structure: [userName, userIpAddress, userPortNumber, userSocket, userP2pPortNumber]
peerList = []

# The activityList keeps track of the user activity of logging in to and out of the 
# server. Each element of the activityList would be a list in the following data 
# structure: [userName, mostRecentLoginTimestamp, mostRecentLogOffTimestamp]. 
# Note: the most recent log off tiem stamp would be set to None when the user is 
# currently active.
activityList = []

# The messageToSend list keeps track of the offline messages which needs to be send 
# to the corresponding user when the user logs into the system. Each element of the 
# messageToSend list would be a list in the following data structure: 
# [userName, messageContentToBeSendToUserName]
messageToSend = []

# The userBlockedList keeps track of a list of whom had currently blocked the user. 
# The userBlockedList would be a dictionary in the following format: 
# {userA: [userB, userC, etc.]}, which userA had been blocked by userB, userC, etc. 
userBlockedList = {}

# Main execution loop of the server
while True:
    serverSocket.listen()
    clientSockt, clientAddress = serverSocket.accept()
    clientThread = ClientThread(clientAddress, clientSockt)
    clientThread.start()
    signal(SIGPIPE, SIG_IGN)