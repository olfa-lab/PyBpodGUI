import logging
from PyQt5.QtWidgets import QDialog
from ui_files.bpod_flex_channel_settings_dialog_ui import Ui_Dialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


class BpodFlexChannelSettingsDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setupUi(self)
        self.setWindowTitle("Bpod Flex Channel Settings")
        self.connectSignalsSlots()
        self.maxFlexVoltage = 5
        self.settingsDict = {
            'channelTypes': [
                self.channelTypeComboBox_1.currentIndex(),
                self.channelTypeComboBox_2.currentIndex(),
                self.channelTypeComboBox_3.currentIndex(),
                self.channelTypeComboBox_4.currentIndex()
            ],
            'thresholds_1': [
                ((self.threshold_1_doubleSpinBox_1.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_1_doubleSpinBox_2.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_1_doubleSpinBox_3.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_1_doubleSpinBox_4.value() / self.maxFlexVoltage) * 4095)
            ],
            'thresholds_2': [
                ((self.threshold_2_doubleSpinBox_1.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_2_doubleSpinBox_2.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_2_doubleSpinBox_3.value() / self.maxFlexVoltage) * 4095),
                ((self.threshold_2_doubleSpinBox_4.value() / self.maxFlexVoltage) * 4095)
            ],
            'polarities_1': [
                self.polarity_1_comboBox_1.currentIndex(),
                self.polarity_1_comboBox_2.currentIndex(),
                self.polarity_1_comboBox_3.currentIndex(),
                self.polarity_1_comboBox_4.currentIndex()
            ],
            'polarities_2': [
                self.polarity_2_comboBox_1.currentIndex(),
                self.polarity_2_comboBox_2.currentIndex(),
                self.polarity_2_comboBox_3.currentIndex(),
                self.polarity_2_comboBox_4.currentIndex()
            ],
            'modes': [
                self.modeComboBox_1.currentIndex(),
                self.modeComboBox_2.currentIndex(),
                self.modeComboBox_3.currentIndex(),
                self.modeComboBox_4.currentIndex()
            ],
            'samplingPeriod': self.samplingPeriodSpinBox.value()
        }

    def connectSignalsSlots(self):
        self.buttonBox.accepted.connect(self.updateSettingsDict)

    def updateSettingsDict(self):
        self.settingsDict['channelTypes'] = [
            self.channelTypeComboBox_1.currentIndex(),
            self.channelTypeComboBox_2.currentIndex(),
            self.channelTypeComboBox_3.currentIndex(),
            self.channelTypeComboBox_4.currentIndex()
        ]
        self.settingsDict['thresholds_1'] = [
            ((self.threshold_1_doubleSpinBox_1.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_1_doubleSpinBox_2.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_1_doubleSpinBox_3.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_1_doubleSpinBox_4.value() / self.maxFlexVoltage) * 4095)
        ]
        self.settingsDict['thresholds_2'] = [
            ((self.threshold_2_doubleSpinBox_1.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_2_doubleSpinBox_2.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_2_doubleSpinBox_3.value() / self.maxFlexVoltage) * 4095),
            ((self.threshold_2_doubleSpinBox_4.value() / self.maxFlexVoltage) * 4095)
        ]
        self.settingsDict['polarities_1'] = [
            self.polarity_1_comboBox_1.currentIndex(),
            self.polarity_1_comboBox_2.currentIndex(),
            self.polarity_1_comboBox_3.currentIndex(),
            self.polarity_1_comboBox_4.currentIndex()
        ]
        self.settingsDict['polarities_2'] = [
            self.polarity_2_comboBox_1.currentIndex(),
            self.polarity_2_comboBox_2.currentIndex(),
            self.polarity_2_comboBox_3.currentIndex(),
            self.polarity_2_comboBox_4.currentIndex()
        ]
        self.settingsDict['modes'] = [
            self.modeComboBox_1.currentIndex(),
            self.modeComboBox_2.currentIndex(),
            self.modeComboBox_3.currentIndex(),
            self.modeComboBox_4.currentIndex()
        ]
        self.settingsDict['samplingPeriod'] = self.samplingPeriodSpinBox.value()

    def loadSettings(self, settingsDict):
        self.channelTypeComboBox_1.setCurrentIndex(settingsDict['channelTypes'][0])
        self.channelTypeComboBox_2.setCurrentIndex(settingsDict['channelTypes'][1])
        self.channelTypeComboBox_3.setCurrentIndex(settingsDict['channelTypes'][2])
        self.channelTypeComboBox_4.setCurrentIndex(settingsDict['channelTypes'][3])
        
        self.threshold_1_doubleSpinBox_1.setValue(settingsDict['thresholds_1'][0])
        self.threshold_1_doubleSpinBox_2.setValue(settingsDict['thresholds_1'][1])
        self.threshold_1_doubleSpinBox_3.setValue(settingsDict['thresholds_1'][2])
        self.threshold_1_doubleSpinBox_4.setValue(settingsDict['thresholds_1'][3])
    
        self.threshold_2_doubleSpinBox_1.setValue(settingsDict['thresholds_2'][0])
        self.threshold_2_doubleSpinBox_2.setValue(settingsDict['thresholds_2'][1])
        self.threshold_2_doubleSpinBox_3.setValue(settingsDict['thresholds_2'][2])
        self.threshold_2_doubleSpinBox_4.setValue(settingsDict['thresholds_2'][3])
    
        self.polarity_1_comboBox_1.setCurrentIndex(settingsDict['polarities_1'][0])
        self.polarity_1_comboBox_2.setCurrentIndex(settingsDict['polarities_1'][1])
        self.polarity_1_comboBox_3.setCurrentIndex(settingsDict['polarities_1'][2])
        self.polarity_1_comboBox_4.setCurrentIndex(settingsDict['polarities_1'][3])

        self.polarity_2_comboBox_1.setCurrentIndex(settingsDict['polarities_2'][0])
        self.polarity_2_comboBox_2.setCurrentIndex(settingsDict['polarities_2'][1])
        self.polarity_2_comboBox_3.setCurrentIndex(settingsDict['polarities_2'][2])
        self.polarity_2_comboBox_4.setCurrentIndex(settingsDict['polarities_2'][3])    
        
        self.modeComboBox_1.setCurrentIndex(settingsDict['modes'][0])
        self.modeComboBox_2.setCurrentIndex(settingsDict['modes'][1])
        self.modeComboBox_3.setCurrentIndex(settingsDict['modes'][2])
        self.modeComboBox_4.setCurrentIndex(settingsDict['modes'][3])

        self.samplingPeriodSpinBox.setValue(settingsDict['samplingPeriod'])
    
    def getSettings(self):
        return self.settingsDict