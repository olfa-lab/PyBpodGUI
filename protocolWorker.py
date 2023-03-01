import logging
import json
import numpy as np
from serial.serialutil import SerialException
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QEventLoop
from pybpodapi.protocol import StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
import os

import olfactometry
from olfactometry.utils import OlfaException
from time import sleep
from datetime import datetime
logging.basicConfig(format="%(message)s", level=logging.INFO)


class ProtocolWorker(QObject):
    newTrialInfoSignal = pyqtSignal(dict)  # sends current trial info with it to update GUI.
    newStateSignal = pyqtSignal(str)  # sends current state with it to update GUI.
    stateNumSignal = pyqtSignal(int)  
    responseResultSignal = pyqtSignal(str)  # sends the response result of the current trial with it to update the GUI.
    totalsDictSignal = pyqtSignal(dict)  # sends the session totals with it to update the GUI.
    resultsCounterListSignal = pyqtSignal(list) # sends the results for each flow rate with it to update the GUI's results plot.
    saveVideoSignal = pyqtSignal(int)
    saveTrialDataDictSignal = pyqtSignal(dict)  # 'dict' is interpreted as 'QVariantMap' by PyQt5 and thus can only have strings as keys. Use 'object' instead if you want to use non-strings as keys. 
    saveTotalResultsSignal = pyqtSignal(dict)
    noResponseAbortSignal = pyqtSignal()
    olfaNotConnectedSignal = pyqtSignal()
    olfaExceptionSignal = pyqtSignal(str)  # sends the olfa exception error string with it to the main thread to notify the user.
    invalidFileSignal = pyqtSignal(str)  # sends the key string that caused the KeyError with it to the main thread to notify the user.
    bpodExceptionSignal = pyqtSignal(str)  # sends the bpod exception error string with it to the main thread to notify the user.
    duplicateVialsSignal = pyqtSignal(dict)  # sends a dict that groups duplicate vials to the resultsPLotWorker.
    # startSDCardLoggingSignal = pyqtSignal()
    # stopSDCardLoggingSignal = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self,
            bpodObject, protocolFileName, olfaConfigFileName, experimentType, camera, shuffleMultiplier, leftSensorPort, leftWaterValvePort, leftWaterValveDuration,
            rightSensorPort, rightWaterValvePort, rightWaterValveDuration, finalValvePort, itiMin, itiMax, noResponseCutoff, autoWaterCutoff, olfaChecked=True, numTrials=1
        ):
        super(ProtocolWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.bpod = bpodObject
        self.olfaChecked = olfaChecked
        self.olfas = None
        self.protocolFileName = protocolFileName
        self.olfaConfigFileName = olfaConfigFileName
        self.experimentType = experimentType
        self.camera = camera
        self.shuffleMultiplier = shuffleMultiplier
        self.correctResponse = ''
        self.currentTrialNum = 1
        self.totalCorrect = 0
        self.totalWrong = 0
        self.totalNoResponses = 0
        self.consecutiveNoResponses = 0
        self.noResponseCutOff = noResponseCutoff if (noResponseCutoff > 0) else (numTrials + 1)  # Zero means to never abort, so set it equal to 1 more than the number of trials to guarantee that it will never abort automatically.
        self.autoWaterCutoff = autoWaterCutoff if (autoWaterCutoff > 0) else (numTrials + 1)  # Zero means to never autoWater, so set it equal to 1 more than the number of trials to guarantee that it will never give water automatically.
        self.currentITI = None
        self.itiMin = itiMin
        self.itiMax = itiMax
        self.nTrials = numTrials
        self.leftSensorPort = leftSensorPort
        self.leftWaterValvePort = leftWaterValvePort
        self.leftWaterDuration = leftWaterValveDuration / 1000  # convert to seconds
        self.rightSensorPort = rightSensorPort
        self.rightWaterValvePort = rightWaterValvePort
        self.rightWaterDuration = rightWaterValveDuration / 1000  # convert to seconds
        self.finalValvePort = finalValvePort
        self.keepRunning = True
        self.saveTrial = True
        self.currentStateName = ''
        self.currentResponseResult = ''
        self.previousResponseResult = ''
        self.vials = []
        self.odors = []
        self.concs = []
        self.flows = []
        self.resultsCounterList = []
        self.vialIndex = 0
        self.flowIndex = 0
        self.stimIndex = 0
        self.stimList = []
        self.nOlfas = 0
        self.shuffleVials = []
        self.shuffleFlows = []
        self.correctResponsesList = ['left', 'right'] * int(self.nTrials / 2)  # Make a list of all the correct responses to be used for the entire experiment (i.e. for self.nTrials). The experiment will contain 50% left trials and 50% right trials.
        np.random.shuffle(self.correctResponsesList)  # Shuffle the correnct responses and then use self.currentTrialNum as an index to iterate through it. Currently only the identityGenerator function uses the self.correctResponsesList.

    def setLeftSensorPort(self, value):
        self.leftSensorPort = value

    def setLeftWaterValvePort(self, value):
        self.leftWaterValvePort = value

    def setLeftWaterDuration(self, duration):
        self.leftWaterDuration = duration / 1000  # Convert to seconds.

    def setRightSensorPort(self, value):
        self.rightSensorPort = value

    def setRightWaterValvePort(self, value):
        self.rightWaterValvePort = value
    
    def setRightWaterDuration(self, duration):
        self.rightWaterDuration = duration / 1000  # Convert to seconds.

    def setNumTrials(self, value):
        #print(value)
        self.nTrials = value
    
    def setMinITI(self, value):
        self.itiMin = value

    def setMaxITI(self, value):
        self.itiMax = value

    def setNoResponseCutoff(self, value):
        self.noResponseCutOff = value if (value > 0) else (self.nTrials + 1)  # Zero means to never abort, so set it equal to 1 more than the number of trials to guarantee that it will never abort automatically.

    def setAutoWaterCutoff(self, value):
        self.autoWaterCutoff = value if (value > 0) else (self.nTrials + 1)  # Zero means to never autoWater, so set it equal to 1 more than the number of trials to guarantee that it will never give water automatically.
    
    def getCorrectResponse(self):
        return self.correctResponse

    def getCurrentTrialNum(self):
        return self.currentTrialNum

    def getCurrentTrialInfoDict(self):
        trialDict = {
            'currentTrialNum': self.currentTrialNum,
            'nTrials': self.nTrials,
            'correctResponse': self.correctResponse,
            'currentITI': self.currentITI,
            'stimList': self.stimList,
            'nStates': self.sma.total_states_added
        }
        return trialDict

    def getEndOfTrialInfoDict(self):
        if (self.currentStateName == 'exit'):
            dict1 = self.getCurrentTrialInfoDict()
            dict2 = self.bpod.session.current_trial.export()
            dict3 = {**dict1, **dict2}  # Merge both dictionaries
            dict3.update({'responseResult': self.currentResponseResult})
            return dict3
        return {}

    def calculateTotalPercentCorrect(self):
        percent = round(((float(self.totalCorrect) / float(self.currentTrialNum)) * 100), 2)  # I used 'self.currentTrialNum' instead of 'self.nTrials' to ensure the percentage only counts the number of completed trials incase the experiment is aborted early.
        return percent

    def getTotalsDict(self):
        totals = {
            'totalCorrect': self.totalCorrect,
            'totalWrong': self.totalWrong,
            'totalNoResponses': self.totalNoResponses,
            'totalPercentCorrect': self.calculateTotalPercentCorrect()
        }
        return totals

    def my_softcode_handler(self, softcode):
        # I will reserve softcode 1 to be an automatic output from every state (that does not already have a softcode) so that the
        # my_softcode_handler function gets called at every state to update the GUI info and emit the necessary signals. If user selects
        # a different softcode other than 1, the instructions below will still be executed. However, I'm still not sure how to implement
        # a way to allow a user to configure softcode actions.
        if softcode == 1:
            pass

        elif softcode == 2:
            try:
                # I manually call the _poll_mfcs() function here because the olfactometer.py uses a QTimer for which its timeout slot connects to
                # _poll_mfcs() at an interval set by mfc_polling_interval, but QTimers do not connect to their timeout slots while the state machine
                # is running because run_state_machine is a blocking function. QTimers do not even work here when called inside the my_softcode_handler
                # function. They only connect to their timeout slots after the run_state_machine function completes. So to prevent olfactometer.py
                # from raising the OlfaException("MFC polling is not OK") when set_stimulus is called a second time for the second odor or for the
                # second trial, I manually call the slot that the QTimer is supposed to connect to, which is _poll_mfcs(). I do this before calling
                # set_stimulus() because inside set_stimulus(), there is a call to check_flows(), which checks the elapsed time since the last time
                # the mfc were polled. By polling the mfcs right before calling set_stimulus(), the elapsed time will never be long enough to raise
                # the OlfaException.
                for i in range(self.nOlfas):
                    self.olfas.olfas[i]._poll_mfcs()
                self.olfas.set_stimulus(self.stimList[self.stimIndex])
                self.stimIndex += 1

            except OlfaException as olf:
                self.olfaExceptionSignal.emit(str(olf))
                self.stopRunning()
                # self.finished.emit()
                return  # Exit the function to avoid continuing with the code below.

        elif softcode == 3:
            self.olfas.set_dummy_vials()
            # I manually call the _valve_lockout_clear() function here because the olfactometer.py uses a QTimer.singleShot to call it 1 second
            # after set_dummy_vial, but QTimers do not connect to their timeout slots while the state machine is running because run_state_machine
            # is a blocking function. QTimers do not even work when called here inside the my_softcode_handler function. They only connect to their
            # timeout slots after the run_state_machine function completes. So I manually call _valve_lockout_clear() so that set_stimulus() can be
            # called a second time for the second odor. Otherwise, the olfactometer will present an error "Cannot open vial. Must wait 1 second
            # after last valve closed to prevent cross=contamination." I assume that 1 second will elapse between the state that called
            # set_dummy_vials() and the state that will call set_stimulus() again for the second odor.
            for i in range(self.nOlfas):
                self.olfas.olfas[i]._valve_lockout_clear()

        # Update trial info for GUI
        self.currentStateName = self.sma.state_names[self.sma.current_state]
        self.newStateSignal.emit(self.currentStateName)
        self.stateNumSignal.emit(self.sma.current_state)
        
        if self.currentStateName == 'Correct':
            self.currentResponseResult = 'Correct'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            if (self.experimentType == 1 or self.experimentType == 3):
                for i in range(self.nOlfas):
                    vialNum = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    flow = self.stimList[0]['olfas'][f'olfa_{i}']['mfc_1_flow']
                    self.resultsCounterList[i][vialNum][str(flow)][self.correctResponse] += 1
                    self.resultsCounterList[i][vialNum][str(flow)]['Correct'] += 1
                    self.resultsCounterList[i][vialNum][str(flow)]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            elif (self.experimentType == 2):
                for i in range(self.nOlfas):
                    firstVial = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    secondVial = self.stimList[1]['olfas'][f'olfa_{i}']['vialNum']
                    self.resultsCounterList[i][firstVial][secondVial][self.correctResponse] += 1
                    self.resultsCounterList[i][firstVial][secondVial]['Correct'] += 1
                    self.resultsCounterList[i][firstVial][secondVial]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            self.totalCorrect += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif self.currentStateName == 'Wrong':
            self.currentResponseResult = 'Wrong'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            if (self.experimentType == 1 or self.experimentType == 3):
                for i in range(self.nOlfas):
                    vialNum = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    flow = self.stimList[0]['olfas'][f'olfa_{i}']['mfc_1_flow']
                    if self.correctResponse == 'left':
                        self.resultsCounterList[i][vialNum][str(flow)]['right'] += 1  # increment the opposite direction because the response was wrong.
                    elif self.correctResponse == 'right':
                        self.resultsCounterList[i][vialNum][str(flow)]['left'] += 1  # increment the opposite direction because the response was wrong.
                    self.resultsCounterList[i][vialNum][str(flow)]['Wrong'] += 1
                    self.resultsCounterList[i][vialNum][str(flow)]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            elif (self.experimentType == 2):
                for i in range(self.nOlfas):
                    firstVial = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    secondVial = self.stimList[1]['olfas'][f'olfa_{i}']['vialNum']
                    if self.correctResponse == 'left':
                        self.resultsCounterList[i][firstVial][secondVial]['right'] += 1  # increment the opposite direction because the response was wrong.
                    elif self.correctResponse == 'right':
                        self.resultsCounterList[i][firstVial][secondVial]['left'] += 1  # increment the opposite direction because the response was wrong.
                    self.resultsCounterList[i][firstVial][secondVial]['Wrong'] += 1
                    self.resultsCounterList[i][firstVial][secondVial]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            self.totalWrong += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif self.currentStateName == 'NoResponse':
            self.currentResponseResult = 'None'
            self.responseResultSignal.emit(self.currentResponseResult)

            if self.previousResponseResult == self.currentResponseResult:
                self.consecutiveNoResponses += 1
            else:
                self.previousResponseResult = self.currentResponseResult
                self.consecutiveNoResponses = 1  # Reset counter to 1 because it should start counting now.

            if (self.experimentType == 1):
                for i in range(self.nOlfas):
                    vialNum = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    flow = self.stimList[0]['olfas'][f'olfa_{i}']['mfc_1_flow']
                    self.resultsCounterList[i][vialNum][str(flow)]['NoResponse'] += 1
                    self.resultsCounterList[i][vialNum][str(flow)]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)

            elif (self.experimentType == 2):
                for i in range(self.nOlfas):
                    firstVial = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    secondVial = self.stimList[1]['olfas'][f'olfa_{i}']['vialNum']
                    self.resultsCounterList[i][firstVial][secondVial]['NoResponse'] += 1
                    self.resultsCounterList[i][firstVial][secondVial]['Total'] += 1
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            self.totalNoResponses += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)
        
        elif self.currentStateName == 'NoSniff':
            self.currentResponseResult = 'None'
            self.responseResultSignal.emit(self.currentResponseResult)

            if (self.experimentType == 1 or self.experimentType == 3):
                for i in range(self.nOlfas):
                    vialNum = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    flow = self.stimList[0]['olfas'][f'olfa_{i}']['mfc_1_flow']
                    self.resultsCounterList[i][vialNum][str(flow)]['Total'] += 1  # Only increment the total since this is technically not a valid trial if there was no sniff.
                    self.resultsCounterListSignal.emit(self.resultsCounterList)
            
            elif (self.experimentType == 2):
                for i in range(self.nOlfas):
                    firstVial = self.stimList[0]['olfas'][f'olfa_{i}']['vialNum']
                    secondVial = self.stimList[1]['olfas'][f'olfa_{i}']['vialNum']
                    self.resultsCounterList[i][firstVial][secondVial]['Total'] += 1  # Only increment the total since this is technically not a valid trial if there was no sniff.
                    self.resultsCounterListSignal.emit(self.resultsCounterList)

    def groupDuplicateVials(self, odors, concs, vials):
        # This will only group duplicates within a single olfactometer, not across other olfactometers.
        duplicateVials = {}
        for x in range(self.nOlfas):  # odors is a list of n lists where n is equal to nOlfas. odors, concs, and vials all have the same length.
            currentOdor = ''
            currentConc = 0
            for i in range(len(odors[x])):
                currentOdor = odors[x][i].split('_')[0]  # If two odors in the olfa config file are the same and have the same concentration, then I put underscore and the vial number at the end of the odor name's string (e.g. 'limonene_5') to bypass the olfactometer code raising an error when two or more vials match.
                currentConc = concs[x][i]
                for j in range(len(odors[x])):
                    if (currentOdor == odors[x][j].split('_')[0]) and (currentConc == concs[x][j]):  # if the odor names are the same and the concentrations are the same, then the two vials are duplicates.
                        if currentOdor not in duplicateVials:
                            duplicateVials[currentOdor] = {str(currentConc): [vials[x][j]]}
                        elif str(currentConc) not in duplicateVials[currentOdor]:  # This means currentOdor must already be in duplicateVials, but there is another conc of that odor in the olfa config file for which another vial was found to match.
                            duplicateVials[currentOdor][str(currentConc)] = [vials[x][j]]  # When first creating the key, put the indices for i and j in the list because they are the first match found.
                        elif vials[x][j] not in duplicateVials[currentOdor][str(currentConc)]:  # Check if vial was already added to avoid appending again when looping over an odor name that was already used.
                            duplicateVials[currentOdor][str(currentConc)].append(vials[x][j])  # Then append vials[j] whenever another match is found.
        
        self.duplicateVialsSignal.emit(duplicateVials)
    
    def getOdorsFromConfigFile(self):
        with open(self.olfaConfigFileName, 'r') as configFile:
            self.olfaConfigDict = json.load(configFile)
            self.nOlfas = len(self.olfaConfigDict['Olfactometers'])
            self.mfc_0_capacity = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['capacity']  # will be used to set 'mfc_0_flow' in every stim dict because the olfactometers have been reconfigured such that the bigger mfc will always push out 1000 sccm.

        if (self.experimentType == 1 or self.experimentType == 3):
            self.stimulusFunction = self.intensityGenerator

            olfaIndex = 0
            for olfaDict in self.olfaConfigDict['Olfactometers']:  # self.olfacConfigDict['Olfactometers'] is a list of dictionaries.
                odors = []
                concs = []
                vials = []
                vialFlows = {}
                shuffleFlows = {}
                resultsCounterDict = {}
                for vialNum, vialInfo in olfaDict['Vials'].items():
                    if not (vialInfo['odor'] == 'dummy'):
                        odors.append(vialInfo['odor'])
                        concs.append(vialInfo['conc'])
                        vials.append(vialNum)
                        vialFlows[vialNum] = vialInfo['flows']  # vialInfo['flows'] is a list.
                        if (self.shuffleMultiplier > 0):
                            shuffleFlowsList = vialInfo['flows'] * self.shuffleMultiplier  # Extend the contents of the flowrates list by multiplying by the int vale of self.shuffleMultiplier. This longer list will increase the "randomness" of the shuffle.
                            np.random.shuffle(shuffleFlowsList)
                            shuffleFlows[vialNum] = shuffleFlowsList
                        resultsCounterDict[vialNum] = {}
                        for flow in vialInfo['flows']:
                            resultsCounterDict[vialNum][str(flow)] = {
                                'right': 0,  # initizialize counters to zero.
                                'left': 0,
                                'Correct': 0,
                                'Wrong': 0,
                                'NoResponse': 0,
                                'Total': 0
                            }
                self.odors.append(odors)
                self.concs.append(concs)
                self.vials.append(vials)
                self.flows.append(vialFlows)  # self.flows is a list of dictionaries. Each dictionary has an olfactometer's vial numbers for keys and each key's value is a list of flowrates for that vial.
                self.resultsCounterList.append(resultsCounterDict)
                if (self.shuffleMultiplier > 0):
                    shuffleVials = vials * self.shuffleMultiplier  # Extend the contents of the vials list by multiplying by the int value of self.shuffleMultiplier. This longer list will increase the "randomness" of the shuffle.
                    np.random.shuffle(shuffleVials)  # shuffle in-place
                    self.shuffleVials.append(shuffleVials)
                    self.shuffleFlows.append(shuffleFlows)
                olfaIndex += 1

            self.groupDuplicateVials(self.odors, self.concs, self.vials)

        elif (self.experimentType == 2):
            self.stimulusFunction = self.identityGenerator

            olfaIndex = 0
            for olfaDict in self.olfaConfigDict['Olfactometers']:  # self.olfacConfigDict['Olfactometers'] is a list of dictionaries.                
                odors = []
                concs = []
                vials = []
                vialFlows = {}
                shuffleFlows = {}
                resultsCounterDict = {}
                for vialNum, vialInfo in olfaDict['Vials'].items():
                    if not (vialInfo['odor'] == 'dummy'):
                        odors.append(vialInfo['odor'])
                        concs.append(vialInfo['conc'])
                        vials.append(vialNum)
                        vialFlows[vialNum] = vialInfo['flows']  # vialInfo['flows'] is a list.
                        if (self.shuffleMultiplier > 0):
                            shuffleFlowsList = vialInfo['flows'] * self.shuffleMultiplier  # Extend the contents of the flowrates list by multiplying by the int vale of self.shuffleMultiplier. This longer list will increase the "randomness" of the shuffle.
                            np.random.shuffle(shuffleFlowsList)  # shuffle in-place
                            shuffleFlows[vialNum] = shuffleFlowsList
                        resultsCounterDict[vialNum] = {}

                # Once we have all the vials as keys for the first odor, loop over a second time to fill the second dimension sub dictionary with keys for the second odor, for which each key's value will be a sub dict with the total results for that vial pair.       
                for vialNum1 in resultsCounterDict.keys():
                    for vialNum2 in vials:
                        resultsCounterDict[vialNum1][vialNum2] = {
                            'right': 0,  # initizialize counters to zero.
                            'left': 0,
                            'Correct': 0,
                            'Wrong': 0,
                            'NoResponse': 0,
                            'Total': 0
                        }
                self.odors.append(odors)
                self.concs.append(concs)
                self.vials.append(vials)
                self.flows.append(vialFlows)  # self.flows is a list of dictionaries. Each dictionary has an olfactometer's vial numbers for keys and each key's value is a list of flowrates for that vial.
                self.resultsCounterList.append(resultsCounterDict)
                if (self.shuffleMultiplier > 0):
                    shuffleVials = vials * self.shuffleMultiplier  # Extend the contents of the vials list by multiplying by the int value of self.shuffleMultiplier. This longer list will increase the "randomness" of the shuffle.
                    np.random.shuffle(shuffleVials)  # shuffle in-place
                    self.shuffleVials.append(shuffleVials)
                    self.shuffleFlows.append(shuffleFlows)
                olfaIndex += 1                

    def intensityGenerator(self):
        # This structure should work fine since its safe to assume intensity experiments will not use mixtures
        # so there will be only one olfactometer. But there will be a problem if more than one olfactometer is
        # used: the correctResponse will be re-determined for each olfactometer because the currentFlow will
        # not always be the same across the olfactometers. Each olfactometer's list of flowrates will get shuffled
        # separately, so the self.flowIndex will not always point to the same flowrate. The correctResponse will
        # be based on the last parameters of the last olfactometer in the loop. Again, if only one olfactometer
        # exists, there will not be a problem.
        ostim = {'olfas': {}}
        for i in range(self.nOlfas):  # Loop thru each olfa if there is more than one (which will create a mixture)
            if (self.shuffleMultiplier > 0):
                if (self.vialIndex == len(self.shuffleVials[i])):
                    np.random.shuffle(self.shuffleVials[i])  # Re-shuffle in-place when the index iterated through the entire list of vials for the olfa with index i.
                    self.vialIndex = 0  # Start iteration from the beginning.
                
                currentVial = self.shuffleVials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.
                
                if (self.flowIndex >= len(self.shuffleFlows[i][currentVial])):  # self.shuffleFlows is a list of dictionaries and self.shuffleFlows[i][currentVial] returns a list of integer flowrates for the vial identified by the currentVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                    np.random.shuffle(self.shuffleFlows[i][currentVial])  # Re-shuffle in-place when the index iterated through the entire list of flowrates for the the currentVial of olfa with index i.
                    self.flowIndex = 0  # Start iteration from the beginning.

                currentFlow = self.shuffleFlows[i][currentVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key currentVial of the olfa with index i.
                flow_threshold = np.sqrt(min(self.shuffleFlows[i][currentVial]) * max(self.shuffleFlows[i][currentVial]))  # Since the list gets shuffled, I cannot use the first and last index as the min and max because the list is no longer sorted.
            
            else:  # Do not shuffle. Just iterate through them in the order given in the olfa config file.
                if (self.vialIndex == len(self.vials[i])):
                    self.vialIndex = 0  # Start iteration from the beginning.
                    self.flowIndex += 1  # Since the lists will not be shuffled (nor extended), only increment the flowIndex when all vials have been iterated through. This way, each flowrate for each vial will be presented.
                
                currentVial = self.vials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.
                
                if (self.flowIndex >= len(self.flows[i][currentVial])):  # self.flows is a list of dictionaries and self.flows[i][currentVial] returns a list of integer flowrates for the vial identified by the currentVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                    self.flowIndex = 0  # Start iteration from the beginning.

                currentFlow = self.flows[i][currentVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key currentVial of the olfa with index i.
                flow_threshold = np.sqrt(min(self.flows[i][currentVial]) * max(self.flows[i][currentVial]))  # Not guaranteed that the order is sorted in the olfa config file, so use min and max functions instead of first and last index.

            # If flow is lower than flow_threshold == ~30 , 'left' is correct. Otherwise, 'right' is correct
            if (currentFlow < flow_threshold):
                self.correctResponse = 'left'
            else:
                self.correctResponse = 'right'       

            ostim['olfas'][f'olfa_{i}'] = {
                'dilutors': {},
                'mfc_0_flow': self.mfc_0_capacity,
                'mfc_1_flow': currentFlow,
                'odor': self.olfaConfigDict['Olfactometers'][i]['Vials'][currentVial]['odor'],
                'vialconc': self.olfaConfigDict['Olfactometers'][i]['Vials'][currentVial]['conc'],
                'vialNum': currentVial
            }
        self.stimList.clear()
        self.stimList.append(ostim)
        self.vialIndex += 1
        if (self.shuffleMultiplier > 0):
            self.flowIndex += 1  # Since the lists are shuffled (and may be extended), then increment the flowIndex together with the vialIndex.

    def identityGenerator(self):
        self.stimList.clear()  # Clear the previous trial's stimuli.
        
        # Generate the first odor presentation.
        firstOdorName = ''
        ostim = {'olfas': {}}
        for i in range(self.nOlfas):  # Loop thru each olfa if there is more than one (which will create a mixture)
            if (self.shuffleMultiplier > 0):
                if (self.vialIndex == len(self.shuffleVials[i])):
                    np.random.shuffle(self.shuffleVials[i])  # Re-shuffle in-place when the index iterated through the entire list of vials for the olfa with index i.
                    self.vialIndex = 0  # Start iteration from the beginning.
                
                firstOdorVial = self.shuffleVials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.

                if (self.flowIndex >= len(self.shuffleFlows[i][firstOdorVial])):  # self.shuffleFlows is a list of dictionaries and self.shuffleFlows[i][firstOdorVial] returns a list of integer flowrates for the vial identified by the firstOdorVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                    np.random.shuffle(self.shuffleFlows[i][firstOdorVial])  # Re-shuffle in-place when the index iterated through the entire list of flowrates for the the firstOdorVial of olfa with index i.
                    self.flowIndex = 0  # Start iteration from the beginning.

                firstOdorFlow = self.shuffleFlows[i][firstOdorVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key firstOdorVial of the olfa with index i.
            
            else:  # Do not shuffle. Just iterate through them in the order given in the olfa config file.
                if (self.vialIndex == len(self.vials[i])):
                    self.vialIndex = 0  # Start iteration from the beginning.
                    self.flowIndex += 1  # Since the lists will not be shuffled (nor extended), only increment the flowIndex when all vials have been iterated through. This way, each flowrate for each vial will be presented.
                
                firstOdorVial = self.vials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.

                if (self.flowIndex >= len(self.flows[i][firstOdorVial])):  # self.flows is a list of dictionaries and self.flows[i][firstOdorVial] returns a list of integer flowrates for the vial identified by the firstOdorVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                    self.flowIndex = 0  # Start iteration from the beginning.

                firstOdorFlow = self.flows[i][firstOdorVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key firstOdorVial of the olfa with index i.

            firstOdorName = self.olfaConfigDict['Olfactometers'][i]['Vials'][firstOdorVial]['odor']
            firstOdorConc = self.olfaConfigDict['Olfactometers'][i]['Vials'][firstOdorVial]['conc']
            
            ostim['olfas'][f'olfa_{i}'] = {
                'dilutors': {},
                'mfc_0_flow': self.mfc_0_capacity,
                'mfc_1_flow': firstOdorFlow,
                'odor': firstOdorName,
                'vialconc': firstOdorConc,
                'vialNum': firstOdorVial
            }
        self.stimList.append(ostim)  # Append the first odor presentation.
        self.vialIndex += 1
        if (self.shuffleMultiplier > 0):
            self.flowIndex += 1  # Since the lists are shuffled (and may be extended), then increment the flowIndex together with the vialIndex.

        self.correctResponse = self.correctResponsesList[self.currentTrialNum - 1]  # Get the current trial's correct response from the list of all the correct responses to use for the entire experiment. Subtract one because currentTrialNum starts at one, not zero.
        if (self.correctResponse == 'left'):
            self.stimList.append(ostim)  # Append the first odor again so that the two odors presented are the same.
        
        elif (self.correctResponse == 'right'):
            # Generate a different odor for the second presentation.
            secondOdorName = firstOdorName
            while (secondOdorName == firstOdorName):  # In the rare case that the second odor chosen is the same as the first, loop until a different odor is chosen.
                ostim = {'olfas': {}}
                for i in range(self.nOlfas):  # Loop thru each olfa if there is more than one (which will create a mixture)
                    if (self.shuffleMultiplier > 0):
                        if (self.vialIndex == len(self.shuffleVials[i])):
                            np.random.shuffle(self.shuffleVials[i])  # Re-shuffle in-place when the index iterated through the entire list of vials for the olfa with index i.
                            self.vialIndex = 0  # Start iteration from the beginning.
                        
                        secondOdorVial = self.shuffleVials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.

                        if (self.flowIndex >= len(self.shuffleFlows[i][secondOdorVial])):  # self.shuffleFlows is a list of dictionaries and self.shuffleFlows[i][secondOdorVial] returns a list of integer flowrates for the vial identified by the secondOdorVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                            np.random.shuffle(self.shuffleFlows[i][secondOdorVial])  # Re-shuffle in-place when the index iterated through the entire list of flowrates for the the secondOdorVial of olfa with index i.
                            self.flowIndex = 0  # Start iteration from the beginning.

                        secondOdorFlow = self.shuffleFlows[i][secondOdorVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key secondOdorVial of the olfa with index i.
                    
                    else:  # Do not shuffle. Just iterate through them in the order given in the olfa config file.
                        if (self.vialIndex == len(self.vials[i])):
                            self.vialIndex = 0  # Start iteration from the beginning.
                            self.flowIndex += 1  # Since the lists will not be shuffled (nor extended), only increment the flowIndex when all vials have been iterated through. This way, each flowrate for each vial will be presented.
                        
                        secondOdorVial = self.vials[i][self.vialIndex]  # This will return a string for a vial number of the olfa with index i.

                        if (self.flowIndex >= len(self.flows[i][secondOdorVial])):  # self.flows is a list of dictionaries and self.flows[i][secondOdorVial] returns a list of integer flowrates for the vial identified by the secondOdorVial key of the olfa with index i. I check if greater than or equal to because the lists of flowrates may not all be the same length across vials.
                            self.flowIndex = 0  # Start iteration from the beginning.

                        secondOdorFlow = self.flows[i][secondOdorVial][self.flowIndex]  # This will return an int for a flowrate of the vial with key secondOdorVial of the olfa with index i.

                    secondOdorName = self.olfaConfigDict['Olfactometers'][i]['Vials'][secondOdorVial]['odor']
                    secondOdorConc = self.olfaConfigDict['Olfactometers'][i]['Vials'][secondOdorVial]['conc']
                    
                    ostim['olfas'][f'olfa_{i}'] = {
                        'dilutors': {},
                        'mfc_0_flow': self.mfc_0_capacity,
                        'mfc_1_flow': secondOdorFlow,
                        'odor': secondOdorName,
                        'vialconc': secondOdorConc,
                        'vialNum': secondOdorVial
                    }
                self.vialIndex += 1
                if (self.shuffleMultiplier > 0):
                    self.flowIndex += 1  # Since the lists are shuffled (and may be extended), then increment the flowIndex together with the vialIndex.
            
            self.stimList.append(ostim)  # Once a different odor is chosen for the second presentation, append it to the stimList.       

    def stimulusFunction(self):
        # Will be overloaded with another function.
        pass

    def run(self):

        #print(self.currentTrialNum)
        try:
            if self.olfaChecked:
                self.getOdorsFromConfigFile()
                self.olfas = olfactometry.Olfactometers(config_obj=self.olfaConfigFileName)

            self.bpod.softcode_handler_function = self.my_softcode_handler    
            self.startTrial()

        # Note that these except clauses can only trigger from the first trial.
        except SerialException:
            if self.olfas:
                self.olfas.close_serials()  # close serial ports and let the user try again.
                del self.olfas
                self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.
            self.olfaNotConnectedSignal.emit()
            self.finished.emit()  

        except KeyError as err:  # error reading from json file.
            self.invalidFileSignal.emit(str(err))
            self.finished.emit() 

        except OlfaException:
            olf = 'olfa exception'
            self.olfaExceptionSignal.emit(str(olf))
            self.stopRunning()  # This would also stop the bpod trial just in case the olfa raised the exception when the state machine is running.
            # self.finished.emit()
        
    def startTrial(self):
        if self.keepRunning and (self.currentTrialNum <= self.nTrials) and (self.consecutiveNoResponses < self.noResponseCutOff):
            sleep(1)
            # load protocol from json file. I do this every trial because I need to reset some values back to their original as read
            # from the file, so instead of looping through the self.stateMachine dictionary a second time just to reset the values
            # after parsing it and adding the state to the state machine, I'll just re-read the file and all value will go back to
            # original. I need the values to go back to their original because the way I check for variables like "leftAction" and 
            # "rightAction" results in them only being modified the first trial. These variables change every trial according to 
            # self.correctResponse, so I need to update what gets added to the state machine every trial. Otherwise, the state change
            # condition for 'Port1In' will always stay the same instead of changing depending on self.correctResponse.
            with open(self.protocolFileName, 'r') as protocolFile:
                self.stateMachine = json.load(protocolFile)

            if self.olfas is not None:
                self.stimulusFunction()

            if (self.itiMin == self.itiMax):  # If they are equal, then self.currentITI will be the same every trial.
                self.currentITI = self.itiMin
            else:
                # Since they are different, randomly choose a value for self.currentITI every trial. Add 1 to the randint's upperbound to include itiMax in the range of possible integers (since the upperbound is non-inclusive).
                self.currentITI = np.random.randint(self.itiMin, self.itiMax + 1)

            # Do this when olfactometer is not used to avoid "referenced before assignment" error because self.correctResponse will not get a value.
            leftAction = None
            rightAction = None
            rewardValve = None
            rewardDuration = None
            if self.correctResponse == 'left':
                leftAction = 'Correct'
                rightAction = 'Wrong'
                rewardValve = self.leftWaterValvePort
                rewardDuration = self.leftWaterDuration
            elif self.correctResponse == 'right':
                leftAction = 'Wrong'
                rightAction = 'Correct'
                rewardValve = self.rightWaterValvePort
                rewardDuration = self.rightWaterDuration
            self.sma = StateMachine(self.bpod)
            listOfTuples = []

            for state in self.stateMachine['states']:
                if 'Olfactometer' in state['outputActions']:
                    # Replace 'Olfactometer': 'set_stimulus' with SoftCode 2.
                    if (state['outputActions']['Olfactometer'] == 'set_stimulus'):
                        state['outputActions']['SoftCode'] = 2  # SoftCode 2 is reserved for set_stimulus.
                        del state['outputActions']['Olfactometer']  # Delete 'Olfactometer' because its not a valid output channel.
                    
                    # Replace 'Olfactometer': 'set_dummy_vials' with SoftCode 3.
                    elif (state['outputActions']['Olfactometer'] == 'set_dummy_vials'):
                        state['outputActions']['SoftCode'] = 3  # SoftCode 3 is reserved for set_dummy_vials.
                        del state['outputActions']['Olfactometer']  # Delete 'Olfactometer because its not a valid output channel.

                # Automatically add a softcode in every state (if the state does not have it already) to call my_softcode_handler
                # function so that GUI gets updated and signals get emitted.
                if 'SoftCode' not in state['outputActions']:
                    state['outputActions']['SoftCode'] = 1  # SoftCode 1 is reserved for this purpose.

                # Replace change state names with respective variable that changes every trial based on self.correctResponse.
                leftInputEvent = f'Port{self.leftSensorPort}In'  # For example: 'Port1In'
                if leftInputEvent in state['stateChangeConditions']:
                    if (state['stateChangeConditions'][leftInputEvent] == 'leftAction'):
                        state['stateChangeConditions'][leftInputEvent] = leftAction
                    elif (state['stateChangeConditions'][leftInputEvent] == 'rightAction'):
                        state['stateChangeConditions'][leftInputEvent] = rightAction

                rightInputEvent = f'Port{self.rightSensorPort}In'  # For example: 'Port3In'
                if rightInputEvent in state['stateChangeConditions']:
                    if (state['stateChangeConditions'][rightInputEvent] == 'leftAction'):
                        state['stateChangeConditions'][rightInputEvent] = leftAction
                    elif (state['stateChangeConditions'][rightInputEvent] == 'rightAction'):
                        state['stateChangeConditions'][rightInputEvent] = rightAction

                # Replace output action values with respective variable.
                if 'Valve' in state['outputActions']:
                    for i in range(len(state['outputActions']['Valve'])):
                        if (state['outputActions']['Valve'][i] == 'finalValve'):
                            state['outputActions']['Valve'][i] = self.finalValvePort
                        elif (state['outputActions']['Valve'][i] == 'rewardValve'):
                            state['outputActions']['Valve'][i] = rewardValve

                if (state['stateTimer'] == 'rewardDuration'):
                    state['stateTimer'] = rewardDuration                    

                if state['stateTimer'] == 'itiDuration':
                    state['stateTimer'] = self.currentITI  # - 5  # Subtract 5 seconds because the QTimer.singleShot starts a new trial 5000 msecs after state machine completes.

                for channelName, channelValue in state['outputActions'].items():
                    # Add the sync byte transmission to the analog input module to signal to the saveDataWorker when to start and stop saving the voltages to the h5 file.
                    if channelName.startswith('Serial'):
                        if (channelValue == 'ADC_start'):
                            channelValue = 1
                        elif (channelValue == 'ADC_stop'):
                            channelValue = 2

                        state['outputActions'][channelName] = channelValue  # update the dictionary to append the tuple below.

                        # This will instruct the bpod to send the 2 byte serial_message instead of channelValue, i.e. instead of sending just 0x01 for a channelValue = 1, it will send 0x23 followed by 0x01,
                        # where 0x23 is ASCII character '#' which is the sync byte on the bpod.
                        self.bpod.load_serial_message(
                            serial_channel=int(channelName[-1]),  # The last character in the channelName string that starts with 'Serial' is the channel number, e.g. 'Serial1' or 'Serial2'.
                            message_ID=channelValue,
                            serial_message=[ord('#'), channelValue]
                        )
                    # Convert output actions from dictionary to list of two-tuples.
                    if isinstance(channelValue, list):
                        for i in channelValue:
                            listOfTuples.append((channelName, i))  # i is the port numbers in the list, such as when opening multiple valves or LEDs simultaneously.
                    else:
                        listOfTuples.append((channelName, channelValue))                       
                
                # print(self.bpod._hardware.outputs) # this prints a lot of stuff
                # print(self.bpod._hardware.inputs)
                # print(self.bpod._hardware.channels)
                
                # Now add the updated state to the state machine.
                self.sma.add_state(
                    state_name=state['stateName'],
                    state_timer=state['stateTimer'],
                    state_change_conditions=state['stateChangeConditions'],
                    output_actions=listOfTuples
                )
                # print(self.sma.manifest)

                listOfTuples = []  # reset to empty list.
            
            # Add timers if they exist
            if 'timers' in self.stateMachine.keys():
                for timer in self.stateMachine['timers']:
                    self.sma.set_global_timer(**timer) # Camera


            # Add the timers from whatever you read from json file
            
            self.currentResponseResult = '--'  # reset until bpod gets response result.
            self.responseResultSignal.emit(self.currentResponseResult)
            currentTrialInfo = self.getCurrentTrialInfoDict()
            self.newTrialInfoSignal.emit(currentTrialInfo)
            
            
            if self.camera is not None:
                try:

                    print('The trial number for saving camera data is {:03d}'.format(currentTrialInfo['currentTrialNum']))
                    # dateString = datetime.now().strftime("%Y-%m-%d")
                    # self.camera.set_camera_data_name(r'{}_Trial_{:03d}'.format(dateString,currentTrialInfo['currentTrialNum']))
                    camera_data_dirbase = os.path.basename(os.path.normpath(self.camera.camera_data_dir))
                    self.camera.set_camera_data_name(r'{}_Trial_{:03d}'.format(camera_data_dirbase,currentTrialInfo['currentTrialNum']))

                    print('Acquiring {}'.format(self.camera.camera_data_name))
                    self.camera.start_acquisition()
                    print('Camera initialized')

                except TimeoutError as timeout_error:
                    self.show_message_box(window_title='Error Initializing Camera',
                                      icon=QMessageBox.Critical,
                                      text=str(timeout_error))
            try:
                self.bpod.send_state_machine(self.sma)  # Send state machine description to Bpod device
                self.bpod.run_state_machine(self.sma)  # Run state machine
               
            except (BpodErrorException, TypeError) as err:
                
                self.bpodExceptionSignal.emit(str(err))
                self.stopRunning()
                self.finished.emit()
                return  # This is here to avoid executing the remaining code below.

            self.currentStateName = 'exit'
            self.stimIndex = 0
            self.saveVideoSignal.emit(1)
            
            if self.saveTrial:
                endOfTrialDict = self.getEndOfTrialInfoDict()
                self.saveTrialDataDictSignal.emit(endOfTrialDict)
                # self.stopSDCardLoggingSignal.emit()
                self.currentTrialNum += 1  # Only increment if trial gets saved.
            
            else:  # Do not send the trial data for this trial to the saveDataWorker.
                self.saveTrialDataDictSignal.emit({})  # Instead, send an empty dict to indicate that the trial was discarded.
                self.saveTrial = True  # Reset to True for the next trial.

            if (self.consecutiveNoResponses == self.autoWaterCutoff):
                self.bpod.manual_override(self.bpod.ChannelTypes.OUTPUT, self.bpod.ChannelNames.VALVE, channel_number=self.leftWaterValvePort, value=1)
                self.bpod.manual_override(self.bpod.ChannelTypes.OUTPUT, self.bpod.ChannelNames.VALVE, channel_number=self.rightWaterValvePort, value=1)
                QTimer.singleShot(1000, lambda: self.bpod.manual_override(self.bpod.ChannelTypes.OUTPUT, self.bpod.ChannelNames.VALVE, channel_number=self.leftWaterValvePort, value=0))
                QTimer.singleShot(1000, lambda: self.bpod.manual_override(self.bpod.ChannelTypes.OUTPUT, self.bpod.ChannelNames.VALVE, channel_number=self.rightWaterValvePort, value=0))
            
            # Start the next trial in 1000 msecs to give some time for saveDataWorker to write all trial data before next trial's info dict gets sent.
            QTimer.singleShot(1000, self.startTrial)

        else:
            if (self.consecutiveNoResponses >= self.noResponseCutOff):
                self.noResponseAbortSignal.emit()

            if self.olfas:
                logging.info("closing olfactometer used by protocolWorker thread.")
                self.olfas.close_serials()  # close serial ports and let the user try again.
                del self.olfas
                self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.

            logging.info("ProtocolWorker finished")
            self.finished.emit()

    # Now that i do not have a while loop that blocks the thread's signal handling, I can probably change this stopRunning() function
    # so that i do not have to use lambda to call it from the main thread. Look into QThread::isInterruptionRequested().
    def stopRunning(self):
        self.keepRunning = False
        self.bpod.stop_trial()
        logging.info("current trial aborted")
        if self.camera is not None:
            self.camera.stop_acquisition()
        if self.olfas:
            self.olfas.set_dummy_vials()  # Close vials in case experiment stopped while olfactometer was on.

    def discardCurrentTrial(self):
        self.saveTrial = False
        self.bpod.stop_trial()
        logging.info("current trial aborted")
        if self.olfas:
            self.olfas.set_dummy_vials()  # Close vials in case experiment stopped while olfactometer was on.
    
    # def launchOlfaGUI(self):
    #     if self.olfas is not None:
    #         self.olfas.show()