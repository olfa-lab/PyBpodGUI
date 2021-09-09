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
        styles = {'color':'blue', 'font-size': '10pt'}
        self.graphWidget.setBackground('w')
        self.graphWidget.setTitle('Flow Rate Distribution', color='b', size='10pt')
        self.graphWidget.setLabel('left', 'Number of Trials Used', **styles)
        self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
        self.xAxis = self.graphWidget.getAxis('bottom')
        self.ymax = 2
        self.graphWidget.setYRange(0, self.ymax, padding=0)
        self.xAxisReady = False

    def getWidget(self):
        return self.graphWidget

    def isXAxisSetup(self):
        return self.xAxisReady

    def setupXaxis(self, resultsDict):
        if not self.xAxisReady:
            ticks = list(resultsDict.keys())
            xdict = dict(enumerate(ticks))
            self.xAxis.setTicks([xdict.items()])
            self.graphWidget.setXRange(-1, len(ticks), padding=0)
            self.xAxisReady = True

    def updatePlot(self, x, y):
        self.graphWidget.clear()
        if (max(y) > self.ymax):
            self.ymax += 2
            self.graphWidget.setYRange(0, self.ymax, padding=0)

        self.graphWidget.plot(x, y, name='Flow Usage', pen=self.pen, symbol='s', symbolSize=10, symbolBrush='r')
        logging.info('flow usage plot updated')
