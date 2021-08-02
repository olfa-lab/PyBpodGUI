import sys
import json

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox,
    QWidget, QInputDialog, QFileDialog)
from PyQt5.QtCore import QObject

from olfa_editor_dialog_ui import Ui_Dialog


class OlfaEditorDialog(QDialog, Ui_Dialog):

    def __init__(self, parent=None):
        super().__init__()
        self.setupUi(self)

        with open('olfa_config.json', 'r') as olfa_config:
            self.olfaConfigDict = json.load(olfa_config)

        self.mfcTypeComboBox.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.addressComboBox.addItems(['A', 'B'])
        self.arduinoPortNumberComboBox.addItems(['1', '2'])
        self.capacityComboBox.addItems(['1000', '100'])
        self.gasComboBox.addItems(['Air', 'Nitrogen'])

        self.mfcTypeComboBox_2.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.addressComboBox_2.addItems(['A', 'B'])
        self.arduinoPortNumberComboBox_2.addItems(['1', '2'])
        self.capacityComboBox_2.addItems(['1000', '100'])
        self.gasComboBox_2.addItems(['Air', 'Nitrogen'])

        mfcType = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['MFC_type']
        self.mfcTypeComboBox.setCurrentText(mfcType)
        address = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['address']
        self.addressComboBox.setCurrentText(address)
        arduinoPortNum = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['arduino_port_num']
        self.arduinoPortNumberComboBox.setCurrentText(str(arduinoPortNum))
        capacity = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['capacity']
        self.capacityComboBox.setCurrentText(str(capacity))
        gas = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['gas']
        self.gasComboBox.setCurrentText(gas)

        mfcType = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['MFC_type']
        self.mfcTypeComboBox_2.setCurrentText(mfcType)
        address = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['address']
        self.addressComboBox_2.setCurrentText(address)
        arduinoPortNum = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['arduino_port_num']
        self.arduinoPortNumberComboBox_2.setCurrentText(str(arduinoPortNum))
        capacity = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['capacity']
        self.capacityComboBox_2.setCurrentText(str(capacity))
        gas = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['gas']
        self.gasComboBox_2.setCurrentText(gas)

        comPort = self.olfaConfigDict['Olfactometers'][0]['com_port']
        self.comPortLineEdit.setText(str(comPort))
        interface = self.olfaConfigDict['Olfactometers'][0]['interface']
        self.interfaceComboBox.addItem('teensy')
        self.interfaceComboBox.setCurrentText(interface)
        cassette_1_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn']
        self.cassette1SNLineEdit.setText(str(cassette_1_sn))
        cassette_2_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn']
        self.cassette2SNLineEdit.setText(str(cassette_2_sn))
        master_sn = self.olfaConfigDict['Olfactometers'][0]['master_sn']
        self.masterSNLineEdit.setText(str(master_sn))
        slaveIndex = self.olfaConfigDict['Olfactometers'][0]['slave_index']
        self.slaveIndexLineEdit.setText(str(slaveIndex))

        odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['odor']
        conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['conc']
        self.odorNameLineEdit.setText(odor)
        self.concentrationLineEdit.setText(str(conc))
        odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['odor']
        conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['conc']
        self.odorNameLineEdit_2.setText(odor)
        self.concentrationLineEdit_2.setText(str(conc))
        odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['odor']
        conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['conc']
        self.odorNameLineEdit_3.setText(odor)
        self.concentrationLineEdit_3.setText(str(conc))
        odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['odor']
        conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['conc']
        self.odorNameLineEdit_4.setText(odor)
        self.concentrationLineEdit_4.setText(str(conc))
