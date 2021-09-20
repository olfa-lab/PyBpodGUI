import logging
import json
import numpy as np
import time
from serial.serialutil import SerialException
from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer, QEventLoop
from pybpodapi.protocol import StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException

import olfactometry
from olfactometry.utils import OlfaException

logging.basicConfig(format="%(message)s", level=logging.INFO)


class ProtocolWorker(QObject):
    trialStartSignal = pyqtSignal(str)  # sends correct response with it for use by inputEventThread.
    newTrialInfoSignal = pyqtSignal(dict)  # sends current trial info with it to update GUI.
    newStateSignal = pyqtSignal(str)  # sends current state with it to update GUI.
    stateNumSignal = pyqtSignal(int)  
    responseResultSignal = pyqtSignal(str)  # sends the response result of the current trial with it to update the GUI.
    totalsDictSignal = pyqtSignal(dict)  # sends the session totals with it to update the GUI.
    flowResultsCounterDictSignal = pyqtSignal(dict) # sends the results for each flow rate with it to update the GUI's results plot.
    saveTrialDataDictSignal = pyqtSignal(dict)  # 'dict' is interpreted as 'QVariantMap' by PyQt5 and thus can only have strings as keys.
    # saveTrialDataDictSignal = pyqtSignal(object)  # Use 'object' instead if you want to use non-strings as keys.
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

    def __init__(self, bpodObject, protocolFileName, olfaConfigFileName, experimentType, leftWaterValveDuration, rightWaterValveDuration, itiMin, itiMax, noResponseCutoff, autoWaterCutoff, olfaChecked=True, numTrials=1):
        super(ProtocolWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.myBpod = bpodObject
        self.olfaChecked = olfaChecked
        self.olfas = None
        self.protocolFileName = protocolFileName
        self.olfaConfigFileName = olfaConfigFileName
        self.experimentType = experimentType
        self.correctResponse = ''
        self.currentOdorName = None
        self.currentOdorConc = None
        self.currentVialNum = None
        self.currentFlow = None
        self.currentTrialNum = 0
        self.totalCorrect = 0
        self.totalWrong = 0
        self.totalNoResponses = 0
        self.consecutiveNoResponses = 0
        self.noResponseCutOff = noResponseCutoff
        self.autoWaterCutoff = autoWaterCutoff
        self.currentITI = None
        self.itiMin = itiMin
        self.itiMax = itiMax
        self.nTrials = numTrials
        self.leftPort = 1
        self.rightPort = 3
        self.leftWaterDuration = leftWaterValveDuration / 1000  # convert to seconds
        self.rightWaterDuration = rightWaterValveDuration / 1000  # convert to seconds
        self.keepRunning = True
        self.currentStateName = ''
        self.currentResponseResult = ''
        self.previousResponseResult = ''
        self.vials = []
        self.odors = []
        self.concs = []
        self.flows = []
        self.vialResultsCounterDict = {}
        self.flowResultsCounterDict = {}
        self.stimIndex = 0

    # @pyqtSlot()  # Even with this decorator, I still need to use lambda when connecting a signal to this function.
    def setLeftWaterDuration(self, duration):
        self.leftWaterDuration = duration / 1000  # Convert to seconds.

    def setRightWaterDuration(self, duration):
        self.rightWaterDuration = duration / 1000  # Convert to seconds.

    def setNumTrials(self, value):
        self.nTrials = value
    
    def setMinITI(self, value):
        self.itiMin = value

    def setMaxITI(self, value):
        self.itiMax = value

    def setNoResponseCutoff(self, value):
        self.noResponseCutOff = value

    def setAutoWaterCutoff(self, value):
        self.autoWaterCutoff = value
    
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
                'currentVialNum': self.currentVialNum,
                'currentOdorName': self.currentOdorName,
                'currentOdorConc': self.currentOdorConc,
                'currentFlow': self.currentFlow,
                'nStates': self.sma.total_states_added
            }
            return trialDict
        return {}

    def getEndOfTrialInfoDict(self):
        if self.currentStateName == 'exit':
            dict1 = self.getCurrentTrialInfoDict()
            dict2 = self.myBpod.session.current_trial.export()
            dict3 = {**dict1, **dict2}  # Merge both dictionaries
            dict3.update({'responseResult': self.currentResponseResult})
            return dict3
        logging.info('could not get end of trial dict')
        return {}

    def calculateTotalPercentCorrect(self):
        logging.info('calculating total percent correct')
        percent = round(((float(self.totalCorrect) / float(self.currentTrialNum)) * 100), 2)  # I used 'self.currentTrialNum' instead of 'self.nTrials' to ensure the percentage only counts the number of completed trials incase the experiment is aborted early.
        logging.info(f"percent correct is {percent}")
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
                self.olfas.olfas[0]._poll_mfcs()
                self.olfas.set_stimulus(self.stimulus[self.stimIndex])
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
            self.olfas.olfas[0]._valve_lockout_clear()

        # Update trial info for GUI
        self.currentStateName = self.sma.state_names[self.sma.current_state]
        self.newStateSignal.emit(self.currentStateName)
        self.stateNumSignal.emit(self.sma.current_state)
        
        if self.currentStateName == 'Correct':
            self.currentResponseResult = 'Correct'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)][self.correctResponse] += 1
            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['Correct'] += 1
            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            
            self.totalCorrect += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif self.currentStateName == 'Wrong':
            self.currentResponseResult = 'Wrong'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            if self.correctResponse == 'left':
                self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['right'] += 1  # increment the opposite direction because the response was wrong.
            elif self.correctResponse == 'right':
                self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['left'] += 1  # increment the opposite direction because the response was wrong.
            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['Wrong'] += 1
            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            
            self.totalWrong += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)

        elif self.currentStateName == 'NoResponse':
            self.currentResponseResult = 'No Response'
            self.responseResultSignal.emit(self.currentResponseResult)

            if self.previousResponseResult == self.currentResponseResult:
                self.consecutiveNoResponses += 1
            else:
                self.previousResponseResult = self.currentResponseResult
                self.consecutiveNoResponses = 1  # Reset counter to 1 because it should start counting now.

            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['NoResponse'] += 1
            self.flowResultsCounterDict[self.currentVialNum][str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            
            self.totalNoResponses += 1
            sessionTotals = self.getTotalsDict()
            self.totalsDictSignal.emit(sessionTotals)
        
        elif self.currentStateName == 'NoSniff':
            self.currentResponseResult = 'No Sniff'
            self.responseResultSignal.emit(self.currentResponseResult)

    def groupDuplicateVials(self, odors, concs, vials):
        currentOdor = ''
        currentConc = 0
        duplicateVials = {}
        for i in range(len(odors)):
            currentOdor = odors[i].split('_')[0]  # If two odors in the olfa config file are the same and have the same concentration, then I put underscore and the vial number at the end of the odor name's string (e.g. 'limonene_5') to bypass the olfactometer code raising an error when two or more vials match.
            currentConc = concs[i]
            for j in range(len(odors)):
                if (currentOdor == odors[j].split('_')[0]) and (currentConc == concs[j]):  # if the odor names are the same and the concentrations are the same, then the two vials are duplicates.
                    if currentOdor not in duplicateVials:
                        duplicateVials[currentOdor] = {str(currentConc): [vials[j]]}
                    elif str(currentConc) not in duplicateVials[currentOdor]:  # This means currentOdor must already be in duplicateVials, but there is another conc of that odor in the olfa config file for which another vial was found to match.
                        duplicateVials[currentOdor][str(currentConc)] = [vials[j]]  # When first creating the key, put the indices for i and j in the list because they are the first match found.
                    elif vials[j] not in duplicateVials[currentOdor][str(currentConc)]:  # Check if vial was already added to avoid appending again when looping over an odor name that was already used.
                        duplicateVials[currentOdor][str(currentConc)].append(vials[j])  # Then append vials[j] whenever another match is found.
        
        self.duplicateVialsSignal.emit(duplicateVials)
    
    def getOdorsFromConfigFile(self):
        with open(self.olfaConfigFileName, 'r') as configFile:
            self.olfaConfigDict = json.load(configFile)

        if (self.experimentType == 'oneOdorIntensity'):
            self.stimulusFunction = self.oneOdorIntensityRandomizer

            if (len(self.olfaConfigDict['Olfactometers'][0]['flowrates']) == 0):
                raise KeyError("No flowrates given in olfa config file.")
            
            self.flows = self.olfaConfigDict['Olfactometers'][0]['flowrates']

            for vialNum, vialInfo in self.olfaConfigDict['Olfactometers'][0]['Vials'].items():
                if not (vialInfo['odor'] == 'dummy'):
                    self.odors.append(vialInfo['odor'])
                    self.concs.append(vialInfo['conc'])
                    self.vials.append(vialNum)
                    self.flowResultsCounterDict[vialNum] = {}
                    for flow in self.flows:
                        self.flowResultsCounterDict[vialNum][str(flow)] = {
                            'right': 0,  # initizialize counters to zero.
                            'left': 0,
                            'Correct': 0,
                            'Wrong': 0,
                            'NoResponse': 0,
                            'Total': 0
                        }            

            self.groupDuplicateVials(self.odors, self.concs, self.vials)

        elif (self.experimentType == 'twoOdorMatch'):
            self.stimulusFunction = self.twoOdorMatchRandomizer
            self.flows.append(100)  # Assume only one flow rate, which is max.
            self.currentFlow = 100   
            for flow in self.flows:
                self.flowResultsCounterDict[str(flow)] = {
                    'right': 0,  # initizialize counters to zero.
                    'left': 0,
                    'Correct': 0,
                    'Wrong': 0,
                    'NoResponse': 0,
                    'Total': 0
                }      

    def oneOdorIntensityRandomizer(self):
        vialIndex = np.random.randint(len(self.vials))  # random int for index of vial
        self.currentVialNum = self.vials[vialIndex]
        self.currentOdorName = self.odors[vialIndex]
        self.currentOdorConc = self.concs[vialIndex]
        
        flow_threshold = np.sqrt(self.flows[0] * self.flows[-1])
        self.currentFlow = np.random.choice(self.flows)
        #If flow is lower than flow_threshold == ~30 , 'left' is correct. Otherwise, 'right' is correct
        if self.currentFlow < flow_threshold:
            self.correctResponse = 'left'
        else:
            self.correctResponse = 'right'        

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
        return [ostim]

    def twoOdorMatchRandomizer(self):
        vialIndex = np.random.randint(len(self.odors))  # random int for index of vial
        odorName0 = self.odors[vialIndex]
        odorConc0 = self.concs[vialIndex]

        vialIndex = np.random.randint(len(self.odors))  # random int for index of vial
        odorName1 = self.odors[vialIndex]
        odorConc1 = self.concs[vialIndex]

        self.currentOdorName = f"{odorName0}, {odorName1}"
        self.currentOdorConc = f"{odorConc0}, {odorConc1}"

        # If the two odor names and concentrations are the same, 'right' is correct. If different, 'left' is correct.
        if (odorName0 == odorName1) and (odorConc0 == odorConc1):
            self.correctResponse = 'right'
        else:
            self.correctResponse = 'left'

        ostim0 = {
            'olfas': {
                'olfa_0': {
                    'dilutors': {},
                    'mfc_0_flow': 1000 - self.currentFlow,
                    'mfc_1_flow': self.currentFlow,
                    'odor': odorName0,
                    'vialconc': odorConc0
                }
            }
        }
        ostim1 = {
            'olfas': {
                'olfa_0': {
                    'dilutors': {},
                    'mfc_0_flow': 1000 - self.currentFlow,
                    'mfc_1_flow': self.currentFlow,
                    'odor': odorName1,
                    'vialconc': odorConc1
                }
            }
        }
        return [ostim0, ostim1]

    def stimulusFunction(self):
        # Will be overloaded with another function.
        pass

    def run(self):
        '''
        I am no longer using a while loop inside here to perform nTrials because the while loop is supposedly blocking the protocolWorker's thread
        from handling signals, namely QTimer's timeout signals that are emitted from the olfactometer code. Those singleShot timers are need to ensure
        at least one second elapsed in between opening vials to prevent cross contamination. Otherwise, there is a _valve_time_lockout flag that never
        gets cleared and so the olfactometer will not open any vial and give an error.The timeout signals never connected to their slot function
        because of the while loop. I could not find any evidence in Qt documentation to prove this, but I suppose that is the reason. Emitting signals
        works just fine, but slot functions do not work when the thread is stuck inside a while loop.
        
        Instead what I am doing now is first checking if the olfaCheckBox is checked in the main GUI, which I pass its bool value to the ProtocolWorker
        during its initialization. I now create the olfa object here, inside the protocolWorker's thread, instead of in the main thread as before
        so that the protocolWorker's thread will take ownership of the QTimers that the olfactometer code uses. Any QTimer must be started and
        stopped by the thread that created it (according to the Qt docs). Then I attempt to connect to the olfactometer and run self.startTrial().

        self.startTrial() executes one trial of the protocol and at the very end of the function, there is a QTimer.singleShot instead of a QThread.sleep.
        The QTimer.singleShot's timeout signal connects the self.startTrial() function again to run the next trial. This will make the protocolWorker's
        thread run nTrials without using a while loop that would block signals. However, the bpod's run_state_machine() function is a blocking function
        that also does not allow signals to be connected to their slot functions while the state machine is running. But because the protocolWorker's
        thread only runs one trial at a time, it can connect signals to their slots after the run_state_machine() function completes, unlike with a
        while loop, in which the protocolWorker's thread could only connect signals to their slots after leaving the while loop. So what happens now is
        timeout signals that get emitted while the run_state_machine() function is being executed do not get connected to their slot functions, but
        instead, either: 
            (1) the QTimer "realizes" that the slot function was not called so it keeps trying again by emitting the timeout signal at the
                specified interval until the timeout signal reaches its slot function (for singleShot timers), or
            (2) the QTimer starts its clock only after completion of the blocking function (also for singleShot timers).

        The timeout signal for the olfactometer code (for the _valve_lockout_clear() method) gets emitted and its slot function gets called
        after the run_state_machine() completes. It only happens for the set_dummy_vials() function, not for the set_stimulus() function. I
        think the _valve_lockout_clear() function only gets called from a QTimer.singleShot when you close a vial. Thats when cross contamination
        can occur when you do not wait at least one second before opening another vial. So the QTimer.singleShot seems to only be created when I
        call set_dummy_vials() because that function closes any open valves before opening the dummy valve.

        After testing, the olfactometer now works every trial and I never got an error that did not allow me to open a valve or to wait at least
        one second before opening vial. 
        '''
        try:
            if self.olfaChecked:
                self.getOdorsFromConfigFile()
                self.olfas = olfactometry.Olfactometers(config_obj=self.olfaConfigFileName)

            self.myBpod.softcode_handler_function = self.my_softcode_handler    
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
            logging.info("olfa exception")
            olf = 'olfa exception'
            self.olfaExceptionSignal.emit(str(olf))
            self.stopRunning()  # This would also stop the bpod trial just in case the olfa raised the exception when the state machine is running.
            # self.finished.emit()
        
    def startTrial(self):
        finalValve = 2  # Final valve for the odor port on bpod's behavior port 2.

        if self.keepRunning and (self.currentTrialNum < self.nTrials) and (self.consecutiveNoResponses < self.noResponseCutOff):
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
                self.stimulus = self.stimulusFunction()

            if (self.itiMin == self.itiMax):  # If they are equal, then self.currentITI will be the same every trial.
                self.currentITI = self.itiMin
            else:
                # Since they are different, randomly choose a value for self.currentITI every trial. Add 1 to the randint's upperbound to include itiMax in the range of possible integers (since the upperbound is non-inclusive).
                self.currentITI = np.random.randint(self.itiMin, self.itiMax + 1)
            
            self.currentTrialNum += 1

            if self.correctResponse == 'left':
                leftAction = 'Correct'
                rightAction = 'Wrong'
                rewardValve = 1  # Left reward valve connected to bpod behavior port 1.
                rewardDuration = self.leftWaterDuration
            elif self.correctResponse == 'right':
                leftAction = 'Wrong'
                rightAction = 'Correct'
                rewardValve = 3  # Right reward valve connected to bpod behavior port 3.
                rewardDuration = self.rightWaterDuration

            self.sma = StateMachine(self.myBpod)
            stateNum = 1
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
                if 'Port1In' in state['stateChangeConditions']:
                    if (state['stateChangeConditions']['Port1In'] == 'leftAction'):
                        state['stateChangeConditions']['Port1In'] = leftAction
                    elif (state['stateChangeConditions']['Port1In'] == 'rightAction'):
                        state['stateChangeConditions']['Port1In'] = rightAction

                if 'Port3In' in state['stateChangeConditions']:
                    if (state['stateChangeConditions']['Port3In'] == 'leftAction'):
                        state['stateChangeConditions']['Port3In'] = leftAction
                    elif (state['stateChangeConditions']['Port3In'] == 'rightAction'):
                        state['stateChangeConditions']['Port3In'] = rightAction

                # Replace output action values with respective variable.
                if 'Valve' in state['outputActions']:
                    for i in range(len(state['outputActions']['Valve'])):
                        if (state['outputActions']['Valve'][i] == 'finalValve'):
                            state['outputActions']['Valve'][i] = finalValve
                        elif (state['outputActions']['Valve'][i] == 'rewardValve'):
                            state['outputActions']['Valve'][i] = rewardValve

                if (state['stateTimer'] == 'rewardDuration'):
                    state['stateTimer'] = rewardDuration                    

                if state['stateTimer'] == 'itiDuration':
                    state['stateTimer'] = self.currentITI  # - 5  # Subtract 5 seconds because the QTimer.singleShot starts a new trial 5000 msecs after state machine completes.

                for channelName, channelValue in state['outputActions'].items():
                    # Automatically add the sync byte transmission to the analog module for every state.
                    if channelName.startswith('Serial') and (channelValue == 'SyncByte'):
                        # reassign channelValue from 'SyncByte' to stateNum so that when appending it to the listOfTuples, the byte value
                        # go into the tuple instead of 'SyncByte'. This way the state machine can replace the byte value with the loaded
                        # serial message. 
                        channelValue = stateNum
                        state['outputActions'][channelName] = stateNum
                        self.myBpod.load_serial_message(
                            serial_channel=int(channelName[-1]),
                            message_ID=stateNum,
                            serial_message=[ord('#'), stateNum]
                        )
                    # Convert output actions from dictionary to list of two-tuples.
                    if isinstance(channelValue, list):
                        for i in channelValue:
                            listOfTuples.append((channelName, i))
                    else:
                        listOfTuples.append((channelName, channelValue))                       

                # Now add the updated state to the state machine.
                self.sma.add_state(
                    state_name=state['stateName'],
                    state_timer=state['stateTimer'],
                    state_change_conditions=state['stateChangeConditions'],
                    output_actions=listOfTuples
                )

                stateNum += 1  # increment state number for record keeping.
                listOfTuples = []  # reset to empty list.

            self.trialStartSignal.emit(self.correctResponse)
            self.currentResponseResult = '--'  # reset until bpod gets response result.
            self.responseResultSignal.emit(self.currentResponseResult)
            currentTrialInfo = self.getCurrentTrialInfoDict()
            self.newTrialInfoSignal.emit(currentTrialInfo)

            try:
                self.myBpod.send_state_machine(self.sma)  # Send state machine description to Bpod device
                self.myBpod.run_state_machine(self.sma)  # Run state machine
            except (BpodErrorException, TypeError) as err:
                self.bpodExceptionSignal.emit(str(err))
                # self.stopRunning()
                self.finished.emit()
                return  # This is here to avoid executing the remaining code below.

            self.currentStateName = 'exit'
            endOfTrialDict = self.getEndOfTrialInfoDict()
            self.saveTrialDataDictSignal.emit(endOfTrialDict)
            logging.info("saveTrialDataDictSignal emitted")
            self.stimIndex = 0
            # self.stopSDCardLoggingSignal.emit()

            if (self.consecutiveNoResponses == self.autoWaterCutoff):
                self.myBpod.manual_override(self.myBpod.ChannelTypes.OUTPUT, self.myBpod.ChannelNames.VALVE, channel_number=self.leftPort, value=1)
                self.myBpod.manual_override(self.myBpod.ChannelTypes.OUTPUT, self.myBpod.ChannelNames.VALVE, channel_number=self.rightPort, value=1)
                QTimer.singleShot(1000, lambda: self.myBpod.manual_override(self.myBpod.ChannelTypes.OUTPUT, self.myBpod.ChannelNames.VALVE, channel_number=self.leftPort, value=0))
                QTimer.singleShot(1000, lambda: self.myBpod.manual_override(self.myBpod.ChannelTypes.OUTPUT, self.myBpod.ChannelNames.VALVE, channel_number=self.rightPort, value=0))
            
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
        # I should probably also check for edge case when (self.currentStateName == '') upon init of the ProtocolWorker class.
        if not (self.currentStateName == 'exit'):
            logging.info("attempting to abort current trial")
            self.myBpod.stop_trial()
            logging.info("current trial aborted")

    # def launchOlfaGUI(self):
    #     if self.olfas is not None:
    #         self.olfas.show()