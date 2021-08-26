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
        self.lickRightData = [np.nan]
        self.lickLeftData = [np.nan]
        self.line = Line2D(self.tdata, self.ydata, animated=True)
        self.lickRightLine = Line2D(self.tdata, self.lickRightData, color='b', marker='>', animated=True)
        self.lickLeftLine = Line2D(self.tdata, self.lickLeftData, color='b', marker='<', animated=True)
        self.ax.add_line(self.line)
        self.ax.add_line(self.lickRightLine)
        self.ax.add_line(self.lickLeftLine)
        self.ax.set_ylim(-6.0, 6.0)
        self.ax.set_xlim(0, self.maxt)
        self.span = self.ax.axvspan(0, 0, color='blue', alpha=0.2)
        self.spanStart = 0
        self.spanEnd = 0
        self.spanColor = 'b'

        self.analogData = np.zeros(self.maxt)
        self.nTotalDataPoints = 0
        self.nDataPointsPlotted = 0

        self.timeText = self.ax.text(0.70, 0.99, '', transform=self.ax.transAxes)
        self.fpsText = self.ax.text(0.70, 0.90, '', transform=self.ax.transAxes)
        self.elapsed = self.ax.text(0.70, 0.80, '', transform=self.ax.transAxes)
        self.nTotalDataPointsText = self.ax.text(0.70, 0.70, '', transform=self.ax.transAxes)
        self.nDataPointsPlottedText = self.ax.text(0.70, 0.60, '', transform=self.ax.transAxes)
        self.lickRightText = self.ax.text(-0.15, 0.90, 'Right Lick', transform=self.ax.transAxes)
        self.lickLeftText = self.ax.text(-0.15, 0.05, 'Left Lick', transform=self.ax.transAxes)
        self.plotTimer = 0
        self.previousTimer = 0
        self.counter = 0
        self.lickRight = np.nan
        self.lickLeft = np.nan
        self.activateResponseWindow = False
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
            self.lickRightData = [self.lickRightData[-1]]
            self.lickLeftData = [self.lickLeftData[-1]]
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
            self.lickRightData.append(self.lickRight)
            self.lickLeftData.append(self.lickLeft)
            self.nDataPointsPlotted += 1

        self.line.set_data(self.tdata, self.ydata)
        self.lickRightLine.set_data(self.tdata, self.lickRightData)
        self.lickLeftLine.set_data(self.tdata, self.lickLeftData)

        if self.activateResponseWindow:
            self.spanEnd = self.tdata[-1]  # Make the responseWindow grow with sniff signal.
            # set_xy() takes an (N, 2) list of the verticies of the polygon. Since axvspan is a rectangle, there are 5 verticies in order to create a complete closed circuit.
            self.span.set_xy([[self.spanStart, -6.0], [self.spanStart, 6.0], [self.spanEnd, 6.0], [self.spanEnd, -6.0], [self.spanStart, -6.0]])
        else:
            # This else statement keeps the responseWindow showing until the canvas gets redrawn because I need to do something with self.span in order to be able to return it.
            self.span.set_xy([[self.spanStart, -6.0], [self.spanStart, 6.0], [self.spanEnd, 6.0], [self.spanEnd, -6.0], [self.spanStart, -6.0]])

        return self.line, self.lickRightLine, self.lickLeftLine, self.span,

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

    def checkResponseWindow(self, stateName):
        # This function gets the newStateSignal from protocolWorker.
        if stateName == 'WaitForResponse':
            self.spanStart = self.tdata[-1]
            self.span.set_color('b')  # reset color to blue until lick occurs.
            self.activateResponseWindow = True
            self.spanColor = 'b'  # also reset the color variable to blue.
        elif stateName == 'Correct':
            self.span.set_color('g')
            self.activateResponseWindow = False
        elif stateName == 'Wrong':
            self.span.set_color('r')
            self.activateResponseWindow = False
        elif stateName == 'NoResponse':
            # No need to set span color here as it is already blue.
            self.activateResponseWindow = False
        
        # This else statement is here to end the response window and set its color based on the inputEventSignal received from the inputEventWorker thread,
        # instead of based on the stateName.
        else:
            if self.activateResponseWindow:  
                # This if statement ensures the span color is set only once: when the 'WaitForResponse' state completes and transitions to the next state.
                # Otherwise, every state that is not named 'WaitForResponse' will call set_color(). I used a QTimer.singleShot to set the span color because
                # there seems to be a timing conflict (or thats what I think is happening) where the checkResponseWindow() function is called by the
                # protocolWorker thread's newStateSignal and it finishes execution before the setInputEvent() function has a chance to change the span color
                # variable based on the type of lick detected by the inputEventWorker thread. Perhaps the newStateSignal is emitted first and then comes the
                # inputEventSignal. Both signals are handled by the main thread (i think) because both slot functions (setInputEvent() and checkResponseWindow())
                # are inside StreamingWorker which is running on the main thread. So maybe two pyqtSignals cannot be handled simultaneously on the same thread?
                # Or maybe they do, but checkResponseWindow() executes faster/finishes earlier than setInputEvent does? This solution works most of the time,
                # except for the rare cases when the left sensor is touched and then the right sensor is touched very shortly after, and vise versa, such that
                # the span color variable changes more than once within the QTimer.singleShot's duration. This can cause the span color to be set incorrectly;
                # opposite to the actual response result. A better solution might be to check if the stateName equals "Correct", "Wrong", or "No Response" 
                # using the string sent by the protocolWorker thread's newStateSignal or responseResultSignal.
                QTimer.singleShot(100, lambda: self.span.set_color(self.spanColor))
                self.activateResponseWindow = False

    def setInputEvent(self, params):
        if (len(params) == 0):
            # Stop plotting the licks.
            self.lickRight = np.nan
            self.lickLeft = np.nan
        else:
            direction = params[0]
            enable = params[1]
            correct = params[2]
            if (direction == 'R'):
                if (enable == 1):
                    self.lickRight = 5  # Y-axis max range is 6.0 so make right licks on top half of plot.
                    if (correct == 1):
                        self.spanColor = 'g'
                    elif (correct == 0):
                        self.spanColor = 'r'
                elif (enable == 0):
                    self.lickRight = np.nan
            elif (direction == 'L'):
                if (enable == 1):
                    self.lickLeft = -5  # Y-axis min range is -6.0 so make left licks on bottom half of plot.
                    if (correct == 1):
                        self.spanColor = 'g'
                    elif (correct == 0):
                        self.spanColor = 'r'
                elif (enable == 0):
                    self.lickLeft = np.nan

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
