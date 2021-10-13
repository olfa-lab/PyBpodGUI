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
        self.currentPort1In = 0
        self.currentPort2In = 0
        self.currentPort3In = 0
        self.currentPort4In = 0
        self.currentPort1Out = 0
        self.currentPort2Out = 0
        self.currentPort3Out = 0
        self.currentPort4Out = 0
        self.inputPorts = [0, 0, 0, 0]

    def run(self):
        logging.info("InputEventThread is running")
        self.checkForNewInputEvent()

    def checkForNewInputEvent(self):
        if self.keepRunning:
            try:
                eventsDict = self.myBpod.session.current_trial.get_all_timestamps_by_event()
            except AttributeError:
                eventsDict = {}  # This means the trial has not started yet.

            if not eventsDict:  # If it is empty.
                self.inputPorts = [0, 0, 0, 0]  # reset valuse to zero at the start of the next trial so that if a
                                                # sensor was triggered but the trial ended before the sensor was
                                                # released, the streaming plot will continue to show a continuous
                                                # line for the input event.
            
            if 'Port1In' in eventsDict:
                newPort1In = eventsDict['Port1In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort1In != newPort1In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort1In = newPort1In  # If so, record the newest event.
                    self.inputPorts[0] = 1  # Set port 1's element to 1 to indicate the input sensor was triggered.

            if 'Port2In' in eventsDict:
                newPort2In = eventsDict['Port2In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort2In != newPort2In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort2In = newPort2In  # If so, record the newest event.
                    self.inputPorts[1] = 1  # Set port 2's element to 1 to indicate the input sensor was triggered.

            if 'Port3In' in eventsDict:
                newPort3In = eventsDict['Port3In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort3In != newPort3In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort3In = newPort3In  # If so, record the newest event.
                    self.inputPorts[2] = 1  # Set port 3's element to 1 to indicate the input sensor was triggered.
            
            if 'Port4In' in eventsDict:
                newPort4In = eventsDict['Port4In'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort4In != newPort4In):  # Compare timestamps to check if its actually a new event.
                    self.currentPort4In = newPort4In  # If so, record the newest event.
                    self.inputPorts[3] = 1  # Set port 4's element to 1 to indicate the input sensor was triggered.

            if 'Port1Out' in eventsDict:
                newPort1Out = eventsDict['Port1Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort1Out != newPort1Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort1Out = newPort1Out  # If so, record the newest event.
                    self.inputPorts[0] = 0  # Set port 1's element to 0 to indicate the input sensor was released.
                    
            if 'Port2Out' in eventsDict:
                newPort2Out = eventsDict['Port2Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort2Out != newPort2Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort2Out = newPort2Out  # If so, record the newest event.
                    self.inputPorts[1] = 0  # Set port 2's element to 0 to indicate the input sensor was released.
            
            if 'Port3Out' in eventsDict:
                newPort3Out = eventsDict['Port3Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort3Out != newPort3Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort3Out = newPort3Out  # If so, record the newest event.
                    self.inputPorts[2] = 0  # Set port 3's element to 0 to indicate the input sensor was released.
                    
            if 'Port4Out' in eventsDict:
                newPort4Out = eventsDict['Port4Out'][-1]  # latest addition to the list of timestamps.
                if (self.currentPort4Out != newPort4Out):  # Compare timestamps to check if its actually a new event.
                    self.currentPort4Out = newPort4Out  # If so, record the newest event.
                    self.inputPorts[3] = 0  # Set port 4's element to 0 to indicate the input sensor was released.
        
            self.inputEventSignal.emit(self.inputPorts)
            
            QTimer.singleShot(10, self.checkForNewInputEvent)  # Call itself every 10 ms to check again.
        
        else:
            logging.info("InputEventWorker Finished")
            self.finished.emit()

    def stopRunning(self):
        self.keepRunning = False
