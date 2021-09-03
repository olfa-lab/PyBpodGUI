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
    QApplication, QDialog, QMainWindow, QMessageBox, QProgressDialog, QFileDialog, QMdiSubWindow)
from PyQt5.QtCore import QObject, QThread, QTime, QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent

from main_window_ui_2 import Ui_MainWindow
from pybpodapi.protocol import Bpod, StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
from BpodAnalogInputModule import AnalogInException, BpodAnalogIn
import olfactometry

from saveDataWorker import SaveDataWorker
from inputEventWorker import InputEventWorker
from protocolWorker import ProtocolWorker
# from streamingWorker import StreamingWorker
from newStreamingWorker import StreamingWorker
from flowUsagePlotWorker import FlowUsagePlotWorker
from resultsPlotWorker import ResultsPlotWorker
# from calibrateWaterWorker import CalibrateWaterWorker
from protocolEditorDialog import ProtocolEditorDialog
from olfaEditorDialog import OlfaEditorDialog
from analogInputSettingsDialog import AnalogInputSettingsDialog

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
    
    * __X__ implement ability to configure flow rates

    * __X__ go back to the ITI state at the end of every trial so that the user can see more lick events instead of only one

    * __X__ implement ability to configure analog module

    * __X__ use SerialException instead of BpodErrorException for when connecting to the analog input module

    * __X__ allow user to run experiments without analog input (modify saveDataWorker to not save analog data, and do not plot a signal)

    * __X__ allow user to run experiments that do not use olfactometer

    * __X__ make the ITI user-adjustable.

    * __X__ implement progress bar for state machine during trial run

    * _____ implement pause button

    * _____ use jonathan olfactometer code

    * _____ have a timer (in the state machine) that aborts experiment when no sniff signal for certain amount of time

    * _____ implement serial port selection for each device with combobox that list available serial ports for user to pick

    * _____ implement validators for the line edits to restrict input values

    * _____ make the streaming plotter run faster/smoother (maybe try pyqtgraph or blitting)

    * _____ try using @pyqtSlot for a function to check if the thread will call it even if its running in an infinite loop.

    * _____ create a metadata for the .h5 file

    * _____ change the worker threads to use timers instead of infinite while loops

    * _____ fix issue of application crashing or does not do anything when start button is clicked again after experiment completion

    * _____ modify saveDataWorker to handle KeyErrors and TypeErrors for when different protocols are used or when olfactometer is not used.

    * _____ show the number of times each flow rate and odor was used throughout the experiment, either with a plot or with QLineEdit fields.

    * _____ before aborting the experiment due to too many consecutive No Response results, create an optional feature that opens the water valves for a few milliseconds to attempt to re-motivate the mouse

    * _____ make the No Response cutoff user-adjustable and allow it to be disabled.

    * _____ make a feature to manually choose what flow rate or what correct response will be for the next trial to de-bias

    * _____ get rid of variables that hold the value/text in fields like lineEdits, spinBoxes, and comboBoxes because it is redundant. 

Questions to research:

    * _____ How to connect signal from one thread to a slot in another thread that is running in an infinite loop without using lambda function?

    * _____ How to block execution within a thread for a certain amount of time?

    * _____ Why does infinite loop in separate thread (without some sort of sleep interval) cause main thread to freeze or lag?

    * _____ Why does infinite loop inside a separate thread block slots from being handled?

    * _____ When a signal is connected to multiple slots, does pyqt execute all of those slots simultaneously or sequentially?
