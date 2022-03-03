# Instant Messaging App

Keywords: An instant messaging application, Socket Programming, Server-Client Architecture with P2P messaging functionality

-------------
**Disclaimer: This application/code was originally developed and submitted as the coding assignment for a UNSW undergraduate course - COMP3331/9331 Computer Networks and Applications. This code should only be used as reference only and has not been verified for commercial or production usage. Additionally, if a similar assignment have been assigned at a later course offering at UNSW, do not plagiarise with this code. Submit your own work.**

-------------


## General

This project implements a simple instant communication software. It contains two major sections, the server, and the client. There will only be one active server for each instance of the software and there may be an unlimited number of clients active on the server, allowing users to communicate via the server, block and unblock a particular user, and start private messaging. Multithreading have been implemented to ensure sufficient communication.

## Execution

- To start the server instance, execute the following code:

        python3.7 server.py server_port block_duration timeout

- To start each client instance, execute the following code:

        python3.7 client.py server_port

Note: 
- The server must start before the start of any clients.
- The server would log a user out if the user has been inactive for over the specified timeout period and the server would block the user from logging in if the user had multiple failure logins.

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

## Reference
- This project was developed based on the starter code provided by the cs3331 teaching team at UNSW Sydney at Term 3, 2021
- The safe_print function which ensures printing incoming messages to a client will not break any threads such as the input and p2p connections was referenced from https://stackoverflow.com/questions/2082387/reading-input-from-raw-input- without-having-the-prompt-overwritten-by-other-th/4653306#4653306