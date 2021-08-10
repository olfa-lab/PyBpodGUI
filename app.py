import sys
import os
import time
import copy
import collections
import tables
import numpy as np
import logging
from datetime import datetime
from serial.serialutil import SerialException

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMainWindow, QMessageBox, QProgressDialog, QFileDialog)
from PyQt5.QtCore import QObject, QThread, QTime, QTimer, pyqtSignal, pyqtSlot, Qt

from main_window_ui import Ui_MainWindow
from pybpodapi.protocol import Bpod, StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
from BpodAnalogInputModule import BpodAnalogIn
import olfactometry

from saveDataWorker import SaveDataWorker
from inputEventWorker import InputEventWorker
from protocolWorker import ProtocolWorker
from streamingWorker import StreamingWorker
from resultsPlotWorker import ResultsPlotWorker
# from calibrateWaterWorker import CalibrateWaterWorker
from protocolEditorDialog import ProtocolEditorDialog
from olfaEditorDialog import OlfaEditorDialog

# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation

import pyqtgraph as pg


logging.basicConfig(format="%(message)s", level=logging.INFO)


'''
Things to do:

    * __X__ use signals/slots instead of passing references to class objects.

    * __X__ close/stop streaming figure when stop button clicked

    * __X__ make gui stop other threads when experiment finished.

    * __X__ implement data recording with pytables

    * __X__ implement water valve buttons to only open for set duration

    * __X__ solve analog module giving error that Serial1_1 is invalid name

    * __X__ make results graph show percent of left licks instead of percent correct

    * __X__ have a counter that counts number of no responses and after certain number, it aborts experiment.

    * __X__ close serial devices and threads when application exits

    * __X__ get rid of the samplingThread and let the saveDataThread do the sampling and saving to .h5 and let it collect 100 or so samples in an array and emit it to the streamingWorker whenever it gets filled instead of one sample at a time.

    * __X__ save sniff signal (voltage over time) for each trial in .h5 file

    * __X__ save timestamps of lick events for each trial in .h5 file

    * __X__ synchronize analog data with state machine timing.

    * __X__ disable buttons that should not be clicked during certain operations

    * __X__ make a separate button to connect to devices first, before starting the experiment.

    * __X__ implement calibrate water valve buttons

    * __X__ implement progress bar dialog window for calibrating water

    * __X__ fix h5 file naming so that datetime format is YYYY-MM-DD_HHMMSS

    * __X__ configure tab order for the LineEdit fields

    * __X__ implement ability to configure protocol

    * __X__ implement ability to configure odors and/or olfa json file

    * __X__ make protocolWorker read from olfa config file before starting experiment to store odors/concentrations for stimulusRandomizer

    * __X__ in olfaEditorDialog, make sure that both odor name and concentration were given for a vial before saving the file

    * _____ implement pause button

    * _____ use jonathan olfactometer code

    * _____ have a timer (in the state machine) that aborts experiment when no sniff signal for certain amount of time

    * _____ implement ability to configure flow rates

    * _____ implement ability to configure analog module

    * _____ implement serial port selection for each device with combobox that list available serial ports for user to pick

    * _____ implement validators for the line edits to restrict input values

    * _____ implement progress bar for state machine during trial run

    * _____ use pyqtgraph instead of matplotlib for the streaming plot to check if faster sampling/plotting is possible

    * _____ try using @pyqtSlot for a function to check if the thread will call it even if its running in an infinite loop.

    * _____ create a metadata for the .h5 file

    * _____ change the worker threads to use timers instead of infinite while loops

    * _____ allow user to run experiments that do not use olfactometer (currently, protocolWorker does nothing when olfaCheckBox is unchecked)

    * _____ fix issue of application crashing or does not do anything when start button is clicked again after experiment completion

    * _____ modify saveDataWorker to handle when NoSniff occurs

    * _____ use SerialException instead of BpodErrorException for when connecting to the analog input module
      

Questions to research:

    * _____ How to connect signal from one thread to a slot in another thread that is running in an infinite loop without using lambda function?

    * _____ How to block execution within a thread for a certain amount of time?

    * _____ Why does infinite loop in separate thread (without some sort of sleep interval) cause main thread to freeze or lag?

    * _____ Why does infinite loop inside a separate thread block slots from being handled?
'''


