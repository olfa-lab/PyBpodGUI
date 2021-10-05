import re
import pyqtgraph as pg
import logging
import numpy as np
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal


logging.basicConfig(format="%(message)s", level=logging.INFO)


class ResultsPlotWorker(QObject):
    def __init__(self):
        super(ResultsPlotWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.graphWidget = pg.PlotWidget()
        self.colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
        self.experimentType = 'oneOdorIntensity'

        # styles = {'color':'blue', 'font-size': '10pt'}
        # self.graphWidget.setBackground('w')
        # self.graphWidget.setTitle('Percent Left Licks For Each Flow Rate', color='b', size='10pt')
        # self.graphWidget.setLabel('left', 'Percent Left Licks', **styles)
        # self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
        # self.xAxis = self.graphWidget.getAxis('bottom')
        # self.graphWidget.setYRange(0, 100, padding=0)
        # self.graphWidget.addLegend()
        # self.xAxisReady = False
        # self.groupedVials = {}
        # self.resultsList = []
        # self.plottingMode = 0

    def getWidget(self):
        return self.graphWidget

    def receiveDuplicatesDict(self, duplicateVials):
        self.groupedVials = duplicateVials

    def setPlottingMode(self, value):
        self.plottingMode = value
        if self.resultsList:  # self.resultsList will only hold the dict(s) after the first trial.
            self.updatePlot(self.resultsList)

    def updatePlot(self, resultsList):
        if (self.experimentType == 'oneOdorIntensity'):
            self.oneOdorIntensity(resultsList)
        elif (self.experimentType == 'twoOdorMatch'):
            self.twoOdorMatch(resultsList)
    
    def oneOdorIntensity(self, resultsList):
        # This function currently only plots vials of the first olfactometer (regardless of the plottingMode).
        logging.info("hello===============================================")
        self.resultsList = resultsList
        if not self.xAxisReady:
            flowrates = list(resultsList[0].values())  # Get a list of each vial's sub dictionary whose keys are flowrates, instead of doing resultsList[0]['vial_5'] since vial number '5' might not always exist.
            ticks = list(flowrates[0].keys())  #  flowrates is a list of dictionaries that contain the flowrates, but the values are all the same because they are the same set of flowrates. So just take the first element in that list and then make a list of the flowrates.
            ticks.sort(key=int)
            xdict = dict(enumerate(ticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(-1, len(ticks), padding=0)
            self.xAxisReady = True
        
        colorIndex = 0
        self.graphWidget.clear()

        if (self.plottingMode == 0):
            # This combines all vials into one line.
            numLeft = []  # list to sum up the left response results from duplicate vials for each flowrate. Will have length equal to the number of flowrates.
            numResponses = []  # list to sum up the total response results (correct + wrong) from duplicate vials for each flowrate. Will have the same length as numLeft.
            for vial, flowrateDict in resultsList[0].items():
                index = 0
                for flow, totals in flowrateDict.items():
                    if (len(numLeft) < len(flowrateDict)):  # Append each flowrate's total left responses and total responses to their lists until the length of the numLeft list equals the number of flowrates. The numLeft and numResponses lists have the same lengths.
                        numLeft.append(totals['left'])
                        numResponses.append(totals['Correct'] + totals['Wrong'])  # I only want the denominator to be the total number of actual responses, not including the NoResponses.
                        index += 1
                    else:  # Once numLeft and numResponses have the same length as the number of flowrates, stop appending and instead use the index to add to each element's sum. 
                        numLeft[index] += totals['left']
                        numResponses[index] += totals['Correct'] + totals['Wrong']
                        index += 1
            
            xValues = []
            yValues = []
            for i in range(len(numLeft)):  # Calculate percentages for each flowrate.
                if not (numResponses[i] == 0):
                    percent = round((float(numLeft[i]) / float(numResponses[i]) * 100), 2)
                else:
                    percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                xValues.append(i)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
                yValues.append(percent)

            self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
            self.graphWidget.plot(xValues, yValues, name='All vials', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
            colorIndex += 1
        
        elif (self.plottingMode == 1):
            # This combines vials with duplicate odor/conc and plots a line for each distinct odor/conc.
            for odor, concDict in self.groupedVials.items():
                for conc, vialsList in concDict.items():
                    numLeft = []  # list to sum up the left response results from duplicate vials for each flowrate. Will have length equal to the number of flowrates.
                    numResponses = []  # list to sum up the total response results (correct + wrong) from duplicate vials for each flowrate. Will have the same length as numLeft.
                    for vial in vialsList:
                        index = 0
                        for flow, totals in resultsList[0][vial].items():
                            if (len(numLeft) < len(resultsList[0][vial])):  # Append each flowrate's total left responses and total responses to their lists until the length of the numLeft list equals the number of flowrates. The numLeft and numResponses lists have the same lengths.
                                numLeft.append(totals['left'])
                                numResponses.append(totals['Correct'] + totals['Wrong'])  # I only want the denominator to be the total number of actual responses, not including the NoResponses.
                                index += 1
                            else:  # Once numLeft and numResponses have the same length as the number of flowrates, stop appending and instead use the index to add to each element's sum. 
                                numLeft[index] += totals['left']
                                numResponses[index] += totals['Correct'] + totals['Wrong']
                                index += 1
                    
                    xValues = []
                    yValues = []
                    for i in range(len(numLeft)):  # Calculate percentages for each flowrate.
                        if not (numResponses[i] == 0):
                            percent = round((float(numLeft[i]) / float(numResponses[i]) * 100), 2)
                        else:
                            percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                        xValues.append(i)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
                        yValues.append(percent)

                    # Plot a line for each distinct odor/conc
                    self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                    self.graphWidget.plot(xValues, yValues, name=f'{odor} {conc}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                    colorIndex += 1
        
        elif (self.plottingMode == 2):
            # This plots a line for each vial's results.
            for vialNum, flowrateDict in resultsList[0].items():
                xValues = []
                yValues = []
                index = 0
                for k, v in flowrateDict.items():
                    numLeft = v['left']
                    # numTotal = v['Total']  # I do not want to use this because if the mouse does not response many times, it will increase the denominator and lower the percentage.
                    numResponses = v['Correct'] + v['Wrong']  # I only want the denominator to be the total number of actual responses.
                    if not (numResponses == 0):
                        percent = round((float(numLeft) / float(numResponses) * 100), 2)
                    else:
                        percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                    xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
                    yValues.append(percent)
                    index += 1

                self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                self.graphWidget.plot(xValues, yValues, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                colorIndex += 1

        logging.info('results plot updated')
    
    def twoOdorMatch(self, resultsList):
        logging.info("hello+++++++++++++++++++++++++++++++++++++++++++++++++++++++")
        if not self.axisReady:
            self.xAxis = self.graphWidget.getAxis('bottom')
            xticks = list(resultsList[0].keys())
            xdict = dict(enumerate(xticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(0, len(xticks))

            self.yAxis = self.graphWidget.getAxis('left')
            firstVials = list(resultsList[0].values())
            yticks = list(firstVials[0].keys())
            ydict = dict(enumerate(yticks))
            self.yAxis.setTicks([ydict.items()])
            self.graphWidget.setYRange(0, len(yticks))
        
            self.axisReady = True

        odor_A_vials = list(resultsList[0].keys())
        odor_B_vials = list(resultsList[0][odor_A_vials[0]].keys())
        data = np.zeros(shape=(len(odor_A_vials), len(odor_B_vials)), dtype=np.float32)

        for i in range(len(odor_A_vials)):
            for j in range(len(odor_B_vials)):
                numCorrect = resultsList[0][odor_A_vials[i]][odor_B_vials[j]]['Correct']
                numResponses = resultsList[0][odor_A_vials[i]][odor_B_vials[j]]['Total']
                if (numResponses != 0):
                    data[i][j] = (numCorrect / numResponses) * 255.0
                else:
                    data[i][j] = 0.0

        # axes = {'t':None, 'x':0, 'y':1, 'c':None}  # When 'x':0 and 'y':1, then each array inside data will be displayed as a column.
        axes = {'t':None, 'x':1, 'y':0, 'c':None}  # When 'x':1 and 'y':0, then each array inside data will be displayed as a row.
        self.image.setImage(img=data, autoLevels=False, levels=(0, 255), axes=axes, levelMode='mono')

    def setExperimentType(self, experimentType):
        self.experimentType = experimentType

        if (experimentType == 'oneOdorIntensity'):
            self.updatePlot = self.oneOdorIntensity
            styles = {'color':'blue', 'font-size': '10pt'}
            self.graphWidget.setBackground('w')
            self.graphWidget.setTitle('Percent Left Licks For Each Flow Rate', color='b', size='10pt')
            self.graphWidget.setLabel('left', 'Percent Left Licks', **styles)
            self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
            self.xAxis = self.graphWidget.getAxis('bottom')
            self.graphWidget.setYRange(0, 100, padding=0)
            self.graphWidget.addLegend()
            self.xAxisReady = False
            self.groupedVials = {}
            self.resultsList = []
            self.plottingMode = 0
        
        elif (experimentType == 'twoOdorMatch'):
            self.updatePlot = self.twoOdorMatch
            self.graphWidget.setBackground('k')
            self.graphWidget.setTitle('Percent Correct For Each Odor', color='w', size='10pt')
            self.image = pg.ImageItem()
            self.graphWidget.addItem(self.image)
            self.axisReady = False
            self.groupedVials = {}
            self.resultsList = []
            self.plottingMode = 0
