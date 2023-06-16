import sys
import logging
import json
import os
from serial.serialutil import SerialException
import serial.tools.list_ports
import serial

from PyQt5.QtWidgets import QApplication, QMainWindow, QMessageBox, QProgressDialog, QFileDialog, QMdiSubWindow, QSlider, QStyle
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal, pyqtSlot, Qt, QUrl, QDir
from PyQt5.QtGui import QCloseEvent
from PyQt5.QtMultimedia import QMediaContent, QMediaPlayer

from pybpodapi.protocol import Bpod, StateMachine
from pybpodapi.exceptions.bpod_error import BpodErrorException
from BpodAnalogInputModule import AnalogInException, BpodAnalogIn
import olfactometry

from trialPlaybackSubWindowWidget import trialPlaybackSubWindowWidget
from ui_files.main_window_ui import Ui_MainWindow
from saveDataWorker import SaveDataWorker
from inputEventWorker import InputEventWorker
from protocolWorker import ProtocolWorker
from playbackWorker import PlaybackWorker
from streamingWorker import StreamingWorker
from readDataWorker import ReadDataWorker
from flowUsagePlotWorker import FlowUsagePlotWorker
from resultsPlotWorker import ResultsPlotWorker
from protocolEditorDialog import ProtocolEditorDialog
from olfaEditorDialog import OlfaEditorDialog
from odorEditorDialog import OdorEditorDialog
from analogInputModuleSettingsDialog import AnalogInputModuleSettingsDialog
from bpodFlexChannelSettingsDialog import BpodFlexChannelSettingsDialog
from PyQt5.QtGui import QPixmap
from imageAcquisition import MicroManagerPrime95B
import numpy as np
import skimage.io as skio
import cv2
from datetime import datetime
logging.basicConfig(format="%(message)s", level=logging.INFO)
from time import sleep


