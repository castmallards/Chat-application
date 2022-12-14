import sys
import socket
import threading
import json
import uuid
import select
import time

# global Variables
roomCap = 5
userList = []
roomsList = []
joinQueue = []


# GLOBALS
HOST = '0.0.0.0'
PORT = 5000
ADDR = (HOST, PORT)
BUFF = 1024
IDCOUNT = 0
FORMAT = "utf-8"
VIEWROOM = "!VIEW-CHATROOMS"
EXITROOM = "!EXIT-ROOM"
LEAVEROOM = "!LEAVE-ROOM"
CREATE = "!CREATE-ROOM"
JOINCHAT = "!JOIN-CHAT"
MESSAGE = "!MESSAGE"
HELP = "!HELP"
SIGNIN = "Signin"
REG = "Register"


serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind(ADDR)

# Premade client, initialized in main function
admin = ""

######################################################
#
#   CLASSES 
#
######################################################

# Client object
class Client:
    
    def __init__(self, addr, conn, ID, Name, password) -> None:
        self.addr = addr
        self.conn = conn
        self.ID = ID
        self.name = Name
        self.password = password
        self.signedIn = False
        self.activeRoom = None

    def setSignedIn(self, bool):
        self.signedIn = bool
    
    def setActRoom(self, roomName):
        self.activeRoom = roomName

    
    def setName(self, name):
        self.name = name


# Chat Room object
class ChatRoom:
    def __init__(self, name) -> None:
        self.name = name
        self.members = []
        self.maxMem = 5
    
    def addMember(self, client):
        if client not in self.members:
            self.members.append(client)
            
    
    def setMaxMem(self, capcity):
        self.maxMem = capcity    
    
    def removeMember(self, client):
        ret = False
        if client in self.members:
            self.members.remove(client)
            ret = True
        return ret
        
            
    def getName(self):
        return self.name
        
    def getMembersList(self):
        ret = "["
        for mem in self.members:
            ret += mem.name + ", "
        ret += "]"
        return ret
        
    def getNumMembers(self):
        return len(self.members)
    
    def getMemberbyID(self,ID):
        user =  next((obj for obj in self.members 
                  if obj.ID == ID),None)
        return user
        

        

######################################################
#
#   FUNCTIONS 
#
######################################################

# Handles all in coming messages and replies back to the client
def commandHandle(data, conn, addr):
    reply = None
    
    if data["type"] == REG:
        pass
    elif data["type"] == SIGNIN:
        reply, cli = clientSignin(data, conn, addr)
        
    elif data["type"] == CREATE:
        reply = makeChatRoom(data)
        return reply
    elif data["type"] ==  VIEWROOM:
        reply = viewRooms()  
        return reply
    elif data["type"] == HELP:    
        reply = sendHelp()
    elif data["type"] == EXITROOM:
        reply = exitRoom(data)
    elif data["type"] == JOINCHAT:
        reply = joinRoom(data)
        return reply
    elif data["type"] == MESSAGE:
        reply = broadcastMsg(data)
    elif data["type"] == LEAVEROOM:
        reply = leaveRoom(data)
    
    return reply


'''
When Client leaves the room
'''
def leaveRoom(data):
    roomName = data["Message"]
    clientID = data["ID"]
    # return the room if its in the list
    # else it returns None
    room =  next((obj for obj in roomsList 
                  if obj.name == roomName),None)
    
    # return the client if its in the list
    # else it returns None
    user =  next((obj for obj in userList 
                  if obj.ID == clientID),None)
    
    reply = {"type" : "LEAVE-REPLY", "Success" : True, 
             "ReplyMessage" : "Left the Chatroom: " + room.name, "RoomName": room.name}
    
    if room != None and user != None:
        if room.removeMember(user):
            user.activeRoom = None
        else:
            reply["Success"] = False
            reply["ReplyMessage"] = "There is no space in Chatroom: " + room.name
    else:
        reply["Success"] = False
        reply["ReplyMessage"] = "Chatroom: " + room.getName() + " doesn't exist"

    return reply
    
    
'''
Registering a new client
'''

