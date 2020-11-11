from tkinter import *
from tkinter import messagebox
from tkinter import ttk
from PIL import Image, ImageTk
import socket
import threading
import sys
import traceback
import os
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    NEXT = 4
    PREVIOUS = 5
    STOP = 6
    DESCRIBE = 7

    RTSP_VERSION = 'RTSP/1.0'
    TRANSPORT = 'RTP/UDP'

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.initialWidgets()
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = 0
        self.requestSent = -1
        self.teardownAcked = 0
        self.frameNbr = 0
        self.connectToServer()

        self.window= None
        self.progressbar={}
        self.extend=0
        self.stopAcked = 0
        self.toggle =0
        self.frameReceive=0
        self.frameLoss=0


    def initialWidgets(self):
        # Create Previous button
        self.start = Button(self.master, width=20, padx=3, pady=3)
        self.start["text"] = "Basic"
        self.start["command"] = self.createWidgetsBasic
        self.start.grid(row=3, column=1, padx=2, pady=2, columnspan=2)

        # Create Next button
        self.pause = Button(self.master, width=20, padx=3, pady=3)
        self.pause["text"] = "Extends"
        self.pause["command"] = self.createWidgetsExtend
        self.pause.grid(row=3, column=3, padx=2, pady=2, columnspan=2)

        



    def createWidgetsBasic(self):

        self.extend = 0
        """Build GUI."""
        if not self.window:
            self.window = Toplevel(self.master)
        else:
            self.window.destroy()
            self.window = Toplevel(self.master)

        # Create Setup button
        self.setup = Button(self.window, width=20, padx=3, pady=3)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie
        self.setup.grid(row=2, column=0, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.window, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.window, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.window, width=20, padx=3, pady=3)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient
        self.teardown.grid(row=2, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.window, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

    def createWidgetsExtend(self):
        self.extend = 1
        if not self.window:
            self.window = Toplevel(self.master)
        else:
            self.window.destroy()
            self.window = Toplevel(self.master)

        # Create Setup button
        self.setup = Button(self.window, width=20, padx=3, pady=3)
        self.setup["text"] = "Stop"
        self.setup["command"] = self.stopMovieExtends
        self.setup.grid(row=3, column=2, padx=2, pady=2)

        # Create Play button
        self.start = Button(self.window, width=20, padx=3, pady=3)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovieExtends
        self.start.grid(row=3, column=0, padx=2, pady=2)

        # Create Pause button
        self.pause = Button(self.window, width=20, padx=3, pady=3)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie
        self.pause.grid(row=3, column=1, padx=2, pady=2)

        # Create Teardown button
        self.teardown = Button(self.window, width=20, padx=3, pady=3)
        self.teardown["text"] = "Describe"
        self.teardown["command"] = self.showDescribeExtends
        self.teardown.grid(row=3, column=3, padx=2, pady=2)

        # Create a label to display the movie
        self.label = Label(self.window, height=19)
        self.label.grid(row=0, column=0, columnspan=4,
                        sticky=W+E+N+S, padx=5, pady=5)

        # Create progress bar
        self.progressbar = ttk.Progressbar(
            self.window, orient='horizontal', length=286, mode='determinate')
        self.progressbar.grid(row=1, column=0, columnspan=4,
                              sticky=W+E+N+S, padx=5, pady=5)

        # Create Previous button
        self.start = Button(self.window, width=20, padx=3, pady=3)
        self.start["text"] = "<<"
        self.start["command"] = self.jumbPrev
        self.start.grid(row=2, column=1, padx=2, pady=2)

        # Create Next button
        self.pause = Button(self.window, width=20, padx=3, pady=3)
        self.pause["text"] = ">>"
        self.pause["command"] = self.jumbNext
        self.pause.grid(row=2, column=2, padx=2, pady=2)

        self.lable_describe = Label(self.window,
                    font=("Arial Bold", 16, ), bg='#1E2F42', fg='White', width=20)


    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        # Delete the cache image from video
        os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def jumbPrev(self):
        if self.state != self.INIT:
            self.sendRtspRequest(self.PREVIOUS)
            data = self.rtpSocket.recv(20480)
            if data:
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)

                currFrameNbr = rtpPacket.seqNum()
                print("Current Seq Num: " + str(currFrameNbr))

                self.frameNbr = currFrameNbr
                self.updateMovie(self.writeFrame(
                    rtpPacket.getPayload()))

    def jumbNext(self):
        if self.state != self.INIT:
            self.sendRtspRequest(self.NEXT)
            data = self.rtpSocket.recv(20480)
            if data:
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)

                currFrameNbr = rtpPacket.seqNum()
                print("Current Seq Num: " + str(currFrameNbr))

                self.frameNbr = currFrameNbr
                self.updateMovie(self.writeFrame(
                    rtpPacket.getPayload()))

    def playMovie(self):
        """Play button handler."""
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def playMovieExtends(self):
        if self.state == self.INIT:
            self.stopAcked = 0
            self.rtspSeq = 0
            self.sessionId = 0
            self.requestSent = -1
            self.teardownAcked = 0
            self.frameNbr = 0
            self.frameReceive=0
            self.frameLoss=0
            self.sendRtspRequest(self.SETUP)

        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)
        
    def stopMovieExtends(self):
        if self.state != self.INIT:
            self.sendRtspRequest(self.STOP)
            try:
                os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
            except:
                pass

    def showDescribeExtends(self):
        if self.toggle == 0:
            self.lable_describe.grid(row=4, column=3, padx=2, pady=2)
            self.toggle = 1
        else:
            self.lable_describe.grid_remove()
            self.toggle =0

        





        
        


    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(20480)
                if data:
                    self.frameReceive +=1
                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    print("Current Seq Num: " + str(currFrameNbr))

                    if currFrameNbr >= self.frameNbr:  # Discard the late packet
                        if currFrameNbr-self.frameNbr>1:
                            self.frameLoss += currFrameNbr-self.frameNbr
                            print('-'*60)
                            print(' '*20+f'FRAME LOSS: {currFrameNbr-self.frameNbr}'+' '*20)
                            print('-'*60)
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(
                            rtpPacket.getPayload()))
                        
                        
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked or self.stopAcked:
                    self.rtpSocket.close()
                    print('-'*60)
                    print(' '*20+f'LOSS: {self.frameLoss}'+' '*20)
                    print(' '*20+f'RECEIVE: {self.frameReceive}'+' '*20)
                    print(' '*20+f'LOSS RATE: {self.frameLoss/self.frameNbr:.6f}'+' '*20)
                    print('-'*60)
                    break
                if self.extend:
                    if self.frameNbr >= self.progressbar['maximum']:
                        self.stopMovieExtends()

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        try:
            photo = ImageTk.PhotoImage(Image.open(imageFile))
            self.label.configure(image=photo, height=288)
            self.label.image = photo
            self.progressbar['value'] = self.frameNbr
        except:
            raise("updateMovie ERROR")

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            messagebox.showwarning(
                'Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""
        # -------------
        # TO COMPLETE
        # -------------

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = f'SETUP {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nTransport: {self.TRANSPORT}; client_port= {self.rtpPort}'
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.SETUP

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1

            # Write the RTSP request to be sent.
            # request = ...
            request = f'PLAY {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PLAY
            # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = f'PAUSE {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.PAUSE

            # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            # Update RTSP sequence number.
            # ...
            self.rtspSeq = self.rtspSeq + 1
            # Write the RTSP request to be sent.
            # request = ...
            request = f'TEARDOWN {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # Keep track of the sent request.
            # self.requestSent = ...
            self.requestSent = self.TEARDOWN

        elif requestCode == self.PREVIOUS:
            self.rtspSeq = self.rtspSeq + 1
            request = f'PREVIOUS {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # self.requestSent = self.PREVIOUS

        elif requestCode == self.NEXT:
            self.rtspSeq = self.rtspSeq + 1
            request = f'NEXT {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # self.requestSent = self.NEXT

        elif requestCode == self.STOP:
            self.rtspSeq = self.rtspSeq + 1
            request = f'STOP {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # self.requestSent = self.NEXT
            self.requestSent = self.STOP

        elif requestCode == self.DESCRIBE:
            request = f'DESCRIBE {self.fileName} {self.RTSP_VERSION}\nCSeq: {self.rtspSeq}\nSession: {self.sessionId}'
            # self.requestSent = self.NEXT
        

        else:
            return

        # Send the RTSP request using rtspSocket.
        # ...
        self.rtspSocket.send(request.encode('utf-8'))

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))
                if self.extend: 
                    self.lable_describe['text'] = reply.decode("utf-8")
                
            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break
            

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = data.split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = int(lines[2].split(' ')[1])
            totalFrame = int(lines[3].split(' ')[1])
            # New RTSP session ID
            if self.sessionId == 0:
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # -------------
                        # TO COMPLETE
                        # -------------
                        # Update RTSP state.
                        # self.state = ...
                        self.state = self.READY
                        self.progressbar['maximum'] = totalFrame
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        # self.state = ...
                        self.state = self.PLAYING
                    elif self.requestSent == self.PAUSE:
                        # self.state = ...
                        self.state = self.READY

                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        # self.state = ...
                        self.state = self.INIT

                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1
                    elif self.requestSent == self.STOP:
                        # self.state = ...
                        self.state = self.INIT
                        self.stopAcked = 1

                    
                        
                        # Flag the teardownAcked to close the socket.

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # -------------
        # TO COMPLETE
        # -------------
        # Create a new datagram socket to receive RTP packets from the server
        # self.rtpSocket = ...
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Set the timeout value of the socket to 0.5sec
        # ...
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            # ...
            self.rtpSocket.bind(('', self.rtpPort))
            self.state = self.READY
            if self.extend:
                self.playMovie()
        except:
            # self.state = self.INIT
            messagebox.showwarning(
                'Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        # self.pauseMovie()
        if messagebox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()
