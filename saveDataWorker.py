import tables
import logging
import os
import numpy as np
import time
from datetime import datetime
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot, Qt

logging.basicConfig(format="%(message)s", level=logging.INFO)


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
    vialNum = tables.StringCol(8, pos=3)
    odorName = tables.StringCol(32, pos=4)  # Size of strings added to the column does not need to exactly match the size given during initialization.
    odorConc = tables.StringCol(16, pos=5)  # I use StringCol instead of Float32Col because of experiments that use two odors will send out two concs as a single string.
    odorFlow = tables.UInt8Col(pos=6)
    leftLicksCount = tables.UInt8Col(pos=7)
    rightLicksCount = tables.UInt8Col(pos=8)
    itiDuration = tables.UInt8Col(pos=9)
    trialStartTime = tables.Float32Col(pos=10)
    trialEndTime = tables.Float32Col(pos=11)
    totalTrialTime = tables.Float32Col(pos=12)
    bpodStartTime = tables.Float32Col(pos=13)


class OneOdorResultsData(tables.IsDescription):
    flowRate = tables.UInt8Col(pos=0)
    totalUsage = tables.UInt16Col(pos=1)
    totalRight = tables.UInt16Col(pos=2)
    totalLeft = tables.UInt16Col(pos=3)
    totalCorrect = tables.UInt16Col(pos=4)
    totalWrong = tables.UInt16Col(pos=5)
    totalNoResponse = tables.UInt16Col(pos=6)

class TwoOdorResultsData(tables.IsDescription):
    firstVial = tables.UInt8Col(pos=0)
    secondVial = tables.UInt8Col(pos=1)
    totalUsage = tables.UInt16Col(pos=2)
    totalRight = tables.UInt16Col(pos=3)
    totalLeft = tables.UInt16Col(pos=4)
    totalCorrect = tables.UInt16Col(pos=5)
    totalWrong = tables.UInt16Col(pos=6)
    totalNoResponse = tables.UInt16Col(pos=7)


class VoltageData(tables.IsDescription):
    stateNum = tables.UInt8Col(pos=0)
    # stateNum = tables.StringCol(1, pos=0)
    # computerTime = tables.Float32Col(pos=1)
    # computerPeriod = tables.Float32Col(pos=2)
    bpodTime = tables.Float32Col(pos=1)
    voltage = tables.Float32Col(shape=(1, ), pos=2)


