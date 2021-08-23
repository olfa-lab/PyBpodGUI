import collections
import numpy as np
import logging
import time
from PyQt5.QtCore import QObject, QThread, QTimer, pyqtSignal
# from matplotlib.backends.backend_qt5agg import (
#     FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.animation as animation


logging.basicConfig(format="%(message)s", level=logging.INFO)



class StreamingWorker(QObject):
    def __init__(self, plotLength=100, numPlots=1):
        super(StreamingWorker, self).__init__()
        # QObject.__init__(self)  # super(...).__init() does this for you in the line above.
        self.plotMaxLength = plotLength
        self.numPlots = numPlots
        self.rawData = []
        self.data = []
        for i in range(numPlots):   # give a deque for each type of data plot and store them in a list
            self.data.append(collections.deque([0] * plotLength, maxlen=plotLength))
        for i in range(4):
            self.data.append(collections.deque([np.nan] * plotLength, maxlen=plotLength))
        self.isRun = False
        self.isSetup = False
        self.plotTimer = 0
        self.previousTimer = 0
        self.lickRightCorrect = np.nan
        self.lickRightWrong = np.nan
        self.lickLeftCorrect = np.nan
        self.lickLeftWrong = np.nan
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(5, 3)))
        self.paused = False

    def getFigure(self):
        return self.dynamic_canvas

    def setupAnimation(self):
        if not self.isSetup:
            # plotting starts below
            pltInterval = 10    # Period at which the plot animation updates [ms]
            xmin = 0
            xmax = self.plotMaxLength
            ymin = -5.0
            ymax = 5.0
            ax = self.dynamic_canvas.figure.add_subplot(111)
            ax.set_xlabel('Time')
            ax.set_ylabel('Voltage')
            ax.set_xlim(xmin, xmax)
            ax.set_ylim(float(ymin - (ymax - ymin) / 10), float(ymax + (ymax - ymin) / 10))
            ax.text(0.05, 0.80, 'Right Licks', transform=ax.transAxes)
            ax.text(0.05, 0.15, 'Left Licks', transform=ax.transAxes)

            lineLabel = ['Voltage', 'W', 'X', 'Y', 'Z']  # The letters are just place holder for the lick points so the 'for loop' below does not raise an "index out of range" error.
            style = ['k-', 'go', 'ro', 'go', 'ro']  # linestyles for the different plots
            timeText = ax.text(0.70, 0.99, '', transform=ax.transAxes)
            lines = []
            lineValueText = []
            for i in range(self.numPlots + 4):
                lines.append(ax.plot([], [], style[i], label=lineLabel[i])[0])
                if i == 0:
                    # I use this if statement because I only want the first line's 'lineValueText' to be written in the top right corner of the plot.
                    # The first line is the voltage line. The other four lines are the points plotted for the licks which will say 'np.nan' and that
                    # gets in the way and does not look nice.
                    lineValueText.append(ax.text(0.70, 0.90-i*0.05, '', transform=ax.transAxes))

            # Make sure to use "self.anim" instead of just "anim". Otherwise animation will freeze because the reference will be garbage collected.
            self.anim = animation.FuncAnimation(self.dynamic_canvas.figure, self.parseData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
            logging.info("animation created")
            # Doing it like this causes the animation to freeze halfway into the plot.
            # anim = animation.FuncAnimation(self.dynamic_canvas.figure, self.getData, fargs=(lines, lineValueText, lineLabel, timeText), interval=pltInterval)    # fargs has to be a tuple
            
            # self.dynamic_canvas.figure.legend(loc="upper left")
            self.isSetup = True

    def getData(self, data):
        self.rawData = data
        # logging.info(f"rawdata is {data}")

    def parseData(self, frame, lines, lineValueText, lineLabel, timeText):
        currentTimer = time.perf_counter()
        self.plotTimer = int((currentTimer - self.previousTimer) * 1000)     # the first reading will be erroneous
        self.previousTimer = currentTimer
        timeText.set_text('Plot Interval = ' + str(self.plotTimer) + 'ms')
        # privateData = copy.deepcopy(self.rawData[:])    # so that the 3 values in our plots will be synchronized to the same sample time
        
        for i in range(0, self.numPlots):
            for j in range(len(self.rawData)):
                self.data[i].append(self.rawData[j])    # we get the latest data point and append it to our deque
                
            lines[i].set_data(range(self.plotMaxLength), self.data[i])
            lineValueText[i].set_text('[' + lineLabel[i] + '] = ' + str(round(self.data[i][-1], 3)))  # I use the latest element for the voltage text.
        
        self.data[self.numPlots].append(self.lickRightCorrect)  # Right correct lick.
        self.data[self.numPlots + 1].append(self.lickRightWrong)    # Right incorrect lick.
        self.data[self.numPlots + 2].append(self.lickLeftCorrect)   # Left correct lick. 
        self.data[self.numPlots + 3].append(self.lickLeftWrong)  # Left incorrect lick.

        # Need to append as many elements to the lick lines as were appended to the voltage line so that all lines scroll at same speed.
        for i in range(self.numPlots, self.numPlots + 4):
            for j in range(len(self.rawData)):
                self.data[i].append(np.nan)

        lines[self.numPlots].set_data(range(self.plotMaxLength), self.data[self.numPlots])  # Set line for right correct lick.
        # lineValueText[self.numPlots].set_text('[' + lineLabel[self.numPlots] + '] = ' + str(value))  # Set text for right correct lick.
        lines[self.numPlots + 1].set_data(range(self.plotMaxLength), self.data[self.numPlots + 1])  # Set line for right incorrect lick.
        # lineValueText[self.numPlots + 1].set_text('[' + lineLabel[self.numPlots + 1] + '] = ' + str(value))  # Set text for right incorrect lick.
        lines[self.numPlots + 2].set_data(range(self.plotMaxLength), self.data[self.numPlots + 2])  # Set line for left correct lick.
        # lineValueText[self.numPlots + 2].set_text('[' + lineLabel[self.numPlots + 2] + '] = ' + str(value))  # Set text for left correct lick.
        lines[self.numPlots + 3].set_data(range(self.plotMaxLength), self.data[self.numPlots + 3])  # Set line for left incorrect lick.
        # lineValueText[self.numPlots + 3].set_text('[' + lineLabel[self.numPlots + 3] + '] = ' + str(value))  # Set text for left incorrect lick.

        # Reset lick values.
        self.lickRightCorrect = np.nan
        self.lickRightWrong = np.nan
        self.lickLeftCorrect = np.nan
        self.lickLeftWrong = np.nan

    def setInputEvent(self, params):
        direction = params[0]
        correct = params[1]
        if (direction == 'R'):
            if (correct == 1):
                self.lickRightCorrect = 4  # Y-axis max range is 2.5 so make right licks on top half of plot.
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = np.nan
            elif (correct == 0):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = 4
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = np.nan
        elif (direction == 'L'):
            if (correct == 1):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = -4  # Y-axis min range is -2.5 so make left licks on bottom half of plot.
                self.lickLeftWrong = np.nan
            elif (correct == 0):
                self.lickRightCorrect = np.nan
                self.lickRightWrong = np.nan
                self.lickLeftCorrect = np.nan
                self.lickLeftWrong = -4

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
            self.dynamic_canvas.draw()
            # FigureCanvas.draw(self.dynamic_canvas)  # This works too instead of "self.dynamic_canvas.draw()"
            logging.info("canvas drawn")
            self.isRun = True
            return True
        return False
