import sys
import socket
import threading
import json
import select
import time
import getpass
import tkinter
import tkinter.scrolledtext


# GLOBALS
HOST = "localhost"
PORT = 5000
ADDR = (HOST,PORT)
SIZE = 1024
FORMAT = "utf-8"
QUIT = "!QUIT"
JOINCHAT = "!JOIN-CHAT"
VIEWROOM = "!VIEW-CHATROOMS"
EXITROOM = "!EXIT-ROOM"
LEAVEROOM = "!LEAVE-ROOM"
CREATE = "!CREATE-ROOM"
MESSAGE = "!MESSAGE"
HELP = "!HELP"
SIGNIN = "Signin"
REG = "Register"

ID = ""
NAME = None

# global Variables
commands = [HELP,JOINCHAT,VIEWROOM,EXITROOM,CREATE,MESSAGE,LEAVEROOM]
roomMem = {}

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.connect(ADDR)


signedIn = False

'''
Makes all rooms inactive that the user is in. Either for:
1) When the user has exited the current room or
2) To make another room active
'''
def makeRoomsInact():
    for room in roomMem:
        roomMem[room] = False


def gui_loop(self):
    self.win = tkinter.TK()

'''
Handles incoming messages and does appropriate tasks 
'''
def handleMessageRecv(data):
    global ID
    global NAME
    global signedIn
    global printed
    
    message = data
    if message["type"] == "Registered":
        print("[Server]:-You have been Registered !-----\n[Server]:- Please sign in to enter Chat Room")
        rep = {"type" : ""}
        cliSignin(rep, SIGNIN) 
    
    
    elif message["type"] == SIGNIN:
        if message["signedIn"]:
            ID = message["ID"]
            NAME = message["Username"]
            print("Welcome to the chat room:- '(Type !HELP for commands)'")
            signedIn = True
        else:
            print("Sign in failed, Try again")
            rep = {"type" : ""}
            cliSignin(rep, SIGNIN)
    
    # When the user tries to join a chatroom, they can if there is space or 
    # are already a member of the chat room. Else the appropriate message is displayed
    elif message["type"] == "JOIN-REPLY":
        if message["Success"] == True:
            makeRoomsInact()
            roomMem[message["RoomName"]] = True    
        # Message from server    
        print(message["ReplyMessage"])
        print("Enter to continue")   
        
    # When a user requests to see chat rooms            
    elif message["type"] ==  "VIEWROOM-REPLY":
        tok = message["RoomList"]
        print("\n------These are the chat rooms-------")
        if message["Success"] == True:
            for token in tok:
                print(token)
        else:
            print(tok)
    # When a user creates a room, shows either user succeeded or failed
    # to make a room        
    elif message["type"] == "CREATE-REPLY":
        print(message["Message"])
        
    # When you leave the chat room and no longer are a member
    elif message["type"] == "LEAVE-REPLY":
        if message["Success"]:
            print("---Left Chat Room---")
            makeRoomsInact()
            print("Enter to continue")
        else:
            print("----No Room Joined yet----")
    
    # When a user exits the current room they are in but 
    # they still are a member
    elif message["type"] == "EXIT-REPLY":
        if message["Success"]:
            print("---Exited Chat Room---")
            makeRoomsInact()
            print("Enter to continue")
        else:
            print("----No Room Joined yet----")
    
    # For the user to see what commands to use    
    elif message["type"] == "HELP-REPLY":
        tok = message["ComList"]
        print()
        print("Here's the list of commands you can use:")
        for token in tok:
            print(token)
    
    # Lets the user know if they are in a chat room
    elif message["type"] == "MESSAGE-REPLY":
        if message["Success"] == False:
            print("No chat Room joined atm")
    
    # Messages from other members
    elif message["type"] == "CLIENT-MSG":
        print(message["Message"])



"""
Recive messages from server
"""
def reciveMsg():
    global ID
    global NAME

    
    while True:
        try:
            msg = sock.recv(SIZE).decode()
            msg = json.loads(msg)
            handleMessageRecv(msg)

        except:
            print("Some thing happened")

# Returns the room currently active for the user
def getActiveRoom():
    for i in roomMem:
        if roomMem[i] == True:
            return i
    return None

# Hanldes messages from the input stream
def handleInput(data):
    toSend = {"ID" : ID, "Name" : NAME}
    tok = data.strip()
    tok = tok.split(" ", 1)
    
    
    if tok[0] in commands:
        toSend["type"] = tok[0]
        if len(tok) == 2:
            
            toSend["Message"] = tok[1]   
        else: 
            toSend["Message"] = ""
    else:
        toSend["type"] = MESSAGE
        toSend["Message"] = data
        toSend["RoomName"] = getActiveRoom()

    return toSend    


"""
Input stream from user
"""
def getInput():
    msg = {"type": ""}
    global NAME
    global ID
    loginType = input("Are you Signing in or Registering? (Type Signin or Register)\n")
    # Initial inputs 
    while True:

        if loginType == REG:
            msg["type"] = loginType
            #msg["Registered"] = False
            if NAME == None:
                NAME = input("Please enter a Username you like:- \n")
                msg["Username"] = NAME
            password = getpass.getpass("Please set your password:-\n")
            confirmPass = getpass.getpass("Confirm your password:-\n")
            if password == confirmPass:
                msg["Password"] = password
                print(msg)
                sock.sendall(json.dumps(msg).encode())
                break
            else:
                print("\n ---Password Did Not Match---\n")    
                    
        elif loginType == SIGNIN:
            cliSignin(msg,loginType)
            break
        
        else:
            print("Sorrry wrong Input:")
            loginType = input("Are you Signing in or Registering? (Type Signin or Register)")
# 
    while True:
        try:
            if signedIn:
                i = getActiveRoom()
                if i == None:
                    msg = input("[]" + ":- ")
                    reply = handleInput(msg)
                    sendMsg(reply)
                elif i != None:
                    msg = input()
                    reply = handleInput(msg)
                    sendMsg(reply)
        except:
            pass
            
"""
Send messages to server
"""
def sendMsg(msg):
    try:
        if signedIn:
            sock.sendall(json.dumps(msg).encode())
    except:
        pass

'''
Hanldes signing in of the client
'''
def cliSignin(data, loginType):
    data["type"] = loginType
    print("In sign in")
    NAME = input("Please enter your Username:- ")
    password = getpass.getpass("Please enter your password:-")
    data["Username"] = NAME
    data["Password"] = password
    msg = data
    sock.sendall(json.dumps(msg).encode())
        
        
        


# Main funciton running everything
def main():
    global NAME
    global ID

    thread1 = threading.Thread(target=reciveMsg)
    thread1.start()
    
    
    thread2 = threading.Thread(target=getInput)
    thread2.start()
    

if __name__ == "__main__":
    main()