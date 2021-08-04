import sys
import json
import logging

from PyQt5.QtWidgets import (
    QApplication, QDialog, QMessageBox,
    QWidget, QInputDialog, QFileDialog)
from PyQt5.QtCore import QObject

from olfa_editor_dialog_ui import Ui_Dialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


class OlfaEditorDialog(QDialog, Ui_Dialog):

    def __init__(self, olfaConfigFileName, parent=None):
        super().__init__()
        self.setupUi(self)
        self.olfaConfigFile = olfaConfigFileName

        with open(self.olfaConfigFile, 'r') as olfa_config:
            self.olfaConfigDict = json.load(olfa_config)
            logging.info(self.olfaConfigDict)
        
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
        self.interfaceComboBox.addItem('teensy')
        self.interfaceComboBox.setCurrentText(interface)
        cassette_1_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn']
        self.cassetteSNLineEdit_1.setText(str(cassette_1_sn))
        cassette_2_sn = self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn']
        self.cassetteSNLineEdit_2.setText(str(cassette_2_sn))
        master_sn = self.olfaConfigDict['Olfactometers'][0]['master_sn']
        self.masterSNLineEdit.setText(str(master_sn))
        slaveIndex = self.olfaConfigDict['Olfactometers'][0]['slave_index']
        self.slaveIndexLineEdit.setText(str(slaveIndex))

        if '1' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['1']:
                odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['1']['odor']
                self.vialOdorNameLineEdit_1.setText(odor)
            if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['1']:
                conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['1']['conc']
                self.vialConcLineEdit_1.setText(str(conc))
        if '2' in self.olfaConfigDict['Olfactometers'][0]['Vials']:  
            if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['2']:  
                odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['2']['odor']
                self.vialOdorNameLineEdit_2.setText(odor)
            if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['2']:    
                conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['2']['conc']
                self.vialConcLineEdit_2.setText(str(conc))
        if '3' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['3']:  
                odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['3']['odor']
                self.vialOdorNameLineEdit_3.setText(odor)
            if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['3']:    
                conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['3']['conc']
                self.vialConcLineEdit_3.setText(str(conc))
        if '4' in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            if 'odor' in self.olfaConfigDict['Olfactometers'][0]['Vials']['4']:  
                odor = self.olfaConfigDict['Olfactometers'][0]['Vials']['4']['odor']
                self.vialOdorNameLineEdit_4.setText(odor)
            if 'conc' in self.olfaConfigDict['Olfactometers'][0]['Vials']['4']:    
                conc = self.olfaConfigDict['Olfactometers'][0]['Vials']['4']['conc']
                self.vialConcLineEdit_4.setText(str(conc))
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

            self.vialOdorNameLineEdit_1.editingFinished.connect(self.recordVialOdorName_1)
            self.vialConcLineEdit_1.editingFinished.connect(self.recordVialConc_1)
            self.vialOdorNameLineEdit_2.editingFinished.connect(self.recordVialOdorName_2)
            self.vialConcLineEdit_2.editingFinished.connect(self.recordVialConc_2)
            self.vialOdorNameLineEdit_3.editingFinished.connect(self.recordVialOdorName_3)
            self.vialConcLineEdit_3.editingFinished.connect(self.recordVialConc_3)
            self.vialOdorNameLineEdit_4.editingFinished.connect(self.recordVialOdorName_4)
            self.vialConcLineEdit_4.editingFinished.connect(self.recordVialConc_4)
            self.vialOdorNameLineEdit_5.editingFinished.connect(self.recordVialOdorName_5)
            self.vialConcLineEdit_5.editingFinished.connect(self.recordVialConc_5)
            self.vialOdorNameLineEdit_6.editingFinished.connect(self.recordVialOdorName_6)
            self.vialConcLineEdit_6.editingFinished.connect(self.recordVialConc_6)
            self.vialOdorNameLineEdit_7.editingFinished.connect(self.recordVialOdorName_7)
            self.vialConcLineEdit_7.editingFinished.connect(self.recordVialConc_7)
            self.vialOdorNameLineEdit_8.editingFinished.connect(self.recordVialOdorName_8)
            self.vialConcLineEdit_8.editingFinished.connect(self.recordVialConc_8)

            self.buttonBox.accepted.connect(self.saveToCurrentFile)
            self.saveAsButton.clicked.connect(self.saveAsNewFile)

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
        self.olfaConfigDict['Olfactometers'][0]['com_port'] = int(self.comPortLineEdit.text())

    def recordInterface(self):
        self.olfaConfigDict['Olfactometers'][0]['interface'] = self.interfaceComboBox.currentText()

    def recordCassetteSN_1(self):
        self.olfaConfigDict['Olfactometers'][0]['cassette_1_sn'] = int(self.cassetteSNLineEdit_1.text())

    def recordCassetteSN_2(self):
        self.olfaConfigDict['Olfactometers'][0]['cassette_2_sn'] = int(self.cassetteSNLineEdit_2.text())

    def recordMasterSN(self):
        self.olfaConfigDict['Olfactometers'][0]['master_sn'] = int(self.masterSNLineEdit.text())

    def recordSlaveIndex(self):
        self.olfaConfigDict['Olfactometers'][0]['slave_index'] = int(self.slaveIndexLineEdit.text())

    def recordVialOdorName_1(self):
        if '1' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['1'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['1']['odor'] = self.vialOdorNameLineEdit_1.text()

    def recordVialConc_1(self):
        if '1' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['1'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['1']['conc'] = float(self.vialConcLineEdit_1.text())

    def recordVialOdorName_2(self):
        if '2' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['2'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['2']['odor'] = self.vialOdorNameLineEdit_2.text()

    def recordVialConc_2(self):
        if '2' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['2'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['2']['conc'] = float(self.vialConcLineEdit_2.text())

    def recordVialOdorName_3(self):
        if '3' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['3'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['3']['odor'] = self.vialOdorNameLineEdit_3.text()

    def recordVialConc_3(self):
        if '3' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['3'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['3']['conc'] = float(self.vialConcLineEdit_3.text())

    def recordVialOdorName_4(self):
        if '4' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['4'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['4']['odor'] = self.vialOdorNameLineEdit_4.text()

    def recordVialConc_4(self):
        if '4' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['4'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['4']['conc'] = float(self.vialConcLineEdit_4.text())

    def recordVialOdorName_5(self):
        if '5' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['odor'] = self.vialOdorNameLineEdit_5.text()

    def recordVialConc_5(self):
        if '5' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['5'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['5']['conc'] = float(self.vialConcLineEdit_5.text())

    def recordVialOdorName_6(self):
        if '6' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['odor'] = self.vialOdorNameLineEdit_6.text()

    def recordVialConc_6(self):
        if '6' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['6'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['6']['conc'] = float(self.vialConcLineEdit_6.text())

    def recordVialOdorName_7(self):
        if '7' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['odor'] = self.vialOdorNameLineEdit_7.text()

    def recordVialConc_7(self):
        if '7' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['7'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['7']['conc'] = float(self.vialConcLineEdit_7.text())

    def recordVialOdorName_8(self):
        if '8' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['odor'] = self.vialOdorNameLineEdit_8.text()

    def recordVialConc_8(self):
        if '8' not in self.olfaConfigDict['Olfactometers'][0]['Vials']:
            self.olfaConfigDict['Olfactometers'][0]['Vials']['8'] = {}
        self.olfaConfigDict['Olfactometers'][0]['Vials']['8']['conc'] = float(self.vialConcLineEdit_8.text())

    def saveToCurrentFile(self):
        with open(self.olfaConfigFile, 'w') as olfa_config:
            json.dump(self.olfaConfigDict, olfa_config, indent=4)

    def saveAsNewFile(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        fileName, _ = QFileDialog.getSaveFileName(self, "QFileDialog.getSaveFileName()", "protocol.json", "All Files (*);;JSON Files (*.json);;Text Files (*.txt)", options=options)
        if fileName:
            with open(fileName, 'w') as olfa_config:
                json.dump(self.olfaConfigDict, olfa_config, indent=4)
                
            self.accept()  # Closes the dialog window.