class SaveDataWorker(QObject):
    analogDataSignal = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self, mouseNum, rigLetter, experimentType, analogInModule=None):
        super(SaveDataWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.experimentType = experimentType
        dateTimeString = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        fileName = f"results/Mouse_{mouseNum}_Rig_{rigLetter}_{dateTimeString}.h5"
        if not os.path.isdir('results'):
            os.mkdir('results')
        self.h5file = tables.open_file(filename=fileName, mode='w', title=f"Mouse {mouseNum} Experiment Data")

        self.licksGroup = self.h5file.create_group(where='/', name='lickTimes', title='Lick Timestamps Per Trial')
        self.trialsTable = self.h5file.create_table(where='/', name='trial_data', description=SessionData, title='Trial Data')
        self.trialRow = self.trialsTable.row
        self.statesTable = None  # Make it None because have to wait for completion of first trial to get names of all the states. Afterwhich, make description dictionary and then table.
        self.statesTableDescDict = {}  # Description for the states table (using this instead of making a class definition and subclassing tables.IsDescription).
        self.licksTable = None
        self.licksTableDescDict = {  # Description for the licks table instead of making a class definition and subclassing tables.IsDescription.
            'leftLickTimes': tables.Float32Col(dflt=np.nan, pos=0),
            'rightLickTimes': tables.Float32Col(dflt=np.nan, pos=1)
        }
        self.keepRunning = True
        self.newData = False
        self.resultsRowsAppended = False  # This will be used to append the results Totals to the resultsTable only once after the first trial and then iterate and update the rows for every successive trial onwards.
        self.trialNum = 1
        self.infoDict = {}
        self.totalResultsDict = {}

        self.adc = analogInModule
        if self.adc:
            self.maxVoltage = self.adc.getChannelInputVoltageMax(0)  # Assuming user is using channel 0.
            self.samplingPeriod = 1 / (self.adc.getSamplingRate())
            self.analogDataBufferSize = 4
            self.analogDataBuffer = np.zeros(shape=self.analogDataBufferSize, dtype='float32')
            self.stateNum = 0
            self.counter = 0
            self.previousTimer = 0
            self.t_start = 0
            self.bpodTime = 0
            self.voltsGroup = self.h5file.create_group(where='/', name='voltages', title='Voltages Per Trial')
            self.voltTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum}', description=VoltageData, title=f'Trial {self.trialNum} Voltage Data')
            self.voltsRow = self.voltTable.row

    def receiveInfoDict(self, infoDict):
        self.newData = True
        logging.info("incoming infoDict")
        self.infoDict = infoDict

    def receiveTotalResultsDict(self, resultsDict):
        logging.info('incoming total results dict')
        self.totalResultsDict = resultsDict

    def saveTotalResults(self):
        logging.info('attempting to save result totals data')
        if self.experimentType == 'oneOdorIntensity':
            if self.resultsRowsAppended:
                # If the rows were appended to the resultsTable for the first trial already, then do not use append again because it will continue to append new rows below the last.
                # Instead, I want to keep the rows from the first trial and just update the values for the totals for each flowrate. To do that, I must iterate through each resultsTable
                # inside the resultsGroup.
                for table in self.h5file.walk_nodes(self.resultsGroup, "Table"):
                    vial = table._v_name.strip('vial_')  # I need the string form of the vial number only, to use as the key.
                    for row in table.iterrows():
                        key = str(row['flowRate'])  # flowrate is saved as a UInt8Col in the table so need to convert back to string.
                        row['totalUsage'] = self.totalResultsDict[vial][key]['Total']
                        row['totalRight'] = self.totalResultsDict[vial][key]['right']
                        row['totalLeft'] = self.totalResultsDict[vial][key]['left']
                        row['totalCorrect'] = self.totalResultsDict[vial][key]['Correct']
                        row['totalWrong'] = self.totalResultsDict[vial][key]['Wrong']
                        row['totalNoResponse'] = self.totalResultsDict[vial][key]['NoResponse']
                        row.update()
                    self.table.flush()
            else:
                # This means the rows have not yet been appended to the results table after the first trial.
                self.resultsGroup = self.h5file.create_group(where='/', name='total_results', title='Total Response Results')
                for vialNum, flowrateDict in self.totalResultsDict.items():
                    self.resultsTable = self.h5file.create_table(where='/total_results', name=f'vial_{vialNum}', description=OneOdorResultsData, title=f'Vial {vialNum} Total Response Results')
                    self.resultsRow = self.resultsTable.row
                    for flowrate, total in flowrateDict.items():
                        self.resultsRow['flowRate'] = flowrate  # flowrate is a string here, but when saved into the table, it gets converted to UInt8Col.
                        self.resultsRow['totalUsage'] = total['Total']
                        self.resultsRow['totalRight'] = total['right']
                        self.resultsRow['totalLeft'] = total['left']
                        self.resultsRow['totalCorrect'] = total['Correct']
                        self.resultsRow['totalWrong'] = total['Wrong']
                        self.resultsRow['totalNoResponse'] = total['NoResponse']
                        self.resultsRow.append()
                    self.resultsTable.flush()
                self.resultsRowsAppended = True

        elif self.experimentType == 'twoOdorMatch':
            if self.resultsRowsAppended:
                # If the rows were appended to the resultsTable for the first trial already, then do not use append again because it will continue to append new rows below the last.
                # Instead, I want to keep the rows from the first trial and just update the values for the totals for each flowrate. To do that, I must iterate through each row
                # inside the resultsTable. Since the table's rows will be iterated in the same order as they were read from the totalResultsDict and appended, there only needs to
                # be one for loop instead of two nested for loops. The number of rows will be equal to the total number of permutations for the two vials used in each trial.
                for row in self.resultsTable.iterrows():
                    firstVial = str(row['firstVial'])  # firstVial is an UInt8Col in the resultsTable, so need to convert back to string to use as a key.
                    secondVial = str(row['secondVial'])  # same goes for secondVial.
                    row['totalUsage'] = self.totalResultsDict[firstVial][secondVial]['Total']
                    row['totalRight'] = self.totalResultsDict[firstVial][secondVial]['right']
                    row['totalLeft'] = self.totalResultsDict[firstVial][secondVial]['left']
                    row['totalCorrect'] = self.totalResultsDict[firstVial][secondVial]['Correct']
                    row['totalWrong'] = self.totalResultsDict[firstVial][secondVial]['Wrong']
                    row['totalNoResponse'] = self.totalResultsDict[firstVial][secondVial]['NoResponse']
                    row.update()
                self.resultsTable.flush()
            else:
                # This means the rows have not yet been appended to the results table after the first trial, so create the table now.
                self.resultsTable = self.h5file.create_table(where='/', name=f'totalResults', description=TwoOdorResultsData, title=f'Total Response Results')
                self.resultsRow = self.resultsTable.row
                for firstVial in self.totalResultsDict.keys():
                    for secondVial in self.totalResultsDict[firstVial].keys():
                        self.resultsRow['firstVial'] = firstVial  # firstVial is a string here, but will be converted to an UInt8Col in the resultsTable.
                        self.resultsRow['secondVial'] = secondVial  # secondVial is also a string here and will also be converted to UInt8Col.
                        self.resultsRow['totalUsage'] = self.totalResultsDict[firstVial][secondVial]['Total']
                        self.resultsRow['totalRight'] = self.totalResultsDict[firstVial][secondVial]['right']
                        self.resultsRow['totalLeft'] = self.totalResultsDict[firstVial][secondVial]['left']
                        self.resultsRow['totalCorrect'] = self.totalResultsDict[firstVial][secondVial]['Correct']
                        self.resultsRow['totalWrong'] = self.totalResultsDict[firstVial][secondVial]['Wrong']
                        self.resultsRow['totalNoResponse'] = self.totalResultsDict[firstVial][secondVial]['NoResponse']
                        self.resultsRow.append()
                    self.resultsTable.flush()
                self.resultsRowsAppended = True
        
        logging.info('results data has been written to disk')

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
        # self.t_start = time.perf_counter()
        while self.keepRunning:
            if self.newData:
                self.newData = False  # reset
                logging.info("attempting to save data")

                self.licksTable = self.h5file.create_table(where='/lickTimes', name=f'trial_{self.trialNum}', description=self.licksTableDescDict, title=f'Trial {self.trialNum} Lick Timestamps')
                self.licksRow = self.licksTable.row

                self.trialRow['trialNum'] = self.infoDict['currentTrialNum']
                self.trialRow['correctResponse'] = self.infoDict['correctResponse']
                self.trialRow['responseResult'] = self.infoDict['responseResult']
                self.trialRow['vialNum'] = self.infoDict['currentVialNum']
                self.trialRow['odorName'] = self.infoDict['currentOdorName']
                self.trialRow['odorConc'] = str(self.infoDict['currentOdorConc'])  # convert to string in case it is a float.
                self.trialRow['odorFlow'] = self.infoDict['currentFlow']
                self.trialRow['itiDuration'] = self.infoDict['currentITI']
                self.trialRow['trialStartTime'] = self.infoDict['Trial start timestamp']
                self.trialRow['trialEndTime'] = self.infoDict['Trial end timestamp']
                self.trialRow['totalTrialTime'] = self.trialRow['trialEndTime'] - self.trialRow['trialStartTime']
                self.trialRow['bpodStartTime'] = self.infoDict['Bpod start timestamp']

                if 'Port1In' in self.infoDict['Events timestamps']:
                    leftLicksList = self.infoDict['Events timestamps']['Port1In']
                    leftLicksCount = len(leftLicksList)
                    self.trialRow['leftLicksCount'] = leftLicksCount

                    if 'Port3In' in self.infoDict['Events timestamps']:
                        rightLicksList = self.infoDict['Events timestamps']['Port3In']
                        rightLicksCount = len(rightLicksList)
                        self.trialRow['rightLicksCount'] = rightLicksCount

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
                        self.trialRow['leftLicksCount'] = len(self.infoDict['Events timestamps']['Port1In'])
                        for t in self.infoDict['Events timestamps']['Port1In']:
                            self.licksRow['leftLickTimes'] = t
                            self.licksRow.append()
                    self.licksTable.flush()

                # Only right licks exist.
                elif 'Port3In' in self.infoDict['Events timestamps']:
                    self.trialRow['rightLicksCount'] = len(self.infoDict['Events timestamps']['Port3In'])
                    for t in self.infoDict['Events timestamps']['Port3In']:
                        self.licksRow['rightLickTimes'] = t
                        self.licksRow.append()
                    self.licksTable.flush()
                
                self.trialRow.append()
                self.trialsTable.flush()
                self.saveStatesTimestamps()
                self.saveTotalResults()
                self.trialNum += 1  # increment trial number.

                if self.adc:
                    # The trial data above comes at the end of a trial, so write the voltages to the disk, and create a new table for the next trial's voltages
                    self.voltTable.flush()
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
            
            elif self.adc:
                analogData = self.adc.getSampleFromUSB()

                # Uses the computer's clock to make the timestamps for the samples and period in between each sample.
                # currentTimer = time.perf_counter()
                # period = currentTimer - self.previousTimer
                # elapsed = currentTimer - self.t_start
                # self.previousTimer = currentTimer

                if analogData is not None:
                    prefix = analogData[0][0]
                    syncByte = analogData[0][1]
                    samples = analogData[1]
                    voltages = [0] * len(samples)

                    if (prefix == 35):  # 35 is the decimal value for the ascii char '#'
                        self.stateNum = syncByte  # update the state number with the syncByte as a uint8.

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

            else:
                QThread.sleep(1)  # Need this or else entire application will become severely unresponsive.

        if self.adc:
            self.voltTable.flush()

        self.trialsTable.flush()
        self.resultsTable.flush()
        logging.info("session data has been written to disk")
        self.h5file.close()
        logging.info("h5 file closed")
        self.finished.emit()
        
    def stopRunning(self):
        self.keepRunning = False