class Window(QMainWindow, Ui_MainWindow):
    stopRunningSignal = pyqtSignal()
    launchOlfaGUISignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self._connectSignalsSlots()
        self.olfas = None
        self.adc = None
        self.myBpod = None
        self.olfaSerialPort = 'COM5'
        self.adcSerialPort = 'COM6'
        self.bpodSerialPort = 'COM7'
        self.analogInputModulePortLineEdit.setText(self.adcSerialPort)
        self.bpodPortLineEdit.setText(self.bpodSerialPort)
        self.streaming = StreamingWorker(plotLength=1000)
        self.streamingGroupBoxVLayout.addWidget(self.streaming.getFigure())
        self.streaming.setupAnimation()
        self.saveDataWorker = None
        self.mouseNumber = None
        self.rigLetter = None
        self.numTrials = None
        self.experimentName = None
        self.leftWaterValve = 1
        self.finalValve = 2
        self.rightWaterValve = 3
        self.leftWaterValveDuration = 100  # milliseconds
        self.leftWaterValveDurationLineEdit.setText(str(self.leftWaterValveDuration))
        self.rightWaterValveDuration = 100  # milliseconds
        self.rightWaterValveDurationLineEdit.setText(str(self.rightWaterValveDuration))
        self.resultsPlot = ResultsPlotWorker()
        self.resultsPlotVLayout.addWidget(self.resultsPlot.getWidget())
        self.protocolFileName = ''
        self.olfaConfigFileName = ''

        self.startButton.setEnabled(False)  # do not enable start button until user connects devices.
        self.finalValveButton.setEnabled(False)
        self.leftWaterValveButton.setEnabled(False)
        self.rightWaterValveButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(False)
        self.calibRightWaterButton.setEnabled(False)

    def _connectSignalsSlots(self):
        self.olfaButton.clicked.connect(self._launchOlfaGUI)
        self.startButton.clicked.connect(self._runTask)
        self.stopButton.clicked.connect(self._endTask)
        self.finalValveButton.clicked.connect(self._toggleFinalValve)
        self.leftWaterValveButton.clicked.connect(self._toggleLeftWaterValve)
        self.rightWaterValveButton.clicked.connect(self._toggleRightWaterValve)
        self.calibLeftWaterButton.clicked.connect(self._calibrateLeftWaterValve)
        self.calibRightWaterButton.clicked.connect(self._calibrateRightWaterValve)
        self.connectDevicesButton.clicked.connect(self._connectDevices)
        self.actionNew.triggered.connect(self._launchProtocolEditor)
        self.actionOpen.triggered.connect(self.openProtocolFileNameDialog)
        self.actionSelectConfigFile.triggered.connect(self.openOlfaConfigFileNameDialog)
        self.olfaConfigButton.clicked.connect(self._launchOlfaEditor)

        self.mouseNumberLineEdit.editingFinished.connect(self._recordMouseNumber)
        self.rigLetterLineEdit.editingFinished.connect(self._recordRigLetter)
        self.nTrialsLineEdit.editingFinished.connect(self._recordNumTrials)
        self.leftWaterValveDurationLineEdit.editingFinished.connect(self._recordLeftWaterValveDuration)
        self.rightWaterValveDurationLineEdit.editingFinished.connect(self._recordRightWaterValveDuration)
        self.bpodPortLineEdit.editingFinished.connect(self._recordBpodSerialPort)
        self.analogInputModulePortLineEdit.editingFinished.connect(self._recordAnalogInputModuleSerialPort)

    def _launchOlfaGUI(self):
        if self.olfaConfigFileName:
            try:
                self.olfas = olfactometry.Olfactometers(config_obj=self.olfaConfigFileName)
                self.olfas.show()
            except SerialException:
                if self.olfas:
                    self.olfas.close_serials()  # close serial ports and let the user try again.
                    del self.olfas
                    self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.
                    QMessageBox.warning(self, "Error", "Please try again.")
        else:
            QMessageBox.warning(self, "Warning", "Please select an olfa config file first! Go to 'Olfactometer' menu > 'Select config file'")

    def _launchOlfaEditor(self):
        self.olfaEditor = OlfaEditorDialog(self.olfaConfigFileName)
        self.olfaEditor.show()

    def _launchProtocolEditor(self):
        if self.myBpod is not None:
            sma = StateMachine(self.myBpod)
            events = sma.hardware.channels.event_names
            outputs = sma.hardware.channels.output_channel_names
            self.protocolEditor = ProtocolEditorDialog(events, outputs, self.protocolFileName)
            self.protocolEditor.show()
        else:
            QMessageBox.warning(self, "Warning", "Please connect to Bpod first. Click the 'Connect Devices' button.")

    def openProtocolFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","JSON Files (*.json)", options=options)
        if fileName:
            self.protocolFileName = fileName
            self.protocolFileLineEdit.setText(fileName)
            logging.info(f"The file {fileName} has been loaded.")

    def openOlfaConfigFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(self,"QFileDialog.getOpenFileName()", "","JSON Files (*.json)", options=options)
        if fileName:
            self.olfaConfigFileName = fileName
            self.olfaFileLineEdit.setText(fileName)
            logging.info(f"The file {fileName} has been loaded.")

    def configureAnalogModule(self):
        self.adc.setSamplingRate(1000)
        self.adc.setNactiveChannels(1)
        # TODO: instead of passing a list, make it such that the user specifies the range of a specific channel by passing an int for the channel and a string for the range.
        self.adc.setInputRange(['-5V:5V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V', '-10V:10V'])
        self.adc.setStream2USB([1, 0, 0, 0, 0, 0, 0, 0])
        self.adc.setSMeventsEnabled([1, 0, 0, 0, 0, 0, 0, 0])
        self.adc.setThresholds([0, 10, 10, 10, 10, 10, 10, 10])  # The default threshold is already set to 10V during initialization, but still need to specify it for the other channels.
        self.adc.setResetVoltages([1, -10, -10, -10, -10, -10, -10, -10])

    def startAnalogModule(self):
        self.adc.startReportingEvents()
        # self.adc.startLogging()
        self.adc.startUSBStream()

    def stopAnalogModule(self):
        logging.info("attempting to stop USB streaming")
        self.adc.stopUSBStream()
        # for i in range(5):
        #     # Try to stop it 5 times because usually the first two tries fail.
        #     logging.info(f'trying to stop logging: trial {i + 1}')
        #     try:
        #         self.adc.stopLogging()
        #         logging.info("analog module stopped logging to SD card")
        #         break
        #     except BpodErrorException:
        #         logging.info("could not stop logging")

        # logging.info("attempting to stop reporting events")
        # self.adc.stopReportingEvents()  # Not necessary to stop event reporting. Will not make difference. And also usually fails first two tries.

    
    # def _getSDCardLog(self):
    #     adcSignal = self.adc.getData()
    #     logging.info('got analog data. here is what is got:')
    #     logging.info(adcSignal)
    #     self.saveDataWorker.receiveAnalogData(adcSignal)
    def _connectDevices(self):
        try:
            if self.analogInputModuleCheckBox.isChecked():
                self.adc = BpodAnalogIn(serial_port=self.adcSerialPort)
        except BpodErrorException:
            QMessageBox.warning(self, "Warning", "Cannot connect analog input module! Check that serial port is correct!")
            return

        # try:
        #     if self.olfaCheckBox.isChecked():
        #         self.olfas = olfactometry.Olfactometers()  # I might need to create the olfactometer object inside the protocolWorker thread.
        #         # self.olfas = Cassette(self.olfaConfigDict)
        # except IOError:
        #     QMessageBox.warning(self, "Warning", "Cannot connect to olfactometer! Check that serial port is correct!")
        #     return

        try:
            self.myBpod = Bpod(serial_port=self.bpodSerialPort)
        except (SerialException, UnicodeDecodeError):
            if self.myBpod:
                self.myBpod.close()
                del self.myBpod
                self.myBpod = None
            QMessageBox.warning(self, "Warning", "Cannot connect to bpod! Check that serial port is correct!")
            return

        self.startButton.setEnabled(True)  # This means successful connection attempt for enabled devices.
        self.connectDevicesButton.setEnabled(False)  # Disable to prevent clicking again.
        self.connectDevicesButton.setText("Connected")

        self.finalValveButton.setEnabled(True)
        self.leftWaterValveButton.setEnabled(True)
        self.rightWaterValveButton.setEnabled(True)
        self.calibLeftWaterButton.setEnabled(True)
        self.calibRightWaterButton.setEnabled(True)

    def _runTask(self):
        if self.mouseNumber is None:
            QMessageBox.warning(self, "Warning", "Please enter mouse number!")
            return
        elif self.rigLetter is None:
            QMessageBox.warning(self, "Warning", "Please enter rig letter!")
            return
        elif self.numTrials is None:
            QMessageBox.warning(self, "Warning", "Please enter number of trials for this experiment!")
            return
        elif self.protocolFileName is '':
            QMessageBox.warning(self, "Warning", "Please load a protocol file. Go to 'File' > 'Open'.")
            return

        # Safety check to close and delete the main thread's olfactometer (if in use or was in use) before running the protocolWorker's thread
        # so that the protocolWorker's thread can access the olfactometer's serial port if the user enables the olfactometer for the experiment.
        if self.olfas:
            self.olfas.close_serials()
            del self.olfas
            self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.

        self.configureAnalogModule()
        self.startAnalogModule()
        self._runSaveDataThread()
        self._runInputEventThread()
        self._runProtocolThread()

        if not self.streaming.startAnimation():
            self.streaming.resumeAnimation()

        self.startButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(False)
        self.calibRightWaterButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        if self.olfaCheckBox.isChecked():
            self.olfaButton.setEnabled(False)  # Disable the alfa GUI button if the olfactometer will be used for the experiment by the protocolWorker's thread.
            # The user can still use the olfactometer GUI during an experiment (i.e. for manual control) but must uncheck the olfa check box to let
            # the protocolWorker's thread know not to use it. Only one object can access a serial port at any given time.

    def _endTask(self):
        self.streaming.pauseAnimation()
        self.stopAnalogModule()
        # self._getSDCardLog()
        self.stopRunningSignal.emit()
        logging.info("stopRunningSignal emitted")
        
        # self._checkIfRunning()  # causes unhandled python exception when called twice. Check definition for details.
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(True)
        self.calibRightWaterButton.setEnabled(True)
        if self.olfaCheckBox.isChecked():
            self.olfaButton.setEnabled(True)  # re-enable the olfa GUI button after the experiment completes.
        self._experimentCompleteDialog()

    def _checkIfRunning(self):
        # When this function is called for the first time upon clicking the stop button
        # to stop the threads, it works without errors or raising exceptions and will
        # return true for all except 'self.saveDataThread.isRunning()' which will be
        # false. Not sure why any of the threads would still be running when they should
        # have quit, but this is another issue to be investigated some other time.

        # However, when this function is called the second time (because the 'protocolWorker.finished'
        # signal connects to 'self._endTask' function and so the 'self._endTask' function will be 
        # called twice when the user clicks the stop button) there will be an error when you try to
        # call 'self.inputEventThread.isRunning()'. My logging.info stops right before that line
        # so my guess is that it is causing an error, as if the inputEventThread does not have an
        # method called 'isRunning'. Maybe its because the thread was deleted and thus does not have
        # that 'isRunning' method anymore, but calling 'self.inputEventThread.isRunning()' even before
        # starting the thread will still work without error (it will return False). Putting it inside
        # a try/except clause with 'AttributeError' as the exception does NOT trigger the except clause.
        # But when I use 'RuntimeError' as the exception, the except clause DOES get triggered.
        logging.info("Checking if threads are still running...")
        if self.inputEventThread:
            logging.info("self.inputEventThread exists. Its type is...")
            logging.info(type(self.inputEventThread))
            try:
                if not self.inputEventThread.isRunning():
                    logging.info("inputEventThread no longer running")
                else:
                    logging.info("ERROR inputEventThread is still running")
            except RuntimeError:
                logging.info("AttributeError: no method named 'isRunning'")
        else:
            logging.info("self.inputEventThread does not exist")
        if not self.samplingThread.isRunning():
            logging.info("samplingThread no longer running")
        else:
            logging.info("ERROR SamplingThread is still running")
        if not self.protocolThread.isRunning():
            logging.info("protocolThread no longer running")
        else:
            logging.info("ERROR protocolThread is still running")
        if not self.saveDataThread.isRunning():
            logging.info("ERROR saveDataThread is still runnning")
        else:
            logging.info("saveDataThread no longer running")

    def closeDevices(self):
        if self.adc is not None:
            self.adc.close()
            logging.info('Analog Input Module closed')
        # if self.olfas is not None:
        #     self.olfas.close_serials()
        #     logging.info('olfas close_serials')
        #     self.olfas.close()
        #     logging.info('olfas close')
        if self.myBpod is not None:
            self.myBpod.close()
            logging.info('Bpod closed')

    def _toggleFinalValve(self):
        if self.myBpod is not None:
            if self.finalValveButton.isChecked():
                self._openValve(self.finalValve)
            else:
                self._closeValve(self.finalValve)

    def _toggleLeftWaterValve(self):
        if self.myBpod is not None:
            self._openValve(self.leftWaterValve)
            QTimer.singleShot(self.leftWaterValveDuration, lambda: self._closeValve(self.leftWaterValve))

    def _toggleRightWaterValve(self):
        if self.myBpod is not None:
            self._openValve(self.rightWaterValve)
            QTimer.singleShot(self.rightWaterValveDuration, lambda: self._closeValve(self.rightWaterValve))

    def _openValve(self, channelNum):
        if self.myBpod is not None:
            self.myBpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=1)

    def _closeValve(self, channelNum):
        if self.myBpod is not None:
            self.myBpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=0)

    def _calibrateLeftWaterValve(self):
        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.calibLeftWaterButton.setEnabled(False)
            self.calibRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._calibrateLeftWaterValveToggler)

            self.progress = QProgressDialog("Calibrating left water valve...", "Cancel", 0, 100, self)
            self.progress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.leftWaterValveDuration)

    def _calibrateLeftWaterValveToggler(self):
        if self.progress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.progress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.leftWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.leftWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.progress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _calibrateRightWaterValve(self):
        # self._runCalibrateWaterThread(self.rightWaterValve, self.rightWaterValveDuration)

        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.calibLeftWaterButton.setEnabled(False)
            self.calibRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._calibrateRightWaterValveToggler)

            self.progress = QProgressDialog("Calibrating right water valve...", "Cancel", 0, 100, self)
            self.progress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.rightWaterValveDuration)

    def _calibrateRightWaterValveToggler(self):
        if self.progress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.progress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.rightWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.rightWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.progress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _recordMouseNumber(self):
        self.mouseNumber = self.mouseNumberLineEdit.text()

    def _recordRigLetter(self):
        self.rigLetter = self.rigLetterLineEdit.text()

    def _recordNumTrials(self):
        self.numTrials = int(self.nTrialsLineEdit.text())

    def _recordLeftWaterValveDuration(self):
        self.leftWaterValveDuration = int(self.leftWaterValveDurationLineEdit.text())
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftWaterDuration(self.leftWaterValveDuration)

    def _recordRightWaterValveDuration(self):
        self.rightWaterValveDuration = int(self.rightWaterValveDurationLineEdit.text())
        if self.protocolWorker is not None:
            self.protocolWorker.setRightWaterDuration(self.rightWaterValveDuration)

    def _recordBpodSerialPort(self):
        self.bpodSerialPort = self.bpodPortLineEdit.text()

    def _recordOlfaSerialPort(self):
        self.olfaSerialPort = self.olfaPortLineEdit.text()

    def _recordAnalogInputModuleSerialPort(self):
        self.adcSerialPort = self.analogInputModulePortLineEdit.text()

    def _updateCurrentState(self, stateName):
        self.currentStateLineEdit.setText(stateName)

    def _updateResponseResult(self, result):
        self.responseResultLineEdit.setText(result)

    def _updateSessionTotals(self, totalsDict):
        logging.info('attempting to update session totals')
        self.totalRewardsLineEdit.setText(str(totalsDict['totalRewards']))
        self.totalWrongLicksLineEdit.setText(str(totalsDict['totalPunishes']))
        self.totalNoResponsesLineEdit.setText(str(totalsDict['totalNoResponses']))
        self.totalPercentCorrectLineEdit.setText(str(totalsDict['totalPercentCorrect']))

    def _updateCurrentTrialInfo(self, trialInfoDict):
        trialInfo = trialInfoDict
        # Check if not empty.
        if trialInfo:
            self.trialLineEdit.setText("{0} of {1}".format(trialInfo['currentTrialNum'], trialInfo['nTrials']))
            self.correctResponseLineEdit.setText(trialInfo['correctResponse'])
            self.itiLineEdit.setText(str(trialInfo['currentITI']))
            self.odorNameLineEdit.setText(trialInfo['currentOdorName'])
            self.odorConcentrationLineEdit.setText(str(trialInfo['currentOdorConc']))
            self.currentFlowLineEdit.setText(str(trialInfo['currentFlow']))

    def _updateResultsPlot(self, flowResultsDict):
        if not self.resultsPlot.isXAxisSetup():
            self.resultsPlot.setupXaxis(flowResultsDict)

        xValues = []
        yValues = []
        index = 0

        # This is to plot percent correct

        # for k, v in flowResultsDict.items():
        #     numCorrect = v['Correct']
        #     numTotal = v['Total']
        #     if not (numTotal == 0):
        #         percent = round((float(numCorrect) / float(numTotal) * 100), 2)
        #     else:
        #         percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
        #     xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
        #     yValues.append(percent)
        #     index += 1

        # This is to plot percent left licks

        for k, v in flowResultsDict.items():
            numLeft = v['left']
            numTotal = v['Total']
            if not (numTotal == 0):
                percent = round((float(numLeft) / float(numTotal) * 100), 2)
            else:
                percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
            xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
            yValues.append(percent)
            index += 1
        self.resultsPlot.updatePlot(xValues, yValues)

    def _noResponseAbortDialog(self):
        QMessageBox.information(self, "Notice", "Session aborted due to too many consecutive no responses.")

    def _experimentCompleteDialog(self):
        QMessageBox.information(self, "Success", "Experiment finished!")

    def _cannotConnectOlfaDialog(self):
        # Since the ProtocolWorker's self.olfas object cannot access the serial port, maybe it is current in use by the main thread.
        # So check if main thread's self.olfas exists and if so, close the serial port and delete the object.
        if self.olfas:
            self.olfas.close_serials()  # close serial ports and let the user try again.
            del self.olfas
        QMessageBox.warning(self, "Warning", "Cannot connect to olfactometer! Check that serial port is correct and try again.")

    def _invalidFileDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Invalid protocol file or olfa config file selected. Experiment aborted.\
            \nThe following key was not found in its respective .json file and thus caused a KeyError:\
            \n{error}")

    def _runInputEventThread(self):
        logging.info(f"from _runInputEventThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.inputEventThread = QThread()
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")
        self.inputEventWorker = InputEventWorker(self.myBpod)
        self.inputEventWorker.moveToThread(self.inputEventThread)
        self.inputEventThread.started.connect(self.inputEventWorker.run)
        self.inputEventWorker.finished.connect(self.inputEventThread.quit)
        self.inputEventWorker.finished.connect(self.inputEventWorker.deleteLater)
        self.inputEventThread.finished.connect(self.inputEventThread.deleteLater)
        self.inputEventWorker.inputEventSignal.connect(self.streaming.setInputEvent)
        self.stopRunningSignal.connect(lambda: self.inputEventWorker.stopRunning())  # Need to use lambda, to explicitly make function call (from the main thread). Because the inputEventThread will never call it since its in a infinite loop.
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")
        logging.info("attempting to start inputEventThread")
        self.inputEventThread.start()
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")

    def _runSaveDataThread(self):
        logging.info(f"from _runSaveDataThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.saveDataThread = QThread()
        self.saveDataWorker = SaveDataWorker(self.mouseNumber, self.rigLetter, self.adc)
        self.saveDataWorker.moveToThread(self.saveDataThread)
        self.saveDataThread.started.connect(self.saveDataWorker.run)
        self.saveDataWorker.finished.connect(self.saveDataThread.quit)
        self.saveDataWorker.finished.connect(self.saveDataWorker.deleteLater)
        self.saveDataThread.finished.connect(self.saveDataThread.deleteLater)
        self.saveDataWorker.analogDataSignal.connect(self.streaming.getData)
        self.stopRunningSignal.connect(lambda: self.saveDataWorker.stopRunning())
        self.saveDataThread.start()
        logging.info(f"saveDataThread running? {self.saveDataThread.isRunning()}")
  
    def _runProtocolThread(self):
        logging.info(f"from _runProtocolThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.protocolThread = QThread()
        self.protocolWorker = ProtocolWorker(self.myBpod, self.protocolFileName, self.olfaConfigFileName, self.olfaCheckBox.isChecked(), self.numTrials)
        self.protocolWorker.moveToThread(self.protocolThread)
        self.protocolThread.started.connect(self.protocolWorker.run)
        self.protocolWorker.finished.connect(self.protocolThread.quit)
        self.protocolWorker.finished.connect(self._endTask)  # This serves to stop the other threads when the protocol thread completes all trials.
        self.protocolWorker.finished.connect(self.protocolWorker.deleteLater)
        self.protocolThread.finished.connect(self.protocolThread.deleteLater)
        self.protocolWorker.trialStartSignal.connect(lambda x: self.inputEventWorker.newTrialSlot(x))
        self.protocolWorker.newStateSignal.connect(self._updateCurrentState)
        self.protocolWorker.responseResultSignal.connect(self._updateResponseResult)
        self.protocolWorker.newTrialInfoSignal.connect(self._updateCurrentTrialInfo)  # This works without lambda because 'self._updateCurrentTrialInfo' is in the main thread.
        self.protocolWorker.flowResultsCounterDictSignal.connect(self._updateResultsPlot)
        self.protocolWorker.totalsDictSignal.connect(self._updateSessionTotals)
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.saveDataWorker.receiveInfoDict(x))  # 'x' is the dictionary parameter emitted from 'saveTrialDataDictSignal' and passed into 'receiveInfoDict(x)'
        self.protocolWorker.saveEndOfSessionDataSignal.connect(lambda x: self.saveDataWorker.receiveFinalResultsDict(x))  # 'x' is the dictionary parameter emitted from 'saveEndOfSessionDataSignal' and passed into 'receiveFinalResultsDict(x)'
        # self.protocolWorker.startSDCardLoggingSignal.connect(self._startSDCardLogging)
        # self.protocolWorker.stopSDCardLoggingSignal.connect(self._stopSDCardLogging)
        self.protocolWorker.noResponseAbortSignal.connect(self._noResponseAbortDialog)
        self.protocolWorker.olfaNotConnectedSignal.connect(self._cannotConnectOlfaDialog)
        self.protocolWorker.invalidFileSignal.connect(self._invalidFileDialog)
        self.stopRunningSignal.connect(lambda: self.protocolWorker.stopRunning())
        self.protocolThread.start()
        logging.info(f"protocolThread running? {self.protocolThread.isRunning()}")

    # def _runCalibrateWaterThread(self, valveNum, duration):
    #     self.calibrateWaterThread = QThread()
    #     self.calibrateWaterWorker = CalibrateWaterWorker(valveNum=valveNum, duration=duration)
    #     self.calibrateWaterWorker.moveToThread(self.calibrateWaterThread)
    #     self.calibrateWaterThread.started.connect(self.calibrateWaterWorker.run)
    #     self.calibrateWaterWorker.finished.connect(self.calibrateWaterThread.quit)
    #     self.calibrateWaterWorker.finished.connect(self.calibrateWaterWorker.deleteLater)
    #     self.calibrateWaterThread.finished.connect(self.calibrateWaterThread.deleteLater)
    #     self.calibrateWaterWorker.openValveSignal.connect(lambda: self._openValve(valveNum))
    #     self.calibrateWaterWorker.closeValveSignal.connect(lambda: self._closeValve(valveNum))
    #     self.calibrateWaterThread.start()
    #     logging.info("calibrateWaterThread start")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Window()
    win.show()
    status = app.exec()
    win.closeDevices()
    sys.exit(status)
