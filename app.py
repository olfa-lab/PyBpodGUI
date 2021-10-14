import sys
import logging
from serial.serialutil import SerialException

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QProgressDialog, QFileDialog, QMdiSubWindow
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QCloseEvent

from pybpodapi.protocol import Bpod, StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
from BpodAnalogInputModule import AnalogInException, BpodAnalogIn
import olfactometry

from python_ui_files.main_window_ui import Ui_MainWindow
from saveDataWorker import SaveDataWorker
from inputEventWorker import InputEventWorker
from protocolWorker import ProtocolWorker
from streamingWorker import StreamingWorker
from flowUsagePlotWorker import FlowUsagePlotWorker
from resultsPlotWorker import ResultsPlotWorker
from protocolEditorDialog import ProtocolEditorDialog
from olfaEditorDialog import OlfaEditorDialog
from analogInputSettingsDialog import AnalogInputSettingsDialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


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
        self.protocolWorker = None
        self.mouseNumber = None
        self.rigLetter = None
        self.experimentType = None
        self.numTrials = self.nTrialsSpinBox.value()
        self.noResponseCutoff = self.noResponseCutoffSpinBox.value()
        self._recordNoResponseCutoff(self.noResponseCutoff)
        self.autoWaterCutoff = self.autoWaterCutoffSpinBox.value()
        self._recordAutoWaterCutoff(self.autoWaterCutoff)
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
        self.isPaused = False

        self.startButton.setEnabled(False)  # do not enable start button until user connects devices.
        self.finalValveButton.setEnabled(False)
        self.leftWaterValveButton.setEnabled(False)
        self.rightWaterValveButton.setEnabled(False)
        self.flushLeftWaterButton.setEnabled(False)
        self.flushRightWaterButton.setEnabled(False)

        self.currentTrialSubWindow = MyQMdiSubWindow()
        self.currentTrialSubWindow.closed.connect(self._updateViewMenu)
        self.currentTrialSubWindow.setObjectName("currentTrialSubWindow")
        self.currentTrialSubWindow.setWidget(self.currentTrialSubWindowWidget)
        self.currentTrialSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.currentTrialSubWindow.resize(720, 230)
        self.mdiArea.addSubWindow(self.currentTrialSubWindow)

        self.bpodControlSubWindow = MyQMdiSubWindow()
        self.bpodControlSubWindow.closed.connect(self._updateViewMenu)
        self.bpodControlSubWindow.setObjectName("bpodControlSubWindow")
        self.bpodControlSubWindow.setWidget(self.bpodControlSubWindowWidget)
        self.bpodControlSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.bpodControlSubWindow.resize(300, 230)
        self.mdiArea.addSubWindow(self.bpodControlSubWindow)

        self.streaming = StreamingWorker(self.maxtSpinBox.value(), self.dtDoubleSpinBox.value(), self.yMinDoubleSpinBox.value(), self.yMaxDoubleSpinBox.value(), self.plotIntervalSpinBox.value())
        self.streamingWidget = self.streaming.getFigure()
        self.streamingWidget.setMinimumSize(500, 250)
        self.streamingPlotSubWindowWidgetGridLayout.addWidget(self.streamingWidget, 0, 2, 5, 1)
        self.streamingSubWindow = MyQMdiSubWindow()
        self.streamingSubWindow.closed.connect(self._updateViewMenu)
        self.streamingSubWindow.setObjectName("streamingSubWindow")
        self.streamingSubWindow.setWidget(self.streamingPlotSubWindowWidget)
        self.streamingSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        # self.streamingSubWindow.resize(1000, 300)
        self.mdiArea.addSubWindow(self.streamingSubWindow)

        self.resultsPlot = ResultsPlotWorker()
        self.resultsPlotSubWindowWidgetGridLayout.addWidget(self.resultsPlot.getWidget(), 1, 0, 1, 3)
        self.resultsPlotSubWindow = MyQMdiSubWindow()
        self.resultsPlotSubWindow.closed.connect(self._updateViewMenu)
        self.resultsPlotSubWindow.setObjectName("resultsPlotSubWindow")
        self.resultsPlotSubWindow.setWidget(self.resultsPlotSubWindowWidget)
        self.resultsPlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.resultsPlotSubWindow.resize(300, 300)
        self.mdiArea.addSubWindow(self.resultsPlotSubWindow)

        self.flowUsagePlot = FlowUsagePlotWorker()
        self.flowUsagePlotSubWindowWidgetGridLayout.addWidget(self.flowUsagePlot.getWidget(), 1, 0, 1, 3)
        self.flowUsagePlotSubWindow = MyQMdiSubWindow()
        self.flowUsagePlotSubWindow.closed.connect(self._updateViewMenu)
        self.flowUsagePlotSubWindow.setObjectName("flowUsagePlotSubWindow")
        self.flowUsagePlotSubWindow.setWidget(self.flowUsagePlotSubWindowWidget)
        self.flowUsagePlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.flowUsagePlotSubWindow.resize(300, 300)
        self.mdiArea.addSubWindow(self.flowUsagePlotSubWindow)

    def _connectSignalsSlots(self):
        self.startButton.clicked.connect(self._runTask)
        self.stopButton.clicked.connect(self._endTask)
        self.pauseButton.clicked.connect(self._pauseExperiment)
        self.finalValveButton.clicked.connect(self._toggleFinalValve)
        self.leftWaterValveButton.clicked.connect(self._toggleLeftWaterValve)
        self.rightWaterValveButton.clicked.connect(self._toggleRightWaterValve)
        self.flushLeftWaterButton.clicked.connect(self._flushLeftWaterValve)
        self.flushRightWaterButton.clicked.connect(self._flushRightWaterValve)
        self.connectDevicesButton.clicked.connect(self._connectDevices)
        self.resultsPlotCombineAllVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(0))
        self.resultsPlotCombineLikeVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(1))
        self.resultsPlotSeparateVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(2))
        self.flowUsagePlotCombineAllVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(0))
        self.flowUsagePlotCombineLikeVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(1))
        self.flowUsagePlotSeparateVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(2))
        
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
        self.actionViewBpodControl.toggled.connect(self._viewBpodControlSubWindow)

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
        self.yMaxDoubleSpinBox.valueChanged.connect(lambda ymax: self.streaming.setYaxis(self.yMinDoubleSpinBox.value(), ymax))
        self.yMinDoubleSpinBox.valueChanged.connect(lambda ymin: self.streaming.setYaxis(ymin, self.yMaxDoubleSpinBox.value()))
        self.maxtSpinBox.valueChanged.connect(lambda maxt: self.streaming.setXaxis(maxt))
        self.dtDoubleSpinBox.valueChanged.connect(lambda dt: self.streaming.set_dt(dt))
        self.plotIntervalSpinBox.valueChanged.connect(lambda x: self.streaming.setPlotInterval(x))

        self.experimentTypeComboBox.currentTextChanged.connect(self._recordExperimentType)

    def _updateViewMenu(self, objectName):
        if (objectName == self.streamingSubWindow.objectName()):
            self.actionViewStreaming.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.resultsPlotSubWindow.objectName()):
            self.actionViewResultsPlot.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.flowUsagePlotSubWindow.objectName()):
            self.actionViewFlowUsagePlot.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.currentTrialSubWindow.objectName()):
            self.actionViewCurrentTrialInfo.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
        elif (objectName == self.bpodControlSubWindow.objectName()):
            self.actionViewBpodControl.setChecked(False)  # Un-check it from the View menu since the subWindow was closed.
    
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

    def _viewBpodControlSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.bpodControlSubWindow.show()
            self.bpodControlSubWindow.widget().show()
        else:
            self.bpodControlSubWindow.hide()
    
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
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption="Open Protocol File", directory="protocol_files", filter="JSON Files (*.json)", options=options)
        if fileName:
            self.protocolFileName = fileName
            self.protocolFileLineEdit.setText(fileName)
            logging.info(f"The file {fileName} has been loaded.")

    def openOlfaConfigFileNameDialog(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption="Open Olfactometer Configuration File", directory="olfactometry_config_files", filter="JSON Files (*.json)", options=options)
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
                self.configureAnalogModule()
        except SerialException:
            QMessageBox.warning(self, "Warning", "Cannot connect analog input module! Check that serial port is correct and try again!")
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
            QMessageBox.warning(self, "Warning", "Cannot connect to bpod! Check that serial port is correct and try again!")
            return

        self.startButton.setEnabled(True)  # This means successful connection attempt for enabled devices.
        self.connectDevicesButton.setEnabled(False)  # Disable to prevent clicking again.
        self.connectDevicesButton.setText("Connected")

        self.finalValveButton.setEnabled(True)
        self.leftWaterValveButton.setEnabled(True)
        self.rightWaterValveButton.setEnabled(True)
        self.flushLeftWaterButton.setEnabled(True)
        self.flushRightWaterButton.setEnabled(True)

    def _runTask(self):
        if self.mouseNumber is None:
            QMessageBox.warning(self, "Warning", "Please enter mouse number!")
            return
        elif self.rigLetter is None:
            QMessageBox.warning(self, "Warning", "Please enter rig letter!")
            return
        elif self.experimentType is None:
            QMessageBox.warning(self, "Warning", "Please choose an experiment type!")
            return
        elif self.numTrials is None:
            QMessageBox.warning(self, "Warning", "Please enter number of trials for this experiment!")
            return
        elif self.protocolFileName is '':
            QMessageBox.warning(self, "Warning", "Please load a protocol file. Go to 'File' > 'Open'.")
            return

        # The following three try-except blocks prevent the application from crashing when trying to start the experiment again after already running it once.
        # The AttributeError always happens upon clicking the start button for the first time because the self.inputEventThread variable was never created yet
        # so the Window object has not attribute 'inputEventThread', and same goes for the other thread variables. After running an experiment once and trying
        # to start the experiment a successive time causes a RuntimeError where the 'wrapped C/C++ object of type QThread has been deleted'. So in that case I
        # delete the thread's variable and continue the remaining code. Actually, I do not even need to delete the thread's variable. The action of catching the
        # RuntimeError seems to prevent crashing alone.
        # try:
        #     if self.inputEventThread.isRunning():
        #         logging.info('inputEventThread is still running')
        #         self.inputEventThread.quit()
        #         self.inputEventThread.deleteLater()
        # except AttributeError as err:
        #     logging.info(f"AttributeError: {err}")
        # except RuntimeError as err:
        #     logging.info(f"RuntimeError: inputEventThread {err}")
        #     # del self.inputEventThread

        # try:    
        #     if self.saveDataThread.isRunning():
        #         logging.info('saveDataThread is still running')
        #         self.saveDataThread.quit()
        #         self.saveDataThread.deleteLater()
        # except AttributeError as err:
        #     logging.info(f"AttributeError: {err}")
        # except RuntimeError as err:
        #     logging.info(f"RuntimeError: saveDataThread {err}")
        #     # del self.saveDataThread
            
        # try:  
        #     if self.protocolThread.isRunning():
        #         logging.info('protocolThread is still running')
        #         self.protocolThread.quit()
        #         self.protocolThread.deleteLater()
        # except AttributeError as err:
        #     logging.info(f"AttributeError: {err}")
        # except RuntimeError as err:
        #     logging.info(f"RuntimeError: protocolThread {err}")
        #     # del self.protocolThread

        # Safety check to close and delete the main thread's olfactometer (if in use or was in use) before running the protocolWorker's thread
        # so that the protocolWorker's thread can access the olfactometer's serial port if the user enables the olfactometer for the experiment.
        if self.olfas:
            self.olfas.close_serials()
            del self.olfas
            self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.

        # Check if adc was created which would mean the user enabled the checkbox and the analog input module was connected.
        if self.adc:
            self.startAnalogModule()
        
        self._runSaveDataThread()
        self._runInputEventThread()
        self._runProtocolThread()

        if not self.streaming.startAnimation():
            self.streaming.resetPlot()
            self.streaming.resumeAnimation()

        self.resultsPlot.setExperimentType(self.experimentType)
        self.flowUsagePlot.setExperimentType(self.experimentType)
        if (self.experimentType == 'twoOdorMatch'):
            self.flowUsagePlotSubWindow.showShaded()

        self.startButton.setEnabled(False)
        self.flushLeftWaterButton.setEnabled(False)
        self.flushRightWaterButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.pauseButton.setEnabled(True)
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
        self.pauseButton.setEnabled(False)
        self.pauseButton.setText('Pause')
        self.isPaused = False
        self.flushLeftWaterButton.setEnabled(True)
        self.flushRightWaterButton.setEnabled(True)
        if self.olfaCheckBox.isChecked():
            self.actionLaunchOlfaGUI.setEnabled(True)  # re-enable the olfa GUI button after the experiment completes.
        self._experimentCompleteDialog()
        self.currentTrialProgressBar.setValue(0)

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

    def _pauseExperiment(self):
        if self.isPaused:
            self.myBpod.resume()
            self.streaming.resumeAnimation()
            if self.adc is not None:
                self.startAnalogModule()
            self.isPaused = False
            self.pauseButton.setText('Pause')
            
        else:
            self.myBpod.pause()
            self.streaming.pauseAnimation()
            if self.adc is not None:
                self.stopAnalogModule()
            self.isPaused = True
            self.pauseButton.setText('Resume')
    
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

    def _flushLeftWaterValve(self):
        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.flushLeftWaterButton.setEnabled(False)
            self.flushRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._flushLeftWaterValveToggler)

            self.waterFlushProgress = QProgressDialog("Flushing left water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.leftWaterValveDuration)

    def _flushLeftWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
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
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _flushRightWaterValve(self):
        if self.myBpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.flushLeftWaterButton.setEnabled(False)
            self.flushRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self._flushRightWaterValveToggler)

            self.waterFlushProgress = QProgressDialog("Flushing right water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.rightWaterValveDuration)

    def _flushRightWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self._closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
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
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def _recordMouseNumber(self):
        self.mouseNumber = self.mouseNumberLineEdit.text()

    def _recordRigLetter(self):
        self.rigLetter = self.rigLetterLineEdit.text()

    def _recordExperimentType(self, text):
        self.experimentType = text

    def _recordNumTrials(self, value):
        self.numTrials = value
        if self.protocolWorker is not None:
            self.protocolWorker.setNumTrials(self.numTrials)

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
        # Check if not empty.
        if trialInfoDict:
            self.trialNumLineEdit.setText(str(trialInfoDict['currentTrialNum']))
            self.correctResponseLineEdit.setText(trialInfoDict['correctResponse'])
            self.itiLineEdit.setText(str(trialInfoDict['currentITI']))
            self.currentTrialProgressBar.setRange(0, trialInfoDict['nStates'])

            if ('stimList' in trialInfoDict) and (len(trialInfoDict['stimList']) > 0):
                odorA_vialString = ''
                odorA_nameString = ''
                odorA_concString = ''
                odorA_flowString = ''
                # In case there are multiple olfactometers used (for creating mixtures), create a string for the parameters of each olfa and separates them by a comma. This is just for viewing purposes on the screen. Each olfa will have its own column in the h5 file.
                for olfaValues in trialInfoDict['stimList'][0]['olfas'].values():
                    if odorA_vialString:  # If string is not empty, that means the first item was concantenated to it already, so put a comma before concatenating the next item. No need to check every string because they all get items concatenated every loop.
                        odorA_vialString += ', '  + olfaValues['vialNum']
                        odorA_nameString += ', '  + olfaValues['odor']
                        odorA_concString += ', '  + str(olfaValues['vialconc'])
                        odorA_flowString += ', '  + str(olfaValues['mfc_1_flow'])
                    
                    else:  # Concatenate without a comma because this will be the first concatenation. And this will avoid putting a comma when only one odor is used.
                        odorA_vialString += olfaValues['vialNum']
                        odorA_nameString += olfaValues['odor']
                        odorA_concString += str(olfaValues['vialconc'])
                        odorA_flowString += str(olfaValues['mfc_1_flow'])

                self.odorA_vialLineEdit.setText(odorA_vialString)
                self.odorA_nameLineEdit.setText(odorA_nameString)
                self.odorA_concLineEdit.setText(odorA_concString)
                self.odorA_flowLineEdit.setText(odorA_flowString)
                
                try:
                    odorB_vialString = ''
                    odorB_nameString = ''
                    odorB_concString = ''
                    odorB_flowString = ''
                    # In case there are multiple olfactometers used (for creating mixtures), create a string for the parameters of each olfa and separates them by a comma. This is just for viewing purposes on the screen. Each olfa will have its own column in the h5 file.
                    for olfaValues in trialInfoDict['stimList'][1]['olfas'].values():
                        if odorB_vialString:  # If string is not empty, that means the first item was concantenated to it already, so put a comma before concatenating the next item. No need to check every string because they all get items concatenated every loop.
                            odorB_vialString += ', '  + olfaValues['vialNum']
                            odorB_nameString += ', '  + olfaValues['odor']
                            odorB_concString += ', '  + str(olfaValues['vialconc'])
                            odorB_flowString += ', '  + str(olfaValues['mfc_1_flow'])

                        else:  # Concatenate without a comma because this will be the first concatenation. And this will avoid putting a comma when only one odor is used.
                            odorB_vialString += olfaValues['vialNum']
                            odorB_nameString += olfaValues['odor']
                            odorB_concString += str(olfaValues['vialconc'])
                            odorB_flowString += str(olfaValues['mfc_1_flow'])

                    self.odorB_vialLineEdit.setText(odorB_vialString)
                    self.odorB_nameLineEdit.setText(odorB_nameString)
                    self.odorB_concLineEdit.setText(odorB_concString)
                    self.odorB_flowLineEdit.setText(odorB_flowString)

                except IndexError:  # That means only one odor presentation is being used for the experiment.
                    self.odorB_vialLineEdit.setText('N/A')
                    self.odorB_nameLineEdit.setText('N/A')
                    self.odorB_concLineEdit.setText('N/A')
                    self.odorB_flowLineEdit.setText('N/A')
            
            else:  # This means olfactometer was not used for the experiment.
                self.odorA_vialLineEdit.setText('N/A')
                self.odorA_nameLineEdit.setText('N/A')
                self.odorA_concLineEdit.setText('N/A')
                self.odorA_flowLineEdit.setText('N/A')
            

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

    def _bpodExceptionDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Experiment aborted because the bpod raised the following exception:\n{error}")

    def _runInputEventThread(self):
        logging.info(f"from _runInputEventThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.inputEventThread = QThread()
        self.inputEventWorker = InputEventWorker(self.myBpod)
        self.inputEventWorker.moveToThread(self.inputEventThread)
        self.inputEventThread.started.connect(self.inputEventWorker.run)
        self.inputEventWorker.finished.connect(self.inputEventThread.quit)
        self.inputEventWorker.finished.connect(self.inputEventWorker.deleteLater)
        self.inputEventThread.finished.connect(self.inputEventThread.deleteLater)
        self.inputEventWorker.inputEventSignal.connect(self.streaming.setInputEvent)
        self.stopRunningSignal.connect(self.inputEventWorker.stopRunning)
        self.inputEventThread.start()
        logging.info(f"inputEventThread is running? {self.inputEventThread.isRunning()}")

    def _runSaveDataThread(self):
        logging.info(f"from _runSaveDataThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.saveDataThread = QThread()
        self.saveDataWorker = SaveDataWorker(self.mouseNumber, self.rigLetter, self.experimentType, self.adc)
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
        self.protocolWorker = ProtocolWorker(self.myBpod, self.protocolFileName, self.olfaConfigFileName, self.experimentType, self.leftWaterValveDuration, self.rightWaterValveDuration, self.itiMin, self.itiMax, self.noResponseCutoff, self.autoWaterCutoff, self.olfaCheckBox.isChecked(), self.numTrials)
        self.protocolWorker.moveToThread(self.protocolThread)
        self.protocolThread.started.connect(self.protocolWorker.run)
        self.protocolWorker.finished.connect(self.protocolThread.quit)
        self.protocolWorker.finished.connect(self._endTask)  # This serves to stop the other threads when the protocol thread completes all trials.
        self.protocolWorker.finished.connect(self.protocolWorker.deleteLater)
        self.protocolThread.finished.connect(self.protocolThread.deleteLater)
        self.protocolWorker.newStateSignal.connect(self._updateCurrentState)
        self.protocolWorker.newStateSignal.connect(self.streaming.checkResponseWindow)
        self.protocolWorker.stateNumSignal.connect(self._updateCurrentTrialProgressBar)
        self.protocolWorker.responseResultSignal.connect(self._updateResponseResult)
        self.protocolWorker.newTrialInfoSignal.connect(self._updateCurrentTrialInfo)  # This works without lambda because 'self._updateCurrentTrialInfo' is in the main thread.
        self.protocolWorker.resultsCounterListSignal.connect(lambda x: self.saveDataWorker.receiveTotalResultsList(x))
        self.protocolWorker.resultsCounterListSignal.connect(self.resultsPlot.updatePlot)
        self.protocolWorker.resultsCounterListSignal.connect(self.flowUsagePlot.updatePlot)
        self.protocolWorker.duplicateVialsSignal.connect(self.resultsPlot.receiveDuplicatesDict)
        self.protocolWorker.duplicateVialsSignal.connect(self.flowUsagePlot.receiveDuplicatesDict)
        self.protocolWorker.totalsDictSignal.connect(self._updateSessionTotals)
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.saveDataWorker.receiveInfoDict(x))  # 'x' is the dictionary parameter emitted from 'saveTrialDataDictSignal' and passed into 'receiveInfoDict(x)'
        # self.protocolWorker.startSDCardLoggingSignal.connect(self._startSDCardLogging)
        # self.protocolWorker.stopSDCardLoggingSignal.connect(self._stopSDCardLogging)
        self.protocolWorker.noResponseAbortSignal.connect(self._noResponseAbortDialog)
        self.protocolWorker.olfaNotConnectedSignal.connect(self._cannotConnectOlfaDialog)
        self.protocolWorker.olfaExceptionSignal.connect(self._olfaExceptionDialog)
        self.protocolWorker.invalidFileSignal.connect(self._invalidFileDialog)
        self.protocolWorker.bpodExceptionSignal.connect(self._bpodExceptionDialog)
        self.stopRunningSignal.connect(lambda: self.protocolWorker.stopRunning())
        self.protocolThread.start()
        logging.info(f"protocolThread running? {self.protocolThread.isRunning()}")


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
