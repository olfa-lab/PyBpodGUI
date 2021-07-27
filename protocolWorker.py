import logging
import json
import numpy as np
import time
from PyQt5.QtCore import QObject, QThread, pyqtSignal
from pybpodapi.protocol import StateMachine

logging.basicConfig(format="%(message)s", level=logging.INFO)


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

    def __init__(self, bpodObject, olfaObject, protocolFileName, numTrials=1):
        super(ProtocolWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.myBpod = bpodObject
        self.analogIn = bpodObject.find_module_by_name('AnalogIn1')  # Check if analog input module is connected. This is of type <class 'pybpodapi.bpod_modules.bpod_module.BpodModule'>, not BpodAnalogIn class.
        self.olfas = olfaObject
        self.protocolFileName = protocolFileName
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
        self.leftPort = 1
        self.rightPort = 3
        self.leftWaterDuration = 0.1  # seconds
        self.rightWaterDuration = 0.1  # seconds
        self.keepRunning = True
        self.currentStateName = ''
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
        # I will reserve softcode 1 to be an automatic output from every state so that the my_softcode_handler function gets called at every
        # state to update the GUI info and emit the necessary signals. If user selects a different softcode other than 1, the instructions
        # below will still be executed. However, I'm still not sure how to implement a way to allow a user to configure softcode actions.
        if softcode == 1:
            pass

        # Update trial info for GUI
        self.currentStateName = self.sma.state_names[self.sma.current_state]
        self.newStateSignal.emit(self.currentStateName)
        
        if self.currentStateName == 'Correct':
            self.currentResponseResult = 'Correct'
            self.responseResultSignal.emit(self.currentResponseResult)

            self.previousResponseResult = self.currentResponseResult
            self.consecutiveNoResponses = 0  # Reset counter to 0 because there was a response.

            self.flowResultsCounterDict[str(self.currentFlow)][self.correctResponse] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Correct'] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Total'] += 1
            self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)
            self.totalRewards += 1

        elif self.currentStateName == 'Wrong':
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
            self.totalPunishes += 1

        elif self.currentStateName == 'NoResponse':
            self.currentResponseResult = 'No Response'
            self.responseResultSignal.emit(self.currentResponseResult)

            if self.previousResponseResult == self.currentResponseResult:
                self.consecutiveNoResponses += 1
            else:
                self.previousResponseResult = self.currentResponseResult
                self.consecutiveNoResponses = 1  # Reset counter to 1 because it should start counting now.

            self.flowResultsCounterDict[str(self.currentFlow)]['NoResponse'] += 1
            self.flowResultsCounterDict[str(self.currentFlow)]['Total'] += 1
            self.totalNoResponses += 1
        
        elif self.currentStateName == 'NoSniff':
            self.currentResponseResult = 'No Sniff'
            self.responseResultSignal.emit(self.currentResponseResult)

        sessionTotals = self.getTotalsDict()
        self.totalsDictSignal.emit(sessionTotals)
        self.flowResultsCounterDictSignal.emit(self.flowResultsCounterDict)


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
                leftAction = 'Correct'
                rightAction = 'Wrong'
                rewardValve = 1  # Left reward valve connected to bpod behavior port 1.
                rewardDuration = self.leftWaterDuration
            elif self.correctResponse == 'right':
                leftAction = 'Wrong'
                rightAction = 'Correct'
                rewardValve = 3  # Right reward valve connected to bpod behavior port 3.
                rewardDuration = self.rightWaterDuration

            # load protocol from json file. I do this every trial because I need to reset some values back to their original as read
            # from the file, so instead of looping through the self.stateMachine dictionary a second time just to reset the values
            # after parsing it and adding the state to the state machine, I'll just re-read the file and all value will go back to
            # original. I need the values to go back to their original because the way I check for variables like "leftAction" and 
            # "rightAction" results in them only being modified the first trial. These variables change every trial according to 
            # self.correctResponse, so I need to update what gets added to the state machine every trial. Otherwise, the state change
            # condition for 'Port1In' will always stay the same instead of changing depending on self.correctResponse.
            with open(self.protocolFileName, 'r') as protocolFile:
                self.stateMachine = json.load(protocolFile)
            
            self.sma = StateMachine(self.myBpod)
            stateNum = 1
            listOfTuples = []

            for state in self.stateMachine['states']:
                # Automatically add a softcode in every state to call my_softcode_handler function so that GUI gets updated and signals get emitted.
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

                if state['stateName'] == 'itiDelay':
                    state['stateTimer'] = self.currentITI 

                for channelName, channelValue in state['outputActions'].items():
                    # Automatically add the sync byte transmission to the analog module for every state.
                    if channelName.startswith('Serial') and (channelValue == 'SyncByte'):
                        # reassign channelValue from 'SyncByte' to stateNum so that when appending it to the listOfTuples, the byte value
                        # go into the tuple instead of 'SyncByte'. This way the state machine can replace the byte value with the loaded
                        # serial message. 
                        channelValue = stateNum
                        # I also update the state['outputActions'] dictionary with stateNum as the value instead of 'SyncByte'
                        # for consistency, which also causes this if statement to be enter only once at the beginning of the experiment instead
                        # of before the start of every trial. But either way it should not make any difference...
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

                logging.info(listOfTuples)
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

            self.myBpod.send_state_machine(self.sma)  # Send state machine description to Bpod device
            self.myBpod.run_state_machine(self.sma)  # Run state machine

            self.currentStateName = 'exit'
            endOfTrialDict = self.getEndOfTrialInfoDict()
            self.saveTrialDataDictSignal.emit(endOfTrialDict)
            logging.info("saveTrialDataDictSignal emitted")

            # self.stopSDCardLoggingSignal.emit()
            
            self.olfas.set_dummy_vials()

            QThread.sleep(1)  # Need this (or similar blocking method) to give the 'saveDataThread' enough time to finish writing data to the buffer before the stopRunningSignal gets emitted.
            
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
        # I should probably also check for edge case when (self.currentStateName == '') upon init of the ProtocolWorker class.
        if not (self.currentStateName == 'exit'):
            logging.info("attempting to abort current trial")
            self.myBpod.stop_trial()
            logging.info("current trial aborted")
