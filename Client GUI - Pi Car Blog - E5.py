"""
This is a WiFi RC app (2 of 2 - Client / Car side). 

It allows for the connection and sending of video from the client at the car to the server at a remote PC.
As well it will recieve control infromation using an array of integar values for each control surface 
(The code at the server was designed with a 18 button - Logitech Dual Action Pad - change as you like)
from the remote server PC. 

The control and video threads are seperate and must be started using GUI on both ends. The client status
will show in the console window. 

Its not perfect but should provide decent base to build a Remote RC or learning rig from. 

Created on Sun Sep 27 21:58:04 2020

@author: Ian Horseman
"""

import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot, QByteArray
from PyQt5.QtGui import QIcon, QImage, QPixmap
import cv2
import io
import socket               # Import socket module
import numpy as np
from gpiozero import Servo
import time
import RPi.GPIO as GPIO
from time import sleep







class InputClientThread(QThread):
    
    offInputFlag = 0
    
    def run(self):
        #----------------------Client Connection Infomration-------------------
        s = socket.socket()         # Create a socket object
        #host = socket.gethostname() # Get local machine name
        host = "192.168.1.81"       # Server address (laptop .68 and tower .81)
        port = 12345                # Reserve a port for your service.

        print(host)

        s.connect((host, port))

        Controller = np.zeros([50])

        #----------------------Motor Setup Infomration-------------------
        #Right motor contorller Lines
        #RR, and RF motors are wired in parallel
        Rin1 = 16
        Rin2 = 20
        Ren = 21

        #Left motor contorller Lines
        Lin1 = 23
        Lin2 = 24
        Len = 25

        #Initialize Right
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Rin1,GPIO.OUT)
        GPIO.setup(Rin2,GPIO.OUT)
        GPIO.setup(Ren,GPIO.OUT)
        GPIO.output(Rin1,GPIO.LOW)
        GPIO.output(Rin2,GPIO.LOW)
        pR=GPIO.PWM(Ren,50)

        #Initialize Left
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(Lin1,GPIO.OUT)
        GPIO.setup(Lin2,GPIO.OUT)
        GPIO.setup(Len,GPIO.OUT)
        GPIO.output(Lin1,GPIO.LOW)
        GPIO.output(Lin2,GPIO.LOW)
        pL=GPIO.PWM(Len,50)
        
        #Initialize Camera Servos
        GPIO.setup(19,GPIO.OUT) # set pin 19 as output,
        GPIO.setup(26,GPIO.OUT)
        servoV = GPIO.PWM(19,50) # set the PWM to 50 = 50 Hz
        servoH = GPIO.PWM(26,50) # set the PWM to 50 = 50 Hz
        servoV.start(0)
        servoH.start(0)
        
        servovalH = 6.8 #centre horz
        servovalV = 6.8 #centre vert
        servoV.ChangeDutyCycle(servovalV)
        servoH.ChangeDutyCycle(servovalH) 
        
        
        #Start Motors in Stop
        pR.start(0)
        pL.start(0)

        #----------------------Contorl Main Loop--------------------------------------
        while(1):
            #control data string - all buttons packaged together - comma delimited.
            ans = s.recv(1024).decode("ascii")

    
            #check for the flag to close remote control pulling from server, break loop once seen and close ports down.
            if ans == "Y":
                break
    
                #*******Parse Inputs
                #normal operation, parse out input commands from remote PC
            i=0
            while(1):
        
                index1 = ans.find(",")
                if index1 == -1:
                    break
            
                if i > 18:
                    break
            
                Controller[i] = float(ans[0:index1])
                ans = ans[index1+1:]
                i=i+1
        
    

            #*******Use Inputs to Update Motor Settings
            if Controller[1] < -0.05:
                print("Rforward")
                GPIO.output(Rin1,GPIO.HIGH)
                GPIO.output(Rin2,GPIO.LOW)
        
                Duty = Controller[1] * 100 * (-1)
                pR.ChangeDutyCycle(Duty)
            elif Controller[1] > 0.05:
                print("Rbackward")
                GPIO.output(Rin1,GPIO.LOW)
                GPIO.output(Rin2,GPIO.HIGH)
        
                Duty = Controller[1] * 100
                pR.ChangeDutyCycle(Duty)
            else:
                pR.ChangeDutyCycle(0)

            if Controller[3] < -0.05:
                print("Lforward")
                GPIO.output(Lin1,GPIO.HIGH)
                GPIO.output(Lin2,GPIO.LOW)
        
                Duty = Controller[3] * 100 * (-1)
                pL.ChangeDutyCycle(Duty)
            
            elif Controller[3] > 0.05:
                print("Lbackward")
                GPIO.output(Lin1,GPIO.LOW)
                GPIO.output(Lin2,GPIO.HIGH)
        
                Duty = Controller[3] * 100
                pL.ChangeDutyCycle(Duty)
            else:
                pL.ChangeDutyCycle(0)
            
            #Move servos in half steps, approx 9 degrees
            #Controller 16 is left(-1) right(1) on the game pad
            #Controller 17 is up(-1) down(1) on the game pad 
            if Controller[16]== -1:
                servovalH = servovalH + 0.2
                
            
            elif Controller[16]== 1:
                servovalH = servovalH - 0.2

            if Controller[17]== -1:
                servovalV = servovalV + 0.2
                

            elif Controller[17]== 1:
                servovalV = servovalV - 0.2
            
            
            # Check for an over condition
            if servovalH > 12:
                servovalH = 12

            elif servovalH < 2:
                servovalH = 2


            if servovalV > 12:
                servovalV = 12

            elif servovalV < 3:
                servovalV = 3
             
             
            #print(Controller[16]," ", Controller[17])
            
            if Controller[16] == 0 and Controller[17] == 0:
                servoV.ChangeDutyCycle(0)
                servoH.ChangeDutyCycle(0)
            
            else:
                #Servo position is from duty = 2 to 12 -> 0 to 180 degress.
                # note that the V servo on the car rig, can really only move from 3 to 12
                servoV.ChangeDutyCycle(servovalV)
                servoH.ChangeDutyCycle(servovalH)
                
                
            
        #-------------------End Client - End Program------------------------    
        print("Client Shutdown")
        s.close                     # Close the socket when done
        GPIO.cleanup()              # Clear GPIO ports
        

