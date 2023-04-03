import pyqtgraph as pg
import logging
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal


logging.basicConfig(format="%(message)s", level=logging.INFO)


class FlowUsagePlotWorker(QObject):
    def __init__(self):
        super(FlowUsagePlotWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.graphWidget = pg.PlotWidget()
        self.pen = pg.mkPen(color='r', width=2)
        self.colors = ['r', 'g', 'b', 'c', 'm', 'y', 'k']
        styles = {'color':'blue', 'font-size': '10pt'}
        self.graphWidget.setBackground('w')
        self.graphWidget.setTitle('Flow Rate Distribution', color='b', size='10pt')
        self.graphWidget.setLabel('left', 'Number of Trials Used', **styles)
        self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
        self.graphWidget.addLegend()
        self.xAxis = self.graphWidget.getAxis('bottom')
        self.ymax = 2
        self.graphWidget.setYRange(0, self.ymax, padding=0)
        self.xAxisReady = False
        self.groupedVials = {}
        self.resultsList = []
        self.plottingMode = 0

    def getWidget(self):
        return self.graphWidget

    def receiveDuplicatesDict(self, duplicateVials):
        self.groupedVials = duplicateVials

    def setPlottingMode(self, value):
        self.plottingMode = value
        if self.resultsList:  # self.resultsList will only hold the dict(s) after the first trial.
            self.updatePlot(self.resultsList)
    
    def updatePlot(self, resultsList):
        if (self.experimentType == 1):
            self.intensityPlot(resultsList)
        # elif (self.experimentType == 2):
        #     self.identityPlot(resultsList)

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

            allFlowsCounterDict = {}  # use this dict to count the total usage for each flowrate.
            for vial, flowrateDict in resultsList[0].items():
                for flow, totalsDict in flowrateDict.items():
                    if flow not in allFlowsCounterDict:
                        allFlowsCounterDict[flow] = 0  # the value will be a counter of the total usage for that flow.
                    allFlowsCounterDict[flow] += totalsDict['Total']
            
            xValues = []
            yValues = []
            for index, flow in self.xAxisDict.items():
                xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
                yValues.append(allFlowsCounterDict[flow])
            
            if (max(yValues) > self.ymax):
                self.ymax += 2
                self.graphWidget.setYRange(0, self.ymax, padding=0)

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
                                allFlowsCounterDict[flow] = 0  # the value will be a counter of the total usage for that flow.
                            allFlowsCounterDict[flow] += totalsDict['Total']
                    
                    xValues = []
                    yValues = []
                    for index, flow in self.xAxisDict.items():
                        if flow in allFlowsCounterDict:
                            xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
                            yValues.append(allFlowsCounterDict[flow])
                    
                    if (max(yValues) > self.ymax):
                        self.ymax += 2
                        self.graphWidget.setYRange(0, self.ymax, padding=0)
                    
                    # Plot a line for each distinct odor/conc
                    self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                    self.graphWidget.plot(xValues, yValues, name=f'{odor} {conc}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                    colorIndex += 1

        elif (self.plottingMode == 2):
            # This is for plotting a line for each vial.
            
            for vialNum, flowrateDict in resultsList[0].items():
                xValues = []
                yValues = []
                for index, flow in self.xAxisDict.items():
                    if flow in flowrateDict:
                        xValues.append(index)  # self.xAxisDict has string flowrates for keys and integer values for the index of the flowrate on the x axis.
                        yValues.append(flowrateDict[flow]['Total'])
                
                if (max(yValues) > self.ymax):
                    self.ymax += 2
                    self.graphWidget.setYRange(0, self.ymax, padding=0)

                self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                self.graphWidget.plot(xValues, yValues, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                colorIndex += 1
        
    def setExperimentType(self, experimentType):
        self.experimentType = experimentType     
