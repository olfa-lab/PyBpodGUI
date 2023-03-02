import collections
import numpy as np
import logging
import time
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QObject, QTimer, pyqtSignal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
import matplotlib.animation as animation
import pyqtgraph as pg
from pyqtgraph import PlotWidget, plot
import math
import warnings
warnings.filterwarnings("ignore", category=RuntimeWarning) 
logging.basicConfig(format="%(message)s", level=logging.INFO)


class StreamingWorker(QObject):  
    finished = pyqtSignal()


    def __init__(self, maxt=2, dt=0.02, ymin=-1.0, ymax=1.0, plotInterval=5, sniffth = 1, adc = None, bpod = None):
        super().__init__()
        #self.dynamic_canvas = FigureCanvas(Figure(figsize=(10, 3)))
        #self.fig = self.dynamic_canvas.figure
        #self.ax = self.dynamic_canvas.figure.subplots()
        self.dynamic_canvas = pg.PlotWidget()  
        self.dynamic_canvas.setBackground('w')
        self.ax = self.dynamic_canvas.getPlotItem()
        self.buffersize = 50

        pensniffsig = pg.mkPen(color=(0, 0, 0))
        penstate = pg.mkPen(color=(0, 0, 0), width=5)
        pensniffth = pg.mkPen(color=(255, 0, 0))
        maxt =1
        self.update_calls_count = 0
        self.dt = dt
        self.maxt = maxt
        self.ymax = ymax
        self.ymin = ymin
        self.plotInterval = plotInterval  # milliseconds
        self.tdata = [0]
        self.ydata = [0]
        self.tports = [0]
        self.port_1_Time = [0]
        self.port_3_Time = [0]
        self.port_1_Data = [np.nan]
        self.port_2_Data = [np.nan]
        self.port_3_Data = [np.nan]
        self.port_4_Data = [np.nan]
        self.sniffth = sniffth
        self.inputPortsTime = [np.nan] * 4
        self.attemptime = [ 0, maxt]
        self.sniffthdata = [ self.sniffth, self.sniffth]
        self.previousTimer = 0
         
        self.line =  self.dynamic_canvas.plot(self.tdata, self.ydata, pen=pensniffsig)
        #self.stateline = self.dynamic_canvas.plot(self.tstate, self.statevalue, pen=pensniffsig) # line that marks the state
        self.sniffthline = self.dynamic_canvas.plot(self.attemptime, self.sniffthdata, pen=pensniffth)
        self.port_1_Line = self.dynamic_canvas.plot(self.tports, self.port_1_Data, pen = 'w',  symbolPen ='w', symbol='o',  symbolSize = 6)
        self.port_3_Line = self.dynamic_canvas.plot(self.tports, self.port_3_Data, pen = 'w', symbolPen ='w', symbol='o', symbolSize = 6)

        self.analogData = []
        self.nTotalDataPoints = 0
        self.nDataPointsPlotted = 0
        
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
        self.keepRunning = True

        self.events = []

        self.event_color_dict = {'WaitForOdor':'k',
            'LedOn':'y',
            'CameraOn':'g',
            'CameraOff':'r',
            'WaitForSniff':'y',
            'PresentOdor': 'g',
            'WaitForResponse':'b',
            'NoResponse':'c',
            'Correct':'g',
            'Wrong':'r',
            'ITI':'m'}

    def setYaxis(self, ymin, ymax):
        self.ymax = ymax
        self.ymin = ymin
        self.dynamic_canvas.setYRange(self.ymin, self.ymax )
        self.triggeredValues = [self.ymax, (self.ymax - ((self.ymax - self.ymin) / 3)), (((self.ymax - self.ymin) / 3) + self.ymin), self.ymin]
        #self.ax.figure.canvas.draw()
    
    def setXaxis(self, maxt):
        self.maxt = maxt
        self.dynamic_canvas.setXRange(self.tdata[0], self.tdata[0] + self.maxt)
        #self.ax.figure.canvas.draw()

    def set_dt(self, dt):
        self.dt = dt

    # def setPlotInterval(self, value):
    #     self.plotInterval = value
    #     if self.anim is not None:
    #         self.anim._stop()  # Since there is no setter function for interval in the FuncAnimation class definition, I need to remove the animation from the timer's callback list and destroy it, which is what _stop() does. Otherwise the animation keeps going even if the self.anim object is deleted.
    #         del self.anim  # Then I delete the object.
    #     self.animate()  # Then I call animate() again to re-create the FuncAnimation with the new interval.
    
    def setSniffLine(self, value):
        self.sniffth = value/1000
        self.attemptime = [ 0, self.maxt]
        self.sniffthdata = [ self.sniffth, self.sniffth]

        #self.sniffthline.setData(self.attemptime,self.sniffthdata )
        #self.ax.figure.canvas.draw()


    def update_port_data(self):
        
        #print('update_port_data')
        #print(self.inputPorts, self.inputPortsTime)
        for i in range(len(self.inputPorts)):
            if self.inputPorts[i] is not np.nan:
                if i == 0:
                   
                    self.port_1_Data.append(self.inputPorts[0]) 
                    self.port_1_Time.append(self.inputPortsTime[0])
                    self.dynamic_canvas.disableAutoRange()
                    self.port_1_Line.setData(self.port_1_Time, self.port_1_Data)
                    self.dynamic_canvas.autoRange()
                elif i == 1:
                    pass
                elif i ==2:
                    self.port_3_Data.append(self.inputPorts[2])
                    self.port_3_Time.append(self.inputPortsTime[2])
                    self.dynamic_canvas.disableAutoRange()
                    self.port_3_Line.setData(self.port_3_Time, self.port_3_Data)
                    self.dynamic_canvas.autoRange()
                    
                elif i ==3:
                    pass

                if len(self.port_1_Data)+len(self.port_3_Data)>10:
                    self.port_1_Data = []
                    self.port_1_Time = []
                    self.port_3_Data = []
                    self.port_3_Time = []
    


    def update(self):

        # Function can be called either regularly whenever enough samples of the Analog Data have been read (flagAnalog = 1)
        # or when one of the lick sensor has been touched (flagLick = 1)
        #Maximum number of samples that can be plotted in the windows (this is decided from the maxt input in the GUI)   
        maxSamples = int(self.maxt/self.dt)
        # Read currrent time
        currentTimer = time.perf_counter()

        # Initialize time vector the very first time you plot
        
        #print(self.port_1_Time)
        if self.keepRunning:
            lastt = self.tdata[-1]
            n_new_datapoints= len(self.analogData)
            
            if self.update_calls_count == 0:
                self.tdata = [currentTimer-n_new_datapoints*self.dt]
                
            
            t = np.linspace(self.previousTimer, currentTimer, n_new_datapoints)
            
            if lastt >= self.tdata[0] + self.maxt:
                self.tdata = self.tdata[n_new_datapoints-1:]
                self.ydata = self.ydata[n_new_datapoints-1:]
                #self.dataColor =  self.dataColor[n_new_datapoints-1:]
                
                self.tdata.extend(t)
                self.ydata.extend(self.analogData)
                
                #self.dynamic_canvas.setXRange(int(self.tdata[0]), int(self.tdata[0] + self.maxt))
            else:
                
                self.tdata.extend(t)
                self.ydata.extend(self.analogData)
                #self.dynamic_canvas.setXRange(self.tdata[0], self.tdata[0] + self.maxt)
            
            nSamples = len(self.tdata)
            timeslist = []
            colorslist = []
            maxtime = self.tdata[-1] - self.tdata[0] + self.dt
         

            #newevents = [ event for i, event in enumerate(self.events[:-1]) if self.events[i+1][1]< self.tdata[0]]
            #newevents.append(self.events[-1])
            #self.events = newevents
            #print(newevents,  self.events)
            #print( self.events)
            i = 0
            while i < len(self.events)-1:
                event = self.events[i]
                if self.events[i+1][1] < self.tdata[0]:  # delete if next event is also in past, leaving only one past event
                    self.events.pop(i)
                i+=1
            #for i, event in enumerate(self.events[:-1]):
            #    if self.events[i+1][1] < self.tdata[0]:  # delete if next event is also in past, leaving only one past event
            #        self.events.pop(i)
            
            #print( self.events)
            for i, event in enumerate(self.events):
                if event[1] < self.tdata[0]:
                    timeslist.append(0)
                    colorslist.append(self.event_color_dict[event[0]])
                    if i < len(self.events)-1:
                        timeslist.append((self.events[i+1][1]-self.tdata[0]-self.dt)/maxtime)
                        colorslist.append(self.event_color_dict[event[0]])
                elif event[1] > self.tdata[0]:
                    timeslist.append((event[1]-self.tdata[0])/maxtime)
                    if i < len(self.events)-1:
                        timeslist.append((self.events[i+1][1]-self.tdata[0]-self.dt)/maxtime)
                    colorslist.append(self.event_color_dict[event[0]])
                    colorslist.append(self.event_color_dict[event[0]])

            
            cm = pg.ColorMap(timeslist,colorslist)

            pen = cm.getPen( span=(self.tdata[0], self.tdata[-1]), width=5 ,orientation='horizontal')
            self.dynamic_canvas.disableAutoRange()
            self.line.setData(self.tdata, self.ydata )
            self.line.setPen(pen)
            self.tsniff = [self.tdata[0], self.tdata[-1]]
            self.sniffthline.setData(self.tsniff, self.sniffthdata)
            self.dynamic_canvas.autoRange()


            # delete events in the past
            neg_idx = [i if j < self.tdata[0] else None for i,j in enumerate(self.port_1_Time )]
            for i in neg_idx:
                if i is not None:
                    self.port_1_Time.pop(i)
                    self.port_1_Data.pop(i)
                    self.port_1_Line.setData(self.port_1_Time, self.port_1_Data)
                    #self.dynamic_canvas.autoRange()

            neg_idx = [i if j < self.tdata[0] else None for i,j in enumerate(self.port_3_Time )]
            for i in neg_idx:
                if i is not None:
                    self.port_3_Time.pop(i)
                    self.port_3_Data.pop(i)
                    self.port_3_Line.setData(self.port_3_Time, self.port_3_Data)
                    #self.dynamic_canvas.autoRange()
        else:
            self.finished.emit()
        self.update_calls_count +=1
        self.previousTimer = currentTimer
        return self.line #self.port_1_Line, self.port_2_Line, self.port_3_Line, self.port_4_Line, self.span,

    def getData(self, data):
        self.analogData.extend(data)
        self.analogFlag = 1
        if len(self.analogData)>self.buffersize:
            self.update()
            self.analogData = []
        self.nTotalDataPoints += len(data)
    
    
    
    def setInputEvent(self, inputs):
        currentTimer = time.perf_counter()
        self.lickFlag = 1
        self.analogFlag = 0
        for i in range(len(inputs)):
            if inputs[i] > 0:
                #('lick')
                self.inputPorts[i] = self.triggeredValues[i]
                self.inputPortsTime[i] = currentTimer
                
        nancheck = [0 if math.isnan(x) else 1 for x in self.inputPorts ]
        if sum(nancheck)>0:
            self.update_port_data()
            self.inputPorts = [np.nan] * 4
            self.inputPortsTime = [np.nan] * 4



    def emitter(self):
        yield self.analogData
        
        # for y in self.analogData:
        #     yield y

    #def animate(self):
    #    # pass a generator in "emitter" to produce data for the update func
    #    #self.anim = animation.FuncAnimation(self.fig, self.update, self.emitter, interval=self.plotInterval, blit=True)
    #    self.timer = QtCore.QTimer()
    #    self.timer.setInterval(1)
    #    self.timer.timeout.connect(self.update)
    #    self.timer.start()

    def getFigure(self):
        return self.dynamic_canvas


    def checkOdorPresentation(self, stateName): 
        if stateName == 'PresentOdor':
            self.presentOdor = True
            self.spanStart = self.tdata[-1]
            self.span.set_color('y')
            self.spanColor = 'y'


    def getStateNameTime(self, stateName):
        currentTimer = time.perf_counter()

        self.events.append((stateName, currentTimer))
        #self.timeCol.append(currentTimer)
        #self.allCol.append(self.currentColor)

    def stopRunning(self):
        self.keepRunning = False

    # def checkResponseWindow(self, stateName):
    #     # This function gets the newStateSignal from protocolWorker.
    #     if stateName == 'WaitForResponse':
    #         self.spanStart = self.tdata[-1]
    #         self.span.set_color('b')  # reset color to blue until lick occurs.
    #         self.activateResponseWindow = True
    #         self.presentOdor = False
    #         self.spanColor = 'b'  # also reset the color variable to blue.
    #     elif stateName == 'Correct':
    #         self.span.set_color('g')
    #         self.activateResponseWindow = False
    #     elif stateName == 'Wrong':
    #         self.span.set_color('r')
    #         self.activateResponseWindow = False
    #     elif stateName == 'NoResponse':
    #         # No need to set span color here as it is already blue.
    #         self.activateResponseWindow = False
        
    #     # This else statement is here to end the response window and set its color based on the inputEventSignal received from the inputEventWorker thread,
    #     # instead of based on the stateName.
    #     else:
    #         if self.activateResponseWindow:  
    #             # This if statement ensures the span color is set only once: when the 'WaitForResponse' state completes and transitions to the next state.
    #             # Otherwise, every state that is not named 'WaitForResponse' will call set_color(). I used a QTimer.singleShot to set the span color because
    #             # there seems to be a timing conflict (or thats what I think is happening) where the checkResponseWindow() function is called by the
    #             # protocolWorker thread's newStateSignal and it finishes execution before the setInputEvent() function has a chance to change the span color
    #             # variable based on the type of lick detected by the inputEventWorker thread. Perhaps the newStateSignal is emitted first and then comes the
    #             # inputEventSignal. Both signals are handled by the main thread (i think) because both slot functions (setInputEvent() and checkResponseWindow())
    #             # are inside StreamingWorker which is running on the main thread. So maybe two pyqtSignals cannot be handled simultaneously on the same thread?
    #             # Or maybe they do, but checkResponseWindow() executes faster/finishes earlier than setInputEvent does? This solution works most of the time,
    #             # except for the rare cases when the left sensor is touched and then the right sensor is touched very shortly after, and vise versa, such that
    #             # the span color variable changes more than once within the QTimer.singleShot's duration. This can cause the span color to be set incorrectly;
    #             # opposite to the actual response result. A better solution might be to check if the stateName equals "Correct", "Wrong", or "No Response" 
    #             # using the string sent by the protocolWorker thread's newStateSignal or responseResultSignal.
    #             QTimer.singleShot(100, lambda: self.span.set_color(self.spanColor))
    #             self.activateResponseWindow = False

   
                

    #def pauseAnimation(self):
    #    if not self.paused:
    #        if self.anim is not None:
    #            self.anim.event_source.stop()
    #        self.paused = True

    #def resumeAnimation(self):
    #    if self.paused:
    #        self.anim.event_source.start()
    #        self.paused = False

    def startAnimation(self):

        self.animate()
        return True
        #if self.isSetup and not self.isRun:
        #    self.animate()
        #    self.t_start = time.perf_counter()
        #    self.isRun = True
        #    return True
        #return False

    def resetPlot(self):
        self.tdata = [0]
        self.ydata = [0]
        self.port_1_Data = [np.nan]
        self.port_2_Data = [np.nan]
        self.port_3_Data = [np.nan]
        self.port_4_Data = [np.nan]

        self.port_1_Time = [np.nan]
        self.port_2_Time = [np.nan]
        self.port_3_Time = [np.nan]
        self.port_4_Time = [np.nan]
        
        self.line.setData(self.tdata, self.ydata)
        self.port_1_Line.setData(self.port_1_Time, self.port_1_Data)
        #self.port_2_Line.setData(self.port_2_Time, self.port_2_Data)
        self.port_3_Line.setData(self.port_3_Time, self.port_3_Data)
        #self.port_4_Line.setData(self.port_4_Time, self.port_4_Data)
        self.keepRunning = True

        #self.ax.set_xlim(0, self.maxt)

        # self.timeText.set_text('')
        # self.fpsText.set_text('')
        # self.elapsed.set_text('')
        # self.nTotalDataPointsText.set_text('')
        # self.nDataPointsPlottedText.set_text('')

        # self.nTotalDataPoints = 0
        # self.nDataPointsPlotted = 0
        # self.plotTimer = 0
        # self.previousTimer = 0
        # self.counter = 0
        # self.inputPorts = [np.nan] * 4
        
        # self.spanStart = 0
        # self.spanEnd = 0
        # self.activateResponseWindow = False
        # self.t_start = time.perf_counter()

        # self.ax.figure.canvas.draw()