class VidThread(QThread):
    changePixmap = pyqtSignal(QImage)
    offVidFlag = 0
    
    def run(self):
        cap = cv2.VideoCapture(0)
        
        #----------------------Video Client Connection Infomration-------------------
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
        #host = socket.gethostname() # Get local machine name
        host = "192.168.1.81"       # Server address (laptop .68 and tower .81)
        port = 12346                # Reserve a port for your video service.

        print(host)

        s2.connect((host, port))
        
        while True:
            ret, frame = cap.read()
            if ret:
                # https://stackoverflow.com/a/55468544/6622587
                rgbImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = rgbImage.shape
                bytesPerLine = ch * w
                convertToQtFormat = QImage(rgbImage.data, w, h, bytesPerLine, QImage.Format_RGB888)
                p = convertToQtFormat.scaled(320, 240, Qt.KeepAspectRatio)
                self.changePixmap.emit(p)
                
                
                
                #dim = Width, Height
                
                W = 320
                H = 240
                ch = 3
                dim = (W, H)
                resized = cv2.resize(rgbImage, dim, interpolation = cv2.INTER_NEAREST)
                                
                #Load image into array for transmission
                imageRGBarray = np.asarray(resized)
                                                               
                #Height Send
                byteRowcountMSG = H.to_bytes(16, 'little')
                s2.send(byteRowcountMSG)
                
                byteWidthMSG = W.to_bytes(16, 'little')
                s2.send(byteWidthMSG)
                
                           
                #flatten image for transmission of sockets to server    
                sendflat = imageRGBarray.flatten()
                    
                chunkst = 0
                           
                #width of full message in bytes 
                fullbytelen = np.size(sendflat,0)    #How many bytes (one byte per uint8 value) is image, and send size
                byteRowsizeMSG = fullbytelen.to_bytes(16, 'little')
                s2.send(byteRowsizeMSG)
                chunkend = fullbytelen

                while True:                              
                        
                    #establish chunk to send
                    byteRow = sendflat[chunkst:chunkend].tobytes()
              
                    #Width of chunk in bytes 
                    chunkbytelen = len(byteRow)    #How many bytes is chunk image, and send size
                    byteRowsizeMSG = chunkbytelen.to_bytes(16, 'little')
                    s2.send(byteRowsizeMSG)
                                                                
                    #send Image as a single row of bytes - "flattened"           
                    s2.send(byteRow)
                    
                    while True:
                        
                        #check for reception of full stream of bytes and confirmed size
                        Checkrxbytes = s2.recv(16)
                        Checkrx = int.from_bytes(Checkrxbytes, 'little')
                                            
                        if Checkrx == chunkbytelen:
                            #print("send finished completely")
                            break
                        else:
                            #if the stream size does not match then wait for confirmation
                            time.sleep(0.005)
                            
                                         
                    break                           
                    #if the loop didn't break, then send remainder
                                                
                if self.offVidFlag == 1:
                    s2.close()
                    break
                    #Add a stop stream break, when stop commend is sent
                    #if Go = "ST"
                      
                            
                
                

class Example(QWidget):

    def __init__(self):
        super().__init__() 

        self.initUI()
        
    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))
        
    
    def ConRunButtonClicked(self):
        self.th2.start()
        
    def VidRunButtonClicked(self):
        self.th.start()
    
    def StopButtonClicked(self):
          self.th.offVidFlag = 1
          cap = cv2.VideoCapture(0)
          cap.release()
          
         
    
    def initUI(self):
            
        lbl1 = QLabel('Sample stream 320x240', self)
        lbl1.move(10, 260)
   

        ConRunButton = QPushButton("Start Control")
        ConRunButton.clicked.connect(self.ConRunButtonClicked)
        
        VidRunButton = QPushButton("Start Video")
        VidRunButton.clicked.connect(self.VidRunButtonClicked)
        
        StopButton = QPushButton("Stop")
        StopButton.clicked.connect(self.StopButtonClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(ConRunButton)
        hbox.addWidget(VidRunButton)
        hbox.addWidget(StopButton)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
             
        self.setGeometry(50, 50, 600, 300)
        self.setWindowTitle('Pi Car - Control and Video')
        
        self.label = QLabel(self)
        self.label.move(10, 10)
        self.label.resize(320, 240)
            
        self.th = VidThread(self)
        self.th.changePixmap.connect(self.setImage)
        
        
        self.th2 = InputClientThread(self)
        
        self.show()


def main():
    app = QApplication(sys.argv)
    ex = Example()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
