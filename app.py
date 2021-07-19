import sys
import os
import time
import copy
import collections
import tables
import numpy as np
import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QProgressDialog)
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot, Qt

from main_window_ui import Ui_MainWindow
from pybpodapi.protocol import Bpod, StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
from BpodAnalogInputModule import BpodAnalogIn
import olfactometry

# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

import pyqtgraph as pg


logging.basicConfig(format="%(message)s", level=logging.INFO)


'''
Things to do:

    * __X__ use signals/slots instead of passing references to class objects.

    * __X__ close/stop streaming figure when stop button clicked

    * __X__ make gui stop other threads when experiment finished.

    * __X__ implement data recording with pytables

    * __X__ implement water valve buttons to only open for set duration

    * __X__ solve analog module giving error that Serial1_1 is invalid name

    * __X__ make results graph show percent of left licks instead of percent correct

    * __X__ have a counter that counts number of no responses and after certain number, it aborts experiment.

    * __X__ close serial devices and threads when application exits

    * __X__ get rid of the samplingThread and let the sessionDataThread do the sampling and saving to .h5 and let it collect 100 or so samples in an array and emit it to the streamingWorker whenever it gets filled instead of one sample at a time.

    * __X__ save sniff signal (voltage over time) for each trial in .h5 file

    * __X__ save timestamps of lick events for each trial in .h5 file

    * __X__ synchronize analog data with state machine timing.

    * __X__ disable buttons that should not be clicked during certain operations

    * __X__ make a separate button to connect to devices first, before starting the experiment.

    * __X__ implement calibrate water valve buttons

    * __X__ implement progress bar dialog window for calibrating water

    * _____ implement pause button

    * _____ use jonathan olfactometer code

    * _____ have a timer (in the state machine) that aborts experiment when no sniff signal for certain amount of time

    * _____ implement ability to configure flow rates

    * _____ implement ability to configure odors and/or olfa json file

    * _____ implement ability to configure protocol

    * _____ implement ability to configure analog module

    * _____ implement serial port selection for each device with combobox that list available serial ports for user to pick

    * _____ implement validators for the line edits to restrict input values

    * _____ implement progress bar for state machine during trial run

    * _____ use pyqtgraph instead of matplotlib for the streaming plot to check if faster sampling/plotting is possible

    * _____ try using @pyqtSlot for a function to check if the thread will call it even if its running in an infinite loop.

    * _____ configure tab order for the LineEdit fields

    * _____ create a metadata for the .h5 file  
      

Questions to research:

    * _____ How to connect signal from one thread to a slot in another thread that is running in an infinite loop without using lambda function?

    * _____ How to block execution within a thread for a certain amount of time?

    * _____ Why does infinite loop in separate cause main thread to freeze or lag?
'''


'''
Example trial info dictionary created by the bpod.
{
    'Bpod start timestamp': 4.344831,
    'Trial start timestamp': 28.050931,
    'Trial end timestamp': 55.769934,
    'States timestamps': {
        'WaitForOdor': [(0, 5.0)],
        'WaitForSniff': [(5.0, 5.1)],
        'WaitForResponse': [(5.1, 9.7189)],
        'Punish': [(9.7189, 9.719)], 
        'ITIdelay': [(9.719, 27.719)],
        'Reward': [(nan, nan)],
        'NoLick': [(nan, nan)]
    },
    'Events timestamps': {
        'Tup': [
            5.0,
            5.1,
            9.719,
            27.719
        ],
        'Port1In': [
            9.7189,
            10.2883,
            10.5192,
        ],
        'Port1Out': [
            10.1076,
            10.393,
            10.6725,
        ]
    }
}
'''

class SessionData(tables.IsDescription):
    trialNum = tables.UInt16Col(pos=0)
    correctResponse = tables.StringCol(5, pos=1)
    responseResult = tables.StringCol(16, pos=2)
    odorName = tables.StringCol(32, pos=3)  # Size of strings added to the column does not need to exactly match the size given during initialization.
    odorConc = tables.Float32Col(pos=4)
    odorFlow = tables.UInt8Col(pos=5)
    leftLicksCount = tables.UInt8Col(pos=6)
    rightLicksCount = tables.UInt8Col(pos=7)
    responseWindowStartTime = tables.Float32Col(pos=8)
    responseWindowEndTime = tables.Float32Col(pos=9)
    responseTimeElapsed = tables.Float32Col(pos=10)
    itiDuration = tables.UInt8Col(pos=11)
    trialStartTime = tables.Float32Col(pos=12)
    trialEndTime = tables.Float32Col(pos=13)
    totalTrialTime = tables.Float32Col(pos=14)
    bpodStartTime = tables.Float32Col(pos=15)


class FinalData(tables.IsDescription):
    flowRate = tables.UInt8Col(pos=0)
    totalUsage = tables.UInt16Col(pos=1)
    totalRight = tables.UInt16Col(pos=2)
    totalLeft = tables.UInt16Col(pos=3)
    totalCorrect = tables.UInt16Col(pos=4)
    totalWrong = tables.UInt16Col(pos=5)
    totalNoResponse = tables.UInt16Col(pos=6)


class VoltageData(tables.IsDescription):
    # stateNum = tables.UInt8Col(pos=0)
    stateNum = tables.StringCol(1, pos=0)
    # computerTime = tables.Float32Col(pos=1)
    # computerPeriod = tables.Float32Col(pos=2)
    bpodTime = tables.Float32Col(pos=1)
    voltage = tables.Float32Col(shape=(1, ), pos=2)


