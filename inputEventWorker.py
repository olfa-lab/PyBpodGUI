import logging
from PyQt5.QtCore import QObject, QTimer, pyqtSignal


logging.basicConfig(format="%(message)s", level=logging.INFO)


class InputEventWorker(QObject):
    inputEventSignal = pyqtSignal(list)
    finished = pyqtSignal()

    def __init__(self, bpodObject):
        super(InputEventWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.myBpod = bpodObject
        self.keepRunning = True
        self.correctResponse = None
        self.currentPort1In = 0
        self.currentPort3In = 0
        self.currentPort1Out = 0
        self.currentPort3Out = 0

    # Since it is not possible for the inputEventThread to call this function when getting
    # a signal (because the thread is in an infinite loop), how about trying to modify the
    # value of 'self.newTrail' directly (instead of via a setter function like this)?
    def newTrialSlot(self, correctResponse):
        self.correctResponse = correctResponse

    def run(self):
        logging.info("InputEventThread is running")
        self.checkForNewInputEvent()

    def checkForNewInputEvent(self):
        if self.keepRunning:
            try:
                eventsDict = self.myBpod.session.current_trial.get_all_timestamps_by_event()
            except AttributeError:
                eventsDict = {}  # This means the trial has not started yet.

            # Left lick sensor touched
            if 'Port1In' in eventsDict:
                newPort1In = eventsDict['Port1In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort1In != newPort1In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort1In = newPort1In
                    if (self.correctResponse == 'left'):
                        self.inputEventSignal.emit(['L', 1, 1])  # left, enabled, correct
                    elif (self.correctResponse == 'right'):
                        self.inputEventSignal.emit(['L', 1, 0])  # left, enabled, wrong
                    elif (self.correctResponse == ''):
                        self.inputEventSignal.emit(['L', 1, 1])  # left, enabled, correct (used when the protocol does not make use of self.correctResponse)

            # Right lick sensor touched
            if 'Port3In' in eventsDict:
                newPort3In = eventsDict['Port3In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort3In != newPort3In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort3In = newPort3In
                    if (self.correctResponse == 'right'):
                        self.inputEventSignal.emit(['R', 1, 1])  # right, enabled, correct
                    elif (self.correctResponse == 'left'):
                        self.inputEventSignal.emit(['R', 1, 0])  # right, enabled, wrong
                    elif (self.correctResponse == ''):
                        self.inputEventSignal.emit(['R', 1, 1])  # right, enabled, correct (used when the protocol does not make use of self.correctResponse)

            # Left lick sensor released
            if 'Port1Out' in eventsDict:
                newPort1Out = eventsDict['Port1Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort1Out != newPort1Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort1Out = newPort1Out
                    if (self.correctResponse == 'left'):
                        self.inputEventSignal.emit(['L', 0, 1])  # left, disabled, correct
                    elif (self.correctResponse == 'right'):
                        self.inputEventSignal.emit(['L', 0, 0])  # left, disabled, wrong
                    elif (self.correctResponse == ''):
                        self.inputEventSignal.emit(['L', 0, 1])  # left, disabled, correct (used when the protocol does not make use of self.correctResponse)
            
            # Right lick sensor released
            if 'Port3Out' in eventsDict:
                newPort3Out = eventsDict['Port3Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort3Out != newPort3Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort3Out = newPort3Out
                    if (self.correctResponse == 'right'):
                        self.inputEventSignal.emit(['R', 0, 1])  # right, disabled, correct
                    elif (self.correctResponse == 'left'):
                        self.inputEventSignal.emit(['R', 0, 0])  # right, disabled, wrong
                    elif (self.correctResponse == ''):
                        self.inputEventSignal.emit(['R', 0, 1])  # right, disabled, correct (used when the protocol does not make use of self.correctResponse)

            if ('Port1In' not in eventsDict) and ('Port1Out' not in eventsDict) and ('Port3In' not in eventsDict) and ('Port3Out' not in eventsDict):
                # Since eventsDict does not contain any of the above, disable the lick lines in case they were enabled from the previous trial and the next trial started before the lick sensor was released.
                # In which case they would never get disabled and would be plotted as a continuous line until the lick sensor is touched and then released.
                self.inputEventSignal.emit([])  # Empty list will be processed as the instruction to disable the left and right lick lines.
        
            QTimer.singleShot(10, self.checkForNewInputEvent)  # Call itself every 10 ms to check again.
        
        else:
            logging.info("InputEventWorker Finished")
            self.finished.emit()

    def stopRunning(self):
        self.keepRunning = False
