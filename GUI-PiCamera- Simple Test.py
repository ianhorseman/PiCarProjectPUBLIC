"""
A very simple GUI using Open CV and QT5 to show a video stream from a local camera. 
Will work with the Pi Camera shown in the Robot Car Blog EP 5.

Change at will. 

Created on Sun Sep 27 21:58:04 2020

@author: Ian (mostly borrowed from the web)
"""

import sys
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout, QApplication
from PyQt5.QtCore import QThread, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QIcon, QImage, QPixmap
import cv2




class Thread(QThread):
    changePixmap = pyqtSignal(QImage)

    def run(self):
        cap = cv2.VideoCapture(0)
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
                



class Example(QWidget):

    def __init__(self):
        super().__init__() 

        self.initUI()
        
    @pyqtSlot(QImage)
    def setImage(self, image):
        self.label.setPixmap(QPixmap.fromImage(image))

    
    def StopButtonClicked(self):
          cap = cv2.VideoCapture(0)
          cap.release()
         
    
    def initUI(self):
            
        lbl1 = QLabel('Sample stream 320x240', self)
        lbl1.move(10, 260)
   

        RunButton = QPushButton("Run")
        StopButton = QPushButton("Stop")
        StopButton.clicked.connect(self.StopButtonClicked)

        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(RunButton)
        hbox.addWidget(StopButton)

        vbox = QVBoxLayout()
        vbox.addStretch(1)
        vbox.addLayout(hbox)

        self.setLayout(vbox)
             
        self.setGeometry(50, 50, 600, 300)
        self.setWindowTitle('Neural Node Demo')
        
        self.label = QLabel(self)
        self.label.move(10, 10)
        self.label.resize(320, 240)
            
        th = Thread(self)
        th.changePixmap.connect(self.setImage)
        th.start()
        
        self.show()


def main():
    app = QApplication(sys.argv)
    ex = Example()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
