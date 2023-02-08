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
        self.experimentType = 1
        self.plottingMode = 0

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

    def getWidget(self):
        return self.graphWidget

    def receiveDuplicatesDict(self, duplicateVials):
        self.groupedVials = duplicateVials

    def setPlottingMode(self, value):
        self.plottingMode = value
        if self.resultsList:  # self.resultsList will only hold the dict(s) after the first trial.
            self.updatePlot(self.resultsList)

    def updatePlot(self, resultsList):
        #print("experiment type is :", self.experimentType)
        if (self.experimentType == 1):
            self.intensityPlot(resultsList)
        elif (self.experimentType == 2):
            self.identityPlot(resultsList)
    
    def intensityPlot(self, resultsList):
        # This function currently only plots vials of the first olfactometer (regardless of the plottingMode).

        self.resultsList = resultsList
        if not self.xAxisReady:
            flowrateDicts = list(resultsList[0].values())  # Get a list of the first olfactometer's vial's values which are each a dictionary whose keys are flowrates, instead of doing resultsList[0]['vial_5'] since vial number '5' might not always exist.
            allFlowrates = list(x for d in flowrateDicts for x in d.keys())  #  Put all the flowrates of all the vials into one list. The flowrates are the keys of each dictionary inside flowrateDicts, where flowrateDicts is a list of dictionaries.
            allFlowrates.sort(key=int)  # Sort all the flowrates in ascending order, even if there are duplicates...
            dict_1 = dict(enumerate(allFlowrates))  # This dict will have integer indices for keys and string flowrates for values, but might have multiple keys holding the same flowrate values...
            dict_2 = dict((flow, index) for index, flow in dict_1.items())  # This dict will swap the keys and values of dict_1, thus removing any duplicate flowrates because every key must be unique. But it might also remove the indices linked to those duplicates...
            dict_3 = dict(enumerate(dict_2.keys()))  # Finally, this dict will contain integer indices for keys and string flowrates for values, such that there will not be any duplicate flowrates or missing indices.
            self.xAxis.setTicks([dict_3.items()])
            self.graphWidget.setXRange(-1, len(dict_3), padding=0)
            self.xAxisDict = dict_3
            self.xAxisReady = True
        
        colorIndex = 0
        self.graphWidget.clear()

        if (self.plottingMode == 0):
            # This combines all vials into one line.

            allFlowsCounterDict = {}  # use this dict to count numLeft and numResponses for each flowrate.
            for vial, flowrateDict in resultsList[0].items():
                for flow, totalsDict in flowrateDict.items():
                    if flow not in allFlowsCounterDict:
                        allFlowsCounterDict[flow] = {'numLeft': 0, 'numResponses': 0}
                    allFlowsCounterDict[flow]['numLeft'] += totalsDict['left']
                    allFlowsCounterDict[flow]['numResponses'] += totalsDict['Correct'] + totalsDict['Wrong']  # I only want the denominator to be the total number of actual responses, not including the NoResponses.

            xValues = []
            yValues = []
            for index, flow in self.xAxisDict.items():
                if not (allFlowsCounterDict[flow]['numResponses'] == 0):
                    percent = round((float(allFlowsCounterDict[flow]['numLeft']) / float(allFlowsCounterDict[flow]['numResponses']) * 100), 2)
                else:
                    percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
                yValues.append(percent)

            self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
            self.graphWidget.plot(xValues, yValues, name='All vials', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
            colorIndex += 1
        
        elif (self.plottingMode == 1):
            # This combines vials with duplicate odor/conc and plots a line for each distinct odor/conc.

            for odor, concDict in self.groupedVials.items():
                for conc, vialsList in concDict.items():
                    allFlowsCounterDict = {}  # use this dict to count numLeft and numResponses for each flowrate.
                    for vial in vialsList:
                        for flow, totalsDict in resultsList[0][vial].items():
                            if flow not in allFlowsCounterDict:
                                allFlowsCounterDict[flow] = {'numLeft': 0, 'numResponses': 0}
                            allFlowsCounterDict[flow]['numLeft'] += totalsDict['left']
                            allFlowsCounterDict[flow]['numResponses'] += totalsDict['Correct'] + totalsDict['Wrong']  # I only want the denominator to be the total number of actual responses, not including the NoResponses.
                    
                    xValues = []
                    yValues = []
                    for index, flow in self.xAxisDict.items():
                        if flow in allFlowsCounterDict:
                            if not (allFlowsCounterDict[flow]['numResponses'] == 0):
                                percent = round((float(allFlowsCounterDict[flow]['numLeft']) / float(allFlowsCounterDict[flow]['numResponses']) * 100), 2)
                            else:
                                percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                            xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
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
                for index, flow in self.xAxisDict.items():
                    if flow in flowrateDict:
                        numLeft = flowrateDict[flow]['left']
                        numResponses = flowrateDict[flow]['Correct'] + flowrateDict[flow]['Wrong']  # I only want the denominator to be the total number of actual responses, not including the NoResponses.
                        if not (numResponses == 0):
                            percent = round((float(numLeft) / float(numResponses) * 100), 2)
                        else:
                            percent = 0.0  # To handle divide-by-zero-error that occurs when the flow has not yet been used.
                        xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
                        yValues.append(percent)

                self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                self.graphWidget.plot(xValues, yValues, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                colorIndex += 1
    
    def identityPlot(self, resultsList):
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

        self.graphWidget.clear()
        
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
        self.image.setImage(image=data, autoLevels=False, levels=(0.0, 255.0), axes=axes, levelMode='mono')
        # self.image.setImage(data)

    def setExperimentType(self, experimentType):
        self.experimentType = experimentType
        self.graphWidget.clear()

        if (experimentType == 1):
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
        
        elif (experimentType == 2):
            self.graphWidget.setBackground('k')
            self.graphWidget.setTitle('Percent Correct For Each Odor', color='w', size='10pt')
            self.image = pg.ImageItem()
            self.graphWidget.addItem(self.image)
            self.axisReady = False
            self.groupedVials = {}
            self.resultsList = []
            self.plottingMode = 0

            
            # This is another way to display an image. This method does not create a PlotWidget.
            # self.image = pg.ImageView(view=pg.PlotItem())
            # self.image.show()
            # self.image.ui.histogram.hide()
            # self.image.ui.roiBtn.hide()
            # self.image.ui.menuBtn.hide()
            # self.image.setImage(img=data, autoLevels=False, levels=(0, 255), axes=axes, levelMode='mono')
