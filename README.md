# Instant Messaging App

Keywords: Instant Messaging Application, Socket Programming, Server-Client Architecture with P2P Messaging Functionality

-------------
**Disclaimer: This application/code was originally developed and submitted as the coding assignment for a UNSW undergraduate course - COMP3331/9331 Computer Networks and Applications. This code should only be used as reference only and has not been verified for commercial or production services. Additionally, if a similar assignment have been assigned at a later course offering at UNSW, do not plagiarise with this code. Submit your own work.**

-------------

## General

This project implements a simple instant communication software. It contains two major sections, the server and the client. There will only be one active server for each instance of the software and there may be an unlimited number of clients active on the server, allowing users to communicate via the server, block and unblock a particular user, and start private messaging. Multithreading have been implemented to ensure sufficient communication.

## Execution

- To start the server instance, execute the following code:

        python3.7 server.py server_port block_duration timeout

- To start each client instance, execute the following code:

        python3.7 client.py server_port

Note: 
- The server must start before the start of any client instances.
- The server would log a user out if the user has been inactive for the specified timeout period and the server would block the user from logging in if the user had multiple failure login attempts.

## Dependencies

The following table shows the dependencies and libraries used within the project. All libraries and dependencies should be properly installed before the execution of any code. Errors might incur otherwise. 

| Server (server.py) | Client (client.py) |
|:------------------:|:------------------:|
| socket | socket|
| threading | threading| 
| sys | sys|
| datetime | readline|
| time | time|
| signal|

## Known Issues
- Note that this project was designed and implemented in the academic environment. All datas sent through the server or via the Peer-to-peer method had not been encrypted by any kinds of encryption. Plain texts will be transferred directly through the system. 
  
    <b>PLEASE DO NOT USE THIS PROJECT TO TRANSFER ANY SENSITIVE DATA WITHOUT ANY SECONDARY ENCRYPTION OR MODIFICATION.</b>
  
- This project was developed under testing envrionment. The default setting was to transfer data/messages within the same computer and hence the server IP address in the client code has been set to 127.0.0.1 localhost by default. If the user wish to communicate between different computers, change the server IP address in the client code accordingly. 

    <b>Note: However, this project does not take care of any type of network address translation and public/private IP addressing issues. To communicate between different computers, proper public/private IP address translation methods will need to be implemented.</b>

- Users might not able to run the server at a particular port. Certain port numbers are reserved for particular services internally by the computer and others might have ongoing threads. Try to start the server at a different port and this issue should be resolved. 

## Potential Improvement
- Json files might be used to communicate data instead of plain text.
- Data might be encrypted before communication to provide confidentiality and integrity.
- Data might be made persistent, i.e., userBlockedList, which keeps track of if a userA have been blocked by any other users, might be stored in a file instead of the dynamic memory of the program and can be made persistent after the shutdown of the server.
- Network Address Translation services might be implemented to the project to allow communications between different computers in the future. 

## Reference
- This project was developed based on the starter code provided by the cs3331 teaching team at UNSW Sydney at Term 3, 2021.
- The safe_print function which ensures printing incoming messages to a client will not break any threads such as the input and p2p connections was referenced from https://stackoverflow.com/questions/2082387/reading-input-from-raw-input- without-having-the-prompt-overwritten-by-other-th/4653306#4653306.