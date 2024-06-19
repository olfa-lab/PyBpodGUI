import json
import os
import logging
from PyQt5.QtWidgets import QDialog, QMessageBox, QTableWidgetItem, QErrorMessage, QFileDialog
from ui_files.sound_config_ui import Ui_Dialog
from PyQt5 import QtCore
from PyQt5.QtCore import pyqtSlot
import random
import tables
import h5py
from datetime import date
from datetime import datetime
import pandas as pd


logging.basicConfig(format="%(message)s", level=logging.INFO)


class SoundEditorDialog(QDialog, Ui_Dialog):
    # This class handles two different table: 
    # - on the left: stimuliTable: this is the list of all possible stimuli that can be given to the mouse, as a combination of channel, freq, amplitude 
    # - on the right: trialTable: this is the list of shuffled stimuli which will be delivered during an experiment
    
    def __init__(self, soundConfigFileName=None, parent=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Sound Configuration Editor")
        self.currentStimuliConfigFileName = 'defaultSoundConfig.xlsx'#'H:\\repos\\pybpod-3.9\\PyBpodGUI\\defaultSoundConfig.h5'
        self.stimuliFilesDirectory = os.getcwd() + '\\soundstimuliFiles\\'
        self.currentStimuliConfigFileName = self.stimuliFilesDirectory + 'defaultSoundConfig.xlsx'
        self.bufferStimuliConfigFileName = self.stimuliFilesDirectory + 'bufferSoundConfig.xlsx'
        
        
        if self.currentStimuliConfigFileName:
            self.soundConfigDict = pd.read_excel(self.currentStimuliConfigFileName)
            # Elements of this dictionary are obtained by querying the attribute which is the 
            # name of the wquantity you want. and the index of the row you want. 
            # Ex: soundConfigDict.Freq[0], Freq = attribute, 0 = index
            cols_labels = self.soundConfigDict.keys()
            self.stimuli_config_columns = dict()
            for ilabel, label in enumerate(cols_labels):
                self.stimuli_config_columns[label] = ilabel
            self.initSoundTable()
        else:
            # Initialize dictionary anyway if you don't find the file
            self.stimuli_config_columns ={ 'Freq':0, 'Amp':1, 'Duration':2, 'Prob':3}
            print('Cannot read soundconfig file.')
        
        #self.tableWidget.itemChanged.connect(self.updateMFCsDilutor) # This is not necessary, no need to compute specific parameters for now 
        
        self.connectSignalsSlots()
    
            
    def initSoundTable(self):
        # Setting labels in the right position
        for colname in self.stimuli_config_columns.keys():
            self.tableWidget.insertColumn(self.stimuli_config_columns[colname])
        self.tableWidget.setHorizontalHeaderLabels(self.stimuli_config_columns.keys())
        # Setting values of table from soundConfigDict
        all_freqs = self.soundConfigDict.Freq
        for irow, freq in enumerate(all_freqs):
            self.tableWidget.insertRow(irow)
            self.tableWidget.setItem(irow,0,QTableWidgetItem(str(self.soundConfigDict.Freq[irow])))
            self.tableWidget.setItem(irow,1,QTableWidgetItem(str(self.soundConfigDict.Amp[irow])))
            self.tableWidget.setItem(irow,2,QTableWidgetItem(str(self.soundConfigDict.Duration[irow])))
            self.tableWidget.setItem(irow,3,QTableWidgetItem(str(self.soundConfigDict.Prob[irow])))
            
            item = self.tableWidget.item(irow,0) # make editable
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            item = self.tableWidget.item(irow,1) # make editable
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            item = self.tableWidget.item(irow,2) # make editable
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
            item = self.tableWidget.item(irow,3) # make editable
            item.setFlags(QtCore.Qt.ItemIsSelectable|QtCore.Qt.ItemIsDragEnabled|QtCore.Qt.ItemIsDropEnabled|QtCore.Qt.ItemIsUserCheckable|QtCore.Qt.ItemIsEnabled)
           

    def saveStimuliConfigTable(self, fileName=None):# Make the description dict for the vials table.
        
        
        self.stimuliTableDescDict = {}
        pos = self.stimuli_config_columns['Freq']
        self.stimuliTableDescDict["freq"] = tables.UInt8Col(pos=pos)
        pos = self.stimuli_config_columns['Amp']
        self.stimuliTableDescDict["amp"] = tables.StringCol(32, pos=pos)
        pos = self.stimuli_config_columns['Duration']
        self.stimuliTableDescDict["duration"] = tables.StringCol(32, pos=pos) #tables.UInt8Col(pos=pos)
        pos = self.stimuli_config_columns['Prob']
        self.stimuliTableDescDict["prob"] = tables.StringCol(32, pos=pos)
        
        
        if fileName is None or fileName is False:
            fileName = self.bufferStimuliConfigFileName
        
        self.stimulus_config_file = tables.open_file(filename=fileName , mode='w', title=f"Stimuli Table")
        
        self.stimulusTable = self.stimulus_config_file.create_table(where = self.stimulus_config_file.root, name='stimuli', description= self.stimuliTableDescDict, title='Stimuli Details')
        self.stimuliRow = self.stimulusTable.row
        self.stimDict= {}
        # Write to the stimuli table.
        for irow in range(0, self.tableWidget.rowCount()):

            self.stimuliRow['freq'] = int(self.tableWidget.item(irow,self.stimuli_config_columns['Freq']).text())
            self.stimuliRow['amp'] = self.tableWidget.item(irow,self.stimuli_config_columns['Amp']).text()
            self.stimuliRow['duration'] = self.tableWidget.item(irow,self.stimuli_config_columns['Duration']).text()
            self.stimuliRow['prob'] = (self.tableWidget.item(irow,self.stimuli_config_columns['Prob']).text())
            self.stimuliRow.append()

            # Create the variable that gets sent to the app
            freq = int(self.tableWidget.item(irow,self.stimuli_config_columns['Freq']).text())
            amps = self.tableWidget.item(irow,self.stimuli_config_columns['Amp']).text()[1:-1].split(',')
            self.stimDict[freq] = dict()
            self.stimDict[freq]['amps'] = amps
            self.stimDict[freq]['duration'] = self.tableWidget.item(irow,self.stimuli_config_columns['Duration']).text()[1:-1].split(',')
            self.stimDict[freq]['prob'] = (self.tableWidget.item(irow,self.stimuli_config_columns['Prob']).text())[1:-1].split(',')
           
        self.stimulusTable.flush()
        self.stimulus_config_file.close()

       

    # def fillOdorTable(self, fileName):

    #     f1 = h5py.File(fileName,'r+')    
    #     while self.tableWidget.rowCount() > 0:
    #         self.tableWidget.removeRow(0)

    #     for icol, colname in enumerate(self.stimuli_config_columns.keys()):
    #         self.tableWidget.insertColumn(icol)
    #     # print(self.stimuli_config_columns.keys())
    #     self.tableWidget.setHorizontalHeaderLabels(self.stimuli_config_columns.keys())
        
    #     for irow, row in enumerate(f1['stimuli']):
            
    #         self.tableWidget.insertRow(irow)
    #         for icol, item in enumerate(row):
    #             # print(type(item), item)
    #             if icol== 2 or icol== 3 or icol == 4 or icol == 5 or icol==6:
    #                 self.tableWidget.setItem(irow,icol,QTableWidgetItem((item.decode())))
    #             else:
    #                 # print(icol, item)
    #                 self.tableWidget.setItem(irow,icol,QTableWidgetItem(str(item)))
    #             #if icol == 0 or icol == 1 or icol == 6:
    #             #    self.tableWidget.setItem(irow,icol,QTableWidgetItem(int(item)))  # set the olfa number
    #             #elif icol== 3 or icol == 4 or icol == 5:
    #             #    self.tableWidget.setItem(irow,icol,QTableWidgetItem((item.decode())))  # set the olfa number
    #             #else:
    #             #    self.tableWidget.setItem(irow,icol,QTableWidgetItem(str(item)))  # set the olfa number


    


    # def fillStimuliListTable(self, fileName):

    #     f1 = h5py.File(fileName,'r+')    
    #     while self.stimuliTable.rowCount() > 0:
    #         self.stimuliTable.removeRow(0)

    #     for icol, colname in enumerate(self.stimuli_list_columns.keys()):
    #         self.stimuliTable.insertColumn(icol)
    #     self.stimuliTable.setHorizontalHeaderLabels(self.stimuli_list_columns.keys())
    #     all_trials = []
    #     for irow, row in enumerate(f1['stimuli_list']):
    #         self.stimuliTable.insertRow(irow)
    #         trial = []
    #         for icol, item in enumerate(row):
    #             # print(type(item), item)
    #             if icol== 2 or icol== 3 or icol == 4 :
    #                 self.stimuliTable.setItem(irow,icol,QTableWidgetItem((item.decode())))
    #                 trial.append(item.decode())
    #             else:
    #                 self.stimuliTable.setItem(irow,icol,QTableWidgetItem(str(item)))
    #                 trial.append(item)
                
    #         all_trials.append(trial)


    #     self.all_trials_dict = [{'olfa_num':int(trial[self.stimuli_list_columns['Olfa']]),
    #                              'vial_num':int(trial[self.stimuli_list_columns['Vial']]),
    #                              'vial_name':trial[self.stimuli_list_columns['Odor']],
    #                              'mfc_flow':int(float(trial[self.stimuli_list_columns['MFC_flow']])),
    #                              'dilutor_flow':int(float(trial[self.stimuli_list_columns['Dilutor_flow']]))} for trial in all_trials]  # list of dictionaries for each trial, to feed to protocol worker

       

   

    

   


    # def loadStimuliConfigTable(self):
    #     dlg = QFileDialog()
    #     dlg.setFileMode(QFileDialog.AnyFile)
    #     dlg.setDirectory(self.stimuliFilesDirectory)
    #     dlg.setNameFilters(["H5 file (*.h5)"])
    #     dlg.selectNameFilter("H5 file (*.h5)")
    #     if dlg.exec_():
    #         filenames = dlg.selectedFiles()
    #     print(f'Loading stimuli config table from {filenames}')
    #     self.fillOdorTable(filenames[0])
    
    # def loadStimuliListTable(self):
    #     dlg = QFileDialog()
    #     dlg.setFileMode(QFileDialog.AnyFile)
    #     dlg.setDirectory(self.stimuliFilesDirectory)
    #     dlg.setNameFilters(["H5 file (*.h5)"])
    #     dlg.selectNameFilter("H5 file (*.h5)")
    #     if dlg.exec_():
    #         filenames = dlg.selectedFiles()
    #     print(f'Loading stimuli list table from {filenames}')
    #     self.fillStimuliListTable(filenames[0])


    # def saveAsStimuliConfigTable(self):
    #     dlg = QFileDialog()
    #     dlg.setDirectory(self.stimuliFilesDirectory)
    #     name  = dlg.getSaveFileName(self, 'Save File')
    #     print( name[0][-3:])
    #     if name[0][-3:] !='.h5':
    #         fileName = name[0] + '.h5'
    #     else:
    #         fileName = name[0]
    #     print(f'Saving stimuli config table to {fileName}')
    #     self.saveStimuliConfigTable(fileName)

    # def saveAsStimuliListTable(self):
    #     dlg = QFileDialog()
    #     dlg.setDirectory(self.stimuliFilesDirectory)
    #     name  = dlg.getSaveFileName(self, 'Save File')
    #     if name[0][-3:] !='.h5':
    #         fileName = name[0] + '.h5'
    #     else:
    #         fileName = name[0]
    #     print(f'Saving stimuli list table to {fileName}')
    #     self.saveStimuliListTable(fileName)

    def connectSignalsSlots(self):
        print('Connecting signals')
        # Connect widgets to function of this class
        self.saveSoundConfigFile.clicked
        self.saveSoundConfigFile.clicked.connect(self.saveStimuliConfigTable)

        # Connect widgets to function of this class
        #self.generateOdorTableButton.clicked
        #self.generateOdorTableButton.clicked.connect(self.generateStimuliTable)

        #self.loadStimuliConfigFile.clicked.connect(self.loadStimuliConfigTable)
        #self.loadStimuliListFile.clicked.connect(self.loadStimuliListTable)
       
        #self.saveStimuliConfigFile.clicked.connect(self.saveStimuliConfigTable)
        #self.saveStimuliListFile.clicked.connect(self.saveStimuliListTable)
        
        #self.saveAsStimuliConfigFile.clicked.connect(self.saveAsStimuliConfigTable)
        #self.saveAsStimuliListFile.clicked.connect(self.saveAsStimuliListTable)
        # add line that loads the table whenever is saved
        

        #print('Connecting')0
        # QtCore.QObject.connect(self.tableWidget, QtCore.SIGNAL('itemChanged(QTableWidgetItem*, QTableWidgetItem*)'), self.quickchange) 
        # self.tableWidget.cellEntered(0,2).connect(self.quickchange)  # why doesn't this signal connect??
        #self.quickchange()
        #print('Connected')