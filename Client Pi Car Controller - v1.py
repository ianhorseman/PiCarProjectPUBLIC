#!/usr/bin/python           
#Remote Pi Car - Skid Steer Controls over WiFi from Server PC
#v1 - no video yet!

import socket               # Import socket module
import numpy as np
from gpiozero import Servo
import time
import RPi.GPIO as GPIO
from time import sleep



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


#Start Motors in Stop
pR.start(0)
pL.start(0)




#----------------------Client Connection Infomration-------------------
s = socket.socket()         # Create a socket object
#host = socket.gethostname() # Get local machine name
host = "192.168.1.81"       # Server address (laptop .68 and tower .81)
port = 12345                # Reserve a port for your service.

print(host)

s.connect((host, port))

Controller = np.zeros([50])



#----------------------Main Loop--------------------------------------
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
        

#-------------------End Client - End Program------------------------    
print("Client Shutdown")
s.close                     # Close the socket when done
GPIO.cleanup()              # Clear GPIO ports