class SessionDataWorker(QObject):
    analogDataSignal = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self, mouseNum, rigLetter, analogInModule):
        super(SessionDataWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.adc = analogInModule
        dateTimeObj = datetime.now()
        dateObj = dateTimeObj.date()
        timeObj = dateTimeObj.time()
        fileName = f"results/Mouse_{mouseNum}_Rig_{rigLetter}_{dateObj}_{timeObj.hour}{timeObj.minute}{timeObj.second}.h5"
        if not os.path.isdir('results'):
            os.mkdir('results')
        self.h5file = tables.open_file(filename=fileName, mode='w', title=f"Mouse {mouseNum} Experiment Data")
        self.voltsGroup = self.h5file.create_group(where='/', name='voltages', title='Voltages Per Trial')
        self.licksGroup = self.h5file.create_group(where='/', name='lickTimes', title='Lick Timestamps Per Trial')
        self.table = self.h5file.create_table(where='/', name='trial_data', description=SessionData, title='Trial Data')
        self.trial = self.table.row
        self.statesTable = None  # Make it None because have to wait for completion of first trial to get names of all the states. Afterwhich, make description dictionary and then table.
        self.statesTableDescDict = {}  # Description for the states table (using this instead of making a class definition and subclassing tables.IsDescription).
        self.licksTable = None
        self.licksTableDescDict = {  # Description for the licks table instead of making a class definition and subclassing tables.IsDescription.
            'leftLickTimes': tables.Float32Col(dflt=np.nan, pos=0),
            'rightLickTimes': tables.Float32Col(dflt=np.nan, pos=1)
        }
        self.keepRunning = True
        self.newData = False
        self.infoDict = {}
        self.finalResultsDict = {}
        self.analogDataBufferSize = 10
        self.analogDataBuffer = np.zeros(shape=self.analogDataBufferSize, dtype='float32')
        self.trialNum = 1
        self.stateNum = 0
        self.maxVoltage = 5
        self.counter = 0
        self.previousTimer = 0
        self.t_start = 0
        self.samplingPeriod = 1 / 1000
        self.bpodTime = 0

    def receiveInfoDict(self, infoDict):
        self.newData = True
        logging.info("incoming infoDict")
        self.infoDict = infoDict

    def receiveFinalResultsDict(self, resultsDict):
        logging.info('incoming final results dict')
        self.finalResultsDict = resultsDict

    def saveFinalResults(self):
        logging.info('attempting to save final results data')
        self.finalTable = self.h5file.create_table(where='/', name='final_results', description=FinalData, title='Final Results')
        self.finalRow = self.finalTable.row

        for flowRate, total in self.finalResultsDict.items():
            self.finalRow['flowRate'] = flowRate
            self.finalRow['totalUsage'] = total['Total']
            self.finalRow['totalRight'] = total['right']
            self.finalRow['totalLeft'] = total['left']
            self.finalRow['totalCorrect'] = total['Correct']
            self.finalRow['totalWrong'] = total['Wrong']
            self.finalRow['totalNoResponse'] = total['NoResponse']
            self.finalRow.append()

        self.finalTable.flush()
        logging.info('final results data has been written to disk')

    def saveStatesTimestamps(self):
        # Define the description for the states table using a dictionary of the states timestamps. Then create the states table (only once).
        if self.statesTable is None:
            pos = 0
            for k, v in self.infoDict['States timestamps'].items():
                keyString = k + 'Start'
                self.statesTableDescDict[keyString] = tables.Float32Col(pos=pos)
                pos += 1
                keyString = k + 'End'
                self.statesTableDescDict[keyString] = tables.Float32Col(pos=pos)
                pos += 1
            
            self.statesTable = self.h5file.create_table(where='/', name='statesTimestamps', description=self.statesTableDescDict, title='States Timestamps')
            self.statesRow = self.statesTable.row

        # Fill in column values for the states timestamps for the current row since statesTable has been created.
        for k, v in self.infoDict['States timestamps'].items():
            keyString = k + 'Start'
            self.statesRow[keyString] = v[0][0]
            keyString = k + 'End'
            self.statesRow[keyString] = v[0][1]

        # only one row per end of trial data so append what was written and flush to disk.
        self.statesRow.append()
        self.statesTable.flush()
   
    def run(self):
        self.voltTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum}', description=VoltageData, title=f'Trial {self.trialNum} Voltage Data')
        self.voltsRow = self.voltTable.row

        self.t_start = time.perf_counter()
        while self.keepRunning:
            if self.newData:
                self.newData = False  # reset
                logging.info("attempting to save data")

                self.licksTable = self.h5file.create_table(where='/lickTimes', name=f'trial_{self.trialNum}', description=self.licksTableDescDict, title=f'Trial {self.trialNum} Lick Timestamps')
                self.licksRow = self.licksTable.row

                self.trial['trialNum'] = self.infoDict['currentTrialNum']
                self.trial['correctResponse'] = self.infoDict['correctResponse']
                self.trial['responseResult'] = self.infoDict['responseResult']
                self.trial['odorName'] = self.infoDict['currentOdorName']
                self.trial['odorConc'] = self.infoDict['currentOdorConc']
                self.trial['odorFlow'] = self.infoDict['currentFlow']
                self.trial['responseWindowStartTime'] = self.infoDict['States timestamps']['WaitForResponse'][0][0]
                self.trial['responseWindowEndTime'] = self.infoDict['States timestamps']['WaitForResponse'][0][1]
                self.trial['responseTimeElapsed'] = self.trial['responseWindowEndTime'] - self.trial['responseWindowStartTime']
                self.trial['itiDuration'] = self.infoDict['currentITI']
                self.trial['trialStartTime'] = self.infoDict['Trial start timestamp']
                self.trial['trialEndTime'] = self.infoDict['Trial end timestamp']
                self.trial['totalTrialTime'] = self.trial['trialEndTime'] - self.trial['trialStartTime']
                self.trial['bpodStartTime'] = self.infoDict['Bpod start timestamp']

                if 'Port1In' in self.infoDict['Events timestamps']:
                    leftLicksList = self.infoDict['Events timestamps']['Port1In']
                    leftLicksCount = len(leftLicksList)
                    self.trial['leftLicksCount'] = leftLicksCount

                    if 'Port3In' in self.infoDict['Events timestamps']:
                        rightLicksList = self.infoDict['Events timestamps']['Port3In']
                        rightLicksCount = len(rightLicksList)
                        self.trial['rightLicksCount'] = rightLicksCount

                        # Save both left and right lick times to each row if both exist, and avoid index out of range errors.
                        if (rightLicksCount >= leftLicksCount):
                            for i in range(rightLicksCount):
                                self.licksRow['rightLickTimes'] = rightLicksList[i]
                                if (i < leftLicksCount):
                                    self.licksRow['leftLickTimes'] = leftLicksList[i]
                                
                                self.licksRow.append()
                        else:
                            for i in range(leftLicksCount):
                                self.licksRow['leftLickTimes'] = leftLicksList[i]
                                if (i < rightLicksCount):
                                    self.licksRow['rightLickTimes'] = rightLicksList[i]
                                
                                self.licksRow.append()
                    else:   
                        # Only left licks exist. 
                        self.trial['leftLicksCount'] = len(self.infoDict['Events timestamps']['Port1In'])
                        for t in self.infoDict['Events timestamps']['Port1In']:
                            self.licksRow['leftLickTimes'] = t
                            self.licksRow.append()
                    self.licksTable.flush()

                # Only right licks exist.
                elif 'Port3In' in self.infoDict['Events timestamps']:
                    self.trial['rightLicksCount'] = len(self.infoDict['Events timestamps']['Port3In'])
                    for t in self.infoDict['Events timestamps']['Port3In']:
                        self.licksRow['rightLickTimes'] = t
                        self.licksRow.append()
                    self.licksTable.flush()
                
                self.trial.append()
                self.table.flush()

                self.saveStatesTimestamps()

                # The trial data above comes at the end of a trial, so write the voltages to the disk, and create a new table for the next trial's voltages
                self.voltTable.flush()
                self.trialNum += 1  # increment trial number.
                self.stateNum = 0  # reset state number back to zero.
                self.bpodTime = 0  # reset timestamps for samples back to zero.
                
                # Re-iterate through the volts table row by row to update the bpodTime so it corresponds to the bpod's trial start time instead of starting it at zero.
                # self.bpodTime = self.infoDict['Trial start timestamp']
                # for voltsRow in self.voltTable.iterrows():
                #     voltsRow['bpodTime'] = self.bpodTime
                #     self.bpodTime += self.samplingPeriod
                #     voltsRow.update()
                # self.voltTable.flush()

                self.voltTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum}', description=VoltageData, title=f'Trial {self.trialNum} Voltage Data')
                self.voltsRow = self.voltTable.row
            
            else:
                analogData = self.adc.getSampleFromUSB()

                # Uses the computer's clock to make the timestamps for the samples and period in between each sample.
                # currentTimer = time.perf_counter()
                # period = currentTimer - self.previousTimer
                # elapsed = currentTimer - self.t_start
                # self.previousTimer = currentTimer

                prefix = analogData[0][0]
                syncByte = analogData[0][1]
                samples = analogData[1]
                voltages = [0] * len(samples)

                if (prefix == 35):  # 35 is the decimal value for the ascii char '#'
                    self.stateNum = chr(syncByte)  # update the state number with the syncByte's ascii character.

                # convert decimal bit value to voltage.
                for i in range(len(samples)):
                    if samples[i] >= 4096:
                        samples[i] -= 4096
                        voltages[i] = (samples[i] * self.maxVoltage) / 4096
                    elif samples[i] < 4096:
                        voltages[i] = ((samples[i] * self.maxVoltage) / 4096) - self.maxVoltage

                # Start saving to file when the trial starts, which is indicated when a syncByte is received and 'self.stateNum' is updated with the syncByte's value.
                if not (self.stateNum == 0):
                    self.voltsRow['stateNum'] = self.stateNum
                    # self.voltsRow['computerTime'] = elapsed
                    # self.voltsRow['computerPeriod'] = period
                    self.voltsRow['bpodTime'] = self.bpodTime
                    self.bpodTime += self.samplingPeriod
                    self.voltsRow['voltage'] = voltages
                    self.voltsRow.append()

                # fill buffer and send it when full using the signal.
                if self.counter < self.analogDataBufferSize:    
                    self.analogDataBuffer[self.counter] = voltages[0]  # Need to use element, not list
                    self.counter += 1
                else:
                    self.analogDataSignal.emit(self.analogDataBuffer)
                    self.counter = 0
                    self.analogDataBuffer[self.counter] = voltages[0]
                    self.counter += 1

        self.table.flush()
        self.voltTable.flush()
        logging.info("session data has been written to disk")

        self.saveFinalResults()
        self.h5file.close()
        logging.info("h5 file closed")
        self.finished.emit()
        
    def stopRunning(self):
        self.keepRunning = False
        

