import collections
#from socket import CAN_BCM_RX_READ
from time import sleep
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
    def __init__(self, trialPlaybackSubWindowWidget, camera):
        super().__init__()
        self.positionSlider = trialPlaybackSubWindowWidget.positionSlider
        self.mediaPlayer = trialPlaybackSubWindowWidget.mediaPlayer
        self.playLastTrial_Button = trialPlaybackSubWindowWidget.playLastTrial_Button
        self.trialLabel = trialPlaybackSubWindowWidget.trialLabel
        self.camera = camera
        self.lastTrialVideo = None
    
    def play(self):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.mediaPlayer.pause()
        else:
            self.mediaPlayer.play()

    def setPosition(self, position):
        self.mediaPlayer.setPosition(position)

    def mediaStateChanged(self, state):
        if self.mediaPlayer.state() == QMediaPlayer.PlayingState:
            self.playLastTrial_Button.setIcon(
                    self.playLastTrial_Button.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.playLastTrial_Button.setIcon(
                    self.playLastTrial_Button.style().standardIcon(QStyle.SP_MediaPlay))

    def updateCamera(self,camera):
        self.camera = camera

    def positionChanged(self, position):
        self.positionSlider.setValue(position)

    def durationChanged(self, duration):
        self.positionSlider.setRange(0, duration)

    def handleError(self):
        self.playLastTrial_Button.setEnabled(False)
        #self.errorLabel.setText("Error: " + self.videoLabel.errorString())

    def findLastTrialVideo(self):
        #folder = 'H:\\repos\\PyBpodGUI\\camera_data\\' # need to change to camera.camera_data_dir
        folder = self.camera.camera_data_dir # need to change to camera.camera_data_dir
        print(f'Saving images in folder {self.camera.camera_data_dir}')
        list_of_tifs = []
        while not bool(list_of_tifs):
            list_of_tifs = glob.glob(folder +'\\*\\*.tif')
        latest_tif = max(list_of_tifs, key=os.path.getctime)
        self.lastTrialVideo = latest_tif

    def playLastTrial(self):
        if self.camera is not None: 
            #fname = QFileDialog.getOpenFileName(self, "Open File", "R:\\Rinberglab\\rinberglabspace\\Users\\Bea\\testimages", "All Files(*);; PNG Files (*.png)")
            self.findLastTrialVideo()
            sleep(1)
            # self.lastTrialVideo = 'H:\\repos\\PyBpodGUI\\camera_data\\test.tif'
            print('Using {0} as most recent tif.'.format(self.lastTrialVideo))

            imstack1 = skio.imread(self.lastTrialVideo)
            meanframe = np.mean(imstack1[:50,:,:], axis = 0)
            normstack = imstack1 - meanframe

            video_name = 'temp.avi' # 'C:\\Users\\barrab01\\Documents\\tiffvideo4.avi'
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            fps = 30
            vidshape = np.shape(normstack)
            perc20 = np.percentile(normstack, 1)
            perc95 = np.percentile(normstack, 99.99)
            normstack[normstack < perc20] = perc20
            normstack[normstack > perc95] = perc95
            normstackn = normstack - np.amin(normstack)
            normstackn = normstackn / np.amax(normstackn)
            vidin = 255 * normstackn
            vidint = vidin.astype('uint8')

            writer = cv2.VideoWriter(video_name, fourcc, fps, (vidshape[1], vidshape[2]), False)
            for i in range(vidshape[0]):
                x = vidint[i,:,:]
                writer.write(x)
            
            writer.release()

            trialNumStart = self.lastTrialVideo.find('Trial_') + 6
            trialNumEnd = trialNumStart + 3
            trialNumString = self.lastTrialVideo[trialNumStart:trialNumEnd]

            self.trialLabel.setText(trialNumString)
            print(f'Trial num is {trialNumString}')
            self.mediaPlayer.setMedia(
                        QMediaContent(QUrl.fromLocalFile(video_name)))
            self.playLastTrial_Button.setEnabled(True)
        

        # self.videoLabel.setMedia(
        #             QMediaContent(QUrl.fromLocalFile(fname[0])))
        # self.playLastTrial_Button.setEnabled(True)
  
            self.play()
        