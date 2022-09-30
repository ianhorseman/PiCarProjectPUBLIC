# -*- coding: utf-8 -*-
"""
SERVER SIDE (not Car) - 1 of 2

This is a WiFi RC app. It allows for the connection and recieving of video from the client at the car.
As well it will send control infromation using the Pi Game tool kit to the car client from the remote PC. 
The control and video threads are seperate and must be started using GUI on both ends. The server status
will show in the console window. 

Its not perfect but should provide decent base to build a Remote RC or learning rig from. Have fun 1

Created on Tue Sep  6 23:05:43 2022

@author: Ian Horseman
"""


import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QImage, QPixmap
import cv2
import io
import numpy as np
import time
from PIL import Image
import pygame               # Import pygame to use joypad for input
import socket               # Import socket module

# Define some colors.
BLACK = pygame.Color('black')
WHITE = pygame.Color('white')



# This is a simple class that will help us print to the screen.
# It has nothing to do with the joysticks, just outputting the
# information.
class TextPrint(object):
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 20)

    def tprint(self, screen, textString):
        textBitmap = self.font.render(textString, True, BLACK)
        screen.blit(textBitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 10
        self.y = 10
        self.line_height = 15

    def indent(self):
        self.x += 10

    def unindent(self):
        self.x -= 10


class VidThread(QThread):
    changePixmap = pyqtSignal(QImage)

            
    def run(self):
        # -------- Video Server Start -----------

        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)         # Create a socket object
        host = socket.gethostname() # Get local machine name
        port = 12346                # Reserve a port for the video service.
        s2.bind((host, port))        # Bind to the port

        print("Video Server Start")

        s2.listen(5)                 # Now wait for client connection.
        while True:
           c, addr = s2.accept()     # Establish connection with client.
           print('Got video connection from', addr)
           break
       
        

        #cap = cv2.VideoCapture(0)
        while True:
            
            #get image height in rows
            byteH = c.recv(16)
            H = int.from_bytes(byteH, 'little')
            #print(H)    
                
            #get image Width in Columns
            byteW = c.recv(16)
            W = int.from_bytes(byteW, 'little')
            #print(W)   
            
            
            #get length of full image in bytes
            fullbyteLen = c.recv(16)
            fullLen = int.from_bytes(fullbyteLen, 'little')
            #print("Full Frame = ", fullLen)
            
            imageRx = np.array([])
            confirmbytes = 0
            rxSoFar = 0
            
            while True:
                
                        
                #get length of chunk of image in bytes
                byteLen = c.recv(16)
                Len = int.from_bytes(byteLen, 'little')
                
                #time.sleep(0.05) 
                
                data_get = bytes()
                while True:
                    #get flattened image as byte stream
                    data_get = data_get + c.recv(Len)
                                
                    if len(data_get) == Len:
                        #if we have all the data, break
                        break
                    else:
                        #if not, add a small delay so the buffer can fill with image data
                        time.sleep(0.005)
                        

                imgRowRaw = np.frombuffer(data_get, dtype='uint8')
                imgSize = np.size(imgRowRaw, 0)
               
                
                #send confirmation with Size
                confirmbytes = imgSize.to_bytes(16, 'little')
                c.send(confirmbytes)
                break
       
                        
            imageFixed = np.reshape(imgRowRaw, (H,W,3))

            #ensure that the image array is unsigned 8-bit so it can be converated back to a QImage
            imageFixedRGB = imageFixed.astype('uint8')
            
            h2, w2, ch = imageFixedRGB.shape
            bytesPerLine = ch * w2
            convertToQtFormat = QImage(imageFixedRGB, w2, h2, bytesPerLine, QImage.Format_RGB888)
               
            self.changePixmap.emit(convertToQtFormat)
        s2.close()              

