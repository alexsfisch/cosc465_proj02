#!/usr/bin/env python

__author__ = "jsommers@colgate.edu"
__doc__ = '''
A simple model-view controller-based message board/chat client application.
'''

import sys
import Tkinter
import socket
#from select import select
import select
import argparse
import time

class MessageBoardNetwork(object):
    '''
    Model class in the MVC pattern.  This class handles
    the low-level network interactions with the server.
    It should make GET requests and POST requests (via the
    respective methods, below) and return the message or
    response data back to the MessageBoardController class.
    '''

    def __init__(self, host, port, retries, timeout):
        '''
        Constructor.  You should create a new socket
        here and do any other initialization.
        '''
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.retries = retries
        self.timeout = timeout

    #checksum from lab. Can now use in both getMessages and in postMessages
    def checkSum(self, message):
        charBinaryRep = []
        for i in range(len(message)):
            charBinaryRep.append(ord(message[i]))

        
        lengthOfList = len(charBinaryRep)
        x = 0

        for g in range(lengthOfList):
            x = x ^ charBinaryRep[g]
        return chr(x)

    def getMessages(self, sequence):
        '''
        You should make calls to get messages from the message 
        board server here.
        '''

        #new header for project 2
        checkSumValue = self.checkSum("GET")
        header = 'C' + sequence + checkSumValue
        tempMessage = header + "GET" 
        print "*" * 50
        print "checkSum " + checkSumValue
        print "tempMessage:" + tempMessage
        
        i = 0
        while i < self.retries:
            print "tempMessage  ", tempMessage
            x = self.sock.sendto(tempMessage, (self.host, self.port))

            (inputready, outputready, exceptready) = select.select([self.sock], [], [], .1) 
            print "input ready    ", inputready
            if inputready: #if there is something to be retreived from server
                print ("*" * 50)
                message = self.sock.recvfrom(1500)
                print "ACK:     ", message
                strlist = message[0].split('::')
                return strlist

            else: #if there is nothing to be retreived from server
                time.sleep(self.timeout) 
                i += 1 
        return 0

    def postMessage(self, user, message, sequence):
        '''
        You should make calls to post messages to the message 
        board server here.
        '''
       
        #print message
        message = "POST " + user + "::" + message
        checkSumValue = self.checkSum(message)
        #print "checkSumValue    ", checkSumValue
        messageFinal = 'C' + sequence + checkSumValue + message
        #print "posting this message:        ", messageFinal

        if len(user) > 8 or len(user) == 0 or "::" in user: #check username length
            return -2
    
        if len(message) >= 60: #make sure length of message is <= 60 characters
            return -1 
        
        i = 0
        while i < self.retries:

            x = self.sock.sendto(messageFinal, (self.host, self.port))

            (inputready, outputready, exceptready) = select.select([self.sock], [], [], .1) 
            print "input ready    ", inputready
            if inputready: #if there is something to be retreived from server
                print ("*" * 50)
                message = self.sock.recvfrom(1500)
                print "ACK:     ", message
                strlist = message[0].split('::')
                return strlist

            else: #if there is nothing to be retreived from server
                time.sleep(self.timeout) 
                i += 1
        return -3 #this is wrong

