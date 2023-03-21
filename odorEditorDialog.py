import json
import os
import logging
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QErrorMessage
from ui_files.odor_config_ui import Ui_Dialog
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
import random

logging.basicConfig(format="%(message)s", level=logging.INFO)


class OdorEditorDialog(QDialog, Ui_Dialog):

    def __init__(self, olfaConfigFileName=None, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Odor Configuration Editor")
        self.olfaConfigFile = olfaConfigFileName

        if self.olfaConfigFile:
            with open(self.olfaConfigFile, 'r') as olfa_config:
                self.olfaConfigDict = json.load(olfa_config)
                print(self.olfaConfigDict)
        else:
            print('Cannot read olfaconfig file.')
        
        self.tableWidget.itemChanged.connect(self.updateMFCsDilutor)

        self.populateOdorTable()
        self.connectSignalsSlots()
        
        # self.connectSignalsSlots()

    def populateOdorTable(self):
        iivial = 0
        for ivial, vial in enumerate( self.olfaConfigDict['Olfactometers'][0]['Vials']):
            
           
            vial_number = int(vial)-4
            
            vial_name = self.olfaConfigDict['Olfactometers'][0]['Vials'][vial]['odor']
            if vial_name != 'dummy':
                print(vial_name, iivial)
               
                self.tableWidget.insertRow(iivial)
                self.tableWidget.setItem(iivial,0,QTableWidgetItem(str(vial_number)))  # set the vial_number
                self.tableWidget.setItem(iivial,1,QTableWidgetItem(vial_name))  # set the vial_name
                
                self.tableWidget.setItem(iivial,3,QTableWidgetItem('100'))  # set the MFC
                self.tableWidget.setItem(iivial,4,QTableWidgetItem('0'))  # set the Dilutor
                self.tableWidget.setItem(iivial,5,QTableWidgetItem('2'))  # set the repetitions

                item = self.tableWidget.item(iivial,3)
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                item = self.tableWidget.item(iivial,4)
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                
                self.tableWidget.setItem(iivial,2,QTableWidgetItem('8'))  # set the vial_name
                iivial += 1


    def generateStimuliTable(self):

        stimuliTable = []
        # Read capacities of the MFCs you need to set for odor delivery : this is needed to compute flow 
        for olfa in self.olfaConfigDict['Olfactometers']:
            for mfc in  olfa['MFCs']:
                if mfc['gas'] == 'Nitrogen':
                    olfa_mfc_capacity = int(mfc['capacity'] )
        dil_mfc_capacity = self.olfaConfigDict['Dilutors'][0]['MFCs'][0]['capacity'] # I take the first one because dilutors are by definition of the same capacity
        print(dil_mfc_capacity)
        all_trials = []
        
        # Build odor stimuli table 
        for irow in range(0, self.tableWidget.rowCount()-1):
            vial_number = self.tableWidget.item(irow,0).text()
            if vial_number != '':
            
                vial_name = self.tableWidget.item(irow,1).text()
                mfc_dil = self.tableWidget.item(irow,3).text()[1:-1].split(',')  # split string to list, '[1,2,3]' into [1,2,3]
                dilutor_dil = self.tableWidget.item(irow,4).text()[1:-1].split(',')
                print(dilutor_dil)
                nRep = int(self.tableWidget.item(irow,5).text())
                for istim, mfc in enumerate(mfc_dil):
                    mfc_flow = (float(mfc)/100)*olfa_mfc_capacity
                    dil_flow = (float(dilutor_dil[istim])/100)*dil_mfc_capacity
                    for irep in range(0, nRep):
                        all_trials.append([vial_number, vial_name, mfc_flow, dil_flow])
                #stimuliTable.append([stimuliTable, odor_name])
        # Shuffle all trials
        random.shuffle(all_trials)

        self.all_trials_dict = [{'vial_num':trial[0],'vial_name':trial[1],'mfc_flow':trial[2],'dilutor_flow':trial[3]} for trial in all_trials]  # list of dictionaries for each trial, to feed to protocol worker

        for itrial, trial in enumerate(all_trials):
            self.stimuliTable.insertRow(itrial)
            for i_item,item in enumerate(trial):
                self.stimuliTable.setItem(itrial,i_item, QTableWidgetItem(str(item)))  # set the vial_number
            



    def updateMFCsDilutor(self,item):
        if item.column() == 2:
            conc_string = item.text()
           
            if conc_string != '':
                conc_list = conc_string.split(',')
                mfc = []
                dilutor = []
                for conc_s in conc_list:
                    try:
                        
                        conc = float(conc_s)   
                        vial_number = item.row()
                       
                        if conc > 10:
                            mfc.append(conc)
                            dilutor.append(0)
                        else:
                            mfc.append(10)
                            dilutor.append(round(100*(1 - (conc/10)),ndigits=3))
                    except:
                        mfc.append(100)
                        dilutor.append(0)
                        error_dialog = QErrorMessage()
                        error_dialog.showMessage('Please enter a valid number.')
                
                self.tableWidget.setItem(vial_number,3,QTableWidgetItem(str(mfc)))  # set the mfc
                self.tableWidget.setItem(vial_number,4,QTableWidgetItem(str(dilutor)))  # set the dilutor

                item = self.tableWidget.item(vial_number,3)
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                item = self.tableWidget.item(vial_number,4)
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
        else:
            pass

    def connectSignalsSlots(self):
        
        # Connect widgets to function of this class
        self.generateOdorTableButton.clicked
        self.generateOdorTableButton.clicked.connect(self.generateStimuliTable)
        #print('Connecting')
        # QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL('itemChanged(QTableWidgetItem*, QTableWidgetItem*)'), self.quickchange) 
        # self.tableWidget.cellEntered(0,2).connect(self.quickchange)  # why doesn't this signal connect??
        #self.quickchange()
        #print('Connected')