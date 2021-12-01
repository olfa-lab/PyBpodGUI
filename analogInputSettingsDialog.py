import logging
from PyQt5.QtWidgets import QDialog
from ui_files.analog_input_settings_ui import Ui_Dialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


class AnalogInputSettingsDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.connectSignalsSlots()
        self._rangeLimits = {'-10V:10V': [-10.0, 10.0], '-5V:5V': [-5.0, 5.0], '-2.5V:2.5V': [-2.5, 2.5],'0V:10V': [0.0, 10.0]}
        self.settingsDict = {
            'nActiveChannels': self.nActiveChannelsSpinBox.value(),
            'samplingRate': self.samplingRateSpinBox.value(),
            'inputRanges': [
                self.inputVoltageRangeComboBox_1.currentText(),
                self.inputVoltageRangeComboBox_2.currentText(),
                self.inputVoltageRangeComboBox_3.currentText(),
                self.inputVoltageRangeComboBox_4.currentText(),
                self.inputVoltageRangeComboBox_5.currentText(),
                self.inputVoltageRangeComboBox_6.currentText(),
                self.inputVoltageRangeComboBox_7.currentText(),
                self.inputVoltageRangeComboBox_8.currentText()
            ],
            'thresholdVoltages': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'resetVoltages': [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
            'enableSMEventReporting': [0, 0, 0, 0, 0, 0, 0, 0],
            'enableUSBStreaming': [0, 0, 0, 0, 0, 0, 0, 0],
            'enableModuleStreaming': [0, 0, 0, 0, 0, 0, 0, 0]
        }

    def connectSignalsSlots(self):
        self.nActiveChannelsSpinBox.valueChanged.connect(self.enableActiveChannels)
        self.samplingRateSpinBox.valueChanged.connect(self.recordSamplingRate)
        self.inputVoltageRangeComboBox_1.currentTextChanged.connect(self.recordInputVoltageRangeChannel_1)
        self.inputVoltageRangeComboBox_2.currentTextChanged.connect(self.recordInputVoltageRangeChannel_2)
        self.inputVoltageRangeComboBox_3.currentTextChanged.connect(self.recordInputVoltageRangeChannel_3)
        self.inputVoltageRangeComboBox_4.currentTextChanged.connect(self.recordInputVoltageRangeChannel_4)
        self.inputVoltageRangeComboBox_5.currentTextChanged.connect(self.recordInputVoltageRangeChannel_5)
        self.inputVoltageRangeComboBox_6.currentTextChanged.connect(self.recordInputVoltageRangeChannel_6)
        self.inputVoltageRangeComboBox_7.currentTextChanged.connect(self.recordInputVoltageRangeChannel_7)
        self.inputVoltageRangeComboBox_8.currentTextChanged.connect(self.recordInputVoltageRangeChannel_8)
        self.thresholdVoltageDoubleSpinBox_1.valueChanged.connect(self.recordThresholdVoltageChannel_1)
        self.thresholdVoltageDoubleSpinBox_2.valueChanged.connect(self.recordThresholdVoltageChannel_2)
        self.thresholdVoltageDoubleSpinBox_3.valueChanged.connect(self.recordThresholdVoltageChannel_3)
        self.thresholdVoltageDoubleSpinBox_4.valueChanged.connect(self.recordThresholdVoltageChannel_4)
        self.thresholdVoltageDoubleSpinBox_5.valueChanged.connect(self.recordThresholdVoltageChannel_5)
        self.thresholdVoltageDoubleSpinBox_6.valueChanged.connect(self.recordThresholdVoltageChannel_6)
        self.thresholdVoltageDoubleSpinBox_7.valueChanged.connect(self.recordThresholdVoltageChannel_7)
        self.thresholdVoltageDoubleSpinBox_8.valueChanged.connect(self.recordThresholdVoltageChannel_8)
        self.resetVoltageDoubleSpinBox_1.valueChanged.connect(self.recordResetVoltageChannel_1)
        self.resetVoltageDoubleSpinBox_2.valueChanged.connect(self.recordResetVoltageChannel_2)
        self.resetVoltageDoubleSpinBox_3.valueChanged.connect(self.recordResetVoltageChannel_3)
        self.resetVoltageDoubleSpinBox_4.valueChanged.connect(self.recordResetVoltageChannel_4)
        self.resetVoltageDoubleSpinBox_5.valueChanged.connect(self.recordResetVoltageChannel_5)
        self.resetVoltageDoubleSpinBox_6.valueChanged.connect(self.recordResetVoltageChannel_6)
        self.resetVoltageDoubleSpinBox_7.valueChanged.connect(self.recordResetVoltageChannel_7)
        self.resetVoltageDoubleSpinBox_8.valueChanged.connect(self.recordResetVoltageChannel_8)
        self.enableSMEventReportingCheckBox_1.stateChanged.connect(self.recordEnableSMEventReportingChannel_1)
        self.enableSMEventReportingCheckBox_2.stateChanged.connect(self.recordEnableSMEventReportingChannel_2)
        self.enableSMEventReportingCheckBox_3.stateChanged.connect(self.recordEnableSMEventReportingChannel_3)
        self.enableSMEventReportingCheckBox_4.stateChanged.connect(self.recordEnableSMEventReportingChannel_4)
        self.enableSMEventReportingCheckBox_5.stateChanged.connect(self.recordEnableSMEventReportingChannel_5)
        self.enableSMEventReportingCheckBox_6.stateChanged.connect(self.recordEnableSMEventReportingChannel_6)
        self.enableSMEventReportingCheckBox_7.stateChanged.connect(self.recordEnableSMEventReportingChannel_7)
        self.enableSMEventReportingCheckBox_8.stateChanged.connect(self.recordEnableSMEventReportingChannel_8)
        self.enableUSBStreamingCheckBox_1.stateChanged.connect(self.recordEnableUSBStreamingChannel_1)
        self.enableUSBStreamingCheckBox_2.stateChanged.connect(self.recordEnableUSBStreamingChannel_2)
        self.enableUSBStreamingCheckBox_3.stateChanged.connect(self.recordEnableUSBStreamingChannel_3)
        self.enableUSBStreamingCheckBox_4.stateChanged.connect(self.recordEnableUSBStreamingChannel_4)
        self.enableUSBStreamingCheckBox_5.stateChanged.connect(self.recordEnableUSBStreamingChannel_5)
        self.enableUSBStreamingCheckBox_6.stateChanged.connect(self.recordEnableUSBStreamingChannel_6)
        self.enableUSBStreamingCheckBox_7.stateChanged.connect(self.recordEnableUSBStreamingChannel_7)
        self.enableUSBStreamingCheckBox_8.stateChanged.connect(self.recordEnableUSBStreamingChannel_8)
        self.enableModuleStreamingCheckBox_1.stateChanged.connect(self.recordEnableModuleStreamingChannel_1)
        self.enableModuleStreamingCheckBox_2.stateChanged.connect(self.recordEnableModuleStreamingChannel_2)
        self.enableModuleStreamingCheckBox_3.stateChanged.connect(self.recordEnableModuleStreamingChannel_3)
        self.enableModuleStreamingCheckBox_4.stateChanged.connect(self.recordEnableModuleStreamingChannel_4)
        self.enableModuleStreamingCheckBox_5.stateChanged.connect(self.recordEnableModuleStreamingChannel_5)
        self.enableModuleStreamingCheckBox_6.stateChanged.connect(self.recordEnableModuleStreamingChannel_6)
        self.enableModuleStreamingCheckBox_7.stateChanged.connect(self.recordEnableModuleStreamingChannel_7)
        self.enableModuleStreamingCheckBox_8.stateChanged.connect(self.recordEnableModuleStreamingChannel_8)

    def loadSettings(self, settingsDict):
        self.settingsDict = settingsDict
        self.nActiveChannelsSpinBox.setValue(settingsDict['nActiveChannels'])
        self.samplingRateSpinBox.setValue(settingsDict['samplingRate'])
        self.inputVoltageRangeComboBox_1.setCurrentText(settingsDict['inputRanges'][0])
        self.inputVoltageRangeComboBox_2.setCurrentText(settingsDict['inputRanges'][1])
        self.inputVoltageRangeComboBox_3.setCurrentText(settingsDict['inputRanges'][2])
        self.inputVoltageRangeComboBox_4.setCurrentText(settingsDict['inputRanges'][3])
        self.inputVoltageRangeComboBox_5.setCurrentText(settingsDict['inputRanges'][4])
        self.inputVoltageRangeComboBox_6.setCurrentText(settingsDict['inputRanges'][5])
        self.inputVoltageRangeComboBox_7.setCurrentText(settingsDict['inputRanges'][6])
        self.inputVoltageRangeComboBox_8.setCurrentText(settingsDict['inputRanges'][7])
        self.thresholdVoltageDoubleSpinBox_1.setValue(settingsDict['thresholdVoltages'][0])
        self.thresholdVoltageDoubleSpinBox_2.setValue(settingsDict['thresholdVoltages'][1])
        self.thresholdVoltageDoubleSpinBox_3.setValue(settingsDict['thresholdVoltages'][2])
        self.thresholdVoltageDoubleSpinBox_4.setValue(settingsDict['thresholdVoltages'][3])
        self.thresholdVoltageDoubleSpinBox_5.setValue(settingsDict['thresholdVoltages'][4])
        self.thresholdVoltageDoubleSpinBox_6.setValue(settingsDict['thresholdVoltages'][5])
        self.thresholdVoltageDoubleSpinBox_7.setValue(settingsDict['thresholdVoltages'][6])
        self.thresholdVoltageDoubleSpinBox_8.setValue(settingsDict['thresholdVoltages'][7])
        self.resetVoltageDoubleSpinBox_1.setValue(settingsDict['resetVoltages'][0])
        self.resetVoltageDoubleSpinBox_2.setValue(settingsDict['resetVoltages'][1])
        self.resetVoltageDoubleSpinBox_3.setValue(settingsDict['resetVoltages'][2])
        self.resetVoltageDoubleSpinBox_4.setValue(settingsDict['resetVoltages'][3])
        self.resetVoltageDoubleSpinBox_5.setValue(settingsDict['resetVoltages'][4])
        self.resetVoltageDoubleSpinBox_6.setValue(settingsDict['resetVoltages'][5])
        self.resetVoltageDoubleSpinBox_7.setValue(settingsDict['resetVoltages'][6])
        self.resetVoltageDoubleSpinBox_8.setValue(settingsDict['resetVoltages'][7])
        self.enableSMEventReportingCheckBox_1.setChecked(settingsDict['enableSMEventReporting'][0])
        self.enableSMEventReportingCheckBox_2.setChecked(settingsDict['enableSMEventReporting'][1])
        self.enableSMEventReportingCheckBox_3.setChecked(settingsDict['enableSMEventReporting'][2])
        self.enableSMEventReportingCheckBox_4.setChecked(settingsDict['enableSMEventReporting'][3])
        self.enableSMEventReportingCheckBox_5.setChecked(settingsDict['enableSMEventReporting'][4])
        self.enableSMEventReportingCheckBox_6.setChecked(settingsDict['enableSMEventReporting'][5])
        self.enableSMEventReportingCheckBox_7.setChecked(settingsDict['enableSMEventReporting'][6])
        self.enableSMEventReportingCheckBox_8.setChecked(settingsDict['enableSMEventReporting'][7])
        self.enableUSBStreamingCheckBox_1.setChecked(settingsDict['enableUSBStreaming'][0])
        self.enableUSBStreamingCheckBox_2.setChecked(settingsDict['enableUSBStreaming'][1])
        self.enableUSBStreamingCheckBox_3.setChecked(settingsDict['enableUSBStreaming'][2])
        self.enableUSBStreamingCheckBox_4.setChecked(settingsDict['enableUSBStreaming'][3])
        self.enableUSBStreamingCheckBox_5.setChecked(settingsDict['enableUSBStreaming'][4])
        self.enableUSBStreamingCheckBox_6.setChecked(settingsDict['enableUSBStreaming'][5])
        self.enableUSBStreamingCheckBox_7.setChecked(settingsDict['enableUSBStreaming'][6])
        self.enableUSBStreamingCheckBox_8.setChecked(settingsDict['enableUSBStreaming'][7])
        self.enableModuleStreamingCheckBox_1.setChecked(settingsDict['enableModuleStreaming'][0])
        self.enableModuleStreamingCheckBox_2.setChecked(settingsDict['enableModuleStreaming'][1])
        self.enableModuleStreamingCheckBox_3.setChecked(settingsDict['enableModuleStreaming'][2])
        self.enableModuleStreamingCheckBox_4.setChecked(settingsDict['enableModuleStreaming'][3])
        self.enableModuleStreamingCheckBox_5.setChecked(settingsDict['enableModuleStreaming'][4])
        self.enableModuleStreamingCheckBox_6.setChecked(settingsDict['enableModuleStreaming'][5])
        self.enableModuleStreamingCheckBox_7.setChecked(settingsDict['enableModuleStreaming'][6])
        self.enableModuleStreamingCheckBox_8.setChecked(settingsDict['enableModuleStreaming'][7])

    def getSettings(self):
        return self.settingsDict

    def recordSamplingRate(self, value):
        self.settingsDict['samplingRate'] = value
    
    def recordInputVoltageRangeChannel_1(self, rangeText):
        self.settingsDict['inputRanges'][0] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_1.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_1.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_2(self, rangeText):
        self.settingsDict['inputRanges'][1] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_2.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_2.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_3(self, rangeText):
        self.settingsDict['inputRanges'][2] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_3.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_3.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_4(self, rangeText):
        self.settingsDict['inputRanges'][3] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_4.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_4.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_5(self, rangeText):
        self.settingsDict['inputRanges'][4] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_5.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_5.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_6(self, rangeText):
        self.settingsDict['inputRanges'][5] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_6.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_6.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_7(self, rangeText):
        self.settingsDict['inputRanges'][6] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_7.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_7.setRange(limits[0], limits[1])

    def recordInputVoltageRangeChannel_8(self, rangeText):
        self.settingsDict['inputRanges'][7] = rangeText
        limits = self._rangeLimits[rangeText]
        self.thresholdVoltageDoubleSpinBox_8.setRange(limits[0], limits[1])
        self.resetVoltageDoubleSpinBox_8.setRange(limits[0], limits[1])

    def recordThresholdVoltageChannel_1(self, value):
        self.settingsDict['thresholdVoltages'][0] = value

    def recordThresholdVoltageChannel_2(self, value):
        self.settingsDict['thresholdVoltages'][1] = value

    def recordThresholdVoltageChannel_3(self, value):
        self.settingsDict['thresholdVoltages'][2] = value

    def recordThresholdVoltageChannel_4(self, value):
        self.settingsDict['thresholdVoltages'][3] = value

    def recordThresholdVoltageChannel_5(self, value):
        self.settingsDict['thresholdVoltages'][4] = value

    def recordThresholdVoltageChannel_6(self, value):
        self.settingsDict['thresholdVoltages'][5] = value

    def recordThresholdVoltageChannel_7(self, value):
        self.settingsDict['thresholdVoltages'][6] = value

    def recordThresholdVoltageChannel_8(self, value):
        self.settingsDict['thresholdVoltages'][7] = value

    def recordResetVoltageChannel_1(self, value):
        self.settingsDict['resetVoltages'][0] = value

    def recordResetVoltageChannel_2(self, value):
        self.settingsDict['resetVoltages'][1] = value

    def recordResetVoltageChannel_3(self, value):
        self.settingsDict['resetVoltages'][2] = value

    def recordResetVoltageChannel_4(self, value):
        self.settingsDict['resetVoltages'][3] = value

    def recordResetVoltageChannel_5(self, value):
        self.settingsDict['resetVoltages'][4] = value

    def recordResetVoltageChannel_6(self, value):
        self.settingsDict['resetVoltages'][5] = value

    def recordResetVoltageChannel_7(self, value):
        self.settingsDict['resetVoltages'][6] = value

    def recordResetVoltageChannel_8(self, value):
        self.settingsDict['resetVoltages'][7] = value

    def recordEnableSMEventReportingChannel_1(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][0] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][0] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_2(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][1] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][1] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_3(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][2] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][2] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_4(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][3] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][3] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_5(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][4] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][4] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_6(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][5] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][5] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_7(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][6] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][6] = 0  # Convert boolean False to 0

    def recordEnableSMEventReportingChannel_8(self, value):
        if value:
            self.settingsDict['enableSMEventReporting'][7] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableSMEventReporting'][7] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_1(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][0] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][0] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_2(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][1] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][1] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_3(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][2] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][2] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_4(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][3] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][3] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_5(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][4] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][4] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_6(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][5] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][5] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_7(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][6] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][6] = 0  # Convert boolean False to 0

    def recordEnableUSBStreamingChannel_8(self, value):
        if value:
            self.settingsDict['enableUSBStreaming'][7] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableUSBStreaming'][7] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_1(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][0] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][0] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_2(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][1] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][1] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_3(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][2] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][2] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_4(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][3] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][3] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_5(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][4] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][4] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_6(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][5] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][5] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_7(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][6] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][6] = 0  # Convert boolean False to 0

    def recordEnableModuleStreamingChannel_8(self, value):
        if value:
            self.settingsDict['enableModuleStreaming'][7] = 1  # Convert boolean True to 1
        else:
            self.settingsDict['enableModuleStreaming'][7] = 0  # Convert boolean False to 0

    def enableActiveChannels(self, nChannels):
        self.settingsDict['nActiveChannels'] = nChannels
        if (nChannels == 1):
            self.enableChannel_2(False)
            self.enableChannel_3(False)
            self.enableChannel_4(False)
            self.enableChannel_5(False)
            self.enableChannel_6(False)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(20000)  # According to docs, the analog input module is capable of up to 20k Hz sampling rate with up to two channels active.
        
        elif (nChannels == 2):
            self.enableChannel_2(True)
            self.enableChannel_3(False)
            self.enableChannel_4(False)
            self.enableChannel_5(False)
            self.enableChannel_6(False)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(20000)

        elif (nChannels == 3):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(False)
            self.enableChannel_5(False)
            self.enableChannel_6(False)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(10000)  # Max sampling rate drops to 10k Hz for three to eight active channels.

        elif (nChannels == 4):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(True)
            self.enableChannel_5(False)
            self.enableChannel_6(False)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(10000)

        elif (nChannels == 5):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(True)
            self.enableChannel_5(True)
            self.enableChannel_6(False)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(10000)
        
        elif (nChannels == 6):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(True)
            self.enableChannel_5(True)
            self.enableChannel_6(True)
            self.enableChannel_7(False)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(10000)

        elif (nChannels == 7):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(True)
            self.enableChannel_5(True)
            self.enableChannel_6(True)
            self.enableChannel_7(True)
            self.enableChannel_8(False)
            self.samplingRateSpinBox.setMaximum(10000)

        elif (nChannels == 8):
            self.enableChannel_2(True)
            self.enableChannel_3(True)
            self.enableChannel_4(True)
            self.enableChannel_5(True)
            self.enableChannel_6(True)
            self.enableChannel_7(True)
            self.enableChannel_8(True)
            self.samplingRateSpinBox.setMaximum(10000)
            
    def enableChannel_2(self, value):
        self.inputVoltageRangeComboBox_2.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_2.setEnabled(value)
        self.resetVoltageDoubleSpinBox_2.setEnabled(value)
        self.enableModuleStreamingCheckBox_2.setEnabled(value)
        self.enableUSBStreamingCheckBox_2.setEnabled(value)
        self.enableSMEventReportingCheckBox_2.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_2.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_2.setValue(0.0)
            self.resetVoltageDoubleSpinBox_2.setValue(0.0)
            self.enableSMEventReportingCheckBox_2.setChecked(False)
            self.enableUSBStreamingCheckBox_2.setChecked(False)
            self.enableModuleStreamingCheckBox_2.setChecked(False)

    def enableChannel_3(self, value):
        self.inputVoltageRangeComboBox_3.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_3.setEnabled(value)
        self.resetVoltageDoubleSpinBox_3.setEnabled(value)
        self.enableModuleStreamingCheckBox_3.setEnabled(value)
        self.enableUSBStreamingCheckBox_3.setEnabled(value)
        self.enableSMEventReportingCheckBox_3.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_3.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_3.setValue(0.0)
            self.resetVoltageDoubleSpinBox_3.setValue(0.0)
            self.enableSMEventReportingCheckBox_3.setChecked(False)
            self.enableUSBStreamingCheckBox_3.setChecked(False)
            self.enableModuleStreamingCheckBox_3.setChecked(False)

    def enableChannel_4(self, value):
        self.inputVoltageRangeComboBox_4.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_4.setEnabled(value)
        self.resetVoltageDoubleSpinBox_4.setEnabled(value)
        self.enableModuleStreamingCheckBox_4.setEnabled(value)
        self.enableUSBStreamingCheckBox_4.setEnabled(value)
        self.enableSMEventReportingCheckBox_4.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_4.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_4.setValue(0.0)
            self.resetVoltageDoubleSpinBox_4.setValue(0.0)
            self.enableSMEventReportingCheckBox_4.setChecked(False)
            self.enableUSBStreamingCheckBox_4.setChecked(False)
            self.enableModuleStreamingCheckBox_4.setChecked(False)

    def enableChannel_5(self, value):
        self.inputVoltageRangeComboBox_5.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_5.setEnabled(value)
        self.resetVoltageDoubleSpinBox_5.setEnabled(value)
        self.enableModuleStreamingCheckBox_5.setEnabled(value)
        self.enableUSBStreamingCheckBox_5.setEnabled(value)
        self.enableSMEventReportingCheckBox_5.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_5.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_5.setValue(0.0)
            self.resetVoltageDoubleSpinBox_5.setValue(0.0)
            self.enableSMEventReportingCheckBox_5.setChecked(False)
            self.enableUSBStreamingCheckBox_5.setChecked(False)
            self.enableModuleStreamingCheckBox_5.setChecked(False)

    def enableChannel_6(self, value):
        self.inputVoltageRangeComboBox_6.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_6.setEnabled(value)
        self.resetVoltageDoubleSpinBox_6.setEnabled(value)
        self.enableModuleStreamingCheckBox_6.setEnabled(value)
        self.enableUSBStreamingCheckBox_6.setEnabled(value)
        self.enableSMEventReportingCheckBox_6.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_6.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_6.setValue(0.0)
            self.resetVoltageDoubleSpinBox_6.setValue(0.0)
            self.enableSMEventReportingCheckBox_6.setChecked(False)
            self.enableUSBStreamingCheckBox_6.setChecked(False)
            self.enableModuleStreamingCheckBox_6.setChecked(False)

    def enableChannel_7(self, value):
        self.inputVoltageRangeComboBox_7.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_7.setEnabled(value)
        self.resetVoltageDoubleSpinBox_7.setEnabled(value)
        self.enableModuleStreamingCheckBox_7.setEnabled(value)
        self.enableUSBStreamingCheckBox_7.setEnabled(value)
        self.enableSMEventReportingCheckBox_7.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_7.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_7.setValue(0.0)
            self.resetVoltageDoubleSpinBox_7.setValue(0.0)
            self.enableSMEventReportingCheckBox_7.setChecked(False)
            self.enableUSBStreamingCheckBox_7.setChecked(False)
            self.enableModuleStreamingCheckBox_7.setChecked(False)

    def enableChannel_8(self, value):
        self.inputVoltageRangeComboBox_8.setEnabled(value)
        self.thresholdVoltageDoubleSpinBox_8.setEnabled(value)
        self.resetVoltageDoubleSpinBox_8.setEnabled(value)
        self.enableModuleStreamingCheckBox_8.setEnabled(value)
        self.enableUSBStreamingCheckBox_8.setEnabled(value)
        self.enableSMEventReportingCheckBox_8.setEnabled(value)

        if not value:
            self.inputVoltageRangeComboBox_8.setCurrentIndex(0)
            self.thresholdVoltageDoubleSpinBox_8.setValue(0.0)
            self.resetVoltageDoubleSpinBox_8.setValue(0.0)
            self.enableSMEventReportingCheckBox_8.setChecked(False)
            self.enableUSBStreamingCheckBox_8.setChecked(False)
            self.enableModuleStreamingCheckBox_8.setChecked(False)