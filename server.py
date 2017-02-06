import SocketServer
import socket
import time
class ChatServerManager:
    """
        this class will handle all the clients connected to server
    """
    def __init__(self):
        #maximum users supported by chat server
        self.max_users=10
        #current no. of users connected to server
        self.cur_users=0
            #this will hold the sockets of connected clients
        self.clientlist={}
        #this list will contain current user names
        self.userlist=[]
        #commands dictionary
        self.commands={
        "/show_users":"list all users in the chatroom",
        "/exit":"leave the chatroom",
        "/user username message":"send private message to user",
        "/help":"lists all commands and their usage"    
        }

    def is_max_users(self):
        if self.cur_users<self.max_users:
            return False;
        return True;

    def set_username(self,clientsock,client):
        self.sendMsg(clientsock,"enter your username (maximum allowed characters is 30): ")
        client.name=self.recvMsg(clientsock,client)#save username in name 
        client.name=client.name.strip()#remove newline from username
        if client.name in self.userlist:
            while(True):
                self.sendMsg(clientsock,"please choose other name ,user with this name already exist\n")
                self.sendMsg(clientsock,"enter username again : ")
                if client.name in self.userlist:
                    pass
                else:
                    self.userlist.append(client.name)
                    break
        else:
            self.userlist.append(client.name)

    def setup_client(self,clientsock,client):
        if(not self.is_max_users()):
            self.set_username(clientsock,client)
            self.cur_users+=1
        else:
            self.sendMsg(clientsock,"sorry maximum users already connected ,try next time thanks for comming.\n")
            return False
        #save client socket in clientlist for later use
        self.clientlist[client.name]=client
        print client.name+" is connected to server"    
        #show current users in  chat room while entering to chat server
        self.show_users(clientsock,client)
        self.sendMsg(clientsock,"====type '/help' to get list of commands====\n")
        return True
    def sendMsg(self,clientsock,msg):
        clientsock.send(msg)

    def recvMsg(self,clientsock,client):
        return clientsock.recv(2048)

    def sendMsgToAll(self,msg,client,flag):
        for i in self.userlist:
            #send msg to all except itself
            if(i==client.name):
                pass
            else:
                if(flag):
                    self.clientlist[i].request.send(client.name+":"+msg)
                else:
                    self.clientlist[i].request.send(msg+"\n")
    def show_users(self,clientsock,client):
        self.sendMsg(clientsock,"====USERS==== \n")
        for i in range(len(self.userlist)):
            self.sendMsg(clientsock,str(i+1)+":"+self.userlist[i]+"\n")
        self.sendMsg(clientsock,"====END==== \n")

    def helperr(self,clientsock,client):
        self.sendMsg(clientsock,"====COMMANDS====\n")
        for i in self.commands:
            self.sendMsg(clientsock,i+" :"+self.commands[i]+"\n")
        self.sendMsg(clientsock,"====END==== \n")

    def private_msg(self,clientsock,client):
        if(client.command[1]==client.name):
            self.sendMsg(clientsock,"you can't send private message to itself\n")
        else:
            p8msg=""
            for i in range(2,len(client.command)):
                if(i<len(client.command)-1):
                    p8msg+=client.command[i]+" "
                else:
                    p8msg+=client.command[i]
            self.clientlist.get(client.command[1]).request.send("PRIVATE MESSAGE by "+client.name+":"+p8msg+"\n")

    def process_command(self,clientsock,client):
        if(client.command[0]=="/help"):
            self.helperr(clientsock,client)
        elif(client.command[0]=="/show_users"):
            self.show_users(clientsock,client)
        elif(client.command[0]=="/user"):
            if(len(client.command)==1):
                self.sendMsg(clientsock,"'invalid command ,type help for usage of command'\n")
                return
            if(client.command[1] in self.userlist):
                self.private_msg(clientsock,client)
            else:
                self.sendMsg(clientsock,"'invalid command ,type help for usage of command'\n")
        else:
            self.sendMsg(clientsock,"'invalid command ,type help for usage of command'\n")

    def remove_client(self,clientsock,client):
        self.cur_users-=1
        del self.clientlist[client.name]
        self.userlist.remove(client.name)

class ClientHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        if(not chat_server_manager.setup_client(self.request,self)):
            #chat_server_manager.remove_client(self.request,self)
            return 
        chat_server_manager.sendMsgToAll("====user '"+self.name+"' entered the chatroom====",self,False)
        while(True):
            print "users= %s"%chat_server_manager.userlist
            print "cur_users= %d"%chat_server_manager.cur_users
            try:
                self.msg=chat_server_manager.recvMsg(self.request,self)
                print self.name+" :"+self.msg.rstrip()
                if((self.msg[0]=="/")):
                    self.msg=self.msg.rstrip()
                    if(len(self.msg)==1):
                        chat_server_manager.sendMsg(self.request,"invalid commands type '/help' for right usage\n")
                        continue
                    self.command=self.msg.split(" ")
                    if(self.command[0]=="/exit"):
                        break
                    chat_server_manager.process_command(self.request,self)
                else:
                    chat_server_manager.sendMsgToAll(self.msg,self,True)
            except:
                print self.name+" left the chat room"
                chat_server_manager.sendMsgToAll("====user '"+self.name+"' left the chatroom====",self,False)
                print  "client left suddenly..exception raised"
                if(self.request):
                    chat_server_manager.remove_client(self.request,self)
                    return
                chat_server_manager.userlist.remove(self.name)
                del chat_server_manager.clientlist[self.name]
                return
        print self.name+" left the chat room"
        chat_server_manager.sendMsgToAll("====user '"+self.name+"' left the chatroom====",self,False)
        chat_server_manager.remove_client(self.request,self)

class MultiThreadedChatServer(SocketServer.ThreadingMixIn,SocketServer.TCPServer):
    """
        our multithreadedserver class
    """
    pass

chat_server_manager=ChatServerManager()
def main():
    try:
        # public ip adrress 192.10.1.2 or registered domain name like mymachinename.example.com
        host=raw_input("enter host ip address or hostname :").strip()
        #some open port better to use some well known port no.
        port=int(raw_input("enter port number for listening :").strip())

        server_addr=(host,port)
        #allows to reuse port no. if somehow server is stopped
        MultiThreadedChatServer.allow_reuse_address=True
        #create server instance
        server=MultiThreadedChatServer(server_addr,ClientHandler)
        #server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR)
        server.daemon=True
        server.serve_forever()
        #shutdown server if at the send of script
        server.shutdown()
    except socket.error ,(errcode,errmsg):
        print errmsg
        return
main() 
