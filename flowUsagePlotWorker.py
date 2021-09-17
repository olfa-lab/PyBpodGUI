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
        # self.graphWidget.addLegend()
        self.xAxis = self.graphWidget.getAxis('bottom')
        self.ymax = 2
        self.graphWidget.setYRange(0, self.ymax, padding=0)
        self.xAxisReady = False

    def getWidget(self):
        return self.graphWidget

    def updatePlot(self, resultsDict):
        if not self.xAxisReady:
            flowrates = list(resultsDict.values())  # Get a list of each vial's sub dictionary whose keys are flowrates, instead of doing resultsDict['vial_5'] since vial number '5' might not always exist.
            ticks = list(flowrates[0].keys())  #  flowrates is a list of dictionaries that contain the flowrates, but the values are all the same because they are the same set of flowrates. So just take the first element in that list and then make a list of the flowrates.
            xdict = dict(enumerate(ticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(-1, len(ticks), padding=0)
            self.xAxisReady = True

        colorIndex = 0
        self.graphWidget.clear()

        # for vialNum, flowrateDict in resultsDict.items():
        #     xValues = []
        #     yValues = []
        #     index = 0
        #     for k, v in flowrateDict.items():
        #         xValues.append(index)  # I use index instead of 'int(k)' because I setup custom tick labels for each flow rate in the ResultsPlot class and inside it, there is a dict with integers as keys and strings as values for the flow rate.
        #         yValues.append(v['Total'])
        #         index += 1
            
        #     if (max(yValues) > self.ymax):
        #         self.ymax += 2
        #         self.graphWidget.setYRange(0, self.ymax, padding=0)

        #     self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
        #     self.graphWidget.plot(xValues, yValues, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
        #     colorIndex += 1

        allTotals = []
        for vialNum, flowrateDict in resultsDict.items():
            totals = []
            for k, v in flowrateDict.items():
                totals.append(v['Total'])
            allTotals.append(totals)  # list of lists
        
        sumTotals = [0] * len(allTotals[0])
        for i in allTotals:  # i is a list inside allTotals.
            index = 0
            for j in i:  # j is an element inside list i.
                sumTotals[index] += j
                index += 1
        
        if (max(sumTotals) > self.ymax):
            self.ymax += 2
            self.graphWidget.setYRange(0, self.ymax, padding=0)

        xValues = list(range(len(sumTotals)))
        self.pen = pg.mkPen(color=self.colors[colorIndex], width=2)
        self.graphWidget.plot(xValues, sumTotals, name=f'Vial {vialNum}', pen=self.pen, symbol='s', symbolSize=10, symbolBrush=self.colors[colorIndex])
        colorIndex += 1
        
        logging.info('flow usage plot updated')            