def registerClient(data):
    toSend = {"type" : data["type"]}
    userName = data["Username"]
    if data["type"]:
        pass

'''
Sends a list of commands to the client
'''
def sendHelp():

    commands = [CREATE + " - Command followed by the name creates a new room '!CREATE-ROOM room_name' (no spaces in the name). You can add a number after the 'room_name' to set max number of members in the group",
                VIEWROOM + " - This command shows the list of rooms and members"
                ,JOINCHAT + " - Command followed by the name of the room adds you as a member of that room"
                ,EXITROOM + " - Command exits you of the current room",
                LEAVEROOM + " - Command followed by the room name permanently leaves the room and you're no longer a member of the room"]
    reply = {"type" : "HELP-REPLY", "ComList" : commands}
    return reply

'''
Makes client inactive so it doesn't receive messages
'''   
def exitRoom(data):
    reply = {"type" : "EXIT-REPLY", "Success" : True}
    clientID = data["ID"]
    user =  next((obj for obj in userList 
                  if obj.ID == clientID),None)
    
    if user != None and user.activeRoom != None:
        forMembers = {"type" : MESSAGE, "ID" : data["ID"], "RoomName" : user.activeRoom, "Message": "(Left the chat room...)"}
        user.activeRoom = None
        broadcastMsg(forMembers)
    else:
        reply["Success"] = False
    
    return reply

'''
Adds client to the Chat room
'''    
def joinRoom(data):
    roomName = data["Message"]
    clientID = data["ID"]
    
    # return the room if its in the list
    # else it returns None
    room =  next((obj for obj in roomsList 
                  if obj.name == roomName),None)
    
    # return the client if its in the list
    # else it returns None
    user =  next((obj for obj in userList 
                  if obj.ID == clientID),None)
    
    reply = {"type" : "JOIN-REPLY", "Success" : True, 
             "ReplyMessage" : "Joined the Chatroom: " + room.name, "RoomName": room.name}
    
    # If both the room and client exits
    if room != None and user != None:
        num1 = room.getNumMembers()
        num2 = room.maxMem
        try:
            if num1 < num2:
                user.setActRoom(roomName)
                room.addMember(user)
            elif user in room.members:
                user.setActRoom(roomName)
            else:
                reply["Success"] = False
                reply["ReplyMessage"] = "There is no space in Chatroom: " + room.name
        except Exception as e:
            print(e)
    else:
        reply["Success"] = False
        reply["ReplyMessage"] = "Chatroom: " + room.getName() + " doesn't exist"
    
    return reply

       
'''
This method returns a list of rooms and its members
'''  
def viewRooms():
    reply = {"type" : "VIEWROOM-REPLY", "RoomList": ""}
    noRoomMsg = "There are no rooms currently :( ...\nWould you like to create one? You can create a room using the command: !CREATE 'Room Name'"
    showRooms = ""
    listToSend = []
    if roomsList:
        num = 1
        for rooms in roomsList:
            memNum = rooms.getNumMembers()
            showRooms = str(num) + ") " + rooms.name + " (" +  str(memNum) + "/" + str(rooms.maxMem) + ")" + rooms.getMembersList() + "\n"
            num += 1
            listToSend.append(showRooms)
            
        reply["RoomList"] = listToSend
        reply["Success"] = True    
    else:
        reply["RoomList"] = noRoomMsg
        reply["Success"] = False 

    return reply
    
'''
Creates a room requested by the client
'''
def makeChatRoom(msg):
    tok = msg["Message"].split(" ")
    roomName = tok[0]
    cap = 5
    if len(tok) == 2:
        cap = int(tok[1])
    reply = {"type" : "CREATE-REPLY", "Success": False}
    if roomExists(roomName) == False:
        newRoom = ChatRoom(roomName)
        newRoom.setMaxMem(cap)
        roomsList.append(newRoom)
        reply["Success"] = True
        reply["Message"] = "Chat Room created!"
    else:
        reply["Success"] = False
        reply["Message"] = "Chat Room already exists"
    
    return reply

# Returns true if rooms exits in the list
def roomExists(name):
    ret = False
    for room in roomsList:
        if room.name == name:
            ret = True
    
    return ret

