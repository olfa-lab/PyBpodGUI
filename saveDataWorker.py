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


class SaveDataWorker(QObject):
    analogDataSignal = pyqtSignal(np.ndarray)
    analogDataSignalProcessed = pyqtSignal(np.ndarray)
    finished = pyqtSignal()

    def __init__(self,
            mouseNum, rigLetter, protocolFile, olfaConfigFile, shuffleMultiplier, itiMin, itiMax, leftWaterValveDuration, rightWaterValveDuration, analogInSettings, analogInModule=None, bpod=None
        ):
        super(SaveDataWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        dateTimeString = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        fileName = f"results/{dateTimeString}_M_{mouseNum}_Rig_{rigLetter}.h5"
        if not os.path.isdir('results'):
            os.mkdir('results')
        self.h5folder = os.getcwd() + '/results'
        
        self.h5file = tables.open_file(filename=fileName, mode='w', title=f"Mouse {mouseNum} Experiment Data")
        
        # File attributes for future reference.
        self.h5file.root._v_attrs.mouseNum = mouseNum
        self.h5file.root._v_attrs.rig = rigLetter
        self.h5file.root._v_attrs.date = dateTimeString
        self.h5file.root._v_attrs.protocolFile = protocolFile
        self.h5file.root._v_attrs.olfaConfigFile = olfaConfigFile
        self.h5file.root._v_attrs.shuffleMultiplier = shuffleMultiplier
        self.h5file.root._v_attrs.itiMax = itiMax
        self.h5file.root._v_attrs.itiMin = itiMin
        self.h5file.root._v_attrs.leftWaterValveDuration = leftWaterValveDuration
        self.h5file.root._v_attrs.rightWaterValveDuration = rightWaterValveDuration
        
        self.eventsGroup = self.h5file.create_group(where='/', name='event_times', title='Event Timestamps Per Trial')
        self.trialsTable = None  # Make it None for now because have to wait for completion of first trial to get the infoDict with data on the trial. Once that comes, make a description dictionary using the infoDict and then use that description dict to create the trialsTable.
        self.trialsTableDescDict = {}  # Description for the trialsTable (using this instead of making a class definition and subclassing tables.IsDescription).
        self.statesTable = None  # Make it None because have to wait for completion of first trial to get names of all the states. Afterwhich, make description dictionary and then table.
        self.statesTableDescDict = {}  # Description for the states table (using this instead of making a class definition and subclassing tables.IsDescription).
        self.eventsTable = None  # Same thing here, and also because I do not want to create the eventsTable if no input events even occurred.
        self.eventsTableDescDict = {}  # Description for the events table instead of making a class definition and subclassing tables.IsDescription.
        
        self.camera = None
        self.keepRunning = True
        self.newData = False
        self.trialNum = 1
        self.infoDict = {}        
        self.adc = analogInModule
        self.bpod = bpod

        if olfaConfigFile:
            with open(olfaConfigFile, 'r') as configFile:
                self.olfaConfigDict = json.load(configFile)
                self.nOlfas = len(self.olfaConfigDict['Olfactometers'])
            
            # Make the description dict for the vials table.
            self.vialsTableDescDict = {}
            pos = 0
            self.vialsTableDescDict["olfa"] = tables.UInt8Col(pos=pos)
            pos += 1
            self.vialsTableDescDict["vial"] = tables.UInt8Col(pos=pos)
            pos += 1
            self.vialsTableDescDict["odor"] = tables.StringCol(32, pos=pos)
            pos += 1
            self.vialsTableDescDict["conc"] = tables.Float32Col(pos=pos)

            # Make the vials table using the description dict above.
            self.vialsTable = self.h5file.create_table(where=self.h5file.root, name='vials', description=self.vialsTableDescDict, title='Vial Details')
            self.vialsRow = self.vialsTable.row

            # Write to the vials table.
            olfaIndex = 0
            for olfaDict in self.olfaConfigDict['Olfactometers']:
                for vialNum, vialInfo in olfaDict['Vials'].items():
                    if not (vialInfo['odor'] == 'dummy'):
                        self.vialsRow['olfa'] = olfaIndex
                        self.vialsRow['vial'] = int(vialNum)
                        self.vialsRow['odor'] = vialInfo['odor']
                        self.vialsRow['conc'] = vialInfo['conc']
                        self.vialsRow.append()
                olfaIndex += 1
            self.vialsTable.flush()

        if self.adc is not None:
            self.bpod = None  # Avoid using the bpod in case it was also given as a parameter.
            self.analogSettings = analogInSettings
            self.rangeLimits = {'-10V:10V': [-10.0, 10.0], '-5V:5V': [-5.0, 5.0], '-2.5V:2.5V': [-2.5, 2.5],'0V:10V': [0.0, 10.0]}
            self.maxVoltages = [self.rangeLimits[x][1] for x in self.analogSettings['inputRanges']]  # Make a list of integers for the max voltage of each channel's input range. analogSettings['inputRanges'] returns a list of strings that are used as keys in self.rangeLimits.
            self.minVoltages = [self.rangeLimits[x][0] for x in self.analogSettings['inputRanges']]  # Make a list of integers for the min voltage of each channel's input range.
            self.samplingPeriod = 1 / (self.analogSettings['samplingRate'])
            self.analogDataBufferSize = 5  # Size of buffer to send to the streamingWorker for plotting the analog data. Larger the buffer, the thicker the line gets and steps become more visible as buffers get sent before the previous buffer is completely plotted.
            self.analogDataBuffer = np.zeros(shape=self.analogDataBufferSize, dtype='float32')
            self.saveVoltages = False
            self.counter = 0
            self.previousTimer = 0
            self.t_start = 0
            self.bpodTime = 0
            self.voltsGroup = self.h5file.create_group(where='/', name='voltages', title='Voltages Per Trial')
            
            # Make the description dict for the setting table.
            self.voltsSettingsDescDict = {}
            pos = 0
            self.voltsSettingsDescDict['samplingRate'] = tables.UInt16Col(pos=pos)
            pos += 1
            self.voltsSettingsDescDict['inputRange'] = tables.StringCol(10, pos=pos)
            pos += 1
            self.voltsSettingsDescDict['thresholdVoltage'] = tables.Float32Col(pos=pos)
            pos += 1
            self.voltsSettingsDescDict['resetVoltage'] = tables.Float32Col(pos=pos)
            
            # Make the settings table using the description dict above.
            self.voltsSettingsTable = self.h5file.create_table(where='/voltages', name='settings', description=self.voltsSettingsDescDict, title='Analog Input Settings')
            self.voltsSettingsRow = self.voltsSettingsTable.row
            
            # Write to the settings table.
            for i in range(self.analogSettings['nActiveChannels']):  # Each active channel will have a row.
                self.voltsSettingsRow['samplingRate'] = self.analogSettings['samplingRate']  # sampling rate is global for all channels.
                self.voltsSettingsRow['inputRange'] = self.analogSettings['inputRanges'][i]
                self.voltsSettingsRow['thresholdVoltage'] = self.analogSettings['thresholdVoltages'][i]
                self.voltsSettingsRow['resetVoltage'] = self.analogSettings['resetVoltages'][i]
                self.voltsSettingsRow.append()
            self.voltsSettingsTable.flush()

            # Make the description dict for the volts table.
            self.voltsTableDescDict = {}  # Description dictionary for the volts table instead of making a class definition and subclassing tables.IsDescription.
            pos = 0
            # self.voltsTableDescDict['prefix'] = tables.UInt8Col(pos=pos)
            # pos += 1
            # self.voltsTableDescDict['syncByte'] = tables.UInt8Col(pos=pos)
            # pos += 1
            self.voltsTableDescDict['bpodTime'] = tables.Float32Col(pos=pos)
            pos += 1
            for i in range(self.analogSettings['nActiveChannels']):
                self.voltsTableDescDict[f'voltageCh{i}'] = tables.Float32Col(pos=pos)  # make a column for each channel used.
                pos += 1
            
            # Make the volts table using the description dict above.
            self.voltsTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum:03d}', description=self.voltsTableDescDict, title=f'Trial {self.trialNum} Voltage Data')
            self.voltsRow = self.voltsTable.row

        elif self.bpod is not None:
            self.channelIndices = self.bpod.hardware.analog_input_channels  # list of channel indices of channels configured for analog input.
            if (self.channelIndices is not None) and (len(self.channelIndices) > 0):
                # This means it is a list of at least one flex channel number that is configured for analog input.
                self.nChannels = len(self.channelIndices)
                self.thresholds_1 = self.bpod.hardware.analog_input_thresholds_1
                self.thresholds_2 = self.bpod.hardware.analog_input_thresholds_2
                self.polarities_1 = self.bpod.hardware.analog_input_threshold_polarity_1
                self.polarities_2 = self.bpod.hardware.analog_input_threshold_polarity_2
                self.maxVoltages = [5] * self.nChannels  # Make a list of integers for the max voltage of each channel's input range.
                self.minVoltages = [0] * self.nChannels  # Make a list of integers for the min voltage of each channel's input range.
                self.samplingPeriod = self.bpod.hardware.analog_input_sampling_interval * 0.0001  # Multiply by the state machines timer period of 100 microseconds.
                self.bpodTime = 0
                self.voltsGroup = self.h5file.create_group(where='/', name='voltages', title='Voltages Per Trial')
                
                # Make the description dict for the setting table.
                self.voltsSettingsDescDict = {}
                pos = 0
                self.voltsSettingsDescDict['samplingRate'] = tables.UInt16Col(pos=pos)
                pos += 1
                self.voltsSettingsDescDict['inputRange'] = tables.StringCol(10, pos=pos)
                pos += 1
                self.voltsSettingsDescDict['thresholdVoltage_1'] = tables.Float32Col(pos=pos)
                pos += 1
                self.voltsSettingsDescDict['thresholdVoltage_2'] = tables.Float32Col(pos=pos)
                pos += 1
                self.voltsSettingsDescDict['thresholdPolarity_1'] = tables.UInt8Col(pos=pos)
                pos += 1
                self.voltsSettingsDescDict['thresholdPolarity_2'] = tables.UInt8Col(pos=pos)
                
                # Make the settings table using the description dict above.
                self.voltsSettingsTable = self.h5file.create_table(where='/voltages', name='settings', description=self.voltsSettingsDescDict, title='Analog Input Settings')
                self.voltsSettingsRow = self.voltsSettingsTable.row
                
                # Write to the settings table.
                for i in range(self.nChannels):  # Each analog input channel will have a row.
                    self.voltsSettingsRow['samplingRate'] = 1 / self.samplingPeriod  # sampling rate is global for all channels.
                    self.voltsSettingsRow['inputRange'] = "0V:5V"  # global for all flex channels.
                    self.voltsSettingsRow['thresholdVoltage_1'] = (self.thresholds_1[self.channelIndices[i]] / 4095) * self.maxVoltages[i]  # Convert to voltage
                    self.voltsSettingsRow['thresholdVoltage_2'] = (self.thresholds_2[self.channelIndices[i]] / 4095) * self.minVoltages[i]  # Convert to voltage
                    self.voltsSettingsRow['thresholdPolarity_1'] = self.polarities_1[self.channelIndices[i]]
                    self.voltsSettingsRow['thresholdPolarity_2'] = self.polarities_2[self.channelIndices[i]]
                    self.voltsSettingsRow.append()
                self.voltsSettingsTable.flush()

                # Make the description dict for the volts table.
                self.voltsTableDescDict = {}  # Description dictionary for the volts table instead of making a class definition and subclassing tables.IsDescription.
                pos = 0
                self.voltsTableDescDict['trialNum'] = tables.UInt8Col(pos=pos)
                pos += 1
                self.voltsTableDescDict['bpodTime'] = tables.Float32Col(pos=pos)
                pos += 1
                for i in range(self.nChannels):
                    self.voltsTableDescDict[f'voltageCh{self.channelIndices[i]}'] = tables.Float32Col(pos=pos)  # make a column for each channel used.
                    pos += 1
                
                # Make the volts table using the description dict above.
                self.voltsTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum:03d}', description=self.voltsTableDescDict, title=f'Trial {self.trialNum} Voltage Data')
                self.voltsRow = self.voltsTable.row
            
            else:
                self.bpod = None  # Make it None to indicate to other functions below that there is no analog input.

    def receiveInfoDict(self, infoDict):
        self.newData = True
        self.infoDict = infoDict

    def saveStatesTimestamps(self):
        # Define the description for the states table using a dictionary of the states timestamps. Then create the states table (only once).
        if self.statesTable is None:
            pos = 0
            for k, v in self.infoDict['States timestamps'].items():
                keyString = k + '_start'
                self.statesTableDescDict[keyString] = tables.Float32Col(pos=pos)
                pos += 1
                keyString = k + '_end'
                self.statesTableDescDict[keyString] = tables.Float32Col(pos=pos)
                pos += 1
            
            self.statesTable = self.h5file.create_table(where='/', name='state_times', description=self.statesTableDescDict, title='States Timestamps')
            self.statesRow = self.statesTable.row

        # Fill in column values for the states timestamps for the current row since statesTable has now been created.
        for k, v in self.infoDict['States timestamps'].items():
            keyString = k + '_start'
            self.statesRow[keyString] = v[0][0]
            keyString = k + '_end'
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
        self.eventsTable = self.h5file.create_table(where='/event_times', name=f'trial_{self.trialNum:03d}', description=self.eventsTableDescDict, title=f'Trial {self.trialNum} Event Timestamps')
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
            # self.trialsTableDescDict['trialNum'] = tables.UInt16Col(pos=pos)
            # pos += 1
            # self.trialsTableDescDict['correctResponse'] = tables.StringCol(8, pos=pos)
            # pos += 1
            self.trialsTableDescDict['responseResult'] = tables.StringCol(7, pos=pos)
            pos += 1
            # self.trialsTableDescDict['itiDuration'] = tables.UInt8Col(pos=pos)
            # pos += 1
            # self.trialsTableDescDict['bpodStartTime'] = tables.Float32Col(pos=pos)
            # pos += 1
            self.trialsTableDescDict['trialStartTime'] = tables.Float32Col(pos=pos)
            pos += 1
            self.trialsTableDescDict['trialEndTime'] = tables.Float32Col(pos=pos)
            pos += 1
            # self.trialsTableDescDict['totalTrialTime'] = tables.Float32Col(pos=pos)
            # pos += 1

            # Loop through the olfactometers used to save each one's parameters for each stimulus in their own column.
            stimIndex = 0
            for stimDict in self.infoDict['stimList']:
                for olfaName in stimDict['olfas'].keys():
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_vial'] = tables.UInt8Col(pos=pos)
                    pos += 1
                    # self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_name'] = tables.StringCol(32, pos=pos)  # Size of strings added to the column does not need to exactly match the size given during initialization.
                    # pos += 1
                    # self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_conc'] = tables.Float32Col(pos=pos)
                    # pos += 1
                    self.trialsTableDescDict[f'odor{stimIndex}_{olfaName}_flow'] = tables.UInt8Col(pos=pos)  # This is assuming that only flowrates between 1 to 100 will be used.
                    pos += 1
                for dilName in stimDict['dilutors'].keys():
                    self.trialsTableDescDict[f'odor{stimIndex}_{dilName}_flow'] = tables.UInt8Col(pos=pos)  # This is assuming that only flowrates between 1 to 100 will be used.
                    pos += 1
                    print('How are the dilutorscalled?')
                stimIndex += 1
                
            
            self.trialsTable = self.h5file.create_table(where='/', name='trial_data', description=self.trialsTableDescDict, title='Trial Data')
            self.trialRow = self.trialsTable.row
            self.h5file.root._v_attrs.bpodStartTime = self.infoDict['Bpod start timestamp']  # Save the bpod start time as an attribute instead of in the table because it remains the same for every trial. So save it when the first trial's data comes.

        # Fill in the column values for the row now that the trialsTable has been created.
        # self.trialRow['trialNum'] = self.infoDict['currentTrialNum']
        # self.trialRow['correctResponse'] = self.infoDict['correctResponse']
        self.trialRow['responseResult'] = self.infoDict['responseResult']
        # self.trialRow['itiDuration'] = self.infoDict['currentITI']
        # self.trialRow['bpodStartTime'] = self.infoDict['Bpod start timestamp']
        self.trialRow['trialStartTime'] = self.infoDict['Trial start timestamp']
        self.trialRow['trialEndTime'] = self.infoDict['Trial end timestamp']
        # self.trialRow['totalTrialTime'] = self.trialRow['trialEndTime'] - self.trialRow['trialStartTime']
        stimIndex = 0
        for stimDict in self.infoDict['stimList']:  # Loop again to save the data to the columns.
            for olfaName, olfaValues in stimDict['olfas'].items():
                self.trialRow[f'odor{stimIndex}_{olfaName}_vial'] = int(olfaValues['vialNum'])
                # self.trialRow[f'odor{stimIndex}_{olfaName}_name'] = olfaValues['odor']
                # self.trialRow[f'odor{stimIndex}_{olfaName}_conc'] = olfaValues['vialconc']
                self.trialRow[f'odor{stimIndex}_{olfaName}_flow'] = olfaValues['mfc_1_flow']
            for dilName, dilValues in stimDict['dilutors'].items():
                self.trialRow[f'odor{stimIndex}_{dilName}_flow'] = int(dilValues['vac_flow'])
            stimIndex += 1
        
        self.trialRow.append()
        self.trialsTable.flush()
    
    def saveAnalogDataFromModule(self):
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

            if (prefix == 35):  # 35 is the decimal value for the ascii char '#' which is the prefix for when the syncByte is received. Otherwise the prefix is 'R' and the syncByte will be zero.
                if (syncByte == 1):
                    self.saveVoltages = True  # Start saving to h5 file when syncByte value of 1 is received.
                elif (syncByte == 2):
                    self.saveVoltages = False  # Stop saving to h5 file when syncByte value of 2 is received.

            # convert decimal bit value to voltage. The length of samples indicates how many channels are streaming to USB.
            for i in range(len(samples)):
                if (self.minVoltages[i] == 0):  # This is when input voltage range is 0V to 10V.
                    voltages[i] = ((samples[i] * self.maxVoltages[i]) / 8192)
                else:
                    if samples[i] >= 4096:
                        samples[i] -= 4096
                        voltages[i] = (samples[i] * self.maxVoltages[i]) / 4096
                    elif samples[i] < 4096:
                        voltages[i] = ((samples[i] * self.maxVoltages[i]) / 4096) - self.maxVoltages[i]
            
            if self.saveVoltages:
                # self.voltsRow['computerTime'] = elapsed
                # self.voltsRow['computerPeriod'] = period
                # self.voltsRow['prefix'] = prefix
                # self.voltsRow['syncByte'] = syncByte
                self.voltsRow['bpodTime'] = self.bpodTime
                self.bpodTime += self.samplingPeriod
                for i in range(len(voltages)):
                    self.voltsRow[f'voltageCh{i}'] = voltages[i]
                self.voltsRow.append()

            # fill buffer and send it when full using the signal.
            if self.counter < self.analogDataBufferSize:    
                self.analogDataBuffer[self.counter] = voltages[0]  # Need to use element, not list
                self.counter += 1
            else:
                # self.voltsTable.flush()  # Write to the file whenever the buffer gets full instead of waiting for the end of trial dict to come from the protocolWorker thread.
                
                self.analogDataSignal.emit(self.analogDataBuffer)
                self.counter = 0
                self.analogDataBuffer[self.counter] = voltages[0]
                self.counter += 1
    
    def saveAnalogDataFromBpod(self, analogData):#modified by Bea in introducing ReadDataThread
        #analogData = self.bpod.read_analog_input()
        
        if len(analogData) > 0:
            # convert decimal bit value to voltage. The length of samples indicates how many channels are streaming to USB.
            nSamples = int(len(analogData) / (self.nChannels + 1))  # Add one to account for the trial number that is included with every sample.
            voltages = [[]] * self.nChannels  # make a sublist for each channel
            ind = 0
            for s in range(nSamples):
                trialNum = analogData[ind]
                ind += 1
                if trialNum == self.trialNum:  # Note that self.trialNum starts at 1 and is incremented each time a new info dict is received.
                    self.voltsRow['trialNum'] = trialNum
                    self.voltsRow['bpodTime'] = self.bpodTime
                    self.bpodTime += self.samplingPeriod
                    for i in range(self.nChannels):
                        samp = (analogData[ind] / 4095) * self.maxVoltages[i]
                        ind += 1
                        voltages[i].append(samp)
                        self.voltsRow[f'voltageCh{self.channelIndices[i]}'] = voltages[i][-1]  # The most recently appended value is the current ind.
                    self.voltsRow.append()
                else:
                    # Skip over this sample. Instead of breaking out of the for loop, run the for loop below to increment ind, just in case analogData
                    # is more than one sample, in which case the next sample could be the correct trialNum.
                    for i in range(self.nChannels):
                        ind += 1

            self.analogDataSignalProcessed.emit(np.array(voltages[0], dtype='float32'))  # StreamingWorker is currently only capable of plotting one channel.
    
    def run(self):
        # self.t_start = time.perf_counter()
        while self.keepRunning:
            if self.newData:
                self.newData = False  # reset

                if not (self.infoDict == {}):
                    self.saveTrialData()
                    self.saveEventsTimestamps()
                    self.saveStatesTimestamps()
                    self.trialNum += 1  # increment trial number.

                    if (self.adc is not None) or (self.bpod is not None):
                        # The trial data above comes at the end of a trial, so write the voltages to the disk, and create a new table for the next trial's voltages
                        self.voltsTable.flush()
                        self.saveVoltages = False  # reset for the next trial.
                        self.bpodTime = 0  # reset timestamps for samples back to zero.
                        
                        # Re-iterate through the volts table row by row to update the bpodTime so it corresponds to the bpod's trial start time instead of starting it at zero.
                        # self.bpodTime = self.infoDict['Trial start timestamp']
                        # for voltsRow in self.voltsTable.iterrows():
                        #     voltsRow['bpodTime'] = self.bpodTime
                        #     self.bpodTime += self.samplingPeriod
                        #     voltsRow.update()
                        # self.voltsTable.flush()

                        self.voltsTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum:03d}', description=self.voltsTableDescDict, title=f'Trial {self.trialNum} Voltage Data')
                        self.voltsRow = self.voltsTable.row
                else:
                    # Empty dict means to discard the trial and repeat it.
                    if (self.adc is not None) or (self.bpod is not None):
                        self.saveVoltages = False
                        self.bpodTime = 0
                        self.voltsTable.remove()  # Delete the current table and create and new empty below.
                        self.voltsTable = self.h5file.create_table(where='/voltages', name=f'trial_{self.trialNum:03d}', description=self.voltsTableDescDict, title=f'Trial {self.trialNum} Voltage Data')
                        self.voltsRow = self.voltsTable.row

            
            #elif self.adc is not None:
            #    self.saveAnalogDataFromModule()
            #
            #elif self.bpod is not None:
            #    self.saveAnalogDataFromBpod()

            else:
                QThread.sleep(1)  # Need this or else entire application will become severely unresponsive.

        if (self.adc is not None) or (self.bpod is not None):
            self.voltsTable.flush()

        self.h5file.close()
        logging.info("h5 file closed")
        logging.info("SaveDataWorker Finished")
        self.finished.emit()
    
    
    def migrateSessionData(self):

    
        # get all camera tifs and h5
       
        folder = self.camera.camera_data_dir
        list_of_tifs = []
        while not bool(list_of_tifs):
            list_of_tifs = glob.glob(folder +'\\*\\*.tif')

        if bool(list_of_tifs):
            for tif in list_of_tifs:
                copy2(tif, self.destination)

        # copy h5 from experiment
        h5folder = self.h5folder
        list_of_h5s = []
        while not bool(list_of_h5s):
            list_of_h5s = glob.glob(folder +'\\*.h5')

        latest_h5 = max(list_of_h5s, key=os.path.getctime)
        copy2(latest_h5, self.destination)
        pass   

    def stopRunning(self):
        self.keepRunning = False
        if self.camera is not None: 
            self.migrateSessionData()
