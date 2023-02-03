import tables
import logging
import os
import json
import numpy as np
from datetime import datetime
from unicodedata import name
from shutil import copy2  # preserve metadata
import glob
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot


class ReadDataWorker(QObject):
    analogDataSignal = pyqtSignal(list)
    analogDataSignalProcessed = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self, analogInModule=None, bpod=None):
        super(ReadDataWorker, self).__init__()
        # properties
        self.adc = analogInModule
        self.bpod = bpod 
        self.newData = False
        self.keepRunning = True
        self.trialNum = 1
        
        # init depending on reading of analog through analog module or Bpod (analog module won't be tested since I don't use it)
        if self.adc is not None:
            self.bpod = None  # Avoid using the bpod in case it was also given as a parameter.
            self.analogSettings = analogInSettings
        elif self.bpod is not None:
            self.samplingPeriod = self.bpod.hardware.analog_input_sampling_interval * 0.0001  # Multiply by the state machines timer period of 100 microseconds.
            self.channelIndices = self.bpod.hardware.analog_input_channels  # list of channel indices of channels configured for analog input.
            if (self.channelIndices is not None) and (len(self.channelIndices) > 0):
                # This means it is a list of at least one flex channel number that is configured for analog input.
                self.nChannels = len(self.channelIndices)
        self.maxVoltages = [5] * self.nChannels  # Make a list of integers for the max voltage of each channel's input range.
        self.minVoltages = [0] * self.nChannels  # Make a list of integers for the min voltage of each channel's input range.

    def receiveInfoDict(self, infoDict):
        self.newData = True
        self.infoDict = infoDict

    def run(self):
        
        while self.keepRunning:
            if self.newData:
                self.newData = False # reset
            elif self.adc is not None:
                self.saveAnalogDataFromModule()
            elif self.bpod is not None:
                self.readAnalogDataFromBpod()
        # When it finishes
        logging.info("ReadDataWorker Finished")
        self.finished.emit()
    
    def saveAnalogDataFromModule(self):# this is placeholder to avoid errors but function is all to be changes accordingly
        analogData = self.bpod.read_analog_input()
        analogDataSignal.emit(analogData)

    def readAnalogDataFromBpod(self):
        analogData = self.bpod.read_analog_input()
        #print("before emitting analogDataSignal")
        self.analogDataSignal.emit(analogData)
        # #print("after emitting analogDataSignal")
        # if len(analogData) > 0:
        #     # convert decimal bit value to voltage. The length of samples indicates how many channels are streaming to USB.
        #     nSamples = int(len(analogData) / (self.nChannels + 1))  # Add one to account for the trial number that is included with every sample.
        #     voltages = [[]] * self.nChannels  # make a sublist for each channel
        #     ind = 0
        #     for s in range(nSamples):
        #         trialNum = analogData[ind]
        #         ind += 1
        #         if trialNum == self.trialNum:  # Note that self.trialNum starts at 1 and is incremented each time a new info dict is received.
        #             #self.bpodTime += self.samplingPeriod
        #             for i in range(self.nChannels):
        #                 samp = (analogData[ind] / 4095) * self.maxVoltages[i]
        #                 ind += 1
        #                 voltages[i].append(samp)
                        
        #         else:
        #             # Skip over this sample. Instead of breaking out of the for loop, run the for loop below to increment ind, just in case analogData
        #             # is more than one sample, in which case the next sample could be the correct trialNum.
        #             for i in range(self.nChannels):
        #                 ind += 1
        #     #print(" emitting analogDataSignalProcessed")
        #     self.analogDataSignalProcessed.emit(np.array(voltages[0], dtype='float32'))  # StreamingWorker is currently only capable of plotting one channel.
    
    
    def stopRunning(self):
        self.keepRunning = False
        