class MessageBoardController(object):
    '''
    Controller class in MVC pattern that coordinates
    actions in the GUI with sending/retrieving information
    to/from the server via the MessageBoardNetwork class.
    '''

    def __init__(self, myname, host, port, retries, timeout):
        self.name = myname
        self.view = MessageBoardView(myname)
        self.view.setMessageCallback(self.post_message_callback)
        self.net = MessageBoardNetwork(host, port, retries, timeout)
        self.sequence = '0'
        #print self.port

    def run(self):
        self.view.after(1000, self.retrieve_messages)
        self.view.mainloop()

    def post_message_callback(self, m):
        '''
        This method gets called in response to a user typing in
        a message to send from the GUI.  It should dispatch
        the message to the MessageBoardNetwork class via the
        postMessage method.
        '''
        x = self.net.postMessage(self.name, m, self.sequence)

        ##Error Handling:
        if x == -1:
            self.view.setStatus("Message longer 60 characters.")
            return "ERROR Message too long" 
        elif x == -2:
            self.view.setStatus("Username invalid.")
            return "ERROR Username invalid."
        elif x == -3:
            self.view.setStatus("No ACK from Server")
            return "No ACK from Server"
        else:
            print "no error!!!!!!!!!!"
            self.view.setStatus("Message posted successfully.")


    def retrieve_messages(self):
        '''
        This method gets called every second for retrieving
        messages from the server.  It calls the MessageBoardNetwork
        method getMessages() to do the "hard" work of retrieving
        the messages from the server, then it should call 
        methods in MessageBoardView to display them in the GUI.

        You'll need to parse the response data from the server
        and figure out what should be displayed.

        Two relevant methods are (1) self.view.setListItems, which
        takes a list of strings as input, and displays that 
        list of strings in the GUI, and (2) self.view.setStatus,
        which can be used to display any useful status information
        at the bottom of the GUI.
        '''
        self.view.after(1000, self.retrieve_messages)

        messagedata = self.net.getMessages(self.sequence)

        if messagedata == 0:
            print "no response from server"
            return 0
        print messagedata
        #print "MESSAGEDATA FULL:    ", messagedata
        #check for OK or Error
        #print "messagedata:    ", messagedata[0]
        tempCheck = messagedata[0]
        tempCheck = tempCheck.split(' ')
        if "ERROR" in tempCheck:
            self.view.setStatus("Messages retrieved unsuccesfully :(")
            return "ERROR"

        if "GET" in tempCheck:
            return 0
        #THIS IS WHERE WE GET RID OF THE HEADER + OK
        messagedata[0] = messagedata[0][6:]
                
        #no new messages on server
        if  len(messagedata[0]) == 6:
            print "NO NEW MESSAGES ON SERVER"
                
            if self.sequence == '0':
                self.sequence = '1'
            else:
                self.sequence = '0'
            
            return 0

        finalMessages = []

        tempMessageData = messagedata[0][3:]
        final = []
        tempstr = ""
        x = 0
        for i in range(len(messagedata)):
            tempstr += " " + messagedata[i]
            if (i % 3) == 2:
                final.append(tempstr)
                tempstr = ""


        self.view.setListItems(final)
        self.view.setStatus("Retrieved " + str(len(final)) + " messages succesfully :)")
        if self.sequence == '0':
           self.sequence = '1'
        else:
           self.sequence = '0'


class MessageBoardView(Tkinter.Frame):
    '''
    The main graphical frame that wraps up the chat app view.
    This class is completely written for you --- you do not
    need to modify the below code.
    '''
    def __init__(self, name):
        self.root = Tkinter.Tk()
        Tkinter.Frame.__init__(self, self.root)
        self.root.title('{} @ messenger465'.format(name))
        self.width = 80
        self.max_messages = 20
        self._createWidgets()
        self.pack()
    def _createWidgets(self):
        self.message_list = Tkinter.Listbox(self, width=self.width, height=self.max_messages)
        self.message_list.pack(anchor="n")

        self.entrystatus = Tkinter.Frame(self, width=self.width, height=2)
        self.entrystatus.pack(anchor="s")

        self.entry = Tkinter.Entry(self.entrystatus, width=self.width)
        self.entry.grid(row=0, column=1)
        self.entry.bind('<KeyPress-Return>', self.newMessage)

        self.status = Tkinter.Label(self.entrystatus, width=self.width, text="starting up")
        self.status.grid(row=1, column=1)

        self.quit = Tkinter.Button(self.entrystatus, text="Quit", command=self.quit)
        self.quit.grid(row=1, column=0)


    def setMessageCallback(self, messagefn):
        '''
        Set up the callback function when a message is generated 
        from the GUI.
        '''
        self.message_callback = messagefn

    def setListItems(self, mlist):
        '''
        mlist is a list of messages (strings) to display in the
        window.  This method simply replaces the list currently
        drawn, with the given list.
        '''
        self.message_list.delete(0, self.message_list.size())
        self.message_list.insert(0, *mlist)
        
    def newMessage(self, evt):
        '''Called when user hits entry in message window.  Send message
        to controller, and clear out the entry'''
        message = self.entry.get()  
        if len(message):
            self.message_callback(message)
        self.entry.delete(0, len(self.entry.get()))

    def setStatus(self, message):
        '''Set the status message in the window'''
        self.status['text'] = message

    def end(self):
        '''Callback when window is being destroyed'''
        self.root.mainloop()
        try:
            self.root.destroy()
        except:
            pass

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='COSC465 Message Board Client')
    parser.add_argument('--host', dest='host', type=str, default='localhost',
                        help='Set the host name for server to send requests to (default: localhost)')
    parser.add_argument('--port', dest='port', type=int, default=1111,
                        help='Set the port number for the server (default: 1111)')
    parser.add_argument("--retries", dest='retries', type=int, default=3,
                        help='Set the number of retransmissions in case of a timeout')
    parser.add_argument("--timeout", dest='timeout', type=float, default=0.1,
                        help='Set the RTO value')
    args = parser.parse_args()
    

    myname = raw_input("What is your user name (max 8 characters)? ")

    app = MessageBoardController(myname, args.host, args.port, args.retries, args.timeout)
    app.run()


