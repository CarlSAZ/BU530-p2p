# BU530-p2p - An exploration of P2P sockets

This repository contains an exercise in peer to peer networking through socket programming.

## Instructions for use

The main entry point is the python script p2p_app.py. It is intended to launch an application that
would allow a user to connect directly to a friend, and also exchange address directories with each other.

python3 p2p_project.py   HOST_IP   PORT

Will launch the application, where the host IP address and port to be bound are input arguments. The Host IP can be 'localhost', 127.0.0.1, or 0.0.0.0 for 
testing the application on a single machine. The port can be any valid port for socket binding, but must be unique and not in use.

Once the app is up, a user can input commands to initiate connections and send messages.

## Implemented commands

>connect IP_ADDR PORT

connect - connect directly to another user at given IP and PORT
Will open up a connection to a user at the specified address. This will initiate a transfer of directories between both users (To be implented)

## Planned commands

>send USER MESSAGE...

Should be able to send a message to any of the open connections

>switch USER

Switch to showing messages from specific user

>connect USER

Connect to a user by providing the displayname or other ID.
