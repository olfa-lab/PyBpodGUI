from PyQt5.QtCore import QObject, QThread, pyqtSignal, QTimer
import serial
import json
import tables
import os
import logging

logging.basicConfig(format="%(message)s", level=logging.INFO)


class RFIDWorker(QObject):
    mouseEnterSignal = pyqtSignal(dict)  # sends the rfid tag and protocol file to use to indicate which mouse entered and thus start the session
    mouseExitSignal = pyqtSignal()
    finished = pyqtSignal()

    def __init__(self, serialPort, scheduleFile):
        super().__init__()

        # self.rfidReader = serial.Serial(serialPort, baudrate=9600)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.checkRFID)
        self.started = False
        self.currentLevel = 0
        self.trials = 0
        self.signal = 0
        self.mouseNum = 1234
        self.funccounter = 0
        
        if not os.path.exists('records.h5'):
            self.h5file = tables.open_file(filename='records.h5', mode='w', title='Records')
            recordsTableDescDict = {
                'mouseNum': tables.UInt16Col(pos=0),
                'level': tables.UInt8Col(pos=1),
                'totalTrials': tables.UInt16Col(pos=2),
                'percentCorrect': tables.UInt16Col(pos=3)
            }
            self.table = self.h5file.create_table(where=self.h5file.root, name='recordsTable', description=recordsTableDescDict, title='Records Table')
            self.row = self.table.row
        else:
            self.h5file = tables.open_file(filename='records.h5', mode='r+')
            self.table = self.h5file.root.recordsTable
            self.row = self.table.row
        
        with open(scheduleFile, 'r') as sched:
            self.scheduleList = json.load(sched)

    def run(self):
        self.timer.start(30000)

    def checkRFID(self):
        logging.info(f"checkRFID call number {self.funccounter}")
        self.funccounter += 1
        # if (self.rfidReader.in_waiting > 0):
        #     prefix = self.rfidReader.read(size=1)
        #     if (prefix == b'M'):
        #         id_tag = self.rfidReader.read(size=5)
        #         enter = self.rfidReader.read(size=1)

        #         if enter:
        #             protocolFile = self.protocolSelector(id_tag)
        #             self.mouseEnterSignal.emit({'mouseNum': id_tag, 'protocolFile': protocolFile})
        #         else:
        #             self.mouseExitSignal.emit()

        if self.started:
            logging.info(f"commencing mouse exit signal emission number {self.signal}")
            self.mouseExitSignal.emit()
            logging.info(f"mouse exit signal number {self.signal} emitted")
            self.signal += 1
            logging.info(self.row)
            self.row['mouseNum'] = self.mouseDict['mouseNum']
            self.row['level'] = self.currentLevel
            self.row['totalTrials'] = self.trials
            self.row['percentCorrect'] = self.trials + 1
            logging.info("appending to records file")
            self.row.append()
            self.table.flush()
            self.started = False
            logging.info("ending session")
        else:
            protocolFile = self.protocolSelector(self.mouseNum)
            self.mouseDict = {'mouseNum': self.mouseNum, 'protocolFile': protocolFile}
            self.mouseEnterSignal.emit(self.mouseDict)
            self.started = True
            self.trials += 11
            self.mouseNum += 1
            
    def protocolSelector(self, mouseNum):
        levels = [row['level'] for row in self.table.where(f"mouseNum == {mouseNum}")]
        logging.info(levels)
        if (len(levels) > 0):
            currentLevel = max(levels)
            self.currentLevel = currentLevel
            row = [r for r in self.table.where(f"(mouseNum == {mouseNum}) & (level == {currentLevel})")]
            logging.info(row[0]['mouseNum'])
            self.row = row[0]
            if (row[0]['totalTrials'] < self.scheduleList[currentLevel]['totalTrials']):
                protocolFile = self.scheduleList[currentLevel]['filename'] 
            elif (row[0]['percentCorrect'] < self.scheduleList[currentLevel]['passingGrade']):
                protocolFile = self.scheduleList[currentLevel]['filename']
            else:
                try:
                    protocolFile = self.scheduleList[currentLevel + 1]['filename']
                except IndexError:
                    protocolFile = self.scheduleList[currentLevel]['filename']
            return protocolFile
        else:
            protocolFile = self.scheduleList[0]['filename']
            return protocolFile

    def stopRunning(self):
        self.timer.stop()
        self.h5file.close()
        # self.rfidReader.close()
        self.finished.emit()
