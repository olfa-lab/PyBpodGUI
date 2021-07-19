import pyqtgraph as pg
import logging
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal


logging.basicConfig(format="%(message)s", level=logging.INFO)


class ResultsPlotWorker(QObject):
    def __init__(self):
        super(ResultsPlotWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.graphWidget = pg.PlotWidget()
        self.pen = pg.mkPen(color='r', width=2)
        styles = {'color':'blue', 'font-size': '10pt'}
        self.graphWidget.setBackground('w')
        self.graphWidget.setTitle('Percent Left Licks For Each Flow Rate', color='b', size='10pt')
        self.graphWidget.setLabel('left', 'Percent Left Licks', **styles)
        self.graphWidget.setLabel('bottom', 'Flow Rate', **styles)
        self.xAxis = self.graphWidget.getAxis('bottom')
        self.graphWidget.setYRange(0, 100, padding=0)
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
        self.graphWidget.plot(x, y, name='Results', pen=self.pen, symbol='s', symbolSize=10, symbolBrush='r')
        logging.info('results plot updated')
