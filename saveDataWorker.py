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


class OneOdorResultsData(tables.IsDescription):
    flowRate = tables.UInt8Col(pos=0)
    totalUsage = tables.UInt16Col(pos=1)
    totalRight = tables.UInt16Col(pos=2)
    totalLeft = tables.UInt16Col(pos=3)
    totalCorrect = tables.UInt16Col(pos=4)
    totalWrong = tables.UInt16Col(pos=5)
    totalNoResponse = tables.UInt16Col(pos=6)


class TwoOdorResultsData(tables.IsDescription):
    odorA_vial = tables.UInt8Col(pos=0)
    odorB_vial = tables.UInt8Col(pos=1)
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
    voltageCh1 = tables.Float32Col(pos=2)
    voltageCh2 = tables.Float32Col(pos=3)
    voltageCh3 = tables.Float32Col(pos=4)
    voltageCh4 = tables.Float32Col(pos=5)
    voltageCh5 = tables.Float32Col(pos=6)
    voltageCh6 = tables.Float32Col(pos=7)
    voltageCh7 = tables.Float32Col(pos=8)
    voltageCh8 = tables.Float32Col(pos=9)


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
        self.eventsGroup = self.h5file.create_group(where='/', name='event_times', title='Event Timestamps Per Trial')
        
        self.trialsTable = None  # Make it None for now because have to wait for completion of first trial to get the infoDict with data on the trial. Once that comes, make a description dictionary using the infoDict and then use that description dict to create the trialsTable.
        self.trialsTableDescDict = {}  # Description for the trialsTable (using this instead of making a class definition and subclassing tables.IsDescription).
        self.statesTable = None  # Make it None because have to wait for completion of first trial to get names of all the states. Afterwhich, make description dictionary and then table.
        self.statesTableDescDict = {}  # Description for the states table (using this instead of making a class definition and subclassing tables.IsDescription).
        self.eventsTable = None  # Same thing here, and also because I do not want to create the eventsTable if no input events even occurred.
        self.eventsTableDescDict = {}  # Description for the events table instead of making a class definition and subclassing tables.IsDescription.
        
        self.keepRunning = True
        self.newData = False
        self.resultsRowsAppended = False  # This will be used to append the results Totals to the resultsTable only once after the first trial and then iterate and update the rows for every successive trial onwards.
        self.trialNum = 1
        self.infoDict = {}
        self.totalResultsList = []

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

    def receiveTotalResultsList(self, resultsList):
        logging.info('incoming total results list')
        self.totalResultsList = resultsList

    def saveTotalResults(self):
        logging.info('attempting to save result totals data')
        if self.experimentType == 'oneOdorIntensity':
            if self.resultsRowsAppended:
                # If the rows were appended to the resultsTable for the first trial already, then do not use append again because it will continue to append new rows below the last.
                # Instead, I want to keep the rows from the first trial and just update the values for the totals for each flowrate. To do that, I must iterate through each resultsTable
                # inside the resultsGroup.
                for table in self.h5file.walk_nodes(self.resultsGroup, "Table"):
                    tableNameSplit = table._v_name.split('_')  # will return ['olfa', '0', 'vial', '5'] as an example
                    olfa = int(tableNameSplit[1])  # convert to int to use as index.  
                    vial = tableNameSplit[3]  # already in string form to use as a key.
                    for row in table.iterrows():
                        key = str(row['flowRate'])  # flowrate is saved as a UInt8Col in the table so need to convert back to string.
                        row['totalUsage'] = self.totalResultsList[olfa][vial][key]['Total']
                        row['totalRight'] = self.totalResultsList[olfa][vial][key]['right']
                        row['totalLeft'] = self.totalResultsList[olfa][vial][key]['left']
                        row['totalCorrect'] = self.totalResultsList[olfa][vial][key]['Correct']
                        row['totalWrong'] = self.totalResultsList[olfa][vial][key]['Wrong']
                        row['totalNoResponse'] = self.totalResultsList[olfa][vial][key]['NoResponse']
                        row.update()
                    table.flush()
            else:
                # This means the rows have not yet been appended to the results table after the first trial.
                if self.totalResultsList:  # Check that its not empty first.
                    self.resultsGroup = self.h5file.create_group(where='/', name='total_results', title='Total Response Results')
                    for i in range(len(self.totalResultsList)):  # self.totalResultsList is a list of dictionaries where each dictionary is a resultsCounterDict from the protocolWorker.
                        for vialNum, flowrateDict in self.totalResultsList[i].items():
                            self.resultsTable = self.h5file.create_table(where='/total_results', name=f'olfa_{i}_vial_{vialNum}', description=OneOdorResultsData, title=f'Olfa {i} Vial {vialNum} Total Response Results')
                            self.resultsRow = self.resultsTable.row
                            sortedFlowrates = sorted(list(flowrateDict.keys()), key=int)  # I sort the flowrates by numeric value because for some reason they get sorted alphabetically ever since I used a list for self.totalResultsList to hold dictionaries for each olfactometer, even though I save the flowrate keys in sorted order to each vial's dictionary.
                            for flowrate in sortedFlowrates:
                                self.resultsRow['flowRate'] = flowrate  # flowrate is a string here, but when saved into the table, it gets converted to UInt8Col.
                                self.resultsRow['totalUsage'] = self.totalResultsList[i][vialNum][flowrate]['Total']
                                self.resultsRow['totalRight'] = self.totalResultsList[i][vialNum][flowrate]['right']
                                self.resultsRow['totalLeft'] = self.totalResultsList[i][vialNum][flowrate]['left']
                                self.resultsRow['totalCorrect'] = self.totalResultsList[i][vialNum][flowrate]['Correct']
                                self.resultsRow['totalWrong'] = self.totalResultsList[i][vialNum][flowrate]['Wrong']
                                self.resultsRow['totalNoResponse'] = self.totalResultsList[i][vialNum][flowrate]['NoResponse']
                                self.resultsRow.append()
                            self.resultsTable.flush()
                    self.resultsRowsAppended = True

        elif self.experimentType == 'twoOdorMatch':
            if self.resultsRowsAppended:
                # If the rows were appended to the resultsTable for the first trial already, then do not use append again because it will continue to append new rows below the last.
                # Instead, I want to keep the rows from the first trial and just update the values for the totals for each flowrate. To do that, I must iterate through each row
                # inside each resultsTable. Since the table's rows will be iterated in the same order as they were read from the totalResultsList and appended, there only needs to
                # be one for loop for each resultsTable instead of two nested for loops. The number of rows will be equal to the total number of permutations for the two vials used in each trial.
                for table in self.h5file.walk_nodes(self.resultsGroup, "Table"):
                    tableNameSplit = table._v_name.split('_')  # will return ['olfa', '0'] as an example
                    olfa = int(tableNameSplit[1])  # convert to int to use as index.  
                    for row in table.iterrows():
                        firstVial = str(row['odorA_vial'])  # odorA_vial is an UInt8Col in the resultsTable, so need to convert back to string to use as a key.
                        secondVial = str(row['odorB_vial'])  # same goes for odorB_vial.
                        row['totalUsage'] = self.totalResultsList[olfa][firstVial][secondVial]['Total']
                        row['totalRight'] = self.totalResultsList[olfa][firstVial][secondVial]['right']
                        row['totalLeft'] = self.totalResultsList[olfa][firstVial][secondVial]['left']
                        row['totalCorrect'] = self.totalResultsList[olfa][firstVial][secondVial]['Correct']
                        row['totalWrong'] = self.totalResultsList[olfa][firstVial][secondVial]['Wrong']
                        row['totalNoResponse'] = self.totalResultsList[olfa][firstVial][secondVial]['NoResponse']
                        row.update()
                    table.flush()
            else:
                # This means the rows have not yet been appended to the results table after the first trial, so create the table now.
                if self.totalResultsList:  # Check that its not empty first.
                    self.resultsGroup = self.h5file.create_group(where='/', name='total_results', title='Total Response Results')
                    for i in range(len(self.totalResultsList)):  # self.totalResultsList is a list of dictionaries where each dictionary is a resultsCounterDict from the protocolWorker.
                        self.resultsTable = self.h5file.create_table(where='/total_results', name=f'olfa_{i}', description=TwoOdorResultsData, title=f'Olfa {i} Total Response Results')
                        self.resultsRow = self.resultsTable.row
                        for firstVial in self.totalResultsList[i].keys():
                            for secondVial in self.totalResultsList[i][firstVial].keys():
                                self.resultsRow['odorA_vial'] = firstVial  # firstVial is a string here, but will be converted to an UInt8Col in the resultsTable.
                                self.resultsRow['odorB_vial'] = secondVial  # secondVial is also a string here and will also be converted to UInt8Col.
                                self.resultsRow['totalUsage'] = self.totalResultsList[i][firstVial][secondVial]['Total']
                                self.resultsRow['totalRight'] = self.totalResultsList[i][firstVial][secondVial]['right']
                                self.resultsRow['totalLeft'] = self.totalResultsList[i][firstVial][secondVial]['left']
                                self.resultsRow['totalCorrect'] = self.totalResultsList[i][firstVial][secondVial]['Correct']
                                self.resultsRow['totalWrong'] = self.totalResultsList[i][firstVial][secondVial]['Wrong']
                                self.resultsRow['totalNoResponse'] = self.totalResultsList[i][firstVial][secondVial]['NoResponse']
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
   
    def saveEventsTimestamps(self):
        # Create the eventsTableDescDict (and then the eventsTable) every trial because it is not always the same every trial. Some events happen one trial but not in another.
        pos = 0
        eventCounters = []
        for event, eventList in self.infoDict['Events timestamps'].items():
            self.eventsTableDescDict[event] = tables.Float32Col(dflt=np.nan, pos=pos)
            eventCounters.append(len(eventList))  # Store the lengths of each eventList because will need to find the longest list below by finding the max.
            pos += 1  
        self.eventsTable = self.h5file.create_table(where='/event_times', name=f'trial_{self.trialNum}', description=self.eventsTableDescDict, title=f'Trial {self.trialNum} Event Timestamps')
        self.eventsRow = self.eventsTable.row
        
        # Use the length of the longest list to make an index to take one element from each eventList and add it to the row. If an IndexError happens because an eventList is shorter
        # than the longest eventList, then add np.nan to that row.
        for i in range(max(eventCounters)):
            for event, eventsList in self.infoDict['Events timestamps'].items():
                try:
                    self.eventsRow[event] = eventsList[i]
                except IndexError:
                    self.eventsRow[event] = np.nan
            self.eventsRow.append()
        self.eventsTable.flush()
    
    def saveTrialData(self):
        # If its None, that means the first trial's data just came, so make the description dict and then create the trialsTable using that description dict. This only happens once.
        if self.trialsTable is None:
            pos = 0
            self.trialsTableDescDict['trialNum'] = tables.UInt16Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['correctResponse'] = tables.StringCol(8, pos=pos)
            pos += 1
            self.trialsTableDescDict['responseResult'] = tables.StringCol(16, pos=pos)
            pos += 1
            self.trialsTableDescDict['itiDuration'] = tables.UInt8Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['bpodStartTime'] = tables.Float32Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['trialStartTime'] = tables.Float32Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['trialEndTime'] = tables.Float32Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['totalTrialTime'] = tables.Float32Col(pos=pos)
            pos += 1

            # Loop through the olfactometers used to save each one's parameters for each stimulus in their own column.
            stimIndex = 0
            for stimDict in self.infoDict['stimList']:
                for olfaName in stimDict['olfas'].keys():
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_vial'] = tables.UInt8Col(pos=pos)
                    pos += 1
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_name'] = tables.StringCol(32, pos=pos)  # Size of strings added to the column does not need to exactly match the size given during initialization.
                    pos += 1
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_conc'] = tables.Float32Col(pos=pos)
                    pos += 1
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_flow'] = tables.UInt8Col(pos=pos)  # This is assuming that only flowrates between 1 to 100 will be used.
                    pos += 1
                stimIndex += 1
            
            self.trialsTable = self.h5file.create_table(where='/', name='trial_data', description=self.trialsTableDescDict, title='Trial Data')
            self.trialRow = self.trialsTable.row

        # Fill in the column values for the row now that the trialsTable has been created.
        self.trialRow['trialNum'] = self.infoDict['currentTrialNum']
        self.trialRow['correctResponse'] = self.infoDict['correctResponse']
        self.trialRow['responseResult'] = self.infoDict['responseResult']
        self.trialRow['itiDuration'] = self.infoDict['currentITI']
        self.trialRow['bpodStartTime'] = self.infoDict['Bpod start timestamp']
        self.trialRow['trialStartTime'] = self.infoDict['Trial start timestamp']
        self.trialRow['trialEndTime'] = self.infoDict['Trial end timestamp']
        self.trialRow['totalTrialTime'] = self.trialRow['trialEndTime'] - self.trialRow['trialStartTime']
        stimIndex = 0
        for stimDict in self.infoDict['stimList']:  # Loop again to save the data to the columns.
            for olfaName, olfaValues in stimDict['olfas'].items():
                self.trialRow[f'odor{stimIndex}_{olfaName}_vial'] = int(olfaValues['vialNum'])
                self.trialRow[f'odor{stimIndex}_{olfaName}_name'] = olfaValues['odor']
                self.trialRow[f'odor{stimIndex}_{olfaName}_conc'] = olfaValues['vialconc']
                self.trialRow[f'odor{stimIndex}_{olfaName}_flow'] = olfaValues['mfc_1_flow']
            stimIndex += 1
        
        self.trialRow.append()
        self.trialsTable.flush()
    
    def run(self):
        # self.t_start = time.perf_counter()
        while self.keepRunning:
            if self.newData:
                self.newData = False  # reset
                logging.info("attempting to save data")

                self.saveTrialData()
                self.saveEventsTimestamps()
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
                        for i in range(len(voltages)):
                            self.voltsRow[f'voltageCh{i + 1}'] = voltages[i]
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

        logging.info("session data has been written to disk")
        self.h5file.close()
        logging.info("h5 file closed")
        self.finished.emit()
        
    def stopRunning(self):
        self.keepRunning = False
