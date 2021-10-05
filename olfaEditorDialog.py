import sys
import json
import logging

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox,
    QWidget, QInputDialog, QFileDialog, QDialogButtonBox)
from PyQt5.QtCore import QObject

from olfa_editor_dialog_ui import Ui_Dialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


class OlfaEditorDialog(QDialog, Ui_Dialog):

    def __init__(self, olfaConfigFileName=None, parent=None):
        super().__init__()
        self.setupUi(self)
        self.olfaConfigFile = olfaConfigFileName

        if self.olfaConfigFile:
            with open(self.olfaConfigFile, 'r') as olfa_config:
                self.olfaConfigDict = json.load(olfa_config)

            if 'Olfactometers' not in self.olfaConfigDict:
                QMessageBox.warning(self, "Warning", "Invalid olfactometer configuration json file. Use this window to create a new one or click cancel and select a different file.")
                self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)  # Disable Save button so that the user can only Save As a new file.
                self.populateFields()
                self.connectSignalsSlots()
                del self.olfaConfigDict  # Delete the invalid dictionary with its contents and create a new empty dictionary below.
                self.olfaConfigDict = {'Olfactometers': [{'MFCs':[{}, {}], 'Vials':{}}]}
            else:
                self.populateFields()
                self.displayCurrentValues()
                self.connectSignalsSlots()  # Connect signals and slots last so that signals do not get fired when populating the fields.
        else:
            # No file given so let the user create new one from scratch using the dialog window as a template.
            self.olfaConfigDict = {'Olfactometers': [{'MFCs':[{}, {}], 'Vials':{}}]}
            self.buttonBox.button(QDialogButtonBox.Save).setEnabled(False)  # Disable Save button so that the user can only Save As a new file.
            self.populateFields()
            self.connectSignalsSlots()

    def populateFields(self):
        self.mfcTypeComboBox_1.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.mfcAddressComboBox_1.addItems(['A', 'B'])
        self.mfcArduinoPortNumComboBox_1.addItems(['1', '2'])
        self.mfcCapacityComboBox_1.addItems(['1000', '100'])
        self.mfcGasComboBox_1.addItems(['Air', 'Nitrogen', 'vac'])

        self.mfcTypeComboBox_2.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.mfcAddressComboBox_2.addItems(['A', 'B'])
        self.mfcArduinoPortNumComboBox_2.addItems(['1', '2'])
        self.mfcCapacityComboBox_2.addItems(['1000', '100'])
        self.mfcGasComboBox_2.addItems(['Air', 'Nitrogen', 'vac'])
        
        self.dilutorMFCTypeComboBox_1.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.dilutorMFCAddressComboBox_1.addItems(['A', 'B'])
        self.dilutorMFCCapacityComboBox_1.addItems(['2000', '1000', '100'])
        self.dilutorMFCGasComboBox_1.addItems(['Air', 'Nitrogen', 'vac'])

        self.dilutorMFCTypeComboBox_2.addItems(['analog', 'alicat_digital', 'alicat_digital_raw'])
        self.dilutorMFCAddressComboBox_2.addItems(['A', 'B'])
        self.dilutorMFCCapacityComboBox_2.addItems(['2000', '1000', '100'])
        self.dilutorMFCGasComboBox_2.addItems(['Air', 'Nitrogen', 'vac'])

        self.dilutorTypeComboBox.addItem('serial_forwarding')
        self.interfaceComboBox.addItem('teensy')

        self.mfcTypeComboBox_1.setCurrentIndex(-1)
        self.mfcAddressComboBox_1.setCurrentIndex(-1)
        self.mfcArduinoPortNumComboBox_1.setCurrentIndex(-1)
        self.mfcCapacityComboBox_1.setCurrentIndex(-1)
        self.mfcGasComboBox_1.setCurrentIndex(-1)

        self.mfcTypeComboBox_2.setCurrentIndex(-1)
        self.mfcAddressComboBox_2.setCurrentIndex(-1)
        self.mfcArduinoPortNumComboBox_2.setCurrentIndex(-1)
        self.mfcCapacityComboBox_2.setCurrentIndex(-1)
        self.mfcGasComboBox_2.setCurrentIndex(-1)
        
        self.dilutorMFCTypeComboBox_1.setCurrentIndex(-1)
        self.dilutorMFCAddressComboBox_1.setCurrentIndex(-1)
        self.dilutorMFCCapacityComboBox_1.setCurrentIndex(-1)
        self.dilutorMFCGasComboBox_1.setCurrentIndex(-1)

        self.dilutorMFCTypeComboBox_2.setCurrentIndex(-1)
        self.dilutorMFCAddressComboBox_2.setCurrentIndex(-1)
        self.dilutorMFCCapacityComboBox_2.setCurrentIndex(-1)
        self.dilutorMFCGasComboBox_2.setCurrentIndex(-1)

        self.dilutorTypeComboBox.setCurrentIndex(-1)
        self.interfaceComboBox.setCurrentIndex(-1)

    def displayCurrentValues(self):
        try:
            mfcType = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['MFC_type']
            self.mfcTypeComboBox_1.setCurrentText(mfcType)
            address = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['address']
            self.mfcAddressComboBox_1.setCurrentText(address)
            arduinoPortNum = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['arduino_port_num']
            self.mfcArduinoPortNumComboBox_1.setCurrentText(str(arduinoPortNum))
            capacity = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['capacity']
            self.mfcCapacityComboBox_1.setCurrentText(str(capacity))
            gas = self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['gas']
            self.mfcGasComboBox_1.setCurrentText(gas)

            mfcType = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['MFC_type']
            self.mfcTypeComboBox_2.setCurrentText(mfcType)
            address = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['address']
            self.mfcAddressComboBox_2.setCurrentText(address)
            arduinoPortNum = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['arduino_port_num']
            self.mfcArduinoPortNumComboBox_2.setCurrentText(str(arduinoPortNum))
            capacity = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['capacity']
            self.mfcCapacityComboBox_2.setCurrentText(str(capacity))
            gas = self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['gas']
            self.mfcGasComboBox_2.setCurrentText(gas)

            comPort = self.olfaConfigDict['Olfactometers'][0]['com_port']
            self.comPortLineEdit.setText(str(comPort))
            interface = self.olfaConfigDict['Olfactometers'][0]['interface']
            self.interfaceComboBox.setCurrentText(interface)
            cassette_1_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn']
            self.cassetteSNLineEdit_1.setText(str(cassette_1_sn))
            cassette_2_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn']
            self.cassetteSNLineEdit_2.setText(str(cassette_2_sn))
            master_sn = self.olfaConfigDict['Olfactometers'][0]['master_sn']
            self.masterSNLineEdit.setText(str(master_sn))
            slaveIndex = self.olfaConfigDict['Olfactometers'][0]['slave_index']
            self.slaveIndexLineEdit.setText(str(slaveIndex))

            if '5' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['5']:
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['odor']
                    self.vialOdorNameLineEdit_5.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['5']:
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['conc']
                    self.vialConcLineEdit_5.setText(str(conc))
            if '6' in self.olfaConfigDict['Olfactometers'][0]['Vials']:  
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['6']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['odor']
                    self.vialOdorNameLineEdit_6.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['6']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['conc']
                    self.vialConcLineEdit_6.setText(str(conc))
            if '7' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['7']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['odor']
                    self.vialOdorNameLineEdit_7.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['7']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['conc']
                    self.vialConcLineEdit_7.setText(str(conc))
            if '8' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['8']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['odor']
                    self.vialOdorNameLineEdit_8.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['8']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['conc']
                    self.vialConcLineEdit_8.setText(str(conc))
            if '9' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['9']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['odor']
                    self.vialOdorNameLineEdit_9.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['9']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['conc']
                    self.vialConcLineEdit_9.setText(str(conc))
            if '10' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['10']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['odor']
                    self.vialOdorNameLineEdit_10.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['10']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['conc']
                    self.vialConcLineEdit_10.setText(str(conc))
            if '11' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['11']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['odor']
                    self.vialOdorNameLineEdit_11.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['11']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['conc']
                    self.vialConcLineEdit_11.setText(str(conc))
            if '12' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['12']:  
                    odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['odor']
                    self.vialOdorNameLineEdit_12.setText(odor)
                if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['12']:    
                    conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['conc']
                    self.vialConcLineEdit_12.setText(str(conc))

            if ('Dilutors' in self.olfaConfigDict['Olfactometers'][0]) and (len(self.olfaConfigDict['Olfactometers'][0]['Dilutors']) > 0):
                dilutorMFCType = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['MFC_type']
                self.dilutorMFCTypeComboBox_1.setCurrentText(dilutorMFCType)
                dilutorMFCAddress = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['address']
                self.dilutorMFCAddressComboBox_1.setCurrentText(dilutorMFCAddress)
                dilutorMFCCapacity = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['capacity']
                self.dilutorMFCCapacityComboBox_1.setCurrentText(str(dilutorMFCCapacity))
                dilutorMFCGas = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['gas']
                self.dilutorMFCGasComboBox_1.setCurrentText(dilutorMFCGas)

                dilutorMFCType = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['MFC_type']
                self.dilutorMFCTypeComboBox_2.setCurrentText(dilutorMFCType)
                dilutorMFCAddress = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['address']
                self.dilutorMFCAddressComboBox_2.setCurrentText(dilutorMFCAddress)
                dilutorMFCCapacity = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['capacity']
                self.dilutorMFCCapacityComboBox_2.setCurrentText(str(dilutorMFCCapacity))
                dilutorMFCGas = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['gas']
                self.dilutorMFCGasComboBox_2.setCurrentText(dilutorMFCGas)

                dilutorCOMPort = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['com_port']
                self.dilutorComPortLineEdit.setText(str(dilutorCOMPort))
                dilutorType = self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['dilutor_type']
                self.dilutorTypeComboBox.setCurrentText(dilutorType)
        except KeyError:
            QMessageBox.warning(self, "Warning", "There was an error displaying contents of the file. One or more values may be missing or invalid.")

    def connectSignalsSlots(self):
            self.mfcTypeComboBox_1.currentIndexChanged.connect(self.recordMFCType_1)
            self.mfcAddressComboBox_1.currentIndexChanged.connect(self.recordMFCAddress_1)
            self.mfcArduinoPortNumComboBox_1.currentIndexChanged.connect(self.recordMFCArduinoPortNum_1)
            self.mfcCapacityComboBox_1.currentIndexChanged.connect(self.recordMFCCapacity_1)
            self.mfcGasComboBox_1.currentIndexChanged.connect(self.recordMFCGas_1)

            self.mfcTypeComboBox_2.currentIndexChanged.connect(self.recordMFCType_2)
            self.mfcAddressComboBox_2.currentIndexChanged.connect(self.recordMFCAddress_2)
            self.mfcArduinoPortNumComboBox_2.currentIndexChanged.connect(self.recordMFCArduinoPortNum_2)
            self.mfcCapacityComboBox_2.currentIndexChanged.connect(self.recordMFCCapacity_2)
            self.mfcGasComboBox_2.currentIndexChanged.connect(self.recordMFCGas_2)

            self.comPortLineEdit.editingFinished.connect(self.recordCOMPort)
            self.interfaceComboBox.currentIndexChanged.connect(self.recordInterface)
            self.cassetteSNLineEdit_1.editingFinished.connect(self.recordCassetteSN_1)
            self.cassetteSNLineEdit_2.editingFinished.connect(self.recordCassetteSN_2)
            self.masterSNLineEdit.editingFinished.connect(self.recordMasterSN)
            self.slaveIndexLineEdit.editingFinished.connect(self.recordSlaveIndex)

            self.vialOdorNameLineEdit_5.editingFinished.connect(self.recordVialOdorName_5)
            self.vialConcLineEdit_5.editingFinished.connect(self.recordVialConc_5)
            self.vialOdorNameLineEdit_6.editingFinished.connect(self.recordVialOdorName_6)
            self.vialConcLineEdit_6.editingFinished.connect(self.recordVialConc_6)
            self.vialOdorNameLineEdit_7.editingFinished.connect(self.recordVialOdorName_7)
            self.vialConcLineEdit_7.editingFinished.connect(self.recordVialConc_7)
            self.vialOdorNameLineEdit_8.editingFinished.connect(self.recordVialOdorName_8)
            self.vialConcLineEdit_8.editingFinished.connect(self.recordVialConc_8)
            self.vialOdorNameLineEdit_9.editingFinished.connect(self.recordVialOdorName_9)
            self.vialConcLineEdit_9.editingFinished.connect(self.recordVialConc_9)
            self.vialOdorNameLineEdit_10.editingFinished.connect(self.recordVialOdorName_10)
            self.vialConcLineEdit_10.editingFinished.connect(self.recordVialConc_10)
            self.vialOdorNameLineEdit_11.editingFinished.connect(self.recordVialOdorName_11)
            self.vialConcLineEdit_11.editingFinished.connect(self.recordVialConc_11)
            self.vialOdorNameLineEdit_12.editingFinished.connect(self.recordVialOdorName_12)
            self.vialConcLineEdit_12.editingFinished.connect(self.recordVialConc_12)

            self.dilutorComPortLineEdit.editingFinished.connect(self.recordDilutorCOMPort)
            self.dilutorTypeComboBox.currentIndexChanged.connect(self.recordDilutorType)

            self.dilutorMFCTypeComboBox_1.currentIndexChanged.connect(self.recordDilutorMFCType_1)
            self.dilutorMFCAddressComboBox_1.currentIndexChanged.connect(self.recordDilutorMFCAddress_1)
            self.dilutorMFCCapacityComboBox_1.currentIndexChanged.connect(self.recordDilutorMFCCapacity_1)
            self.dilutorMFCGasComboBox_1.currentIndexChanged.connect(self.recordDilutorMFCGas_1)

            self.dilutorMFCTypeComboBox_2.currentIndexChanged.connect(self.recordDilutorMFCType_2)
            self.dilutorMFCAddressComboBox_2.currentIndexChanged.connect(self.recordDilutorMFCAddress_2)
            self.dilutorMFCCapacityComboBox_2.currentIndexChanged.connect(self.recordDilutorMFCCapacity_2)
            self.dilutorMFCGasComboBox_2.currentIndexChanged.connect(self.recordDilutorMFCGas_2)

            self.buttonBox.accepted.connect(self.saveToCurrentFile)
            self.saveAsButton.clicked.connect(self.saveAsNewFile)
            self.clearDilutorButton.clicked.connect(self.clearDilutor)

    def recordMFCType_1(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['MFC_type'] = self.mfcTypeComboBox_1.currentText()
        
    def recordMFCAddress_1(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['address'] = self.mfcAddressComboBox_1.currentText()

    def recordMFCArduinoPortNum_1(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['arduino_port_num'] = int(self.mfcArduinoPortNumComboBox_1.currentText())

    def recordMFCCapacity_1(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['capacity'] = int(self.mfcCapacityComboBox_1.currentText())

    def recordMFCGas_1(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][0]['gas'] = self.mfcGasComboBox_1.currentText()

    def recordMFCType_2(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['MFC_type'] = self.mfcTypeComboBox_2.currentText()

    def recordMFCAddress_2(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['address'] = self.mfcAddressComboBox_2.currentText()

    def recordMFCArduinoPortNum_2(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['arduino_port_num'] = int(self.mfcArduinoPortNumComboBox_2.currentText())

    def recordMFCCapacity_2(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['capacity'] = int(self.mfcCapacityComboBox_2.currentText())

    def recordMFCGas_2(self):
        self.olfaConfigDict['Olfactometers'][0]['MFCs'][1]['gas'] = self.mfcGasComboBox_2.currentText()

    def recordCOMPort(self):
        if not (self.comPortLineEdit.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['com_port'] = int(self.comPortLineEdit.text())
        elif 'com_port' in self.olfaConfigDict['Olfactometers'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['com_port']  # Delete the key if it was created.

    def recordInterface(self):
        self.olfaConfigDict['Olfactometers'][0]['interface'] = self.interfaceComboBox.currentText()

    def recordCassetteSN_1(self):
        if not (self.cassetteSNLineEdit_1.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn'] = int(self.cassetteSNLineEdit_1.text())
        elif 'cassette_1_sn' in self.olfaConfigDict['Olfactometers'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn']  # Delete the key if it was created.

    def recordCassetteSN_2(self):
        if not (self.cassetteSNLineEdit_2.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn'] = int(self.cassetteSNLineEdit_2.text())
        elif 'cassette_2_sn' in self.olfaConfigDict['Olfactometers'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn']  # Delete the key if it was created.

    def recordMasterSN(self):
        if not (self.masterSNLineEdit.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['master_sn'] = int(self.masterSNLineEdit.text())
        elif 'master_sn' in self.olfaConfigDict['Olfactometers'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['master_sn']  # Delete the key if it was created.

    def recordSlaveIndex(self):
        if not (self.slaveIndexLineEdit.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['slave_index'] = int(self.slaveIndexLineEdit.text())
        elif 'slave_index' in self.olfaConfigDict['Olfactometers'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['slave_index']  # Delete the key if it was created.

    def recordVialOdorName_5(self):
        if '5' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5'] = {}
        if not (self.vialOdorNameLineEdit_5.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['odor'] = self.vialOdorNameLineEdit_5.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['5']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['odor']  # Delete the key if it was created.

    def recordVialConc_5(self):
        if '5' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5'] = {}
        if not (self.vialConcLineEdit_5.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['conc'] = float(self.vialConcLineEdit_5.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['5']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['conc']  # Delete the key if it was created.

    def recordVialOdorName_6(self):
        if '6' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6'] = {}
        if not (self.vialOdorNameLineEdit_6.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['odor'] = self.vialOdorNameLineEdit_6.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['6']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['odor']  # Delete the key if it was created.

    def recordVialConc_6(self):
        if '6' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6'] = {}
        if not (self.vialConcLineEdit_6.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['conc'] = float(self.vialConcLineEdit_6.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['6']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['conc']  # Delete the key if it was created.

    def recordVialOdorName_7(self):
        if '7' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7'] = {}
        if not (self.vialOdorNameLineEdit_7.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['odor'] = self.vialOdorNameLineEdit_7.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['7']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['odor']  # Delete the key if it was created.

    def recordVialConc_7(self):
        if '7' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7'] = {}
        if not (self.vialConcLineEdit_7.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['conc'] = float(self.vialConcLineEdit_7.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['7']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['conc']  # Delete the key if it was created.

    def recordVialOdorName_8(self):
        if '8' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8'] = {}
        if not (self.vialOdorNameLineEdit_8.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['odor'] = self.vialOdorNameLineEdit_8.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['8']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['odor']  # Delete the key if it was created.

    def recordVialConc_8(self):
        if '8' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8'] = {}
        if not (self.vialConcLineEdit_8.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['conc'] = float(self.vialConcLineEdit_8.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['8']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['conc']  # Delete the key if it was created.

    def recordVialOdorName_9(self):
        if '9' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['9'] = {}
        if not (self.vialOdorNameLineEdit_9.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['odor'] = self.vialOdorNameLineEdit_9.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['9']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['odor']  # Delete the key if it was created.

    def recordVialConc_9(self):
        if '9' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['9'] = {}
        if not (self.vialConcLineEdit_9.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['conc'] = float(self.vialConcLineEdit_9.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['9']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['9']['conc']  # Delete the key if it was created.

    def recordVialOdorName_10(self):
        if '10' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['10'] = {}
        if not (self.vialOdorNameLineEdit_10.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['odor'] = self.vialOdorNameLineEdit_10.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['10']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['odor']  # Delete the key if it was created.

    def recordVialConc_10(self):
        if '10' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['10'] = {}
        if not (self.vialConcLineEdit_10.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['conc'] = float(self.vialConcLineEdit_10.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['10']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['10']['conc']  # Delete the key if it was created.

    def recordVialOdorName_11(self):
        if '11' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['11'] = {}
        if not (self.vialOdorNameLineEdit_11.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['odor'] = self.vialOdorNameLineEdit_11.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['11']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['odor']  # Delete the key if it was created.

    def recordVialConc_11(self):
        if '11' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['11'] = {}
        if not (self.vialConcLineEdit_11.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['conc'] = float(self.vialConcLineEdit_11.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['11']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['11']['conc']  # Delete the key if it was created.

    def recordVialOdorName_12(self):
        if '12' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['12'] = {}
        if not (self.vialOdorNameLineEdit_12.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['odor'] = self.vialOdorNameLineEdit_12.text()
        elif 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['12']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['odor']  # Delete the key if it was created.

    def recordVialConc_12(self):
        if '12' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['12'] = {}
        if not (self.vialConcLineEdit_12.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['conc'] = float(self.vialConcLineEdit_12.text())
        elif 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['12']:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Vials']['12']['conc']  # Delete the key if it was created.

    def recordDilutorCOMPort(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if not (self.dilutorComPortLineEdit.text() == ''):
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['com_port'] = int(self.dilutorComPortLineEdit.text())
        elif 'com_port' in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:  # Therefore lineEdit must be an empty string.
            del self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['com_port']  # Delete the key if it was created.

    def recordDilutorType(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['dilutor_type'] = self.dilutorTypeComboBox.currentText()

    def recordDilutorMFCType_1(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['MFC_type'] = self.dilutorMFCTypeComboBox_1.currentText()

    def recordDilutorMFCAddress_1(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['address'] = self.dilutorMFCAddressComboBox_1.currentText()

    def recordDilutorMFCCapacity_1(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['capacity'] = int(self.dilutorMFCCapacityComboBox_1.currentText())

    def recordDilutorMFCGas_1(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][0]['gas'] = self.dilutorMFCGasComboBox_1.currentText()

    def recordDilutorMFCType_2(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['MFC_type'] = self.dilutorMFCTypeComboBox_2.currentText()

    def recordDilutorMFCAddress_2(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['address'] = self.dilutorMFCAddressComboBox_2.currentText()

    def recordDilutorMFCCapacity_2(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['capacity'] = int(self.dilutorMFCCapacityComboBox_2.currentText())

    def recordDilutorMFCGas_2(self):
        if 'Dilutors' not in self.olfaConfigDict['Olfactometers'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'] = [{}]
        if 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
            self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'] = [{}, {}]  # Create a list of two dictionaries, one dictionary per MFC.
        self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][1]['gas'] = self.dilutorMFCGasComboBox_2.currentText()

    def clearDilutor(self):
        if 'Dilutors' in self.olfaConfigDict['Olfactometers'][0]:
            self.dilutorMFCTypeComboBox_1.setCurrentIndex(-1)
            self.dilutorMFCAddressComboBox_1.setCurrentIndex(-1)
            self.dilutorMFCCapacityComboBox_1.setCurrentIndex(-1)
            self.dilutorMFCGasComboBox_1.setCurrentIndex(-1)

            self.dilutorMFCTypeComboBox_2.setCurrentIndex(-1)
            self.dilutorMFCAddressComboBox_2.setCurrentIndex(-1)
            self.dilutorMFCCapacityComboBox_2.setCurrentIndex(-1)
            self.dilutorMFCGasComboBox_2.setCurrentIndex(-1)

            self.dilutorTypeComboBox.setCurrentIndex(-1)
            self.dilutorComPortLineEdit.clear()

            # I delete the 'Dilutors' key AFTER changing the ComboBox indices to avoid recreating the key when the comboBox currentIndexChanged
            # signals fire and connect to their respective slots that create the 'Dilutors' key if its not already there.
            del self.olfaConfigDict['Olfactometers'][0]['Dilutors']
    
    def saveToCurrentFile(self):
        if 'com_port' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please enter the COM port number for the olfactometer!")
            return
        elif 'interface' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please choose the interface for the olfactometer!")
            return
        elif 'cassette_1_sn' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please enter the SN for Cassette 1!")
            return
        elif 'cassette_2_sn' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please enter the SN for Cassette 2!")
            return
        elif 'master_sn' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please enter the master SN!")
            return
        elif 'slave_index' not in self.olfaConfigDict['Olfactometers'][0]:
            QMessageBox.warning(self, "Warning", "Please enter the slave index number!")
            return
        
        for i in range(len(self.olfaConfigDict['Olfactometers'][0]['MFCs'])):  # There should only be two MFCs here.
            if 'MFC_type' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                QMessageBox.warning(self, "Warning", f"Please choose the MFC type of the olfactometer MFC {i}!")
                return
            elif 'address' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                QMessageBox.warning(self, "Warning", f"Please choose the address of the olfactometer MFC {i}!")
                return
            elif 'arduino_port_num' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                QMessageBox.warning(self, "Warning", f"Please choose the Arduino port number of the olfactometer MFC {i}!")
                return
            elif 'capacity' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                QMessageBox.warning(self, "Warning", f"Please choose the capacity of the olfactometer MFC {i}!")
                return
            elif 'gas' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                QMessageBox.warning(self, "Warning", f"Please choose the gas type of the olfactometer MFC {i}!")
                return

        if (len(self.olfaConfigDict['Olfactometers'][0]['Vials']) > 0):
            emptyVials = []
            for vialNum, vialInfo in self.olfaConfigDict['Olfactometers'][0]['Vials'].items():
                if ('conc' not in vialInfo) and ('odor' in vialInfo):
                    QMessageBox.warning(self, "Warning", f"Please enter concentration for vial {vialNum} before saving.")
                    return
                elif ('odor' not in vialInfo) and ('conc' in vialInfo):
                    QMessageBox.warning(self, "Warning", f"Please enter odor name for vial {vialNum} before saving.")
                    return
                elif (vialInfo == {}):
                    emptyVials.append(vialNum)

            for vialNum in emptyVials:
                del self.olfaConfigDict['Olfactometers'][0]['Vials'][vialNum]  # Delete keys that have empty dict as their value.
        else:
            QMessageBox.warning(self, "Warning", "Please enter at least one vial!")
            return

        if 'Dilutors' in self.olfaConfigDict['Olfactometers'][0]:  # This means at least one input field was edited with a valid input.
            if (self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0] == {}):
                self.olfaConfigDict['Olfactometers'][0]['Dilutors'].clear()  # Empty all contents of the list but do not delete the 'Dilutors' key
                # self.olfaConfigDict['Olfactometers'][0]['Dilutors'].pop(0)
                # del self.olfaConfigDict['Olfactometers'][0]['Dilutors']
            elif 'com_port' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                QMessageBox.warning(self, "Warning", "Please enter COM port number for the dilutor!")
                return
            elif 'dilutor_type' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                QMessageBox.warning(self, "Warning", "Please choose an option for dilutor type!")
                return
            elif 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                QMessageBox.warning(self, "Warning", "Please choose options for both MFCs!")
                return
            else:
                for i in range(len(self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'])):  # There should only be two MFCs here.
                    if 'MFC_type' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                        QMessageBox.warning(self, "Warning", f"Please choose an MFC type for MFC {i}!")
                        return
                    elif 'address' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                        QMessageBox.warning(self, "Warning", f"Please choose an address for MFC {i}!")
                        return
                    elif 'capacity' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                        QMessageBox.warning(self, "Warning", f"Please choose a capacity for MFC {i}!")
                        return
                    elif 'gas' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                        QMessageBox.warning(self, "Warning", f"Please choose a gas for MFC {i}!")
                        return

        with open(self.olfaConfigFile, 'w') as olfa_config:
            json.dump(self.olfaConfigDict, olfa_config, indent=4)
            self.accept()  # Closes the dialog window.

    def saveAsNewFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "olfa_config.json", "JSON Files (*.json)", options=options)
        if fileName:
            if 'com_port' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please enter the COM port number for the olfactometer!")
                return
            elif 'interface' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please choose the interface for the olfactometer!")
                return
            elif 'cassette_1_sn' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please enter the SN for Cassette 1!")
                return
            elif 'cassette_2_sn' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please enter the SN for Cassette 2!")
                return
            elif 'master_sn' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please enter the master SN!")
                return
            elif 'slave_index' not in self.olfaConfigDict['Olfactometers'][0]:
                QMessageBox.warning(self, "Warning", "Please enter the slave index number!")
                return
            
            for i in range(len(self.olfaConfigDict['Olfactometers'][0]['MFCs'])):  # There should only be two MFCs here.
                if 'MFC_type' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                    QMessageBox.warning(self, "Warning", f"Please choose the MFC type of the olfactometer MFC {i}!")
                    return
                elif 'address' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                    QMessageBox.warning(self, "Warning", f"Please choose the address of the olfactometer MFC {i}!")
                    return
                elif 'arduino_port_num' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                    QMessageBox.warning(self, "Warning", f"Please choose the Arduino port number of the olfactometer MFC {i}!")
                    return
                elif 'capacity' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                    QMessageBox.warning(self, "Warning", f"Please choose the capacity of the olfactometer MFC {i}!")
                    return
                elif 'gas' not in self.olfaConfigDict['Olfactometers'][0]['MFCs'][i]:
                    QMessageBox.warning(self, "Warning", f"Please choose the gas type of the olfactometer MFC {i}!")
                    return

            if (len(self.olfaConfigDict['Olfactometers'][0]['Vials']) > 0):
                emptyVials = []
                for vialNum, vialInfo in self.olfaConfigDict['Olfactometers'][0]['Vials'].items():
                    if ('conc' not in vialInfo) and ('odor' in vialInfo):
                        QMessageBox.warning(self, "Warning", f"Please enter concentration for vial {vialNum} before saving.")
                        return
                    elif ('odor' not in vialInfo) and ('conc' in vialInfo):
                        QMessageBox.warning(self, "Warning", f"Please enter odor name for vial {vialNum} before saving.")
                        return
                    elif (vialInfo == {}):
                        emptyVials.append(vialNum)

                for vialNum in emptyVials:
                    del self.olfaConfigDict['Olfactometers'][0]['Vials'][vialNum]  # Delete keys that have empty dict as their value.
            else:
                QMessageBox.warning(self, "Warning", "Please enter at least one vial!")
                return

            if ('Dilutors' in self.olfaConfigDict['Olfactometers'][0]) and (len(self.olfaConfigDict['Olfactometers'][0]['Dilutors']) > 0):  # This means at least one input field was edited with a valid input.
                if (self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0] == {}):
                    self.olfaConfigDict['Olfactometers'][0]['Dilutors'].clear()  # Empty all contents of the list but do not delete the 'Dilutors' key
                    # self.olfaConfigDict['Olfactometers'][0]['Dilutors'].pop(0)
                    # del self.olfaConfigDict['Olfactometers'][0]['Dilutors']
                elif 'com_port' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                    QMessageBox.warning(self, "Warning", "Please enter COM port number for the dilutor!")
                    return
                elif 'dilutor_type' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                    QMessageBox.warning(self, "Warning", "Please choose an option for dilutor type!")
                    return
                elif 'MFCs' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]:
                    QMessageBox.warning(self, "Warning", "Please choose options for both MFCs!")
                    return
                else:
                    for i in range(len(self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'])):  # There should only be two MFCs here.
                        if 'MFC_type' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                            QMessageBox.warning(self, "Warning", f"Please choose an MFC type for MFC {i}!")
                            return
                        elif 'address' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                            QMessageBox.warning(self, "Warning", f"Please choose an address for MFC {i}!")
                            return
                        elif 'capacity' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                            QMessageBox.warning(self, "Warning", f"Please choose a capacity for MFC {i}!")
                            return
                        elif 'gas' not in self.olfaConfigDict['Olfactometers'][0]['Dilutors'][0]['MFCs'][i]:
                            QMessageBox.warning(self, "Warning", f"Please choose a gas for MFC {i}!")
                            return
        
            with open(fileName, 'w') as olfa_config:
                json.dump(self.olfaConfigDict, olfa_config, indent=4)
                
            self.accept()  # Closes the dialog window.
