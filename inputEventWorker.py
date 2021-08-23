import time
import logging
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal


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
                    elif self.correctResponse == '':
                        self.inputEventSignal.emit(['L', 1])  # Just show green dot for the lick.


            # Right Lick
            if 'Port3In' in eventsDict:
                newPort3In = eventsDict['Port3In'][-1]
                if newPort3In != currentPort3In:  # Compare timestamps to check if its actually a new event.
                    currentPort3In = newPort3In
                    if self.correctResponse == 'right':
                        self.inputEventSignal.emit(['R', 1])  # Correct lick
                    elif self.correctResponse == 'left':
                        self.inputEventSignal.emit(['R', 0])  # Wrong lick
                    elif self.correctResponse == '':
                        self.inputEventSignal.emit(['R', 1])  # Just show green dot for the lick.


            time.sleep(0.1)  # Without this sleep, the plotter launches but is extremely unresponsive.
        logging.info("InputEventWorker Finished")
        self.finished.emit()

    def stopRunning(self):
        self.keepRunning = False
