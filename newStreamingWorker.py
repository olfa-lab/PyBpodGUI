import collections
import numpy as np
import logging
import time
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.animation as animation


logging.basicConfig(format="%(message)s", level=logging.INFO)



class StreamingWorker(QObject):  
    def __init__(self, maxt=2, dt=0.02):
        super().__init__()
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))

        self.fig = self.dynamic_canvas.figure
        self.ax = self.dynamic_canvas.figure.subplots()

        self.dt = dt
        self.maxt = maxt
        self.tdata = [0]
        self.ydata = [0]
        self.lickRightCorrectData = [np.nan]
        # self.lickRightWrongData = [np.nan]
        self.lickLeftCorrectData = [np.nan]
        # self.lickLeftWrongData = [np.nan]
        self.line = Line2D(self.tdata, self.ydata, animated=True)
        self.lickRightCorrectLine = Line2D(self.tdata, self.lickRightCorrectData, color='g', marker='>', animated=True)
        # self.lickRightWrongLine = Line2D(self.tdata, self.lickRightWrongData, color='r', marker='>', animated=True)
        self.lickLeftCorrectLine = Line2D(self.tdata, self.lickLeftCorrectData, color='g', marker='<', animated=True)
        # self.lickLeftWrongLine = Line2D(self.tdata, self.lickLeftWrongData, color='r', marker='<', animated=True)
        self.ax.add_line(self.line)
        self.ax.add_line(self.lickRightCorrectLine)
        # self.ax.add_line(self.lickRightWrongLine)
        self.ax.add_line(self.lickLeftCorrectLine)
        # self.ax.add_line(self.lickLeftWrongLine)
        self.ax.set_ylim(-5.0, 10.0)
        self.ax.set_xlim(0, self.maxt)

        self.analogData = np.zeros(self.maxt)
        self.nTotalDataPoints = 0
        self.nDataPointsPlotted = 0

        self.timeText = self.ax.text(0.70, 0.99, '', transform=self.ax.transAxes)
        self.fpsText = self.ax.text(0.70, 0.90, '', transform=self.ax.transAxes)
        self.elapsed = self.ax.text(0.70, 0.80, '', transform=self.ax.transAxes)
        self.nTotalDataPointsText = self.ax.text(0.70, 0.70, '', transform=self.ax.transAxes)
        self.nDataPointsPlottedText = self.ax.text(0.70, 0.60, '', transform=self.ax.transAxes)
        self.plotTimer = 0
        self.previousTimer = 0
        self.counter = 0
        self.lickRightCorrect = np.nan
        # self.lickRightWrong = np.nan
        self.lickLeftCorrect = np.nan
        # self.lickLeftWrong = np.nan
        self.paused = False
        self.isRun = False
        self.isSetup = True

    def update(self, y):
        currentTimer = time.perf_counter()
        self.plotTimer = round(((currentTimer - self.previousTimer) * 1000), 3)     # the first reading will be erroneous
        self.previousTimer = currentTimer
        self.timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        tx = 'Mean Frame Rate: {fps:.3f}FPS'.format(fps= ((self.counter) / (time.perf_counter() - self.t_start)) ) 
        self.fpsText.set_text(tx)
        self.counter += 1
        elap = 'Elapsed Time: {dt:.3f} sec'.format(dt= (time.perf_counter() - self.t_start))
        self.elapsed.set_text(elap)
        self.nTotalDataPointsText.set_text('Total data points: {0}'.format(self.nTotalDataPoints))
        self.nDataPointsPlottedText.set_text('Plotted data points: {0}'.format(self.nDataPointsPlotted))

        lastt = self.tdata[-1]
        if lastt > self.tdata[0] + self.maxt:  # reset the arrays
            self.tdata = [self.tdata[-1]]
            self.ydata = [self.ydata[-1]]
            self.lickRightCorrectData = [self.lickRightCorrectData[-1]]
            # self.lickRightWrongData = [self.lickRightWrongData[-1]]
            self.lickLeftCorrectData = [self.lickLeftCorrectData[-1]]
            # self.lickLeftWrongData = [self.lickLeftWrongData[-1]]
            self.ax.set_xlim(self.tdata[0], self.tdata[0] + self.maxt)
            self.ax.figure.canvas.draw()

        # t = self.tdata[-1] + self.dt
        # self.tdata.append(t)
        # self.ydata.append(y)
        # self.lickRightCorrectData.append(self.lickRightCorrect)
        # self.lickRightWrongData.append(self.lickRightWrong)
        # self.lickLeftCorrectData.append(self.lickLeftCorrect)
        # self.lickLeftWrongData.append(self.lickLeftWrong)
        # self.nDataPointsPlotted += 1

        for i in range(len(y)):
            t = self.tdata[-1] + self.dt
            self.tdata.append(t)
            self.ydata.append(y[i])
            self.lickRightCorrectData.append(self.lickRightCorrect)
            # self.lickRightWrongData.append(self.lickRightWrong)
            self.lickLeftCorrectData.append(self.lickLeftCorrect)
            # self.lickLeftWrongData.append(self.lickLeftWrong)
            self.nDataPointsPlotted += 1

        self.line.set_data(self.tdata, self.ydata)
        self.lickRightCorrectLine.set_data(self.tdata, self.lickRightCorrectData)
        # self.lickRightWrongLine.set_data(self.tdata, self.lickRightWrongData)
        self.lickLeftCorrectLine.set_data(self.tdata, self.lickLeftCorrectData)
        # self.lickLeftWrongLine.set_data(self.tdata, self.lickLeftWrongData)

        # return self.line, self.lickRightCorrectLine, self.lickRightWrongLine, self.lickLeftCorrectLine, self.lickLeftWrongLine,
        return self.line, self.lickRightCorrectLine, self.lickLeftCorrectLine,

    def getData(self, data):
        self.analogData = data
        self.nTotalDataPoints += len(data)

    def emitter(self):
        yield self.analogData
        
        # for y in self.analogData:
        #     yield y

    def animate(self):
        # pass a generator in "emitter" to produce data for the update func
        self.anim = animation.FuncAnimation(self.fig, self.update, self.emitter, interval=7, blit=True)

    def getFigure(self):
        return self.dynamic_canvas

    def setInputEvent(self, params):
        direction = params[0]
        enable = params[1]
        correct = params[2]
        if (direction == 'R'):
            if (enable == 1):
                self.lickRightCorrect = 9  # Y-axis max range is 2.5 so make right licks on top half of plot.
                if (correct == 1):
                    self.lickRightCorrectLine.set_color('g')
                elif (correct == 0):
                    self.lickRightCorrectLine.set_color('r')
            elif (enable == 0):
                self.lickRightCorrect = np.nan
        elif (direction == 'L'):
            if (enable == 1):
                self.lickLeftCorrect = 7  # Y-axis min range is -2.5 so make left licks on bottom half of plot.
                if (correct == 1):
                    self.lickLeftCorrectLine.set_color('g')
                elif (correct == 0):
                    self.lickLeftCorrectLine.set_color('r')
            elif (enable == 0):
                self.lickLeftCorrect = np.nan

    def pauseAnimation(self):
        if not self.paused:
            logging.info("attempting to pause animation")
            self.anim.event_source.stop()
            self.paused = True
            logging.info("animation paused")

    def resumeAnimation(self):
        if self.paused:
            logging.info("attempting to start animation")
            self.anim.event_source.start()
            self.paused = False
            logging.info("animation resumed")

    def startAnimation(self):
        if self.isSetup and not self.isRun:
            self.animate()
            self.t_start = time.perf_counter()
            logging.info("canvas drawn")
            self.isRun = True
            return True
        return False
