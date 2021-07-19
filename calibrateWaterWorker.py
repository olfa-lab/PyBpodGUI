from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal


class CalibrateWaterWorker(QObject):
    openValveSignal = pyqtSignal(int)
    closeValveSignal = pyqtSignal(int)
    finished = pyqtSignal()

    def __init__(self, valveNum, duration):
        super(CalibrateWaterWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.valveNum = valveNum
        self.duration = duration
        self.counter = 0

    def run(self):
        while (self.counter < 100):
            self.openValveSignal.emit(self.valveNum)
            QThread.msleep(self.duration)  # According to Qt documentation, this blocking method does not guarantee accurate timing.
            self.closeValveSignal.emit(self.valveNum)
            QThread.msleep(100)
            self.counter += 1
        
        self.finished.emit()
