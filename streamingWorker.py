import collections
import numpy as np
import logging
import time
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.animation as animation


logging.basicConfig(format="%(message)s", level=logging.INFO)


class StreamingWorker(QObject):  
    def __init__(self, maxt=2, dt=0.02, ymin=-1.0, ymax=1.0, plotInterval=5):
        super().__init__()
        self.dynamic_canvas = FigureCanvas(Figure(figsize=(10, 3)))

        self.fig = self.dynamic_canvas.figure
        self.ax = self.dynamic_canvas.figure.subplots()

        self.dt = dt
        self.maxt = maxt
        self.ymax = ymax
        self.ymin = ymin
        self.plotInterval = plotInterval  # milliseconds
        self.tdata = [0]
        self.ydata = [0]
        self.port_1_Data = [np.nan]
        self.port_2_Data = [np.nan]
        self.port_3_Data = [np.nan]
        self.port_4_Data = [np.nan]

        self.line = Line2D(self.tdata, self.ydata, animated=True)
        self.port_1_Line = Line2D(self.tdata, self.port_1_Data, color='b', marker='.', animated=True)
        self.port_2_Line = Line2D(self.tdata, self.port_2_Data, color='b', marker='.', animated=True)
        self.port_3_Line = Line2D(self.tdata, self.port_3_Data, color='b', marker='.', animated=True)
        self.port_4_Line = Line2D(self.tdata, self.port_4_Data, color='b', marker='.', animated=True)
        
        self.ax.add_line(self.line)
        self.ax.add_line(self.port_1_Line)
        self.ax.add_line(self.port_2_Line)
        self.ax.add_line(self.port_3_Line)
        self.ax.add_line(self.port_4_Line)
        
        self.ax.set_ylim(self.ymin - 0.1, self.ymax + 0.1)
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
        self.port_1_Text = self.ax.text(1.01, 0.91, 'Port_1', transform=self.ax.transAxes)
        self.port_2_Text = self.ax.text(1.01, 0.60, 'Port_2', transform=self.ax.transAxes)
        self.port_3_Text = self.ax.text(1.01, 0.30, 'Port_3', transform=self.ax.transAxes)
        self.port_4_Text = self.ax.text(1.01, 0.01, 'Port_4', transform=self.ax.transAxes)
        
        self.plotTimer = 0
        self.previousTimer = 0
        self.counter = 0
        self.inputPorts = [np.nan] * 4
        self.triggeredValues = [self.ymax, (self.ymax - ((self.ymax - self.ymin) / 3)), (((self.ymax - self.ymin) / 3) + self.ymin), self.ymin]
        
        self.activateResponseWindow = False
        self.presentOdor = False
        self.paused = False
        self.isRun = False
        self.isSetup = True

    def setYaxis(self, ymin, ymax):
        self.ymax = ymax
        self.ymin = ymin
        self.ax.set_ylim(self.ymin - 0.1, self.ymax + 0.1)
        self.triggeredValues = [self.ymax, (self.ymax - ((self.ymax - self.ymin) / 3)), (((self.ymax - self.ymin) / 3) + self.ymin), self.ymin]
        self.ax.figure.canvas.draw()

    def setXaxis(self, maxt):
        self.maxt = maxt
        self.ax.set_xlim(self.tdata[-1], self.tdata[-1] + self.maxt)
        self.ax.figure.canvas.draw()

    def set_dt(self, dt):
        self.dt = dt

    def setPlotInterval(self, value):
        self.plotInterval = value
        self.anim._stop()  # Since there is no setter function for interval in the FuncAnimation class definition, I need to remove the animation from the timer's callback list and destroy it, which is what _stop() does. Otherwise the animation keeps going even if the self.anim object is deleted.
        del self.anim  # Then I delete the object.
        self.animate()  # Then I call animate() again to re-create the FuncAnimation with the new interval.
    
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
            self.port_1_Data = [self.port_1_Data[-1]]
            self.port_2_Data = [self.port_2_Data[-1]]
            self.port_3_Data = [self.port_3_Data[-1]]
            self.port_4_Data = [self.port_4_Data[-1]]
            
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
            self.port_1_Data.append(self.inputPorts[0])
            self.port_2_Data.append(self.inputPorts[1])
            self.port_3_Data.append(self.inputPorts[2])
            self.port_4_Data.append(self.inputPorts[3])
            self.nDataPointsPlotted += 1

        self.line.set_data(self.tdata, self.ydata)
        self.port_1_Line.set_data(self.tdata, self.port_1_Data)
        self.port_2_Line.set_data(self.tdata, self.port_2_Data)
        self.port_3_Line.set_data(self.tdata, self.port_3_Data)
        self.port_4_Line.set_data(self.tdata, self.port_4_Data)
        
        #if self.presentOdor: # Bea 16/12/2022
        #    self.spanEnd = self.tdata[-1]  # Make the responseWindow grow with sniff signal.
        #    # set_xy() takes an (N, 2) list of the verticies of the polygon. Since axvspan is a rectangle, there are 5 verticies in order to create a complete closed circuit.
        #    self.span.set_xy([[self.spanStart, self.ymin], [self.spanStart, self.ymax], [self.spanEnd, self.ymax], [self.spanEnd, self.ymin], [self.spanStart, self.ymin]])
        #else:
        #    self.span.set_xy([[self.spanStart, self.ymin], [self.spanStart, self.ymax], [self.spanEnd, self.ymax], [self.spanEnd, self.ymin], [self.spanStart, self.ymin]])

        if self.activateResponseWindow or self.presentOdor:
            self.spanEnd = self.tdata[-1]  # Make the responseWindow grow with sniff signal.
            # set_xy() takes an (N, 2) list of the verticies of the polygon. Since axvspan is a rectangle, there are 5 verticies in order to create a complete closed circuit.
            self.span.set_xy([[self.spanStart, self.ymin], [self.spanStart, self.ymax], [self.spanEnd, self.ymax], [self.spanEnd, self.ymin], [self.spanStart, self.ymin]])
        else:
            # This else statement keeps the responseWindow showing until the canvas gets redrawn because I need to do something with self.span in order to be able to return it.
            self.span.set_xy([[self.spanStart, self.ymin], [self.spanStart, self.ymax], [self.spanEnd, self.ymax], [self.spanEnd, self.ymin], [self.spanStart, self.ymin]])

        return self.line, self.port_1_Line, self.port_2_Line, self.port_3_Line, self.port_4_Line, self.span,

    def getData(self, data):
        self.analogData = data
        self.nTotalDataPoints += len(data)

    def emitter(self):
        yield self.analogData
        
        # for y in self.analogData:
        #     yield y

    def animate(self):
        # pass a generator in "emitter" to produce data for the update func
        self.anim = animation.FuncAnimation(self.fig, self.update, self.emitter, interval=self.plotInterval, blit=True)

    def getFigure(self):
        return self.dynamic_canvas

    def checkOdorPresentation(self, stateName): 
        if stateName == 'PresentOdor':
            self.presentOdor = True
            self.spanStart = self.tdata[-1]
            self.span.set_color('y')
            self.spanColor = 'y'
           

    def checkResponseWindow(self, stateName):
        # This function gets the newStateSignal from protocolWorker.
        if stateName == 'WaitForResponse':
            self.presentOdor = False
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

    def setInputEvent(self, inputs):
        for i in range(len(inputs)):
            if inputs[i]:
                self.inputPorts[i] = self.triggeredValues[i]
            else:
                self.inputPorts[i] = np.nan

    def pauseAnimation(self):
        if not self.paused:
            self.anim.event_source.stop()
            self.paused = True

    def resumeAnimation(self):
        if self.paused:
            self.anim.event_source.start()
            self.paused = False

    def startAnimation(self):
        if self.isSetup and not self.isRun:
            self.animate()
            self.t_start = time.perf_counter()
            self.isRun = True
            return True
        return False

    def resetPlot(self):
        self.tdata = [0]
        self.ydata = [0]
        self.port_1_Data = [np.nan]
        self.port_2_Data = [np.nan]
        self.port_3_Data = [np.nan]
        self.port_4_Data = [np.nan]
        
        self.ax.set_xlim(0, self.maxt)

        self.timeText.set_text('')
        self.fpsText.set_text('')
        self.elapsed.set_text('')
        self.nTotalDataPointsText.set_text('')
        self.nDataPointsPlottedText.set_text('')

        self.nTotalDataPoints = 0
        self.nDataPointsPlotted = 0
        self.plotTimer = 0
        self.previousTimer = 0
        self.counter = 0
        self.inputPorts = [np.nan] * 4
        
        self.spanStart = 0
        self.spanEnd = 0
        self.activateResponseWindow = False
        self.presentOdor = False
        self.t_start = time.perf_counter()

        self.ax.figure.canvas.draw()
