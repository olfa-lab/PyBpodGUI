import json
import os
import logging
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QErrorMessage
from ui_files.odor_config_ui import Ui_Dialog
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
import random
import tables
import h5py
from datetime import date
from datetime import datetime


logging.basicConfig(format="%(message)s", level=logging.INFO)


class OdorEditorDialog(QDialog, Ui_Dialog):
    # This class handles two different table: 
    # - on the left: stimuliTable: this is the list of all possible stimuli that can be given to the mouse, as a combination of vials, mfc flows and dilutor flows
    # - on the right: trialTable: this is the list of shuffled stimuli which will be delivered during an experiment
    
    
    def __init__(self, olfaConfigFileName=None, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Odor Configuration Editor")
        self.olfaConfigFile = olfaConfigFileName
        self.currentStimuliConfigFileName = 'H:\\repos\\pybpod-3.9\\PyBpodGUI\\currentStimuliConfig.h5'
        #self.currentStimuliListFileName = 'H:\\repos\\pybpod-3.9\\PyBpodGUI\\currentStimuliList.h5'
        #try:
            #self.loadStimuliTable()
        #except:
        
        if self.olfaConfigFile:
            with open(self.olfaConfigFile, 'r') as olfa_config:
                self.olfaConfigDict = json.load(olfa_config)
                print(self.olfaConfigDict)
        else:
            print('Cannot read olfaconfig file.')
        
        self.tableWidget.itemChanged.connect(self.updateMFCsDilutor)

        # set stimuli_config column variables
        self.stimuli_config_columns = {'Olfa':0,
                                       'Vial':1,
                                       'Odor':2,
                                       'Headspace':3,
                                       'MFC_flow':4,
                                       'Dilutor_flow':5,
                                       'Reps':6}
        
        self.stimuli_list_columns = {'Olfa':0,
                                       'Vial':1,
                                       'Odor':2,
                                       'MFC_flow':3,
                                       'Dilutor_flow':4}

        self.initOdorTable()
        self.connectSignalsSlots()
        
           
        
        # self.connectSignalsSlots()

    def initOdorTable(self):
        for icol, colname in enumerate(self.stimuli_config_columns.keys()):
            self.tableWidget.insertColumn(icol)
        self.tableWidget.setHorizontalHeaderLabels(self.stimuli_config_columns.keys())

        irow = 0
        for iolfa, olfa in enumerate( self.olfaConfigDict['Olfactometers']):

            for vial in self.olfaConfigDict['Olfactometers'][0]['Vials']:
                                
                vial_name = self.olfaConfigDict['Olfactometers'][0]['Vials'][vial]['odor']
                if vial_name != 'dummy':
                
                    self.tableWidget.insertRow(irow)
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Olfa'],QTableWidgetItem(str(iolfa)))  # set the olfa number
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Vial'],QTableWidgetItem(str(vial)))  # set the vial_number
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Odor'],QTableWidgetItem(vial_name))  # set the vial_name
                    
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['MFC_flow'],QTableWidgetItem('100'))  # set the MFC
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Dilutor_flow'],QTableWidgetItem('0'))  # set the Dilutor
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Reps'],QTableWidgetItem('2'))  # set the repetitions

                    item = self.tableWidget.item(irow,self.stimuli_config_columns['MFC_flow']) # make editable
                    item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                    item = self.tableWidget.item(irow,self.stimuli_config_columns['Dilutor_flow']) # make editable
                    item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                    
                    # this must be called last to update the other columns
                    self.tableWidget.setItem(irow,self.stimuli_config_columns['Headspace'],QTableWidgetItem('8'))  # set the headspace %

                    irow += 1
    

    def generateStimuliTable(self):
        while self.stimuliTable.rowCount() > 0:
            self.stimuliTable.removeRow(0)
         
        for icol, colname in enumerate(self.stimuli_list_columns.keys()):
            self.stimuliTable.insertColumn(icol)
            self.stimuliTable.setHorizontalHeaderLabels(self.stimuli_list_columns.keys())
    
        # Read capacities of the MFCs you need to set for odor delivery : this is needed to compute flow 
        for olfa in self.olfaConfigDict['Olfactometers']:
            for mfc in  olfa['MFCs']:
                if mfc['gas'] == 'Nitrogen':
                    olfa_mfc_capacity = int(mfc['capacity'] )
        dil_mfc_capacity = self.olfaConfigDict['Dilutors'][0]['MFCs'][0]['capacity'] # I take the first one because dilutors are by definition of the same capacity
        all_trials = []
        
        # Build odor stimuli table 
        for irow in range(0, self.tableWidget.rowCount()):  # removed -1
            olfa_number = self.tableWidget.item(irow,self.stimuli_config_columns['Olfa']).text()
            vial_number = self.tableWidget.item(irow,self.stimuli_config_columns['Vial']).text()
            if vial_number != '':
                vial_name = self.tableWidget.item(irow,self.stimuli_config_columns['Odor']).text()
                mfc_dil = self.tableWidget.item(irow,self.stimuli_config_columns['MFC_flow']).text()[1:-1].split(',')  # split string to list, '[1,2,3]' into [1,2,3]
                dilutor_dil = self.tableWidget.item(irow,self.stimuli_config_columns['Dilutor_flow']).text()[1:-1].split(',')
                nRep = int(self.tableWidget.item(irow,self.stimuli_config_columns['Reps']).text())
                for istim, mfc in enumerate(mfc_dil):
                    mfc_flow = (float(mfc)/100)*olfa_mfc_capacity
                    dil_flow = (float(dilutor_dil[istim])/100)*dil_mfc_capacity
                    for irep in range(0, nRep):
                        all_trials.append([olfa_number, vial_number, vial_name, mfc_flow, dil_flow])
                #stimuliTable.append([stimuliTable, odor_name])
        # Shuffle all trials
        random.shuffle(all_trials)

        self.all_trials_dict = [{'olfa_num':int(trial[self.stimuli_list_columns['Olfa']]),
                                 'vial_num':int(trial[self.stimuli_list_columns['Vial']]),
                                 'vial_name':trial[self.stimuli_list_columns['Odor']],
                                 'mfc_flow':int(trial[self.stimuli_list_columns['MFC_flow']]),
                                 'dilutor_flow':int(trial[self.stimuli_list_columns['Dilutor_flow']])} for trial in all_trials]  # list of dictionaries for each trial, to feed to protocol worker

        for itrial, trial in enumerate(all_trials):
            self.stimuliTable.insertRow(itrial)
            for i_item,item in enumerate(trial):
                self.stimuliTable.setItem(itrial,i_item, QTableWidgetItem(str(item)))  # set the vial_number
        self.saveStimuliListTable()


    def updateMFCsDilutor(self,item):
        if item.column() == self.stimuli_config_columns['Headspace']:
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
                
                self.tableWidget.setItem(vial_number,self.stimuli_config_columns['MFC_flow'],QTableWidgetItem(str(mfc)))  # set the mfc
                self.tableWidget.setItem(vial_number,self.stimuli_config_columns['Dilutor_flow'],QTableWidgetItem(str(dilutor)))  # set the dilutor

                item = self.tableWidget.item(vial_number,self.stimuli_config_columns['MFC_flow'])
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
                item = self.tableWidget.item(vial_number,self.stimuli_config_columns['Dilutor_flow'])
                item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
        else:
            pass
    
    def saveStimuliConfigTable(self):# Make the description dict for the vials table.
        self.stimuliTableDescDict = {}
        pos = self.stimuli_config_columns['Olfa']
        self.stimuliListDict["olfa"] = tables.UInt8Col(pos=pos)
        pos = self.stimuli_config_columns['Vial']
        self.stimuliListDict["vialnum"] = tables.UInt8Col(pos=pos)
        pos = self.stimuli_config_columns['Odor']
        self.stimuliListDict["odor"] = tables.StringCol(32, pos=pos) #tables.UInt8Col(pos=pos)
        pos = self.stimuli_config_columns['Headspace']
        self.stimuliListDict["headspace"] = tables.StringCol(32, pos=pos)
        pos = self.stimuli_config_columns['MFC_flow']
        self.stimuliListDict["mfc"] = tables.StringCol(32, pos=pos)
        pos = self.stimuli_config_columns['Dilutor_flow']
        self.stimuliListDict["dilutor"] = tables.StringCol(32, pos=pos)
        pos = self.stimuli_config_columns['Reps']
        self.stimuliListDict["repetition"] = tables.StringCol(32, pos=pos)
        
        self.stimulus_config_file = tables.open_file(filename=self.currentConfigFileName , mode='w', title=f"Stimuli Table")
        
        self.stimulusTable = self.stimulus_config_file.create_table(where=self.stimulus_config_file.root, name='stimuli', description= self.stimuliTableDescDict, title='Vial Details')
        self.stimuliRow = self.stimulusTable.row

        # Write to the stimuli table.
        for irow in range(0, self.tableWidget.rowCount()):

            self.stimuliRow['olfa'] = int(self.tableWidget.item(irow,self.stimuli_config_columns['Olfa']).text())
            self.stimuliRow['vialnum'] = int(self.tableWidget.item(irow,self.stimuli_config_columns['Vial']).text())
            self.stimuliRow['odor'] = self.tableWidget.item(irow,self.stimuli_config_columns['Odor']).text()
            self.stimuliRow['headspace'] = (self.tableWidget.item(irow,self.stimuli_config_columns['Headspace']).text())
            self.stimuliRow['mfc'] = (self.tableWidget.item(irow,self.stimuli_config_columns['MFC_flow']).text())
            self.stimuliRow['dilutor'] = (self.tableWidget.item(irow,self.stimuli_config_columns['Dilutor_flow']).text())
            self.stimuliRow['repetition'] = int(self.tableWidget.item(irow,self.stimuli_config_columns['Reps']).text())
            self.stimuliRow.append()
           
        
        self.stimulusTable.flush()
        self.stimulus_config_file.close()

    def saveStimuliListTable(self):

        self.stimuliListDict = {}
        pos = self.stimuli_list_columns['Olfa']
        self.stimuliListDict["olfa"] = tables.UInt8Col(pos=pos)
        pos = self.stimuli_list_columns['Vial']
        self.stimuliListDict["vial"] = tables.UInt8Col(pos=pos)
        pos = self.stimuli_list_columns['Odor']
        self.stimuliListDict["odor"] = tables.StringCol(32, pos=pos) #tables.UInt8Col(pos=pos)
        pos = self.stimuli_list_columns['MFC_flow']
        self.stimuliListDict["mfc"] = tables.StringCol(32, pos=pos)
        pos = self.stimuli_list_columns['Dilutor_flow']
        self.stimuliListDict["dilutor"] = tables.StringCol(32, pos=pos)
        

        date_and_time = datetime.now()
        currentTime = date_and_time.strftime("%H-%M-%S")
        self.currentStimuliListFileName = f'stimuliFiles/stimuliList_{date.today()}_{currentTime}.h5' ## Ad something else otherwise you can'r run experiment twice in a day
        self.stimulus_list_file = tables.open_file(filename=self.currentStimuliListFileName , mode='w', title=f"Stimuli LIst")
        
        self.stimulusList = self.stimulus_list_file.create_table(where=self.stimulus_list_file.root, name='stimuli_list', description= self.stimuliListDict, title='Stimulus List')
        self.stimuliListRow = self.stimulusList.row

        # Write to the stimuli table.
        for irow in range(self.stimuliTable.rowCount()):
            #print(f"Printing the row in the table: {self.stimuliTable.item(irow,self.stimuli_list_columns['Olfa'])}")
            print(irow)
            self.stimuliListRow['olfa'] = int(self.stimuliTable.item(irow,self.stimuli_list_columns['Olfa']).text())
            self.stimuliListRow['vial'] = int(self.stimuliTable.item(irow,self.stimuli_list_columns['Vial']).text())
            self.stimuliListRow['odor'] = self.stimuliTable.item(irow,self.stimuli_list_columns['Odor']).text()
            self.stimuliListRow['mfc'] = (self.stimuliTable.item(irow,self.stimuli_list_columns['MFC_flow']).text())
            self.stimuliListRow['dilutor'] = (self.stimuliTable.item(irow,self.stimuli_list_columns['Dilutor_flow']).text())
            self.stimuliListRow.append()
           
        
        self.stimulusList.flush()
        self.stimulus_list_file.close()
       

    def saveOdorFile(self):
        pass
    def loadStimuliTable(self):

        pass
    def connectSignalsSlots(self):
        
        # Connect widgets to function of this class
        self.generateOdorTableButton.clicked
        self.generateOdorTableButton.clicked.connect(self.generateStimuliTable)
        self.saveOdorTableButton.clicked.connect(self.saveStimuliConfigTable)
        self.saveOdorTableButton.clicked.connect(self.saveStimuliListTable)
        self.saveOdorTableAsFileButton.clicked.connect(self.saveOdorFile)
        # add line that loads the table whenever is saved
        

        #print('Connecting')0
        # QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL('itemChanged(QTableWidgetItem*, QTableWidgetItem*)'), self.quickchange) 
        # self.tableWidget.cellEntered(0,2).connect(self.quickchange)  # why doesn't this signal connect??
        #self.quickchange()
        #print('Connected')