class ControlThread(QThread):
    
    
    def run(self):
        
        
        pygame.init()

        # Set the width and height of the screen (width, height).
        screen = pygame.display.set_mode((500, 700))

        pygame.display.set_caption("Joypad Input for Pi Car")

        # Loop until the user clicks the close button.
        done = False

        # Used to manage how fast the screen updates.
        clock = pygame.time.Clock()

        # Initialize the joysticks.
        pygame.joystick.init()

        # Get ready to print.
        textPrint = TextPrint()        
        
        
        
        # -------- Controller Server Start -----------

        s = socket.socket()         # Create a socket object
        host = socket.gethostname() # Get local machine name
        port = 12345                # Reserve a port for controller service.
        s.bind((host, port))        # Bind to the port

        print("Control Server Start")

        s.listen(5)                 # Now wait for client connection.
        while True:
           c, addr = s.accept()     # Establish connection with client.
           print('Got controller connection from', addr)
           break
       
        
       
        # -------- Main Program Loop -----------
        while not done:
            #
            # EVENT PROCESSING STEP
            #
            # Possible joystick actions: JOYAXISMOTION, JOYBALLMOTION, JOYBUTTONDOWN,
            # JOYBUTTONUP, JOYHATMOTION
            for event in pygame.event.get(): # User did something.
                if event.type == pygame.QUIT: # If user clicked close.
                    done = True # Flag that we are done so we exit this loop.
                elif event.type == pygame.JOYBUTTONDOWN:
                    print("Joystick button pressed.")
                elif event.type == pygame.JOYBUTTONUP:
                    print("Joystick button released.")

            #
            # DRAWING STEP
            #
            # First, clear the screen to white. Don't put other drawing commands
            # above this, or they will be erased with this command.
            screen.fill(WHITE)
            textPrint.reset()

            # Get count of joysticks.
            joystick_count = pygame.joystick.get_count()

            textPrint.tprint(screen, "Number of joysticks: {}".format(joystick_count))
            textPrint.indent()

            # For each joystick:
            for i in range(joystick_count):
                joystick = pygame.joystick.Joystick(i)
                joystick.init()

                textPrint.tprint(screen, "Joystick {}".format(i))
                textPrint.indent()

                # Get the name from the OS for the controller/joystick.
                name = joystick.get_name()
                textPrint.tprint(screen, "Joystick name: {}".format(name))

                # Usually axis run in pairs, up/down for one, and left/right for
                # the other.
                axes = joystick.get_numaxes()
                textPrint.tprint(screen, "Number of axes: {}".format(axes))
                textPrint.indent()
                

                ConInfo = ""
                
                for i in range(axes):
                    axis = joystick.get_axis(i)
                    textPrint.tprint(screen, "Axis {} value: {:>6.3f}".format(i, axis))
                    ConInfo = ConInfo + str(axis) + ","
                    
                textPrint.unindent()

                buttons = joystick.get_numbuttons()
                textPrint.tprint(screen, "Number of buttons: {}".format(buttons))
                textPrint.indent()


                for i in range(buttons):
                    button = joystick.get_button(i)
                    textPrint.tprint(screen,
                                     "Button {:>2} value: {}".format(i, button))
                    ConInfo = ConInfo + str(button) + ","
                    
                textPrint.unindent()

                hats = joystick.get_numhats()
                textPrint.tprint(screen, "Number of hats: {}".format(hats))
                textPrint.indent()

                # Hat position. All or nothing for direction, not a float like
                # get_axis(). Position is a tuple of int values (x, y).
                for i in range(hats):
                    hat = joystick.get_hat(i)
                    textPrint.tprint(screen, "Hat {} value: {}".format(i, str(hat)))
                    
                    #Remove brackets on hat values so it can be converted to two floats at far end.
                    trimhat = str(hat)
                    ConInfo = ConInfo + trimhat[1:-1] + ","
                textPrint.unindent()

                textPrint.unindent()
                
                #send the car the contorller state string.
                #print(ConInfo)
                
                byteConInfo = ConInfo.encode("ascii")
                c.send(byteConInfo)
                


            #
            # ALL CODE TO DRAW SHOULD GO ABOVE THIS COMMENT
            #

            # Go ahead and update the screen with what we've drawn.
            pygame.display.flip()

            # Limit to 20 frames per second.
            clock.tick(20)

        
        # Shut the connection to the Car down, send client close flag. 
        print("Server Shut")
        closeclient = "Y"
        byteclose = closeclient.encode("ascii")
        c.send(byteclose)
        c.close()                # Close the connection
        

        # Close the window and quit.
        # If you forget this line, the program will 'hang'
        # on exit if running from IDLE.
        pygame.quit()
    

# The GUI Window for control and video viewing. 
#------------------------------------------------
class Example(QWidget):
    
    

    def __init__(self):
        super().__init__() 
        
       
        self.initUI()
        
    @pyqtSlot(QImage)
    def setImage(self, image):
        self.Imagelbl1.setPixmap(QPixmap.fromImage(image))

    
    def ControlOnButtonClicked(self):
        self.lbl1.setText('Control ON')
        self.th2.start()  
        
    #def ControlOffButtonClicked(self):
  
	#    self.lbl1.setText('Control OFF')
        
    
    #def RunButtonClicked(self):
    #    self.lbl2.setText('Video ON')
          
          
    def StopButtonClicked(self):
        cap = cv2.VideoCapture(0)
        cap.release()
        self.lbl2.setText('Video OFF')
         
    
    def initUI(self):
            
        self.lbl1 = QLabel('C Idle', self)
        self.lbl1.move(10, 260)
        
        self.lbl2 = QLabel('Video ON', self)
        self.lbl2.move(10, 240)
   
        ControlOnButton = QPushButton("Control Start")
        ControlOnButton.clicked.connect(self.ControlOnButtonClicked)
        
        
        #ControlOffButton = QPushButton("Control Stop")
        #ControlOffButton.clicked.connect(self.ControlOffButtonClicked)
        
        
        #RunButton = QPushButton("Video Start")
        #RunButton.clicked.connect(self.RunButtonClicked)
        
        
        StopButton = QPushButton("Video Stop")
        StopButton.clicked.connect(self.StopButtonClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(ControlOnButton)
        #hbox.addWidget(ControlOffButton)
        #hbox.addWidget(RunButton)
        hbox.addWidget(StopButton)
        

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
             
        self.setGeometry(50, 50, 600, 300)
        self.setWindowTitle('Neural Node Demo')
        
        self.Imagelbl1 = QLabel(self)
        self.Imagelbl1.move(10, 10)
        self.Imagelbl1.resize(320, 240)
            
        th = VidThread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        
        
        self.th2 = ControlThread(self)
        
        
        self.show()


def main():
    app = QApplication(sys.argv)
    ex = Example()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()