class InputEventWorker(QObject):
    inputEventSignal = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, bpodObject):
        super(InputEventWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.myBpod = bpodObject
        self.keepRunning = True
        self.correctResponse = None

    # Since it is not possible for the inputEventThread to call this function when getting
    # a signal (because the thread is in an infinite loop), how about trying to modify the
    # value of 'self.newTrail' directly (instead of via a setter function like this)?
    def newTrialSlot(self, correctResponse):
        self.correctResponse = correctResponse

    def run(self):
        logging.info("InputEventThread is running")
        currentPort1In = 0
        currentPort3In = 0
        while self.keepRunning:
            try:
                eventsDict = self.myBpod.session.current_trial.get_all_timestamps_by_event()
            except AttributeError:
                eventsDict = {}

            # Left Lick
            if 'Port1In' in eventsDict:
                newPort1In = eventsDict['Port1In'][-1]  # latest addition to the list of timestamps.
                if newPort1In != currentPort1In:  # Compare timestamps to check if its actually a new event.
                    currentPort1In = newPort1In
                    if self.correctResponse == 'left':
                        self.inputEventSignal.emit(['L', 1])  # Correct lick
                    elif self.correctResponse == 'right':
                        self.inputEventSignal.emit(['L', 0])  # Wrong lick

            # Right Lick
            if 'Port3In' in eventsDict:
                newPort3In = eventsDict['Port3In'][-1]
                if newPort3In != currentPort3In:  # Compare timestamps to check if its actually a new event.
                    currentPort3In = newPort3In
                    if self.correctResponse == 'right':
                        self.inputEventSignal.emit(['R', 1])  # Correct lick
                    elif self.correctResponse == 'left':
                        self.inputEventSignal.emit(['R', 0])  # Wrong lick

            time.sleep(0.1)  # Without this sleep, the plotter launches but is extremely unresponsive.
        logging.info("InputEventWorker Finished")
        self.finished.emit()

    def stopRunning(self):
        self.keepRunning = False


class ProtocolWorker(QObject):
    trialStartSignal = pyqtSignal(str)  # sends correct response with it for use by inputEventThread.
    newTrialInfoSignal = pyqtSignal(dict)  # sends current trial info with it to update GUI.
    newStateSignal = pyqtSignal(str)  # sends current state with it to update GUI.
    responseResultSignal = pyqtSignal(str)  # sends the response result of the current trial with it to update the GUI.
    totalsDictSignal = pyqtSignal(dict)  # sends the session totals with it to update the GUI.
    flowResultsCounterDictSignal = pyqtSignal(dict) # sends the results for each flow rate with it to update the GUI's results plot.
    saveTrialDataDictSignal = pyqtSignal(dict)  # 'dict' is interpreted as 'QVariantMap' by PyQt5 and thus can only have strings as keys.
    # saveTrialDataDictSignal = pyqtSignal(object)  # Use 'object' instead if you want to use non-strings as keys.
    saveEndOfSessionDataSignal = pyqtSignal(dict)
    noResponseAbortSignal = pyqtSignal()
    # startSDCardLoggingSignal = pyqtSignal()
    # stopSDCardLoggingSignal = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, bpodObject, olfaObject, numTrials=1):
        super(ProtocolWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.myBpod = bpodObject
        self.olfas = olfaObject
        self.correctResponse = None
        self.currentOdorName = None
        self.currentOdorConc = None
        self.currentFlow = None
        self.currentTrialNum = 0
        self.totalRewards = 0
        self.totalPunishes = 0
        self.totalNoResponses = 0
        self.consecutiveNoResponses = 0
        self.noResponseCutOff = 10
        self.currentITI = None
        self.nTrials = numTrials
        self.leftWaterDuration = 0.1  # seconds
        self.rightWaterDuration = 0.1  # seconds
        self.keepRunning = True
        self.currentState = ''
        self.currentResponseResult = ''
        self.previousResponseResult = ''
        self.vials = ["pinene0", "pinene1", "pinene2", "pinene3"]
        self.concs = [0.1, 0.1, 0.1, 0.1]
        self.flows = [10, 25, 40, 60, 75, 100]
        self.flowResultsCounterDict = {}
        for flow in self.flows:
            self.flowResultsCounterDict[str(flow)] = {
                'right': 0,  # initizialize counters to zero.
                'left': 0,
                'Correct': 0,
                'Wrong': 0,
                'NoResponse': 0,
                'Total': 0
            }
    # @pyqtSlot()  # Even with this decorator, I still need to use lambda when connecting a signal to this function.
    def setLeftWaterDuration(self, duration):
        self.leftWaterDuration = duration / 1000  # Convert to seconds.

    def setRightWaterDuration(self, duration):
        self.rightWaterDuration = duration / 1000  # Convert to seconds.
    
    def getCorrectResponse(self):
        return self.correctResponse

    def getCurrentTrialNum(self):
        return self.currentTrialNum

    def getCurrentTrialInfoDict(self):
        if self.currentTrialNum > 0:
            trialDict = {
                'currentTrialNum': self.currentTrialNum,
                'nTrials': self.nTrials,
                'correctResponse': self.correctResponse,
                'currentITI': self.currentITI,
                'currentOdorName': self.currentOdorName,
                'currentOdorConc': self.currentOdorConc,
                'currentFlow': self.currentFlow
            }
            return trialDict
        return {}

    def getEndOfTrialInfoDict(self):
        if self.currentState == 'exit':
            dict1 = self.getCurrentTrialInfoDict()
            dict2 = self.myBpod.session.current_trial.export()
            dict3 = {**dict1, **dict2}  # Merge both dictionaries
            dict3.update({'responseResult': self.currentResponseResult})
            return dict3
        logging.info('could not get end of trial dict')
        return {}

    def calculateTotalPercentCorrect(self):
        logging.info('calculating total percent correct')
        percent = round(((float(self.totalRewards) / float(self.currentTrialNum)) * 100), 2)  # I used 'self.currentTrialNum' instead of 'self.nTrials' to ensure the percentage only counts the number of completed trials incase the experiment is aborted early.
        logging.info(f"percent correct is {percent}")
        return percent

    def getTotalsDict(self):
        totals = {
            'totalRewards': self.totalRewards,
            'totalPunishes': self.totalPunishes,
            'totalNoResponses': self.totalNoResponses,
            'totalPercentCorrect': self.calculateTotalPercentCorrect()
        }
        return totals

    def my_softcode_handler(self, softcode):
        '''
        mybpod.session.current_trial will contain timestamps of the states,
        but only upon completion of the trial. So this work around gives
        me the current state while the trial is running.
        '''
        if softcode == 1:
            self.currentState = 'WaitForOdor'
            self.trialStartSignal.emit(self.correctResponse)
            self.newStateSignal.emit(self.currentState)
            self.currentResponseResult = '--'  # reset until bpod gets response result.
            self.responseResultSignal.emit(self.currentResponseResult)
            currentTrialInfo = self.getCurrentTrialInfoDict()
            self.newTrialInfoSignal.emit(currentTrialInfo)
            logging.info(f'starting trial {self.currentTrialNum}')

        elif softcode == 2:
            self.currentState = 'WaitForSniff'
            self.newStateSignal.emit(self.currentState)
            # self.startSDCardLoggingSignal.emit()

        elif softcode == 3:
            self.currentState = 'WaitForResponse'
            self.newStateSignal.emit(self.currentState)

        elif softcode == 4:
            self.currentState = 'Reward'
            self.newStateSignal.emit(self.currentState)
            self.currentResponseResult = 'Correct'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            self.flowResultsCounterDict[str(self.currentFlow)][self.correctResponse] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Correct'] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            self.totalRewards += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif softcode == 5:
            self.currentState = 'Punish'
            self.newStateSignal.emit(self.currentState)
            self.currentResponseResult = 'Wrong'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            if self.correctResponse == 'left':
                self.flowResultsCounterDict[str(self.currentFlow)]['right'] += 1  # increment the opposite direction because the response was wrong.
            elif self.correctResponse == 'right':
                self.flowResultsCounterDict[str(self.currentFlow)]['left'] += 1  # increment the opposite direction because the response was wrong.
            self.flowResultsCounterDict[str(self.currentFlow)]['Wrong'] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            self.totalPunishes += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif softcode == 6:
            self.currentState = 'NoLick'
            self.newStateSignal.emit(self.currentState)
            self.currentResponseResult = 'No Response'
            self.responseResultSignal.emit(self.currentResponseResult)

            if self.previousResponseResult == self.currentResponseResult:
                self.consecutiveNoResponses += 1
            else:
                self.previousResponseResult = self.currentResponseResult
                self.consecutiveNoResponses = 1  # Reset counter to 1 because it should start counting now.

            self.flowResultsCounterDict[str(self.currentFlow)]['NoResponse'] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            self.totalNoResponses += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif softcode == 7:
            self.currentState = 'ITIdelay'
            self.newStateSignal.emit(self.currentState)

    def stimulusRandomizer(self):
        flow_threshold = np.sqrt(self.flows[0] * self.flows[-1])
        
        self.currentFlow = np.random.choice(self.flows)
        #If flow is lower than flow_threshold == ~30 , 'Left' is correct. Otherwise, 'Right' is correct
        if self.currentFlow < flow_threshold:
            self.correctResponse = 'left'
        else:
            self.correctResponse = 'right'

        vialIndex = np.random.randint(4)  # random int for index of vial
        self.currentOdorName = self.vials[vialIndex]
        self.currentOdorConc = self.concs[vialIndex]

        ostim = {
            'olfas': {
                'olfa_0': {
                    'dilutors': {},
                    'mfc_0_flow': 1000 - self.currentFlow,
                    'mfc_1_flow': self.currentFlow,
                    'odor': self.currentOdorName,
                    'vialconc': self.currentOdorConc
                }
            }
        }
        return ostim

    def run(self):
        self.myBpod.softcode_handler_function = self.my_softcode_handler
        finalValve = 2  # Final valve for the odor port on bpod's behavior port 2.

        while self.keepRunning and (self.currentTrialNum < self.nTrials) and (self.consecutiveNoResponses < self.noResponseCutOff):   
            # self.olfas = olfactometry.Olfactometers()
            odorDict = self.stimulusRandomizer()
            self.olfas.set_stimulus(odorDict)
            self.currentITI = np.random.randint(5, 10)  # inter trial interval in seconds.
            self.currentTrialNum += 1

            if self.correctResponse == 'left':
                leftAction = 'Reward'
                rightAction = 'Punish'
                rewardValve = 1  # Left reward valve connected to bpod behavior port 1.
                rewardDuration = self.leftWaterDuration
            elif self.correctResponse == 'right':
                leftAction = 'Punish'
                rightAction = 'Reward'
                rewardValve = 3  # Right reward valve connected to bpod behavior port 3.
                rewardDuration = self.rightWaterDuration

            sma = StateMachine(self.myBpod)

            sma.add_state(
                state_name='WaitForOdor',
                state_timer=1,
                state_change_conditions={'Tup': 'WaitForSniff'},
                output_actions=[
                    ('SoftCode', 1),
                    ('Serial1', ord('1'))  # Sync data to connect the analog signal to this state.
                ]
            )
            sma.add_state(
                state_name='WaitForSniff',
                state_timer=0,
                # Change state when 0x01 is received from the analog input module connected to the bpod's module port 1.
                # This is a trigger indicating the voltage threshold was crossed on channel 1 of the analog input module,
                # meaning a sniff was detected.
                state_change_conditions={'AnalogIn1_1': 'WaitForResponse'},
                output_actions=[
                    ('SoftCode', 2),
                    ('Serial1', ord('2'))  # Sync data to show start of sniff detection state in analog input stream.
                ]  #(Bpod.OutputChannels.Valve, rewardValve)]  # ShapingReward
            )
            sma.add_state(
                state_name='WaitForResponse',
                state_timer=10,
                state_change_conditions={
                    'Port1In': leftAction,
                    'Port3In': rightAction,
                    'Tup': 'NoLick'
                },
                output_actions=[
                    ('Valve', finalValve),
                    ('SoftCode', 3),
                    ('Serial1', ord('3'))  # Sync data to show start of response window in analog input stream.
                ]                             
            )
            sma.add_state(
                state_name='Reward',
                state_timer=rewardDuration,
                state_change_conditions={'Tup': 'ITIdelay'},
                output_actions=[
                    ('Valve', rewardValve),  # Reward correct choice.
                    ('SoftCode', 4),
                    ('Serial1', ord('4'))  # Sync data to show point of response in analog input stream.
                ] 
            )
            sma.add_state(
                state_name='Punish',  # No reward.
                state_timer=0,
                state_change_conditions={'Tup': 'ITIdelay'},
                output_actions=[
                    ('SoftCode', 5),
                    ('Serial1', ord('5'))  # Sync data to show point of response in analog input stream.
                ]
            )
            sma.add_state(
                state_name='NoLick',
                state_timer=0,
                state_change_conditions={'Tup': 'ITIdelay'},
                output_actions=[
                    ('SoftCode', 6),
                    ('Serial1', ord('6'))  # Sync data to show point of response in analog input stream.
                ]
            )
            sma.add_state(
                state_name='ITIdelay',
                state_timer=self.currentITI,
                state_change_conditions={'Tup': 'exit'},
                output_actions=[
                    ('SoftCode', 7),
                    ('Serial1', ord('7'))  # Sync data to connect the analog signal to this state.
                ]
            )

            # Load serial messages for the sync data to the analog module.
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('1'), serial_message=[ord('#'), ord('1')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('2'), serial_message=[ord('#'), ord('2')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('3'), serial_message=[ord('#'), ord('3')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('4'), serial_message=[ord('#'), ord('4')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('5'), serial_message=[ord('#'), ord('5')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('6'), serial_message=[ord('#'), ord('6')])
            self.myBpod.load_serial_message(serial_channel=1, message_ID=ord('7'), serial_message=[ord('#'), ord('7')])

            self.myBpod.send_state_machine(sma)  # Send state machine description to Bpod device
            self.myBpod.run_state_machine(sma)  # Run state machine

            self.currentState = 'exit'
            endOfTrialDict = self.getEndOfTrialInfoDict()
            self.saveTrialDataDictSignal.emit(endOfTrialDict)
            logging.info("saveTrialDataDictSignal emitted")

            # self.stopSDCardLoggingSignal.emit()
            
            self.olfas.set_dummy_vials()

            QThread.sleep(1)  # Need this (or similar blocking method) to give the 'sessionDataThread' enough time to finish writing data to the buffer before the stopRunningSignal gets emitted.
            
            # The olfas object close at the end of each trial and a new object is
            # created at the start of the next trial because there is an error 
            # "Cannot poll MFCs" that only comes when trying to set_stimulus a second time
            # but does not come when set_stimulus is called once for the first time.

            # olfas.close_serials()
            # olfas.close()

        self.saveEndOfSessionDataSignal.emit(self.flowResultsCounterDict)
        logging.info('saveEndOfSessionDataSignal emitting')
        QThread.sleep(1)

        if (self.consecutiveNoResponses >= self.noResponseCutOff):
            self.noResponseAbortSignal.emit()

        logging.info("ProtocolWorker finished")
        self.finished.emit()
        
    def stopRunning(self):
        self.keepRunning = False
        # I should probably also check for edge case when (self.currentState == '') upon init of the ProtocolWorker class.
        if not (self.currentState == 'exit'):
            logging.info("attempting to abort current trial")
            self.myBpod.stop_trial()
            logging.info("current trial aborted")


class StreamingWorker(QObject):
    def __init__(self, plotLength=100, numPlots=1):
        super(StreamingWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.plotMaxLength = plotLength
        self.numPlots = numPlots
        self.rawData = []
        self.data = []
        for i in range(numPlots):   # give a deque for each type of data plot and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
        for i in range(4):
            self.data.append(collections.deque([np.nan] * plotLength, maxlen=plotLength))
        self.isRun = False
        self.isSetup = False
        self.plotTimer = 0
        self.previousTimer = 0
        self.lickRightCorrect = np.nan
        self.lickRightWrong = np.nan
        self.lickLeftCorrect = np.nan
        self.lickLeftWrong = np.nan
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.paused = False

    def getFigure(self):
        return self.dynamic_canvas

    def setupAnimation(self):
        if not self.isSetup:
            # plotting starts below
            pltInterval = 10    # Period at which the plot animation updates [ms]
            xmin = 0
            xmax = self.plotMaxLength
            ymin = -5.0
            ymax = 5.0
            ax = self.dynamic_canvas.figure.add_subplot(111)
            ax.set_xlabel('Time')
            ax.set_ylabel('Voltage')
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10))
            ax.text(0.05, 0.80, 'Right Licks', transform=ax.transAxes)
            ax.text(0.05, 0.15, 'Left Licks', transform=ax.transAxes)

            lineLabel = ['Voltage', 'W', 'X', 'Y', 'Z']  # The letters are just place holder for the lick points so the 'for loop' below does not raise an "index out of range" error.
            style = ['k-', 'go', 'ro', 'go', 'ro']  # linestyles for the different plots
            timeText = ax.text(0.70, 0.99, '', transform=ax.transAxes)
            lines = []
            lineValueText = []
            for i in range(self.numPlots + 4):
                lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
                if i == 0:
                    # I use this if statement because I only want the first line's 'lineValueText' to be written in the top right corner of the plot.
                    # The first line is the voltage line. The other four lines are the points plotted for the licks which will say 'np.nan' and that
                    # gets in the way and does not look nice.
                    lineValueText.append(ax.text(0.70, 0.90-i*0.05, '', transform=ax.transAxes))

            # Make sure to use "self.anim" instead of just "anim". Otherwise animation will freeze because the reference will be garbage collected.
            self.anim = animation.FuncAnimation(self.dynamic_canvas.figure, self.parseData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
            logging.info("animation created")
            # Doing it like this causes the animation to freeze halfway into the plot.
            # anim = animation.FuncAnimation(self.dynamic_canvas.figure, self.getData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
            
            # self.dynamic_canvas.figure.legend(loc="upper left")
            self.isSetup = True

    def getData(self, data):
        self.rawData = data
        # logging.info(f"rawdata is {data}")

    def parseData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        # privateData = copy.deepcopy(self.rawData[:])    # so that the 3 values in our plots will be synchronized to the same sample time
        
        for i in range(0, self.numPlots):
            for j in range(len(self.rawData)):
                self.data[i].append(self.rawData[j])    # we get the latest data point and append it to our deque
                
            lines[i].set_data(range(self.plotMaxLength), self.data[i])
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(round(self.data[i][-1], 3)))  # I use the latest element for the voltage text.
        
        self.data[self.numPlots].append(self.lickRightCorrect)  # Right correct lick.
        self.data[self.numPlots + 1].append(self.lickRightWrong)    # Right incorrect lick.
        self.data[self.numPlots + 2].append(self.lickLeftCorrect)   # Left correct lick. 
        self.data[self.numPlots + 3].append(self.lickLeftWrong)  # Left incorrect lick.

        # Need to append as many elements to the lick lines as were appended to the voltage line so that all lines scroll at same speed.
        for i in range(self.numPlots, self.numPlots + 4):
            for j in range(len(self.rawData)):
                self.data[i].append(np.nan)

        lines[self.numPlots].set_data(range(self.plotMaxLength), self.data[self.numPlots])  # Set line for right correct lick.
        # lineValueText[self.numPlots].set_text('[' + lineLabel[self.numPlots] + '] = ' + str(value))  # Set text for right correct lick.
        lines[self.numPlots + 1].set_data(range(self.plotMaxLength), self.data[self.numPlots + 1])  # Set line for right incorrect lick.
        # lineValueText[self.numPlots + 1].set_text('[' + lineLabel[self.numPlots + 1] + '] = ' + str(value))  # Set text for right incorrect lick.
        lines[self.numPlots + 2].set_data(range(self.plotMaxLength), self.data[self.numPlots + 2])  # Set line for left correct lick.
        # lineValueText[self.numPlots + 2].set_text('[' + lineLabel[self.numPlots + 2] + '] = ' + str(value))  # Set text for left correct lick.
        lines[self.numPlots + 3].set_data(range(self.plotMaxLength), self.data[self.numPlots + 3])  # Set line for left incorrect lick.
        # lineValueText[self.numPlots + 3].set_text('[' + lineLabel[self.numPlots + 3] + '] = ' + str(value))  # Set text for left incorrect lick.

        # Reset lick values.
        self.lickRightCorrect = np.nan
        self.lickRightWrong = np.nan
        self.lickLeftCorrect = np.nan
        self.lickLeftWrong = np.nan

    def setInputEvent(self, params):
        direction = params[0]
        correct = params[1]
        if (direction == 'R'):
            if (correct == 1):
                self.lickRightCorrect = 2  # Y-axis max range is 2.5 so make right licks on top half of plot.
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = np.nan
            elif (correct == 0):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = 2
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = np.nan
        elif (direction == 'L'):
            if (correct == 1):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = -2  # Y-axis min range is -2.5 so make left licks on bottom half of plot.
                self.lickLeftWrong = np.nan
            elif (correct == 0):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = -2

    def pauseAnimation(self):
        if not self.paused:
            logging.info("attempting to pause animation")
            self.anim.event_source.stop()
            self.paused = True
            logging.info("animation paused")

    def resumeAnimation(self):
        if self.paused:
            logging.info("attempting to start animation")
            self.anim.event_source.start()
            self.paused = False
            logging.info("animation resumed")

    def startAnimation(self):
        if self.isSetup and not self.isRun:
            self.dynamic_canvas.draw()
            # FigureCanvas.draw(self.dynamic_canvas)  # This works too instead of "self.dynamic_canvas.draw()"
            logging.info("canvas drawn")
            self.isRun = True
            return True
        return False


class ResultsPlotWorker(QObject):
    def __init__(self):
        super(ResultsPlotWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.graphWidget = pg.PlotWidget()
        self.pen = pg.mkPen(color='r', width=2)
        styles = {'color':'blue', 'font-size': '10pt'}
        self.graphWidget.setBackground('w')
        self.graphWidget.setTitle('Percent Left Licks For Each Flow Rate', color='b', size='10pt')
        self.graphWidget.setLabel('left', 'Percent Left Licks', **styles)
        self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
        self.xAxis = self.graphWidget.getAxis('bottom')
        self.graphWidget.setYRange(0, 100, padding=0)
        self.xAxisReady = False

    def getWidget(self):
        return self.graphWidget

    def isXAxisSetup(self):
        return self.xAxisReady

    def setupXaxis(self, resultsDict):
        if not self.xAxisReady:
            ticks = list(resultsDict.keys())
            xdict = dict(enumerate(ticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(-1, len(ticks), padding=0)
            self.xAxisReady = True

    def updatePlot(self, x, y):
        self.graphWidget.clear()
        self.graphWidget.plot(x, y, name='Results', pen=self.pen, symbol='s', symbolSize=10, symbolBrush='r')
        logging.info('results plot updated')


class CalibrateWaterWorker(QObject):
    openValveSignal = pyqtSignal(int)
    closeValveSignal = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, valveNum, duration):
        super(CalibrateWaterWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.valveNum = valveNum
        self.duration = duration
        self.counter = 0

    def run(self):
        while (self.counter < 100):
            self.openValveSignal.emit(self.valveNum)
            QThread.msleep(self.duration)  # According to Qt documentation, this blocking method does not guarantee accurate timing.
            self.closeValveSignal.emit(self.valveNum)
            QThread.msleep(100)
            self.counter += 1
        
        self.finished.emit()



class Window(QMainWindow, Ui_MainWindow):
    stopRunningSignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connectSignalsSlots()
        self.olfas = None
        self.adc = None
        self.myBpod = None
        self.olfaSerialPort = 'COM5'
        self.adcSerialPort = 'COM6'
        self.bpodSerialPort = 'COM7'
        self.olfaPortLineEdit.setText(self.olfaSerialPort)
        self.analogInputModulePortLineEdit.setText(self.adcSerialPort)
        self.bpodPortLineEdit.setText(self.bpodSerialPort)
        self.streaming = StreamingWorker(plotLength=1000)
        self.streamingGroupBoxVLayout.addWidget(self.streaming.getFigure())
        self.streaming.setupAnimation()
        self.sessionDataWorker = None
        self.mouseNumber = None
        self.rigLetter = None
        self.numTrials = None
        self.experimentName = None
        self.leftWaterValve = 1
        self.finalValve = 2
        self.rightWaterValve = 3
        self.leftWaterValveDuration = 100  # milliseconds
        self.leftWaterValveDurationLineEdit.setText(str(self.leftWaterValveDuration))
        self.rightWaterValveDuration = 100  # milliseconds
        self.rightWaterValveDurationLineEdit.setText(str(self.rightWaterValveDuration))
        self.resultsPlot = ResultsPlotWorker()
        self.resultsPlotVLayout.addWidget(self.resultsPlot.getWidget())

        self.startButton.setEnabled(False)  # do not enable start button until user connects buttons.
        self.finalValveButton.setEnabled(False)
        self.leftWaterValveButton.setEnabled(False)
        self.rightWaterValveButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(False)
        self.calibRightWaterButton.setEnabled(False)

    def _connectSignalsSlots(self):
        self.olfaButton.clicked.connect(self._launchOlfaGUI)
        self.startButton.clicked.connect(self._runTask)
        self.stopButton.clicked.connect(self._endTask)
        self.finalValveButton.clicked.connect(self._toggleFinalValve)
        self.leftWaterValveButton.clicked.connect(self._toggleLeftWaterValve)
        self.rightWaterValveButton.clicked.connect(self._toggleRightWaterValve)
        self.calibLeftWaterButton.clicked.connect(self._calibrateLeftWaterValve)
        self.calibRightWaterButton.clicked.connect(self._calibrateRightWaterValve)
        self.connectDevicesButton.clicked.connect(self._connectDevices)

        self.mouseNumberLineEdit.editingFinished.connect(self._recordMouseNumber)
        self.rigLetterLineEdit.editingFinished.connect(self._recordRigLetter)
        self.nTrialsLineEdit.editingFinished.connect(self._recordNumTrials)
        self.leftWaterValveDurationLineEdit.editingFinished.connect(self._recordLeftWaterValveDuration)
        self.rightWaterValveDurationLineEdit.editingFinished.connect(self._recordRightWaterValveDuration)
        self.bpodPortLineEdit.editingFinished.connect(self._recordBpodSerialPort)
        self.analogInputModulePortLineEdit.editingFinished.connect(self._recordAnalogInputModuleSerialPort)
        self.olfaPortLineEdit.editingFinished.connect(self._recordOlfaSerialPort)

    def _launchOlfaGUI(self):
        if self.olfas is not None:
            self.olfas.show()

    def configureAnalogModule(self):
        self.adc.setSamplingRate(1000)
        self.adc.setNactiveChannels(1)
        # TODO: instead of passing a list, make it such that the user specifies the range of a specific channel by passing an int for the channel and a string for the range.
        self.adc.setInputRange(['-5V:5V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V'])
        self.adc.setStream2USB([1, 0, 0, 0, 0, 0, 0, 0])
        self.adc.setSMeventsEnabled([1, 0, 0, 0, 0, 0, 0, 0])
        self.adc.setThresholds([0, 10, 10, 10, 10, 10, 10, 10])  # The default threshold is already set to 10V during initialization, but still need to specify it for the other channels.
        self.adc.setResetVoltages([1, -10, -10, -10, -10, -10, -10, -10])

    def startAnalogModule(self):
        self.adc.startReportingEvents()
        # self.adc.startLogging()
        self.adc.startUSBStream()

    def stopAnalogModule(self):
        logging.info("attempting to stop USB streaming")
        self.adc.stopUSBStream()
        # for i in range(5):
        #     # Try to stop it 5 times because usually the first two tries fail.
        #     logging.info(f'trying to stop logging: trial {i + 1}')
        #     try:
        #         self.adc.stopLogging()
        #         logging.info("analog module stopped logging to SD card")
        #         break
        #     except BpodErrorException:
        #         logging.info("could not stop logging")

        # logging.info("attempting to stop reporting events")
        # self.adc.stopReportingEvents()  # Not necessary to stop event reporting. Will not make difference. And also usually fails first two tries.

    
    # def _getSDCardLog(self):
    #     adcSignal = self.adc.getData()
    #     logging.info('got analog data. here is what is got:')
    #     logging.info(adcSignal)
    #     self.sessionDataWorker.receiveAnalogData(adcSignal)
    def _connectDevices(self):
        try:
            if self.analogInputModuleCheckBox.isChecked():
                self.adc = BpodAnalogIn(serial_port=self.adcSerialPort)
        except BpodErrorException:
            QMessageBox.warning(self, "Warning", "Cannot connect analog input module! Check that serial port is correct!")
            return

        try:
            if self.olfaCheckBox.isChecked():
                self.olfas = olfactometry.Olfactometers()  # Import to only create object once up here.
        except IOError:
            QMessageBox.warning(self, "Warning", "Cannot connect to olfactometer! Check that serial port is correct!")
            return

        try:
            self.myBpod = Bpod(serial_port=self.bpodSerialPort)
        except IOError:
            QMessageBox.warning(self, "Warning", "Cannot connect to bpod! Check that serial port is correct!")
            return
        
        self.startButton.setEnabled(True)  # This means successful connection attempt for enabled devices.
        self.connectDevicesButton.setEnabled(False)  # Disable to prevent clicking again.
        self.connectDevicesButton.setText("Connected")

        self.finalValveButton.setEnabled(True)
        self.leftWaterValveButton.setEnabled(True)
        self.rightWaterValveButton.setEnabled(True)
        self.calibLeftWaterButton.setEnabled(True)
        self.calibRightWaterButton.setEnabled(True)

    def _runTask(self):
        if self.mouseNumber is None:
            QMessageBox.warning(self, "Warning", "Please enter mouse number!")
            return
        elif self.rigLetter is None:
            QMessageBox.warning(self, "Warning", "Please enter rig letter!")
            return
        elif self.numTrials is None:
            QMessageBox.warning(self, "Warning", "Please enter number of trials for this experiment!")
            return

        self.configureAnalogModule()
        self.startAnalogModule()
        self._runSessionDataThread()
        self._runInputEventThread()
        self._runProtocolThread()

        if not self.streaming.startAnimation():
            self.streaming.resumeAnimation()

        self.startButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(False)
        self.calibRightWaterButton.setEnabled(False)
        self.stopButton.setEnabled(True)

    def _endTask(self):
        self.streaming.pauseAnimation()
        self.stopAnalogModule()
        # self._getSDCardLog()
        self.stopRunningSignal.emit()
        logging.info("stopRunningSignal emitted")
        
        # self._checkIfRunning()  # causes unhandled python exception when called twice. Check definition for details.
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self._experimentCompleteDialog()

    def _checkIfRunning(self):
        # When this function is called for the first time upon clicking the stop button
        # to stop the threads, it works without errors or raising exceptions and will
        # return true for all except 'self.sessionDataThread.isRunning()' which will be
        # false. Not sure why any of the threads would still be running when they should
        # have quit, but this is another issue to be investigated some other time.

        # However, when this function is called the second time (because the 'protocolWorker.finished'
        # signal connects to 'self._endTask' function and so the 'self._endTask' function will be 
        # called twice when the user clicks the stop button) there will be an error when you try to
        # call 'self.inputEventThread.isRunning()'. My logging.info stops right before that line
        # so my guess is that it is causing an error, as if the inputEventThread does not have an
        # method called 'isRunning'. Maybe its because the thread was deleted and thus does not have
        # that 'isRunning' method anymore, but calling 'self.inputEventThread.isRunning()' even before
        # starting the thread will still work without error (it will return False). Putting it inside
        # a try/except clause with 'AttributeError' as the exception does NOT trigger the except clause.
        # But when I use 'RuntimeError' as the exception, the except clause DOES get triggered.
        logging.info("Checking if threads are still running...")
        if self.inputEventThread:
            logging.info("self.inputEventThread exists. Its type is...")
            logging.info(type(self.inputEventThread))
            try:
                if not self.inputEventThread.isRunning():
                    logging.info("inputEventThread no longer running")
                else:
                    logging.info("ERROR inputEventThread is still running")
            except RuntimeError:
                logging.info("AttributeError: no method named 'isRunning'")
        else:
            logging.info("self.inputEventThread does not exist")
        if not self.samplingThread.isRunning():
            logging.info("samplingThread no longer running")
        else:
            logging.info("ERROR SamplingThread is still running")
        if not self.protocolThread.isRunning():
            logging.info("protocolThread no longer running")
        else:
            logging.info("ERROR protocolThread is still running")
        if not self.sessionDataThread.isRunning():
            logging.info("ERROR sessionDataThread is still runnning")
        else:
            logging.info("sessionDataThread no longer running")

    def closeDevices(self):
        if self.adc is not None:
            self.adc.close()
            logging.info('Analog Input Module closed')
        # if self.olfas is not None:
        #     self.olfas.close_serials()
        #     logging.info('olfas close_serials')
        #     self.olfas.close()
        #     logging.info('olfas close')
        if self.myBpod is not None:
            self.myBpod.close()
            logging.info('Bpod closed')

    def _toggleFinalValve(self):
        if self.myBpod is not None:
            if self.finalValveButton.isChecked():
                self._openValve(self.finalValve)
            else:
                self._closeValve(self.finalValve)

    def _toggleLeftWaterValve(self):
        if self.myBpod is not None:
            self._openValve(self.leftWaterValve)
            QTimer.singleShot(self.leftWaterValveDuration, lambda: self._closeValve(self.leftWaterValve))

    def _toggleRightWaterValve(self):
        if self.myBpod is not None:
            self._openValve(self.rightWaterValve)
            QTimer.singleShot(self.rightWaterValveDuration, lambda: self._closeValve(self.rightWaterValve))

    def _openValve(self, channelNum):
        if self.myBpod is not None:
            self.myBpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=1)

    def _closeValve(self, channelNum):
        if self.myBpod is not None:
            self.myBpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=0)

    def _calibrateLeftWaterValve(self):
        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.calibLeftWaterButton.setEnabled(False)
            self.calibRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._calibrateLeftWaterValveToggler)

            self.progress = QProgressDialog("Calibrating left water valve...", "Cancel", 0, 100, self)
            self.progress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.leftWaterValveDuration)

    def _calibrateLeftWaterValveToggler(self):
        if self.progress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.progress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.leftWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.leftWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.progress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _calibrateRightWaterValve(self):
        # self._runCalibrateWaterThread(self.rightWaterValve, self.rightWaterValveDuration)

        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.calibLeftWaterButton.setEnabled(False)
            self.calibRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._calibrateRightWaterValveToggler)

            self.progress = QProgressDialog("Calibrating right water valve...", "Cancel", 0, 100, self)
            self.progress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.rightWaterValveDuration)

    def _calibrateRightWaterValveToggler(self):
        if self.progress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.progress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.rightWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.rightWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.progress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _recordMouseNumber(self):
        self.mouseNumber = self.mouseNumberLineEdit.text()

    def _recordRigLetter(self):
        self.rigLetter = self.rigLetterLineEdit.text()

    def _recordNumTrials(self):
        self.numTrials = int(self.nTrialsLineEdit.text())

    def _recordLeftWaterValveDuration(self):
        self.leftWaterValveDuration = int(self.leftWaterValveDurationLineEdit.text())
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftWaterDuration(self.leftWaterValveDuration)

    def _recordRightWaterValveDuration(self):
        self.rightWaterValveDuration = int(self.rightWaterValveDurationLineEdit.text())
        if self.protocolWorker is not None:
            self.protocolWorker.setRightWaterDuration(self.rightWaterValveDuration)

    def _recordBpodSerialPort(self):
        self.bpodSerialPort = self.bpodPortLineEdit.text()

    def _recordOlfaSerialPort(self):
        self.olfaSerialPort = self.olfaPortLineEdit.text()

    def _recordAnalogInputModuleSerialPort(self):
        self.adcSerialPort = self.analogInputModulePortLineEdit.text()

    def _updateCurrentState(self, stateName):
        self.currentStateLineEdit.setText(stateName)

    def _updateResponseResult(self, result):
        self.responseResultLineEdit.setText(result)

    def _updateSessionTotals(self, totalsDict):
        logging.info('attempting to update session totals')
        self.totalRewardsLineEdit.setText(str(totalsDict['totalRewards']))
        self.totalWrongLicksLineEdit.setText(str(totalsDict['totalPunishes']))
        self.totalNoResponsesLineEdit.setText(str(totalsDict['totalNoResponses']))
        self.totalPercentCorrectLineEdit.setText(str(totalsDict['totalPercentCorrect']))

    def _updateCurrentTrialInfo(self, trialInfoDict):
        trialInfo = trialInfoDict
        # Check if not empty.
        if trialInfo:
            self.trialLineEdit.setText("{0} of {1}".format(trialInfo['currentTrialNum'], trialInfo['nTrials']))
            self.correctResponseLineEdit.setText(trialInfo['correctResponse'])
            self.itiLineEdit.setText(str(trialInfo['currentITI']))
            self.odorNameLineEdit.setText(trialInfo['currentOdorName'])
            self.odorConcentrationLineEdit.setText(str(trialInfo['currentOdorConc']))
            self.currentFlowLineEdit.setText(str(trialInfo['currentFlow']))

    def _updateResultsPlot(self, flowResultsDict):
        if not self.resultsPlot.isXAxisSetup():
            self.resultsPlot.setupXaxis(flowResultsDict)

        xValues = []
        yValues = []
        index = 0

        # This is to plot percent correct

        # for k, v in flowResultsDict.items():
        #     numCorrect = v['Correct']
        #     numTotal = v['Total']
        #     if not (numTotal == 0):
        #         percent = round((float(numCorrect) / float(numTotal) * 100), 2)
        #     else:
        #         percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
        #     xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
        #     yValues.append(percent)
        #     index += 1

        # This is to plot percent left licks

        for k, v in flowResultsDict.items():
            numLeft = v['left']
            numTotal = v['Total']
            if not (numTotal == 0):
                percent = round((float(numLeft) / float(numTotal) * 100), 2)
            else:
                percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
            xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
            yValues.append(percent)
            index += 1
        self.resultsPlot.updatePlot(xValues, yValues)

    def _noResponseAbortDialog(self):
        QMessageBox.information(self, "Notice", "Session aborted due to too many consecutive no responses.")

    def _experimentCompleteDialog(self):
        QMessageBox.information(self, "Success", "Experiment finished!")

    def _runInputEventThread(self):
        self.inputEventThread = QThread()
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")
        self.inputEventWorker = InputEventWorker(self.myBpod)
        self.inputEventWorker.moveToThread(self.inputEventThread)
        self.inputEventThread.started.connect(self.inputEventWorker.run)
        self.inputEventWorker.finished.connect(self.inputEventThread.quit)
        self.inputEventWorker.finished.connect(self.inputEventWorker.deleteLater)
        self.inputEventThread.finished.connect(self.inputEventThread.deleteLater)
        self.inputEventWorker.inputEventSignal.connect(self.streaming.setInputEvent)
        self.stopRunningSignal.connect(lambda: self.inputEventWorker.stopRunning())  # Need to use lambda, to explicitly make function call (from the main thread). Because the inputEventThread will never call it since its in a infinite loop.
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")
        logging.info("attempting to start inputEventThread")
        self.inputEventThread.start()
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")

    def _runSessionDataThread(self):
        self.sessionDataThread = QThread()
        self.sessionDataWorker = SessionDataWorker(self.mouseNumber, self.rigLetter, self.adc)
        self.sessionDataWorker.moveToThread(self.sessionDataThread)
        self.sessionDataThread.started.connect(self.sessionDataWorker.run)
        self.sessionDataWorker.finished.connect(self.sessionDataThread.quit)
        self.sessionDataWorker.finished.connect(self.sessionDataWorker.deleteLater)
        self.sessionDataThread.finished.connect(self.sessionDataThread.deleteLater)
        self.sessionDataWorker.analogDataSignal.connect(self.streaming.getData)
        self.stopRunningSignal.connect(lambda: self.sessionDataWorker.stopRunning())
        self.sessionDataThread.start()
        logging.info(f"sessionDataThread running? {self.sessionDataThread.isRunning()}")
  
    def _runProtocolThread(self):
        self.protocolThread = QThread()
        self.protocolWorker = ProtocolWorker(self.myBpod, self.olfas, self.numTrials)
        self.protocolWorker.moveToThread(self.protocolThread)
        self.protocolThread.started.connect(self.protocolWorker.run)
        self.protocolWorker.finished.connect(self.protocolThread.quit)
        self.protocolWorker.finished.connect(self._endTask)  # This serves to stop the other threads when the protocol thread completes all trials.
        self.protocolWorker.finished.connect(self.protocolWorker.deleteLater)
        self.protocolThread.finished.connect(self.protocolThread.deleteLater)
        self.protocolWorker.trialStartSignal.connect(lambda x: self.inputEventWorker.newTrialSlot(x))
        self.protocolWorker.newStateSignal.connect(self._updateCurrentState)
        self.protocolWorker.responseResultSignal.connect(self._updateResponseResult)
        self.protocolWorker.newTrialInfoSignal.connect(self._updateCurrentTrialInfo)  # This works without lambda because 'self._updateCurrentTrialInfo' is in the main thread.
        self.protocolWorker.flowResultsCounterDictSignal.connect(self._updateResultsPlot)
        self.protocolWorker.totalsDictSignal.connect(self._updateSessionTotals)
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.sessionDataWorker.receiveInfoDict(x))  # 'x' is the dictionary parameter emitted from 'saveTrialDataDictSignal' and passed into 'receiveInfoDict(x)'
        self.protocolWorker.saveEndOfSessionDataSignal.connect(lambda x: self.sessionDataWorker.receiveFinalResultsDict(x))  # 'x' is the dictionary parameter emitted from 'saveEndOfSessionDataSignal' and passed into 'receiveFinalResultsDict(x)'
        # self.protocolWorker.startSDCardLoggingSignal.connect(self._startSDCardLogging)
        # self.protocolWorker.stopSDCardLoggingSignal.connect(self._stopSDCardLogging)
        self.protocolWorker.noResponseAbortSignal.connect(self._noResponseAbortDialog)
        self.stopRunningSignal.connect(lambda: self.protocolWorker.stopRunning())
        self.protocolThread.start()
        logging.info("protocolThread started")

    # def _runCalibrateWaterThread(self, valveNum, duration):
    #     self.calibrateWaterThread = QThread()
    #     self.calibrateWaterWorker = CalibrateWaterWorker(valveNum=valveNum, duration=duration)
    #     self.calibrateWaterWorker.moveToThread(self.calibrateWaterThread)
    #     self.calibrateWaterThread.started.connect(self.calibrateWaterWorker.run)
    #     self.calibrateWaterWorker.finished.connect(self.calibrateWaterThread.quit)
    #     self.calibrateWaterWorker.finished.connect(self.calibrateWaterWorker.deleteLater)
    #     self.calibrateWaterThread.finished.connect(self.calibrateWaterThread.deleteLater)
    #     self.calibrateWaterWorker.openValveSignal.connect(lambda: self._openValve(valveNum))
    #     self.calibrateWaterWorker.closeValveSignal.connect(lambda: self._closeValve(valveNum))
    #     self.calibrateWaterThread.start()
    #     logging.info("calibrateWaterThread start")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    status = app.exec()
    win.closeDevices()
    sys.exit(status)
