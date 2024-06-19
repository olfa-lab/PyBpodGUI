import os
# import package to read excel files
import pandas as pd
import xlrd

stimuliFilesDirectory = os.getcwd() + '\\soundstimuliFiles\\'
currentStimuliConfigFileName = stimuliFilesDirectory + 'defaultSoundConfig.xlsx'

if currentStimuliConfigFileName:
    
    print(currentStimuliConfigFileName)
    #excel_workbook = xlrd.open_workbook('sales_data.xls')

    soundConfigDict = pd.read_excel(currentStimuliConfigFileName)
    attr= soundConfigDict.keys()
    
    print(list(attr))
else:
    print('Cannot read olfaconfig file.')