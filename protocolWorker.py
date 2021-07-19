import logging
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
        # I should probably also check for edge case when (self.currentState == '') upon init of the ProtocolWorker class.
        if not (self.currentState == 'exit'):
            logging.info("attempting to abort current trial")
            self.myBpod.stop_trial()
            logging.info("current trial aborted")