ACQ_CONFIG_FILE = os.path.abspath(r'.default_acq')

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
    startExperimentSignal = pyqtSignal()
    # launchOlfaGUISignal = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)
        self.setWindowTitle("PyBpod GUI")
        self.camera = None
        self.createMdiSubWindows()
        self.connectSignalsSlots()
        self.olfas = None
        self.adc = None
        self.bpod = None
        self.saveDataWorker = None
        self.protocolWorker = None
        self.itiMinSpinBox.setMaximum(self.itiMaxSpinBox.value())  # I do not want the itiMinSpinBox to be higher than the itiMaxSpinBox's current value.
        self.itiMaxSpinBox.setMinimum(self.itiMinSpinBox.value())  # I do not want the itiMaxSpinBox to be lower than the itiMinSpinBox's current value.
        self.leftWaterValve = int(self.leftWaterValvePortNumComboBox.currentText())
        self.finalValve = int(self.finalValvePortNumComboBox.currentText())
        self.rightWaterValve = int(self.rightWaterValvePortNumComboBox.currentText())
        self.protocolFileName = ''
        self.olfaConfigFileName = ''
        self.analogInputModuleSettingsDialog = None
        self.bpodFlexChannelSettingsDialog = None
        self.isPaused = False
        self.loadDefaults()

        
        ## fix for QThread deleted error:
        ## I think that the error is caused when you run a new experiment because it sets the thread variable to a new thread leaving the previous thread open for garbage collection. I think that when the thread object is destroyed Qt throws an error because the underlying os thread is still running.
        ## instead of figuring out how to fix that, I'm using a hack wher I simply add the old thread to a list to prevent garbage collection

        self.oldProtocolThreads = []
        self.oldSaveDataThreads = []
        self.oldInputEventThreads = []

        self.oldProtocolWorkers= []
        self.protocolThread = None
        self.streamingThread =None
        self.playbackThread =None



    def createMdiSubWindows(self):
        self.currentTrialSubWindow = MyQMdiSubWindow()
        self.currentTrialSubWindow.closed.connect(self.updateViewMenu)
        self.currentTrialSubWindow.setObjectName("currentTrialSubWindow")
        self.currentTrialSubWindow.setWidget(self.currentTrialSubWindowWidget)
        self.currentTrialSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        # self.currentTrialSubWindow.resize(720, 230)
        self.mdiArea.addSubWindow(self.currentTrialSubWindow)

        self.streaming = StreamingWorker(self.maxtSpinBox.value(), self.dtDoubleSpinBox.value(), self.yMinDoubleSpinBox.value(), self.yMaxDoubleSpinBox.value(), self.plotIntervalSpinBox.value(),  self.sniffThresholdSpinBox.value())
        self.streamingWidget = self.streaming.getFigure()
        self.streamingWidget.setMinimumSize(500, 250)
        self.streamingPlotSubWindowWidgetGridLayout.addWidget(self.streamingWidget, 0, 2, 5, 1)
        self.streamingSubWindow = MyQMdiSubWindow()
        self.streamingSubWindow.closed.connect(self.updateViewMenu)
        self.streamingSubWindow.setObjectName("streamingSubWindow")
        self.streamingSubWindow.setWidget(self.streamingPlotSubWindowWidget)
        self.streamingSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        # self.streamingSubWindow.resize(1000, 300)
        self.mdiArea.addSubWindow(self.streamingSubWindow)

        self.bpodControlSubWindow = MyQMdiSubWindow()
        self.bpodControlSubWindow.closed.connect(self.updateViewMenu)
        self.bpodControlSubWindow.setObjectName("bpodControlSubWindow")
        self.bpodControlSubWindow.setWidget(self.bpodControlSubWindowWidget)
        self.bpodControlSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        # self.bpodControlSubWindow.resize(300, 230)
        self.mdiArea.addSubWindow(self.bpodControlSubWindow)

        self.resultsPlot = ResultsPlotWorker()
        self.resultsPlotSubWindowWidgetGridLayout.addWidget(self.resultsPlot.getWidget(), 1, 0, 1, 3)
        self.resultsPlotSubWindow = MyQMdiSubWindow()
        self.resultsPlotSubWindow.closed.connect(self.updateViewMenu)
        self.resultsPlotSubWindow.setObjectName("resultsPlotSubWindow")
        self.resultsPlotSubWindow.setWidget(self.resultsPlotSubWindowWidget)
        self.resultsPlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.resultsPlotSubWindow.resize(300, 320)
        self.mdiArea.addSubWindow(self.resultsPlotSubWindow)



        self.flowUsagePlot = FlowUsagePlotWorker()
        self.flowUsagePlotSubWindowWidgetGridLayout.addWidget(self.flowUsagePlot.getWidget(), 1, 0, 1, 3)
        self.flowUsagePlotSubWindow = MyQMdiSubWindow()
        self.flowUsagePlotSubWindow.closed.connect(self.updateViewMenu)
        self.flowUsagePlotSubWindow.setObjectName("flowUsagePlotSubWindow")
        self.flowUsagePlotSubWindow.setWidget(self.flowUsagePlotSubWindowWidget)
        self.flowUsagePlotSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.flowUsagePlotSubWindow.resize(300, 320)
        self.mdiArea.addSubWindow(self.flowUsagePlotSubWindow)

        
        self.trialPlaybackSubWindow = MyQMdiSubWindow()        
        self.trialPlaybackSubWindow.setObjectName("trialPlaybackSubWindow")
        self.trialPlaybackSubWindow.setWidget(self.trialPlaybackSubWindowWidget)
        self.trialPlaybackSubWindowWidget.build_playback_window()
        self.playBackWorker = PlaybackWorker(self.trialPlaybackSubWindowWidget, self.camera)
        self.mediaPlayer = self.playBackWorker.mediaPlayer
        self.trialPlaybackSubWindow.closed.connect(self.updateViewMenu)

        self.trialPlaybackSubWindow.setAttribute(Qt.WA_DeleteOnClose, False)  # Set to False because I do not want the subWindow's wrapped C/C++ object to get deleted and removed from the mdiArea's subWindowList when it closes.
        self.trialPlaybackSubWindow.resize(300, 320)
        self.mdiArea.addSubWindow(self.trialPlaybackSubWindow)
        self.positionSlider = self.trialPlaybackSubWindowWidget.positionSlider
        self.playLastTrial_Button = self.trialPlaybackSubWindowWidget.playLastTrial_Button #widget before

    def connectSignalsSlots(self):
        self.startButton.clicked.connect(self.runTask)
        self.stopButton.clicked.connect(self.endTask)
        self.pauseButton.clicked.connect(self.pauseExperiment)
        self.finalValveButton.clicked.connect(self.toggleFinalValve)
        self.leftWaterValveButton.clicked.connect(self.toggleLeftWaterValve)
        self.rightWaterValveButton.clicked.connect(self.toggleRightWaterValve)
        self.flushLeftWaterButton.clicked.connect(self.flushLeftWaterValve)
        self.flushRightWaterButton.clicked.connect(self.flushRightWaterValve)
        self.connectDevicesButton.clicked.connect(self.connectDevices)
        self.disconnectDevicesButton.clicked.connect(self.disconnectDevices)
        self.resultsPlotCombineAllVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(0))
        self.resultsPlotCombineLikeVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(1))
        self.resultsPlotSeparateVialsButton.clicked.connect(lambda: self.resultsPlot.setPlottingMode(2))
        self.flowUsagePlotCombineAllVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(0))
        self.flowUsagePlotCombineLikeVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(1))
        self.flowUsagePlotSeparateVialsButton.clicked.connect(lambda: self.flowUsagePlot.setPlottingMode(2))
        


        self.actionNewProtocol.triggered.connect(self.launchProtocolEditor)
        self.actionOpenProtocol.triggered.connect(self.openProtocolFileNameDialog)
        self.actionLoadDefaults.triggered.connect(self.loadDefaults)
        self.actionSelectOlfaConfigFile.triggered.connect(self.openOlfaConfigFileNameDialog)
        self.actionConfigureOlfaSettings.triggered.connect(self.launchOlfaEditor)
        self.actionLaunchOlfaGUI.triggered.connect(self.launchOlfaGUI)
        self.actionOdors.triggered.connect(self.setOdorStimuli)
        self.actionConfigureBpodFlexChannels.triggered.connect(self.launchBpodFlexChannelSettingsDialog)
        self.actionConfigureAnalogInputModuleSettings.triggered.connect(self.launchAnalogInputModuleSettingsDialog)
        self.actionViewStreaming.toggled.connect(self.viewStreamingSubWindow)
        self.actionViewResultsPlot.toggled.connect(self.viewResultsPlotSubWindow)
        self.actionViewCurrentTrialInfo.toggled.connect(self.viewCurrentTrialSubWindow)
        self.actionViewFlowUsagePlot.toggled.connect(self.viewFlowUsagePlotSubWindow)
        self.actionViewBpodControl.toggled.connect(self.viewBpodControlSubWindow)
        self.actionViewExperimentSetup.toggled.connect(self.viewExperimentSetupDockWindow)

        self.applicationModeComboBox.currentIndexChanged.connect(self.switchApplicationMode)

        # self.experimentSetupDockWidget.visibilityChanged.connect(lambda x: self.updateViewMenu(self.experimentSetupDockWidget.objectName(), x))  # this unchecks the Expreiment Setup window when the whole app is minimized

        self.nTrialsSpinBox.valueChanged.connect(self.recordNumTrials)
        self.itiMinSpinBox.valueChanged.connect(self.recordMinITI)
        self.itiMaxSpinBox.valueChanged.connect(self.recordMaxITI)
        self.noResponseCutoffSpinBox.valueChanged.connect(self.recordNoResponseCutoff)
        self.autoWaterCutoffSpinBox.valueChanged.connect(self.recordAutoWaterCutoff)
        self.yMaxDoubleSpinBox.valueChanged.connect(lambda ymax: self.streaming.setYaxis(self.yMinDoubleSpinBox.value(), ymax))
        self.yMinDoubleSpinBox.valueChanged.connect(lambda ymin: self.streaming.setYaxis(ymin, self.yMaxDoubleSpinBox.value()))
        self.maxtSpinBox.valueChanged.connect(lambda maxt: self.streaming.setXaxis(maxt))
        self.dtDoubleSpinBox.valueChanged.connect(lambda dt: self.streaming.set_dt(dt))
        #self.plotIntervalSpinBox.valueChanged.connect(lambda x: self.streaming.setPlotInterval(x))
        self.sniffThresholdSpinBox.valueChanged.connect(lambda sniffth: self.streaming.setSniffLine(self.sniffThresholdSpinBox.value()))
        #self.sniffThresholdSpinBox.valueChanged.connect(lambda sniffth: self.BpodFlexChannelSettingsDialog.setSniffLine(self.sniffThresholdSpinBox.value()))
       
        self.leftSensorPortNumComboBox.currentTextChanged.connect(self.recordLeftSensorPort)
        self.leftWaterValvePortNumComboBox.currentTextChanged.connect(self.recordLeftWaterValvePort)
        self.leftWaterValveDurationSpinBox.valueChanged.connect(self.recordLeftWaterValveDuration)
        self.rightSensorPortNumComboBox.currentTextChanged.connect(self.recordRightSensorPort)
        self.rightWaterValvePortNumComboBox.currentTextChanged.connect(self.recordRightWaterValvePort)
        self.rightWaterValveDurationSpinBox.valueChanged.connect(self.recordRightWaterValveDuration)
        self.finalValvePortNumComboBox.currentTextChanged.connect(self.recordFinalValvePort)

        self.positionSlider.sliderMoved.connect(self.playBackWorker.setPosition)
        self.playLastTrial_Button.clicked.connect(self.playBackWorker.playLastTrial)
        self.mediaPlayer.stateChanged.connect(self.playBackWorker.mediaStateChanged)
        self.mediaPlayer.positionChanged.connect(self.playBackWorker.positionChanged)
        self.mediaPlayer.durationChanged.connect(self.playBackWorker.durationChanged)
        self.mediaPlayer.error.connect(self.playBackWorker.handleError)

        self.sniffThresholdSpinBox.valueChanged.connect(lambda sniffth: self.updateFlexChanThreshold1(sniffth))
        
        self.experimentTypeComboBox.currentTextChanged.connect(self.setExperimentType)

        self.selectCameraDataDestinationPushButton.clicked.connect(self.selectCameraDataDestination)



    def selectCameraDataDestination(self):
        dlg = QFileDialog()
        dlg.setDirectory(os.getcwd() + '\\camera_data')
        fname = dlg.getExistingDirectory(self, "Open Folder")
        self.CameraDataDestinationLineEdit.setText(fname)

    def setExperimentType(self):
        if self.experimentTypeComboBox.currentIndex() == 3:
            self.experimentType = 'Imaging'
            self.imaging = 1
        else:
            #self.experimentType = 'Behavior'
            self.imaging = 0
        

    def loadDefaults(self):

        
        if os.path.exists("defaults.json"):
           
            with open("defaults.json", 'r') as defaultSettings:
                self.defaultSettings = json.load(defaultSettings)

            self.bpodCOMPortSpinBox.setValue(self.defaultSettings['experimentSetup']['bpodCOMPort'])
            self.analogInputModuleCOMPortSpinBox.setValue(self.defaultSettings['experimentSetup']['analogInputModuleCOMPort'])
            self.olfaCheckBox.setChecked(self.defaultSettings['experimentSetup']['enableOlfactometer'])
            self.olfaConfigFileName = self.defaultSettings['experimentSetup']['olfaConfigFile']
            self.olfaConfigFileLineEdit.setText(self.defaultSettings['experimentSetup']['olfaConfigFile'])
            self.protocolFileName = self.defaultSettings['experimentSetup']['protocolFile']
            self.protocolFileLineEdit.setText(self.defaultSettings['experimentSetup']['protocolFile'])
            self.experimentTypeComboBox.setCurrentIndex(self.defaultSettings['experimentSetup']['experimentType'])
            self.shuffleMultiplierSpinBox.setValue(self.defaultSettings['experimentSetup']['shuffleMultiplier'])
            self.nTrialsSpinBox.setValue(self.defaultSettings['experimentSetup']['nTrials'])
            self.noResponseCutoffSpinBox.setValue(self.defaultSettings['experimentSetup']['noResponseCutoff'])
            self.autoWaterCutoffSpinBox.setValue(self.defaultSettings['experimentSetup']['autoWaterCutoff'])
            self.itiMaxSpinBox.setValue(self.defaultSettings['experimentSetup']['maxITI'])
            self.itiMinSpinBox.setValue(self.defaultSettings['experimentSetup']['minITI'])
            self.mouseNumberLineEdit.setText(str(self.defaultSettings['experimentSetup']['mouseNum']))
            self.rigLetterLineEdit.setText(self.defaultSettings['experimentSetup']['rig'])

            self.leftSensorPortNumComboBox.setCurrentIndex(self.defaultSettings['bpodChannels']['leftSensorPortNum'] - 1)  # Subtract 1 to get the index.
            self.leftWaterValvePortNumComboBox.setCurrentIndex(self.defaultSettings['bpodChannels']['leftWaterValvePortNum'] - 1)  # Subtract 1 to get the index.
            self.leftWaterValveDurationSpinBox.setValue(self.defaultSettings['bpodChannels']['leftWaterValveDuration'])
            self.rightSensorPortNumComboBox.setCurrentIndex(self.defaultSettings['bpodChannels']['rightSensorPortNum'] - 1)  # Subtract 1 to get the index.
            self.rightWaterValvePortNumComboBox.setCurrentIndex(self.defaultSettings['bpodChannels']['rightWaterValvePortNum'] - 1)  # Subtract 1 to get the index.
            self.rightWaterValveDurationSpinBox.setValue(self.defaultSettings['bpodChannels']['rightWaterValveDuration'])
            
            
            self.yMaxDoubleSpinBox.setValue(self.defaultSettings['streamingPlot']['y_max'])
            self.yMinDoubleSpinBox.setValue(self.defaultSettings['streamingPlot']['y_min'])
            self.maxtSpinBox.setValue(self.defaultSettings['streamingPlot']['max_t'])
            self.dtDoubleSpinBox.setValue(self.defaultSettings['streamingPlot']['dt'])
            self.plotIntervalSpinBox.setValue(self.defaultSettings['streamingPlot']['plotInterval'])

            if self.bpodFlexChannelSettingsDialog is None:  # In case the user starts experiment without configuring the bpod flex channel settings from the dialog window, create the dialog window object once here. There get the default settings for it.
                self.bpodFlexChannelSettingsDialog = BpodFlexChannelSettingsDialog(parent=self)
                self.bpodFlexChannelSettingsDialog.loadSettings(self.defaultSettings['bpodFlexChannels'])
                
                self.bpodFlexChannelSettingsDialog.accepted.connect(self.configureBpodFlexChannels)
                self.bpodFlexChannelSettingsDialog.accept()

            self.bpodFlexChannelSettingsDialog.loadSettings(self.defaultSettings['bpodFlexChannels'])
            flex_settings = self.bpodFlexChannelSettingsDialog.getSettings()
            self.dtDoubleSpinBox.setValue(flex_settings['samplingPeriod']/10000)
       

            if self.analogInputModuleSettingsDialog is None:  # In case the user starts experiment without configuring the analog input settings from the dialog window, create the dialog window object once here. Then get the default settings for it.
                self.analogInputModuleSettingsDialog = AnalogInputModuleSettingsDialog(parent=self)
                self.analogInputModuleSettingsDialog.accepted.connect(self.configureAnalogInputModule)
            self.analogInputModuleSettingsDialog.loadSettings(self.defaultSettings['analogInputModule'])

        else:
            QMessageBox.warning(self, 'Not Found', 'The defaults.json file was not found.')

    def updateViewMenu(self, objectName, visibility=None):
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
        elif (objectName == self.experimentSetupDockWidget.objectName()) and not visibility:
            self.actionViewExperimentSetup.setChecked(False)  # Un-check it from the View menu since the dock window was closed.

    def viewStreamingSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.streamingSubWindow.show()
            self.streamingSubWindow.widget().show()
        else:
            self.streamingSubWindow.hide()

    def viewResultsPlotSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.resultsPlotSubWindow.show()
            self.resultsPlotSubWindow.widget().show()
        else:
            self.resultsPlotSubWindow.hide()

    def viewFlowUsagePlotSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.flowUsagePlotSubWindow.show()
            self.flowUsagePlotSubWindow.widget().show()
        else:
            self.flowUsagePlotSubWindow.hide()

    def viewCurrentTrialSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.currentTrialSubWindow.show()
            self.currentTrialSubWindow.widget().show()
        else:
            self.currentTrialSubWindow.hide()

    def viewBpodControlSubWindow(self, checked):
        if checked:
            # I also need to show the subWindow's internal widget because for some reason it does not show automatically
            # when the subwindow is closed and then you check on the subWindow's View menu action to re-activate the subWindow,
            # despite the subWindow object not being deleted and not being removed from the mdiArea's subWindowList, and the subWindow's
            # internal widget object not being deleted either, all due to the setAttribute(Qt.WA_DeleteOnClose, False) declared above.
            self.bpodControlSubWindow.show()
            self.bpodControlSubWindow.widget().show()
        else:
            self.bpodControlSubWindow.hide()

    def viewExperimentSetupDockWindow(self, checked):
        if checked:
            self.experimentSetupDockWidget.show()
        else:
            self.experimentSetupDockWidget.hide()

    def launchBpodFlexChannelSettingsDialog(self):
        if self.bpodFlexChannelSettingsDialog is None:
            self.bpodFlexChannelSettingsDialog = BpodFlexChannelSettingsDialog(parent=self)
            self.bpodFlexChannelSettingsDialog.accepted.connect(self.configureBpodFlexChannels)
        self.bpodFlexChannelSettingsDialog.show()

    def launchAnalogInputModuleSettingsDialog(self):
        if self.analogInputModuleSettingsDialog is None:
            self.analogInputModuleSettingsDialog = AnalogInputModuleSettingsDialog(parent=self)
            self.analogInputModuleSettingsDialog.accepted.connect(self.configureAnalogInputModule)
        self.analogInputModuleSettingsDialog.show()

    def launchOlfaGUI(self):
        if self.olfaConfigFileName:
            try:
                self.olfas = olfactometry.Olfactometers(config_obj=self.olfaConfigFileName)
                self.olfas.show()
            except SerialException as err:
                QMessageBox.critical(self, "Error", f"Cannot connect to olfactometer.\n{err}")
                if self.olfas:
                    self.olfas.close_serials()  # close serial ports and let the user try again.
                    del self.olfas
                    self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.
                    QMessageBox.warning(self, "Error", "Please try again.")
        else:
            QMessageBox.warning(self, "Warning", "Please select an olfa config file first! Go to 'Olfactometer' menu > 'Select config file'")

    def setOdorStimuli(self):
        self.odorEditor = OdorEditorDialog(self.olfaConfigFileName)
        self.odorEditor.show()

    def launchOlfaEditor(self):
        # Loop through olfaConfigFileName, find number of olfas
        with open(self.olfaConfigFileName, 'r') as olfa_config:
            self.olfaConfigDict = json.load(olfa_config)
        self.olfaEditor = []
        for olfa_idx in range(0, len(self.olfaConfigDict['Olfactometers'])):
            self.olfaEditor.append(OlfaEditorDialog(self.olfaConfigFileName, olfa_idx))
            self.olfaEditor[olfa_idx].show()

    def launchProtocolEditor(self):
        if self.bpod is not None:
            events = self.bpod.hardware.channels.event_names
            outputs = self.bpod.hardware.channels.output_channel_names
            self.protocolEditor = ProtocolEditorDialog(events, outputs, self.protocolFileName)
            self.protocolEditor.show()
        else:
            QMessageBox.warning(self, "Warning", "Please connect to Bpod first. Click the 'Connect Devices' button.")

    def openProtocolFileNameDialog(self):
        if not os.path.isdir('protocol_files'):
            os.mkdir('protocol_files')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption="Open Protocol File", directory="protocol_files", filter="JSON Files (*.json)", options=options)
        if fileName:
            self.protocolFileName = fileName
            self.protocolFileLineEdit.setText(fileName)

    def openOlfaConfigFileNameDialog(self):
        if not os.path.isdir('olfactometry_config_files'):
            os.mkdir('olfactometry_config_files')
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getOpenFileName(parent=self, caption="Open Olfactometer Configuration File", directory="olfactometry_config_files", filter="JSON Files (*.json)", options=options)
        
        if fileName:
           
            self.olfaConfigFileName = fileName
            self.olfaConfigFileLineEdit.setText(fileName)


    def updateFlexChanThreshold1(self, sniffth):
        
        settings = self.bpodFlexChannelSettingsDialog.getSettings()
        settings['thresholds_1'][0] = ((sniffth/1000 / self.bpodFlexChannelSettingsDialog.maxFlexVoltage) * 4095)
        
        self.bpodFlexChannelSettingsDialog.loadSettings(settings)
        self.bpod.set_analog_input_thresholds(settings['thresholds_1'], settings['thresholds_2'])
        

    def configureBpodFlexChannels(self):
     
        if self.bpod is not None:
            if self.bpod.hardware.machine_type > 3:
                
                if self.bpodFlexChannelSettingsDialog is None:
                    self.bpodFlexChannelSettingsDialog = BpodFlexChannelSettingsDialog(parent=self)
                    self.bpodFlexChannelSettingsDialog.accepted.connect(self.configureBpodFlexChannels)
                
                self.bpodFlexChannelSettingsDialog.updateSettingsDict()
                settings = self.bpodFlexChannelSettingsDialog.getSettings()
               
                self.bpod.set_flex_channel_types(settings['channelTypes'])
                self.bpod.set_analog_input_sampling_interval(settings['samplingPeriod'])
                self.bpod.set_analog_input_thresholds(settings['thresholds_1'], settings['thresholds_2'])
                self.bpod.set_analog_input_threshold_polarity(settings['polarities_1'], settings['polarities_2'])
                self.bpod.set_analog_input_threshold_mode(settings['modes'])
                # update linked parameters in the streaming window accordingly
                self.dtDoubleSpinBox.setValue(settings['samplingPeriod']/10000)

    def configureAnalogInputModule(self):
        if self.adc is not None:
            if self.analogInputModuleSettingsDialog is None:  # In case the user starts experiment without configuring the analog input settings from the dialog window, create the dialog window object once here. Then get the default settings from it.
                self.analogInputModuleSettingsDialog = AnalogInputModuleSettingsDialog(parent=self)
                self.analogInputModuleSettingsDialog.accepted.connect(self.configureAnalogInputModule)
            settings = self.analogInputModuleSettingsDialog.getSettings()
            self.adc.setNactiveChannels(settings['nActiveChannels'])
            self.adc.setSamplingRate(settings['samplingRate'])
            self.adc.setInputRange(settings['inputRanges'])
            self.adc.setStream2USB(settings['enableUSBStreaming'])
            self.adc.setSMeventsEnabled(settings['enableSMEventReporting'])
            self.adc.setThresholds(settings['thresholdVoltages'])
            self.adc.setResetVoltages(settings['resetVoltages'])

    def startAnalogModule(self):
        self.adc.startReportingEvents()
        self.adc.startUSBStream()

    def stopAnalogModule(self):
        self.adc.stopUSBStream()

    def connectDevices(self):
        self.disconnectDevices()
        
        
        try:
            if self.analogInputModuleCOMPortSpinBox.value() > 0:
                self.adc = BpodAnalogIn(serial_port=f"COM{self.analogInputModuleCOMPortSpinBox.value()}")
                self.configureAnalogInputModule()
                # print('We are actually doing it!')
        except SerialException:
            if self.adc is not None:
                self.adc.close()
                del self.adc
                self.adc = None
            QMessageBox.warning(self, "Warning", "Cannot connect analog input module! Check that serial port is correct and try again!")
            return
        except AnalogInException as err:
            QMessageBox.warning(self, "Warning", f"Analog Input Module Error.\n{err}")
            return

      
        try:
           
            self.bpod = Bpod(serial_port=f"COM{self.bpodCOMPortSpinBox.value()}" if self.bpodCOMPortSpinBox.value() > 0 else None)
            self.configureBpodFlexChannels()

        except (BpodErrorException, SerialException, UnicodeDecodeError):
           
            if self.bpod is not None:
                self.bpod.close()
                del self.bpod
                self.bpod = None

            # Check if analog input module was already connected and close it to free the serial port because if it is connected, then when user clicks the "Connect Devices" button again,
            # a Serial Exception will be raised for the analog module since the program connects to it first before the bpod.
            if self.adc is not None:
                self.adc.close()
                del self.adc
                self.adc = None
            QMessageBox.warning(self, "Warning", "Cannot connect to bpod! Check that serial port is correct and try again!")
            return

        self.startButton.setEnabled(True)  # This means successful connection attempt for enabled devices.
        self.connectDevicesButton.setEnabled(False)  # Disable to prevent clicking again.
        self.connectDevicesButton.setText("Connected")
        self.disconnectDevicesButton.setEnabled(True)

        self.finalValveButton.setEnabled(True)
        self.leftWaterValveButton.setEnabled(True)
        self.rightWaterValveButton.setEnabled(True)
        self.flushLeftWaterButton.setEnabled(True)
        self.flushRightWaterButton.setEnabled(True)

    def disconnectDevices(self):
        if self.adc is not None:
            self.adc.close()
            del self.adc
            self.adc = None

        if self.bpod is not None:
            self.bpod.close()
            del self.bpod
            self.bpod = None

        self.startButton.setEnabled(False)
        self.connectDevicesButton.setEnabled(True)
        self.connectDevicesButton.setText("Connect Devices")
        self.disconnectDevicesButton.setEnabled(False)

        self.finalValveButton.setEnabled(False)
        self.leftWaterValveButton.setEnabled(False)
        self.rightWaterValveButton.setEnabled(False)
        self.flushLeftWaterButton.setEnabled(False)
        self.flushRightWaterButton.setEnabled(False)


    def endTask(self):
        #self.streaming.pauseAnimation()
        if self.adc is not None:
            self.stopAnalogModule()
            # self.getSDCardLog()

        self.stopRunningSignal.emit()
        logging.info("stopRunningSignal emitted")

        self.disconnectDevicesButton.setEnabled(True)
        self.startButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.pauseButton.setEnabled(False)
        self.pauseButton.setText('Pause')
        self.isPaused = False
        self.flushLeftWaterButton.setEnabled(True)
        self.flushRightWaterButton.setEnabled(True)
        self.actionConfigureBpodFlexChannels.setEnabled(True)  # re-enable the ability to configure flex channels since an experiment is not running.
        if self.adc is not None:
            #print('Placeholder')
            self.analogInputModuleCOMPortSpinBox.setEnabled(True)  # re-enable the ability to configure analog input settings since an experiment is not running.
        if self.olfaCheckBox.isChecked():
            self.actionLaunchOlfaGUI.setEnabled(True)  # re-enable the olfa GUI button after the experiment completes.
        self.experimentCompleteDialog()
        self.currentTrialProgressBar.setValue(0)

    def pauseExperiment(self):
        if self.isPaused:  # then resume
            if self.adc is not None:
                self.startAnalogModule()
            self.bpod.resume()
            self.protocolWorker.discardCurrentTrial()  # The analog data becomes out of sync with the bpod's time and the bpod erroneously detects a threshold crossing event immediately after resuming and thus transitions to the next state, so this stops the current trial and discards the data.
            self.streaming.resetPlot()
            self.streaming.resumeAnimation()
            self.isPaused = False
            self.pauseButton.setText('Pause')

        else:  # then pause
            if self.adc is not None:
                self.stopAnalogModule()
            self.bpod.pause()
            self.streaming.pauseAnimation()
            self.isPaused = True
            self.pauseButton.setText('Resume')

    def closeDevices(self):
        if self.adc is not None:
            self.adc.close()
            del self.adc
            self.adc = None
        if self.olfas is not None:
            self.olfas.close_serials()
            del self.olfas
            self.olfas = None
            # self.olfas.close()
        if self.bpod is not None:
            self.bpod.close()
            del self.bpod
            self.bpod = None

    def toggleFinalValve(self):
        if self.bpod is not None:
            if self.finalValveButton.isChecked():
                self.openValve(self.finalValve)
            else:
                self.closeValve(self.finalValve)

    def toggleLeftWaterValve(self):
        if self.bpod is not None:
            self.openValve(self.leftWaterValve)
            QTimer.singleShot(self.leftWaterValveDurationSpinBox.value(), lambda: self.closeValve(self.leftWaterValve))

    def toggleRightWaterValve(self):
        if self.bpod is not None:
            self.openValve(self.rightWaterValve)
            QTimer.singleShot(self.rightWaterValveDurationSpinBox.value(), lambda: self.closeValve(self.rightWaterValve))

    def openValve(self, channelNum):
        if self.bpod is not None:
            self.bpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=1)

    def closeValve(self, channelNum):
        if self.bpod is not None:
            self.bpod.manual_override(Bpod.ChannelTypes.OUTPUT, Bpod.ChannelNames.VALVE, channel_number=channelNum, value=0)

    def flushLeftWaterValve(self):
        if self.bpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.flushLeftWaterButton.setEnabled(False)
            self.flushRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.flushLeftWaterValveToggler)

            self.waterFlushProgress = QProgressDialog("Flushing left water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.leftWaterValveDurationSpinBox.value())

    def flushLeftWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self.closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.waterFlushProgress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self.closeValve(self.leftWaterValve)
                self.isOpen = False
            else:
                self.openValve(self.leftWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.waterFlushProgress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self.closeValve(self.leftWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def flushRightWaterValve(self):
        if self.bpod is not None:
            self.leftWaterValveButton.setEnabled(False)
            self.rightWaterValveButton.setEnabled(False)
            self.flushLeftWaterButton.setEnabled(False)
            self.flushRightWaterButton.setEnabled(False)
            self.startButton.setEnabled(False)

            self.timerCounter = 0
            self.isOpen = False
            self.timer = QTimer(self)
            self.timer.timeout.connect(self.flushRightWaterValveToggler)

            self.waterFlushProgress = QProgressDialog("Flushing right water valve...", "Cancel", 0, 100, self)
            self.waterFlushProgress.setWindowModality(Qt.WindowModal)

            self.timer.start(self.rightWaterValveDurationSpinBox.value())

    def flushRightWaterValveToggler(self):
        if self.waterFlushProgress.wasCanceled():  # first check if user cancelled.
            self.closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

        elif (self.timerCounter < 100):
            self.waterFlushProgress.setValue(self.timerCounter)  # update the progress bar.
            if self.isOpen:
                self.closeValve(self.rightWaterValve)
                self.isOpen = False
            else:
                self.openValve(self.rightWaterValve)
                self.isOpen = True
                self.timerCounter += 1  # increment inside if-else statement so that the valve opens 100 times.
        else:
            self.waterFlushProgress.setValue(self.timerCounter)  # At this point, self.timerCounter should be 100 so update the progress bar with final value.
            self.closeValve(self.rightWaterValve)
            self.timer.stop()

            self.leftWaterValveButton.setEnabled(True)
            self.rightWaterValveButton.setEnabled(True)
            self.flushLeftWaterButton.setEnabled(True)
            self.flushRightWaterButton.setEnabled(True)
            self.startButton.setEnabled(True)

    def recordNumTrials(self, value):
        if self.protocolWorker is not None:
            self.protocolWorker.setNumTrials(self.nTrialsSpinBox.value())

    def recordNoResponseCutoff(self, value):
        if self.protocolWorker is not None:
            self.protocolWorker.setNoResponseCutoff(value)
        if (value > 0):
            self.autoWaterCutoffSpinBox.setMaximum(value - 1)  # Make it 1 less than noResponseCutoff so that it happens before the experiment is aborted.
        else:
            self.autoWaterCutoffSpinBox.setMaximum(value)  # When value equals 0, the spinBox displays 'Never'. So set the maximum to zero to prevent it from happening.

    def recordAutoWaterCutoff(self, value):
        if self.protocolWorker is not None:
            self.protocolWorker.setAutoWaterCutoff(value)

    def recordMinITI(self, value):
        self.itiMaxSpinBox.setMinimum(value)  # Do not allow itiMaxSpinBox to hold a value less than itiMinSpinBox's current value.
        if self.protocolWorker is not None:
            self.protocolWorker.setMinITI(value)

    def recordMaxITI(self, value):
        self.itiMinSpinBox.setMaximum(value)  # Do not allow itiMinSpinBox to hold a value greater than itiMaxSpinBox's current value.
        if self.protocolWorker is not None:
            self.protocolWorker.setMaxITI(value)

    def recordLeftSensorPort(self, text):
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftSensorPort(int(text))

    def recordLeftWaterValvePort(self, text):
        self.leftWaterValve = int(text)
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftWaterValvePort(int(text))

    def recordLeftWaterValveDuration(self, value):
        if self.protocolWorker is not None:
            self.protocolWorker.setLeftWaterDuration(value)

    def recordRightSensorPort(self, text):
        if self.protocolWorker is not None:
            self.protocolWorker.setRightSensorPort(int(text))

    def recordRightWaterValvePort(self, text):
        self.rightWaterValve = int(text)
        if self.protocolWorker is not None:
            self.protocolWorker.setRightWaterValvePort(int(text))

    def recordRightWaterValveDuration(self, value):
        if self.protocolWorker is not None:
            self.protocolWorker.setRightWaterDuration(value)

    def recordFinalValvePort(self, text):
        self.finalValve = int(text)
        if self.protocolWorker is not None:
            self.protocolWorker.setFinalValvePort(int(text))

    def switchApplicationMode(self, currentIndex):
        if (currentIndex == 0):
            self.rfidReaderCOMPortSpinBox.setEnabled(False)
            self.protocolFileLabel.setText("Protocol File:")
            self.nTrialsSpinBox.setEnabled(True)
            self.noResponseCutoffSpinBox.setEnabled(True)
            self.autoWaterCutoffSpinBox.setEnabled(True)
            self.itiMaxSpinBox.setEnabled(True)
            self.itiMinSpinBox.setEnabled(True)
            self.mouseNumberLineEdit.setEnabled(True)
            self.rigLetterLineEdit.setEnabled(True)
        elif (currentIndex == 1):
            self.rfidReaderCOMPortSpinBox.setEnabled(True)
            self.protocolFileLabel.setText("Schedule File:")
            self.nTrialsSpinBox.setEnabled(False)
            self.noResponseCutoffSpinBox.setEnabled(False)
            self.autoWaterCutoffSpinBox.setEnabled(False)
            self.itiMaxSpinBox.setEnabled(False)
            self.itiMinSpinBox.setEnabled(False)
            self.mouseNumberLineEdit.setEnabled(False)
            self.rigLetterLineEdit.setEnabled(False)

    def updateCurrentState(self, stateName):
        self.currentStateLineEdit.setText(stateName)

    def updateCurrentTrialProgressBar(self, value):
        self.currentTrialProgressBar.setValue(value + 1)

    def updateResponseResult(self, result):
        self.responseResultLineEdit.setText(result)

    def updateSessionTotals(self, totalsDict):
        self.totalCorrectLineEdit.setText(str(totalsDict['totalCorrect']))
        self.totalWrongLineEdit.setText(str(totalsDict['totalWrong']))
        self.totalNoResponsesLineEdit.setText(str(totalsDict['totalNoResponses']))
        self.totalPercentCorrectLineEdit.setText(str(totalsDict['totalPercentCorrect']))

    def updateCurrentTrialInfo(self, trialInfoDict):
        # Check if not empty.
        
        if trialInfoDict:
            self.trialNumLineEdit.setText(str(trialInfoDict['currentTrialNum']))
            self.correctResponseLineEdit.setText(trialInfoDict['correctResponse'])
            self.itiLineEdit.setText(str(trialInfoDict['currentITI']))
            self.currentTrialProgressBar.setRange(0, trialInfoDict['nStates'])

            if ('stimList' in trialInfoDict) and (len(trialInfoDict['stimList']) > 0):
                # Show olfa name
                olfa_names =  list(trialInfoDict['stimList'][0]['olfas'].keys()  )
                self.olfaNamesLineEdit.setText(olfa_names[0])
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

    def noResponseAbortDialog(self):
        QMessageBox.information(self, "Notice", "Session aborted due to too many consecutive no responses.")

    def experimentCompleteDialog(self):
        QMessageBox.information(self, "Success", "Experiment finished!")

    def cannotConnectOlfaDialog(self):
        # Since the ProtocolWorker's self.olfas object cannot access the serial port, maybe it is current in use by the main thread.
        # So check if main thread's self.olfas exists and if so, close the serial port and delete the object.
        if self.olfas:
            self.olfas.close_serials()  # close serial ports and let the user try again.
            del self.olfas
        QMessageBox.warning(self, "Warning", "Cannot connect to olfactometer! Check that serial port is correct and try again.")

    def invalidFileDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Invalid protocol file or olfa config file selected. Experiment aborted.\
            \nThe following key was not found in its respective .json file and thus caused a KeyError:\
            \n{error}")

    def olfaExceptionDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Experiment aborted because the olfactometer raised the following exception:\n{error}")

    def bpodExceptionDialog(self, error):
        QMessageBox.warning(self, "Warning", f"Experiment aborted because the bpod raised the following exception:\n{error}")

    def runTask(self):

        if (self.mouseNumberLineEdit.text() == ''):
            QMessageBox.warning(self, "Warning", "Please enter mouse number!")
            return
        elif (self.rigLetterLineEdit.text() == ''):
            QMessageBox.warning(self, "Warning", "Please enter rig letter!")
            return
        elif (self.protocolFileName == ''):
            QMessageBox.warning(self, "Warning", "Please load a protocol file. Go to 'File' > 'Open'.")
            return

        if self.imaging:
                self.camera = MicroManagerPrime95B(ACQ_CONFIG_FILE)                
                  
                dateTimeString = datetime.now().strftime("%Y-%m-%d_%H%M%S")
                #camera_data_dir = f"H:\\repos\\PyBpodGUI\\camera_data\\{dateTimeString}_M_{self.mouseNumberLineEdit.text()}\\"
                camera_data_dir = self.CameraDataDestinationLineEdit.text() +'\\' +  f'{dateTimeString}_M_{self.mouseNumberLineEdit.text()}\\'
                if not os.path.exists(camera_data_dir):
                    os.makedirs(camera_data_dir)

                self.camera.set_camera_data_dir(camera_data_dir)
                self.playBackWorker.updateCamera(self.camera)     

        # Safety check to close and delete the main thread's olfactometer (if in use or was in use) before running the protocolWorker's thread
        # so that the protocolWorker's thread can access the olfactometer's serial port if the user enables the olfactometer for the experiment.
        if self.olfas:
            self.olfas.close_serials()
            del self.olfas
            self.olfas = None  # Create the empty variable after deleting to avoid AttributeError.

        # Check if adc was created which would mean the user provided a COM port and the analog input module was connected.
        if self.adc is not None:
            self.startAnalogModule()
        
        print(self.bpod)
        
        self.runInputEventThread()
        self.runSaveDataThread()
        self.runReadingDataThread()
        self.runProtocolThread()
       
        self.runStreamingThread()
        if self.trialPlaybackcheckBox.isChecked():
            self.runPlaybackThread()
        # Emit signal for experiment start
        self.startExperimentSignal.emit()

        #if not self.streaming.startAnimation():
        #    self.streaming.resetPlot()
        #    self.streaming.resumeAnimation()

        self.resultsPlot.setExperimentType(self.experimentTypeComboBox.currentIndex())
        self.flowUsagePlot.setExperimentType(self.experimentTypeComboBox.currentIndex())
        if (self.experimentTypeComboBox.currentIndex() == 2):
            self.flowUsagePlotSubWindow.showShaded()

        
        self.startButton.setEnabled(False)
        self.flushLeftWaterButton.setEnabled(False)
        self.flushRightWaterButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.pauseButton.setEnabled(True)
        self.disconnectDevicesButton.setEnabled(False)  # Do not let user disconnect devices while experiment is running.
        self.actionConfigureBpodFlexChannels.setEnabled(False)  # Prevent user from configuring flex channels while experiment is running.
        if self.adc is not None:
            self.analogInputModuleCOMPortSpinBox.setEnabled(False)  # Prevent user from configuring analog input settings while experiment is running.
        if self.olfaCheckBox.isChecked():
            self.actionLaunchOlfaGUI.setEnabled(False)  # Disable the olfa GUI button if the olfactometer will be used for the experiment by the protocolWorker's thread.
            # The user can still use the olfactometer GUI during an experiment (i.e. for manual control) but must uncheck the olfa check box to let
            # the protocolWorker's thread know not to use it. Only one object can access a serial port at any given time.

## THREADS

    def runInputEventThread(self):
        logging.info(f"from _runInputEventThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        self.inputEventThread = QThread(parent=self)

        ## hack fix for Qthread deleted error, more info in __init__
        self.oldInputEventThreads.append(self.inputEventThread)

        self.inputEventWorker = InputEventWorker(self.bpod)
        self.inputEventWorker.moveToThread(self.inputEventThread)
        self.inputEventThread.started.connect(self.inputEventWorker.run)
        self.inputEventWorker.finished.connect(self.inputEventThread.quit)
        self.inputEventWorker.finished.connect(self.inputEventWorker.deleteLater)
        self.inputEventThread.finished.connect(self.inputEventThread.deleteLater)
        self.inputEventWorker.inputEventSignal.connect(self.streaming.setInputEvent)
        #self.stopRunningSignal.connect(self.inputEventWorker.stopRunning)
        self.stopRunningSignal.connect(lambda: self.inputEventWorker.stopRunning())
        self.inputEventThread.start()
        logging.info(f"inputEventThread is running {self.inputEventThread.isRunning()}")
    

    def runSaveDataThread(self):
        logging.info(f"from _runSaveDataThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        if self.analogInputModuleSettingsDialog is None:  # if it wasnt created yet, then create it but only create it once.
            self.analogInputModuleSettingsDialog = AnalogInputModuleSettingsDialog(parent=self)
            self.analogInputModuleSettingsDialog.accepted.connect(self.configureAnalogInputModule)
        settingsDict = self.analogInputModuleSettingsDialog.getSettings()
        self.saveDataThread = QThread(parent=self)

        ## hack fix for Qthread deleted error, more info in __init__
        self.oldSaveDataThreads.append(self.saveDataThread)

        self.saveDataWorker = SaveDataWorker(
            self.mouseNumberLineEdit.text(), self.rigLetterLineEdit.text(), self.protocolFileName, self.olfaConfigFileName, self.shuffleMultiplierSpinBox.value(), self.itiMinSpinBox.value(), self.itiMaxSpinBox.value(),
            self.leftWaterValveDurationSpinBox.value(), self.rightWaterValveDurationSpinBox.value(), settingsDict, self.adc, self.bpod
        )
        self.saveDataWorker.moveToThread(self.saveDataThread)
        self.saveDataThread.started.connect(self.saveDataWorker.run)
        self.saveDataWorker.finished.connect(self.saveDataThread.quit)
        self.saveDataWorker.finished.connect(self.saveDataWorker.deleteLater)
        self.saveDataThread.finished.connect(self.saveDataThread.deleteLater)
        #self.saveDataWorker.analogDataSignal.connect(self.streaming.getData)
        self.stopRunningSignal.connect(lambda: self.saveDataWorker.stopRunning())  # Need to use lambda, to explicitly make function call (from the main thread). Because the saveDataWorker thread will never call it since its in a infinite loop.
        self.saveDataThread.start()
        logging.info(f"saveDataThread running? {self.saveDataThread.isRunning()}")
        

    def runReadingDataThread(self):
        self.readingDataThread = QThread(parent=self)
        
        if self.analogInputModuleSettingsDialog is None:  # if it wasnt created yet, then create it but only create it once.
            self.analogInputModuleSettingsDialog = AnalogInputModuleSettingsDialog(parent=self)
            self.analogInputModuleSettingsDialog.accepted.connect(self.configureAnalogInputModule)
        settingsDict = self.analogInputModuleSettingsDialog.getSettings()
        print(f'\nPrinting bpod {self.bpod}\n\n')
        self.readDataWorker = ReadDataWorker(settingsDict, self.bpod, self.adc)
        self.readDataWorker.moveToThread(self.readingDataThread)
        
        
        
        self.readDataWorker.finished.connect(self.saveDataThread.quit)
        self.readDataWorker.finished.connect(self.saveDataWorker.deleteLater)
        self.readingDataThread.finished.connect(self.saveDataWorker.deleteLater)

        self.readDataWorker.finished.connect(self.readingDataThread.quit)
        self.readDataWorker.finished.connect(self.readDataWorker.deleteLater)
        self.readingDataThread.finished.connect(self.readingDataThread.deleteLater)

        self.readingDataThread.started.connect(self.readDataWorker.run)

        self.saveDataWorker.analogDataSignalProcessed.connect(lambda x :self.streaming.getData(x))# give analog data to streamer for plotting
        self.readDataWorker.flexAnalogDataSignal.connect(lambda x : self.saveDataWorker.saveFlexAnalogDataFromBpod(x)) # give analog data to SaveDataWorker for saving
        self.readDataWorker.analogDataSignal.connect( lambda x : self.saveDataWorker.saveAnalogDataFromModule(x)) # give analog data to SaveDataWorker for saving
        
        self.stopRunningSignal.connect(lambda: self.readDataWorker.stopRunning()) 
        self.readingDataThread.start()
        logging.info(f"readDataThread running? {self.readingDataThread.isRunning()}")


    def runStreamingThread(self):
        # The streaming Thread is associated to a worker that is created before ever starting,
        # so it can never be deleted and recreated or the worker won't recognize it as its own thread
        if self.streamingThread is None:
            self.streamingThread = QThread(parent=self)

        self.streaming.moveToThread(self.streamingThread)
        #self.saveDataWorker.analogDataSignal.connect(self.streaming.getData)
        #self.inputEventWorker.inputEventSignal.connect(self.streaming.setInputEvent)
        self.streaming.finished.connect(self.streamingThread.quit)
        #self.streaming.finished.connect(self.streaming.deleteLater)
        #self.streamingThread.finished.connect(self.streamingThread.deleteLater)
        self.startExperimentSignal.connect(self.streaming.resetPlot)
        self.stopRunningSignal.connect(self.streaming.stopRunning)
        #self.streaming.inputPlottedSignal.connect(self.streaming.clear)
        self.streamingThread.start()
        logging.info(f"streamingDataThread running? {self.streamingThread.isRunning()}")


    def runProtocolThread(self):
        logging.info(f"from _runProtocolThread, thread is {QThread.currentThread()} and ID is {int(QThread.currentThreadId())}")
        
        self.protocolThread = QThread(parent=self)

        ## hack fix for Qthread deleted error, more info in __init__
        self.oldProtocolThreads.append(self.protocolThread)
        #self.oldProtocolWorkers.append(self.protocolWorker)

    
        self.protocolWorker = ProtocolWorker(
            self.bpod, self.protocolFileName, self.olfaConfigFileName, self.experimentTypeComboBox.currentText(), self.camera, self.shuffleMultiplierSpinBox.value(), self.odorEditor.all_trials_dict,
            int(self.leftSensorPortNumComboBox.currentText()), self.leftWaterValve, self.leftWaterValveDurationSpinBox.value(),
            int(self.rightSensorPortNumComboBox.currentText()), self.rightWaterValve, self.rightWaterValveDurationSpinBox.value(),
            self.finalValve, self.itiMinSpinBox.value(), self.itiMaxSpinBox.value(), self.noResponseCutoffSpinBox.value(), self.autoWaterCutoffSpinBox.value(), self.olfaCheckBox.isChecked(), self.nTrialsSpinBox.value()
        )
        self.protocolWorker.moveToThread(self.protocolThread)
        self.protocolThread.started.connect(self.protocolWorker.run)
        
        self.protocolWorker.finished.connect(self.protocolThread.quit)
        self.protocolWorker.finished.connect(self.endTask)  # This serves to stop the other threads when the protocol thread completes all trials.
        self.protocolWorker.finished.connect(self.protocolWorker.deleteLater)
        self.protocolThread.finished.connect(self.protocolThread.deleteLater)

        self.protocolWorker.newStateSignal.connect(self.updateCurrentState)
        self.protocolWorker.newStateSignal.connect(self.streaming.getStateNameTime)
        #self.protocolWorker.newStateSignal.connect(self.streaming.checkOdorPresentation)
        self.protocolWorker.stateNumSignal.connect(self.updateCurrentTrialProgressBar)
        self.protocolWorker.responseResultSignal.connect(self.updateResponseResult)
        self.protocolWorker.newTrialInfoSignal.connect(self.updateCurrentTrialInfo)  # This works without lambda because 'self.updateCurrentTrialInfo' is in the main thread. # the input to the function is the trial_dict
        self.protocolWorker.resultsCounterListSignal.connect(self.resultsPlot.updatePlot)
        self.protocolWorker.resultsCounterListSignal.connect(self.flowUsagePlot.updatePlot)
        self.protocolWorker.duplicateVialsSignal.connect(self.resultsPlot.receiveDuplicatesDict)
        self.protocolWorker.duplicateVialsSignal.connect(self.flowUsagePlot.receiveDuplicatesDict)
        self.protocolWorker.totalsDictSignal.connect(self.updateSessionTotals)
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.saveDataWorker.receiveInfoDict(x))
        self.protocolWorker.saveTrialDataDictSignal.connect(lambda x: self.readDataWorker.receiveInfoDict(x))  # 'x' is the dictionary parameter emitted from 'saveTrialDataDictSignal' and passed into 'receiveInfoDict(x)'
        self.protocolWorker.noResponseAbortSignal.connect(self.noResponseAbortDialog)
        self.protocolWorker.olfaNotConnectedSignal.connect(self.cannotConnectOlfaDialog)
        self.protocolWorker.olfaExceptionSignal.connect(self.olfaExceptionDialog)
        self.protocolWorker.invalidFileSignal.connect(self.invalidFileDialog)
        self.protocolWorker.bpodExceptionSignal.connect(self.bpodExceptionDialog)
        self.stopRunningSignal.connect(lambda: self.protocolWorker.stopRunning())  # I use lambda because the run_state_machine is a blocking function so the protocolThread will not be able to call stop_trial if the user clicks the stop button mid trial.
        #self.stopRunningSignal.connect(self.protocolWorker.stopRunning) 
        self.protocolThread.start()
        logging.info(f"protocolThread running? {self.protocolThread.isRunning()}")
 

    def runPlaybackThread(self):
        # The playback Thread is associated to a worker that is created before ever starting,
        # so it can never be deleted and recreated or the worker won't recognize it as its own thread

        if self.playbackThread is None:
            self.playbackThread = QThread(parent=self)

        self.playBackWorker.moveToThread(self.playbackThread)
        self.protocolWorker.saveVideoSignal.connect(self.playBackWorker.playLastTrial)
        self.stopRunningSignal.connect(lambda: self.playbackThread.quit())  # I use lambda because the run_state_machine is a blocking function so the protocolThread will not be able to call stop_trial if the user clicks the stop button mid trial.
       
        self.playbackThread.start()
        


    def bpodClose(self):
        self.bpod.close()
        
import atexit

if __name__ == "__main__":
    # Check whether there is already a running QApplication (e.g., if running
    # from an IDE).
    qapp = QApplication.instance()
    if not qapp:
        qapp = QApplication(sys.argv)

    win = Window()
    # Solution for bpod conncetion issue
    #atexit.register(win.bpodClose)

    win.show()
    win.activateWindow()
    win.raise_()
    status = qapp.exec_()
    win.closeDevices()
    sys.exit(status)