'''


class MyQMdiSubWindow(QMdiSubWindow):
    '''
    I re-implemented the QMdiSubWindow class by sub-classing it into my own version that contains a 'closed' signal
    that gets emitted whenever the subwindow is closed. The original QMdiSubWindow implementation does not have such
    notifier signal, which is why I created this implementation. I override the original class's closeEvent method
    so it emits the close signal when the subwindow is closed.
    '''

    closed = pyqtSignal(str)

    # This method is the result of VScode's auto-complete text. I only wrote the line that emits the closed signal.
    def closeEvent(self, closeEvent: QCloseEvent) -> None:
        self.closed.emit(self.objectName())
        return super().closeEvent(closeEvent)

    # Out of curiosity, I tried this version of the above method instead, and it works the same.
    # def closeEvent(self, closeEvent):
    #     self.closed.emit(self.objectName())
    #     closeEvent.accept()


class Window(QMainWindow, Ui_MainWindow):
    stopRunningSignal = pyqtSignal()
    # launchOlfaGUISignal = pyqtSignal()

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
        self.saveDataWorker = None
        self.mouseNumber = None
        self.rigLetter = None
        self.numTrials = self.nTrialsSpinBox.value()
        self.noResponseCutoff = self.noResponseCutoffSpinBox.value()
        self.noResponseCutoffSpinBox.setMaximum(self.numTrials)
        self.autoWaterCutoff = self.autoWaterCutoffSpinBox.value()
        self.autoWaterCutoffSpinBox.setMaximum(self.noResponseCutoff - 1)
        self.experimentName = None
        self.itiMin = self.itiMinSpinBox.value()
        self.itiMax = self.itiMaxSpinBox.value()
        self.itiMinSpinBox.setMaximum(self.itiMax)  # I do not want the itiMinSpinBox to be higher than the itiMaxSpinBox's current value.
        self.itiMaxSpinBox.setMinimum(self.itiMin)  # I do not want the itiMaxSpinBox to be lower than the itiMinSpinBox's current value.
        self.leftWaterValve = 1
        self.finalValve = 2
        self.rightWaterValve = 3
        self.leftWaterValveDuration = self.leftWaterValveDurationSpinBox.value()
        self.rightWaterValveDuration = self.rightWaterValveDurationSpinBox.value()
        self.protocolFileName = ''
        self.olfaConfigFileName = ''
        self.analogInputSettings = AnalogInputSettingsDialog()
        self.protocolWorker = None

        self.startButton.setEnabled(False)  # do not enable start button until user connects devices.
        self.finalValveButton.setEnabled(False)
        self.leftWaterValveButton.setEnabled(False)
        self.rightWaterValveButton.setEnabled(False)
        self.calibLeftWaterButton.setEnabled(False)
        self.calibRightWaterButton.setEnabled(False)

        self.currentTrialSubWindow = MyQMdiSubWindow()
        self.currentTrialSubWindow.closed.connect(self._updateViewMenu)
        self.currentTrialSubWindow.setObjectName("currentTrialSubWindow")
        self.currentTrialSubWindow.setWidget(self.currentTrialSubwindowWidget)
        self.currentTrialSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.currentTrialSubWindow.resize(720, 230)
        self.mdiArea.addSubWindow(self.currentTrialSubWindow)

        self.streaming = StreamingWorker(maxt=20, dt=0.001)
        self.streamingSubWindow = MyQMdiSubWindow()
        self.streamingSubWindow.closed.connect(self._updateViewMenu)
        self.streamingSubWindow.setObjectName("streamingSubWindow")
        self.streamingSubWindow.setWidget(self.streaming.getFigure())
        self.streamingSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.streamingSubWindow.resize(1000, 300)
        self.mdiArea.addSubWindow(self.streamingSubWindow)

        self.resultsPlot = ResultsPlotWorker()
        self.resultsPlotSubWindow = MyQMdiSubWindow()
        self.resultsPlotSubWindow.closed.connect(self._updateViewMenu)
        self.resultsPlotSubWindow.setObjectName("resultsPlotSubWindow")
        self.resultsPlotSubWindow.setWidget(self.resultsPlot.getWidget())
        self.resultsPlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.resultsPlotSubWindow.resize(300, 300)
        self.mdiArea.addSubWindow(self.resultsPlotSubWindow)

        self.flowUsagePlot = FlowUsagePlotWorker()
        self.flowUsagePlotSubWindow = MyQMdiSubWindow()
        self.flowUsagePlotSubWindow.closed.connect(self._updateViewMenu)
        self.flowUsagePlotSubWindow.setObjectName("flowUsagePlotSubWindow")
        self.flowUsagePlotSubWindow.setWidget(self.flowUsagePlot.getWidget())
        self.flowUsagePlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.flowUsagePlotSubWindow.resize(330, 300)
        self.mdiArea.addSubWindow(self.flowUsagePlotSubWindow)

    def _connectSignalsSlots(self):
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
        self.actionSelectOlfaConfigFile.triggered.connect(self.openOlfaConfigFileNameDialog)
        self.actionConfigureOlfaSettings.triggered.connect(self._launchOlfaEditor)
        self.actionConfigureAnalogInSettings.triggered.connect(self._launchAnalogInputSettings)
        self.actionLaunchOlfaGUI.triggered.connect(self._launchOlfaGUI)
        self.actionViewStreaming.toggled.connect(self._viewStreamingSubWindow)
        self.actionViewResultsPlot.toggled.connect(self._viewResultsPlotSubWindow)
        self.actionViewCurrentTrialInfo.toggled.connect(self._viewCurrentTrialSubWindow)
        self.actionViewFlowUsagePlot.toggled.connect(self._viewFlowUsagePlotSubWindow)

        self.mouseNumberLineEdit.editingFinished.connect(self._recordMouseNumber)
        self.rigLetterLineEdit.editingFinished.connect(self._recordRigLetter)
        self.bpodPortLineEdit.editingFinished.connect(self._recordBpodSerialPort)
        self.analogInputModulePortLineEdit.editingFinished.connect(self._recordAnalogInputModuleSerialPort)
        
        self.nTrialsSpinBox.valueChanged.connect(self._recordNumTrials)
        self.leftWaterValveDurationSpinBox.valueChanged.connect(self._recordLeftWaterValveDuration)
        self.rightWaterValveDurationSpinBox.valueChanged.connect(self._recordRightWaterValveDuration)
        self.itiMinSpinBox.valueChanged.connect(self._recordMinITI)
        self.itiMaxSpinBox.valueChanged.connect(self._recordMaxITI)
        self.noResponseCutoffSpinBox.valueChanged.connect(self._recordNoResponseCutoff)
        self.autoWaterCutoffSpinBox.valueChanged.connect(self._recordAutoWaterCutoff)

    def _updateViewMenu(self, objectName):
        if (objectName == self.streamingSubWindow.objectName()):
            self.actionViewStreaming.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.resultsPlotSubWindow.objectName()):
            self.actionViewResultsPlot.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.flowUsagePlotSubWindow.objectName()):
            self.actionViewFlowUsagePlot.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.currentTrialSubWindow.objectName()):
            self.actionViewCurrentTrialInfo.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
    
    def _viewStreamingSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.streamingSubWindow.show()
            self.streamingSubWindow.widget().show()
        else:
            self.streamingSubWindow.hide()

    def _viewResultsPlotSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.resultsPlotSubWindow.show()
            self.resultsPlotSubWindow.widget().show()
        else:
            self.resultsPlotSubWindow.hide()

    def _viewFlowUsagePlotSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.flowUsagePlotSubWindow.show()
            self.flowUsagePlotSubWindow.widget().show()
        else:
            self.flowUsagePlotSubWindow.hide()

    def _viewCurrentTrialSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.currentTrialSubWindow.show()
            self.currentTrialSubWindow.widget().show()
        else:
            self.currentTrialSubWindow.hide()

    def _launchAnalogInputSettings(self):
        self.analogInputSettings.show()

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
        settings = self.analogInputSettings.getSettings()
        logging.info(settings)
        self.adc.setNactiveChannels(settings['nActiveChannels'])
        self.adc.setSamplingRate(settings['samplingRate'])
        self.adc.setInputRange(settings['inputRanges'])
        self.adc.setStream2USB(settings['enableUSBStreaming'])
        self.adc.setSMeventsEnabled(settings['enableSMEventReporting'])
        self.adc.setThresholds(settings['thresholdVoltages'])
        self.adc.setResetVoltages(settings['resetVoltages'])

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
        except SerialException:
            QMessageBox.warning(self, "Warning", "Cannot connect analog input module! Check that serial port is correct!")
            return
        except AnalogInException as err:
            QMessageBox.warning(self, "Warning", f"Analog Input Module Error.\n{err}")
            return

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

        # Check if adc was created which would mean the user enabled the checkbox and the analog input module was connected.
        if self.adc:
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
            self.actionLaunchOlfaGUI.setEnabled(False)  # Disable the olfa GUI button if the olfactometer will be used for the experiment by the protocolWorker's thread.
            # The user can still use the olfactometer GUI during an experiment (i.e. for manual control) but must uncheck the olfa check box to let
            # the protocolWorker's thread know not to use it. Only one object can access a serial port at any given time.

    def _endTask(self):
        self.streaming.pauseAnimation()
        if self.adc:
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
            self.actionLaunchOlfaGUI.setEnabled(True)  # re-enable the olfa GUI button after the experiment completes.
        self._experimentCompleteDialog()
        self.currentTrialProgressBar.setValue(0)
        self.currentTrialProgressBarLabel.setText('')

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

            self.waterFlushProgress = QProgressDialog("Flushing left water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.leftWaterValveDuration)

    def _calibrateLeftWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.waterFlushProgress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.leftWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.leftWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.waterFlushProgress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
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

            self.waterFlushProgress = QProgressDialog("Flushing right water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.rightWaterValveDuration)

    def _calibrateRightWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.calibLeftWaterButton.setEnabled(True)
            self.calibRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.waterFlushProgress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self._closeValve(self.rightWaterValve)
                self.isOpen = False
            else:
                self._openValve(self.rightWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.waterFlushProgress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
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

    def _recordNumTrials(self, value):
        self.numTrials = value

    def _recordNoResponseCutoff(self, value):
        if not (value == 0):
            self.noResponseCutoff = value
            self.autoWaterCutoffSpinBox.setMaximum(value - 1)
        else:
            # When value equals 0, the spinBox displays 'Never'
            self.noResponseCutoff = self.numTrials + 1  # Set it equal to 1 more than the number of trials to guarantee that it will never happen.
            self.autoWaterCutoffSpinBox.setMaximum(value)
        if self.protocolWorker is not None:
            self.protocolWorker.setNoResponseCutoff(self.noResponseCutoff)

    def _recordAutoWaterCutoff(self, value):
        if not (value == 0):
            self.autoWaterCutoff = value
        else:
            # When value equals 0, the spinBox displays 'Never'
            self.autoWaterCutoff = self.numTrials + 1  # Set it equal to 1 more than the number of trials to guarantee that it will never happen.
        if self.protocolWorker is not None:
            self.protocolWorker.setAutoWaterCutoff(self.autoWaterCutoff)

    def _recordMinITI(self, value):
        self.itiMin = value
        self.itiMaxSpinBox.setMinimum(value)  # Do not allow itiMaxSpinBox to hold a value less than itiMinSpinBox's current value.
        if self.protocolWorker is not None:
            self.protocolWorker.setMinITI(value)

    def _recordMaxITI(self, value):
        self.itiMax = value
        self.itiMinSpinBox.setMaximum(value)  # Do not allow itiMinSpinBox to hold a value greater than itiMaxSpinBox's current value.
        if self.protocolWorker is not None:
            self.protocolWorker.setMaxITI(value)

    def _recordLeftWaterValveDuration(self, value):
        self.leftWaterValveDuration = value
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftWaterDuration(value)

    def _recordRightWaterValveDuration(self, value):
        self.rightWaterValveDuration = value
        if self.protocolWorker is not None:
            self.protocolWorker.setRightWaterDuration(value)

    def _recordBpodSerialPort(self):
        self.bpodSerialPort = self.bpodPortLineEdit.text()

    def _recordOlfaSerialPort(self):
        self.olfaSerialPort = self.olfaPortLineEdit.text()

    def _recordAnalogInputModuleSerialPort(self):
        self.adcSerialPort = self.analogInputModulePortLineEdit.text()

    def _updateCurrentState(self, stateName):
        self.currentStateLineEdit.setText(stateName)
        self.currentTrialProgressBarLabel.setText(stateName)
        
    def _updateCurrentTrialProgressBar(self, value):
        self.currentTrialProgressBar.setValue(value + 1)

    def _updateResponseResult(self, result):
        self.responseResultLineEdit.setText(result)

    def _updateSessionTotals(self, totalsDict):
        logging.info('attempting to update session totals')
        self.totalCorrectLineEdit.setText(str(totalsDict['totalCorrect']))
        self.totalWrongLineEdit.setText(str(totalsDict['totalWrong']))
        self.totalNoResponsesLineEdit.setText(str(totalsDict['totalNoResponses']))
        self.totalPercentCorrectLineEdit.setText(str(totalsDict['totalPercentCorrect']))

    def _updateCurrentTrialInfo(self, trialInfoDict):
        trialInfo = trialInfoDict
        # Check if not empty.
        if trialInfo:
            self.trialNumLineEdit.setText(str(trialInfo['currentTrialNum']))
            self.correctResponseLineEdit.setText(trialInfo['correctResponse'])
            self.itiLineEdit.setText(str(trialInfo['currentITI']))
            self.odorNameLineEdit.setText(trialInfo['currentOdorName'])
            self.odorConcentrationLineEdit.setText(str(trialInfo['currentOdorConc']))
            self.currentFlowLineEdit.setText(str(trialInfo['currentFlow']))
            self.currentTrialProgressBar.setRange(0, trialInfo['nStates'])

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
            # numTotal = v['Total']  # I do not want to use this because if the mouse does not response many times, it will increase the denominator and lower the percentage.
            numResponses = v['Correct'] + v['Wrong']  # I only want the denominator to be the total number of actual responses.
            if not (numResponses == 0):
                percent = round((float(numLeft) / float(numResponses) * 100), 2)
            else:
                percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
            xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
            yValues.append(percent)
            index += 1
        
        self.resultsPlot.updatePlot(xValues, yValues)

    def _updateFlowUsagePlot(self, flowResultsDict):
        if not self.flowUsagePlot.isXAxisSetup():
            self.flowUsagePlot.setupXaxis(flowResultsDict)

        xValues = []
        yValues = []
        index = 0
        for k, v in flowResultsDict.items():
            xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
            yValues.append(v['Total'])
            index += 1
        self.flowUsagePlot.updatePlot(xValues, yValues)
    
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

    def _olfaExceptionDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Experiment aborted because the olfactometer raised the following exception:\n{error}")

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
        self.stopRunningSignal.connect(self.inputEventWorker.stopRunning)
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
        self.stopRunningSignal.connect(lambda: self.saveDataWorker.stopRunning())  # Need to use lambda, to explicitly make function call (from the main thread). Because the saveDataWorker thread will never call it since its in a infinite loop.
        self.saveDataThread.start()
        logging.info(f"saveDataThread running? {self.saveDataThread.isRunning()}")
  
    def _runProtocolThread(self):
        logging.info(f"from _runProtocolThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.protocolThread = QThread()
        self.protocolWorker = ProtocolWorker(self.myBpod, self.protocolFileName, self.olfaConfigFileName, self.leftWaterValveDuration, self.rightWaterValveDuration, self.itiMin, self.itiMax, self.noResponseCutoff, self.autoWaterCutoff, self.olfaCheckBox.isChecked(), self.numTrials)
        self.protocolWorker.moveToThread(self.protocolThread)
        self.protocolThread.started.connect(self.protocolWorker.run)
        self.protocolWorker.finished.connect(self.protocolThread.quit)
        self.protocolWorker.finished.connect(self._endTask)  # This serves to stop the other threads when the protocol thread completes all trials.
        self.protocolWorker.finished.connect(self.protocolWorker.deleteLater)
        self.protocolThread.finished.connect(self.protocolThread.deleteLater)
        self.protocolWorker.trialStartSignal.connect(self.inputEventWorker.newTrialSlot)
        self.protocolWorker.newStateSignal.connect(self._updateCurrentState)
        self.protocolWorker.newStateSignal.connect(self.streaming.checkResponseWindow)
        self.protocolWorker.stateNumSignal.connect(self._updateCurrentTrialProgressBar)
        self.protocolWorker.responseResultSignal.connect(self._updateResponseResult)
        self.protocolWorker.newTrialInfoSignal.connect(self._updateCurrentTrialInfo)  # This works without lambda because 'self._updateCurrentTrialInfo' is in the main thread.
        self.protocolWorker.flowResultsCounterDictSignal.connect(self._updateResultsPlot)
        self.protocolWorker.flowResultsCounterDictSignal.connect(self._updateFlowUsagePlot)
        self.protocolWorker.totalsDictSignal.connect(self._updateSessionTotals)
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.saveDataWorker.receiveInfoDict(x))  # 'x' is the dictionary parameter emitted from 'saveTrialDataDictSignal' and passed into 'receiveInfoDict(x)'
        self.protocolWorker.saveEndOfSessionDataSignal.connect(lambda x: self.saveDataWorker.receiveFinalResultsDict(x))  # 'x' is the dictionary parameter emitted from 'saveEndOfSessionDataSignal' and passed into 'receiveFinalResultsDict(x)'
        # self.protocolWorker.startSDCardLoggingSignal.connect(self._startSDCardLogging)
        # self.protocolWorker.stopSDCardLoggingSignal.connect(self._stopSDCardLogging)
        self.protocolWorker.noResponseAbortSignal.connect(self._noResponseAbortDialog)
        self.protocolWorker.olfaNotConnectedSignal.connect(self._cannotConnectOlfaDialog)
        self.protocolWorker.olfaExceptionSignal.connect(self._olfaExceptionDialog)
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
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(sys.argv)

    win = Window()
    win.show()
    win.activateWindow()
    win.raise_()
    status = qapp.exec_()
    win.closeDevices()
    sys.exit(status)