# Send messages to other clients
def broadcastMsg(data):
    roomName = data["RoomName"]
    clientID = data["ID"]
    reply  = {"type" : "MESSAGE-REPLY"}
    toClients = {"type" : "CLIENT-MSG"}
    # return the room if its in the list
    # else it returns None
    room =  next((obj for obj in roomsList 
                  if obj.name == roomName),None)
    
    # return the client if its in the list
    # else it returns None
    # This is the client sending the message
    user =  next((obj for obj in userList 
                  if obj.ID == clientID),None)
    
    # If room and user exist then we send message to every member of the room
    if room and user:
        chatMem = room.members
        # What other members will recieve
        toClients["Message"] = "[" + user.name + "]:- " + data["Message"]
        for members in chatMem:
            # If the member is not the sender and they are currently active in that room
            if members != user and members.activeRoom == roomName:
                sendMessage(members, json.dumps(toClients))
        reply["Success"] = True    
    else:
        reply["Success"] = False
    return reply


# Send messages to a certain client
def sendMessage(cli, data):
    try:
        cli.conn.sendall(data.encode())
    except Exception as e:
        print("[Exception]", e)

'''
Client signin
'''
def clientSignin(data, conn, addr):
    global admin
    
    replyToCli = {"type" : "Signin"}
    print(data)
    userName = data["Username"]
    password = data["Password"]
    
    # find a user in the list that is trying to sign in
    print("Checking for valid user")
    user =  next((obj for obj in userList 
                if obj.name == userName),None)
    
    client = None
    if user != None and user.password == password:
        print("User valid")
        replyToCli = {"type" : "Signin" , "ID" : user.ID, "signedIn" : True,
                        "Username" : user.name}
        user.conn = conn
        user.addr = addr
        user.setSignedIn(True)
        client = user
    
    else:
        replyToCli = {"type" : "Signin" , "ID" : user.ID, "signedIn" : False}
    
    return replyToCli, client

# Constantly recive messages from clients      
def receiveMsg(conn,addr):
    
    # Always get login type frist
    # Gets the name of the client and adds it to the list of clients
    loginType = conn.recv(BUFF).decode()
    recv_msg = json.loads(loginType)
    client = None
    
    print(recv_msg)
    # Hanldes the initial registeration
    if recv_msg["type"] == REG:
        cli = Client(addr, conn, getID(), recv_msg["Username"] , recv_msg["Password"])
        userList.append(cli)
        client = cli
        replyToCli = {"type" : "Registered" , "Registered" : True, "ID" : cli.ID }
        conn.sendall(json.dumps(replyToCli).encode())
        
    # Handles the signin
    if recv_msg["type"] == SIGNIN:
        reply, cli = clientSignin(recv_msg, conn, addr)
        client = cli
        conn.sendall(json.dumps(reply).encode())

    while True:
        try:
            msg = json.loads(conn.recv(BUFF).decode())
            print(msg)
            reply = commandHandle(msg, conn, addr)
            print(reply)
            # Sends messages to clients
            # Make sure both there's client and reply 
            if reply != None and client != None:
                sendMessage(client,json.dumps(reply))
            else:
                print("Reply or client is None")           
        except:
            pass

# Gets id for new clients that connect and increaments the global ID counter        
def getID():
    global IDCOUNT
    id = IDCOUNT
    IDCOUNT += 1
    return id
    
# Handles new clients connecting to the server
def incomingClients():
     while True:
        try:
            conn, addr = serversocket.accept()
            print(f"[{time.time()}]:-Client connected successfully, {addr[0]}, {addr[1]}")
            threading.Thread(target=receiveMsg, args=(conn, addr,)).start()
            
        except Exception as e:
            print("Error", e)
            break


# Main function starting the server
def main():
    serversocket.listen()
    print("SERVER STARTED, waiting for client")
    
    thread = threading.Thread(target=incomingClients)
    thread.start()
    thread.join()

    serversocket.close() 


if __name__ == "__main__":
    admin = Client(None,None, getID(), "Admin", "password")
    userList.append(admin)
    main()
    