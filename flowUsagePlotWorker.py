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
        self.resultsDict = {}
        self.plottingMode = 0

    def getWidget(self):
        return self.graphWidget

    def receiveDuplicatesDict(self, duplicateVials):
        self.groupedVials = duplicateVials

    def setPlottingMode(self, value):
        self.plottingMode = value
        if self.resultsDict:  # self.resultsDict will only hold the dict after the first trial.
            self.updatePlot(self.resultsDict)
    
    def updatePlot(self, resultsDict):
        self.resultsDict = resultsDict
        if not self.xAxisReady:
            flowrates = list(resultsDict.values())  # Get a list of each vial's sub dictionary whose keys are flowrates, instead of doing resultsDict['vial_5'] since vial number '5' might not always exist.
            ticks = list(flowrates[0].keys())  #  flowrates is a list of dictionaries that contain the flowrates, but the values are all the same because they are the same set of flowrates. So just take the first element in that list and then make a list of the flowrates.
            xdict = dict(enumerate(ticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(-1, len(ticks), padding=0)
            self.xAxisReady = True

        colorIndex = 0
        self.graphWidget.clear()

        if (self.plottingMode == 0):
            # This combines all vials into one line.
            allTotals = []  # list to sum up the total usage from all vials for each flowrate.
            for vialNum, flowrateDict in resultsDict.items():
                index = 0
                for flow, totals in flowrateDict.items():
                    if (len(allTotals) < len(flowrateDict)):  # Append each flowrate's total usage to the list until the length of the allTotals list equals the number of flowrates.
                        allTotals.append(totals['Total'])
                        index += 1
                    else:  # Once allTotals has the same length as the number of flowrates, stop appending and instead use the index to add to each element's sum. 
                        allTotals[index] += totals['Total']
                        index += 1
            
            if (max(allTotals) > self.ymax):
                self.ymax += 2
                self.graphWidget.setYRange(0, self.ymax, padding=0)

            xValues = list(range(len(allTotals)))
            self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
            self.graphWidget.plot(xValues, allTotals, name='All vials', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
            colorIndex += 1
        
        elif (self.plottingMode == 1):
            # This combines vials with duplicate odor/conc and plots a line for each distinct odor/conc.
            for odor, concDict in self.groupedVials.items():
                for conc, vialsList in concDict.items():
                    numTotal = []  # list to sum up the total usage from duplicate vials for each flowrate.
                    for vial in vialsList:
                        index = 0
                        for flow, totals in resultsDict[vial].items():
                            if (len(numTotal) < len(resultsDict[vial])):  # Append each flowrate's total usage to the list until the length of the list equals the number of flowrates.
                                numTotal.append(totals['Total'])
                                index += 1
                            else:  # Once numTotal has the same length as the number of flowrates, stop appending and instead use the index to add to each element's sum. 
                                numTotal[index] += totals['Total']
                                index += 1
                    
                    if (max(numTotal) > self.ymax):
                        self.ymax += 2
                        self.graphWidget.setYRange(0, self.ymax, padding=0)
                    
                    # Plot a line for each distinct odor/conc
                    xValues = list(range(len(numTotal)))  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
                    self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                    self.graphWidget.plot(xValues, numTotal, name=f'{odor} {conc}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                    colorIndex += 1

        elif (self.plottingMode == 2):
            # This is for plotting a line for each vial.
            for vialNum, flowrateDict in resultsDict.items():
                xValues = []
                yValues = []
                index = 0
                for k, v in flowrateDict.items():
                    xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
                    yValues.append(v['Total'])
                    index += 1
                
                if (max(yValues) > self.ymax):
                    self.ymax += 2
                    self.graphWidget.setYRange(0, self.ymax, padding=0)

                self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
                self.graphWidget.plot(xValues, yValues, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
                colorIndex += 1
        
        logging.info('flow usage plot updated')            
