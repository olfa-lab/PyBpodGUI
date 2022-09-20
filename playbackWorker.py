import collections
import numpy as np
import logging
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import glob
import os
import numpy as np
import skimage.io as skio
import cv2
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QUrl, QDir
from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QProgressDialog, QFileDialog, QMdiSubWindow, QSlider, QStyle

logging.basicConfig(format="%(message)s", level=logging.INFO)


class PlaybackWorker(QObject):  
    def __init__(self, mediaplayer,playLastTrial_Button , positionSlider):
        super().__init__()
        self.positionSlider = positionSlider
        self.mediaplayer = mediaplayer
        self.playLastTrial_Button = playLastTrial_Button
    
    def play(self):
        if self.mediaplayer.state() == QMediaPlayer.PlayingState:
            self.mediaplayer.pause()
        else:
            self.mediaplayer.play()

    def setPosition(self, position):
        self.mediaplayer.setPosition(position)

    def mediaStateChanged(self, state):
        if self.mediaplayer.state() == QMediaPlayer.PlayingState:
            self.playLastTrial_Button.setIcon(
                    self.playLastTrial_Button.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playLastTrial_Button.setIcon(
                    self.playLastTrial_Button.style().standardIcon(QStyle.SP_MediaPlay))

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def handleError(self):
        self.playLastTrial_Button.setEnabled(False)
        #self.errorLabel.setText("Error: " + self.videoLabel.errorString())

    def findLastTrialVideo(self):
        folder = 'R:\\Rinberglab\\rinberglabspace\\Users\\Bea\\testimages'


        list_of_files = glob.glob(folder +'\\*') # * means all if need specific format then *.csv
        latest_file = max(list_of_files, key=os.path.getctime)
        self.lastTrialVideo = latest_file

        

    def playLastTrial(self):
        #fname = QFileDialog.getOpenFileName(self, "Open File", "R:\\Rinberglab\\rinberglabspace\\Users\\Bea\\testimages", "All Files(*);; PNG Files (*.png)")
        self.findLastTrialVideo()
       
        imstack1    = skio.imread(self.lastTrialVideo)
        meanframe = np.mean(imstack1[:100,:,:], axis = 0)
        normstack = imstack1 - meanframe
        print(type(imstack1), imstack1.shape)
        video_name = 'C:\\Users\\barrab01\\Documents\\tiffvideo4.avi'
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        fps = 30
        vidshape = np.shape(normstack)
        perc20 = np.percentile(normstack, 1)
        perc95 = np.percentile(normstack, 99.99)
        normstack[normstack < perc20] = perc20
        normstack[normstack > perc95] = perc95
        normstackn = normstack - np.amin(normstack)
        normstackn = normstackn / np.amax(normstackn)
        print(type(normstackn), normstackn.shape)
        vidin = 255 * normstackn
        vidint = vidin.astype('uint8')

        writer = cv2.VideoWriter(video_name, fourcc, fps, (vidshape[1], vidshape[2]), False)
        for i in range(vidshape[0]):
            x = vidint[i,:,:]
            writer.write(x)
        
        writer.release()
        print('done')

        self.mediaplayer.setMedia(
                    QMediaContent(QUrl.fromLocalFile(video_name)))
        self.playLastTrial_Button.setEnabled(True)
        

        # self.videoLabel.setMedia(
        #             QMediaContent(QUrl.fromLocalFile(fname[0])))
        # self.playLastTrial_Button.setEnabled(True)
  
        self.play()
        