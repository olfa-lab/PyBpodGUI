from pybpodapi.com.arcom import ArCOM, ArduinoTypes
import time
import numpy as np


class AnalogInException(Exception):
    pass


class BpodAnalogIn(object):
    
    def __init__(self, serial_port):

        self.Port = ArCOM().open(serial_port=serial_port, baudrate=1312500, timeout=1)  # ArCOM Serial port

        # Private variables
        self._CurrentFirmwareVersion = 1
        self._opMenuByte = 213  # Byte code to access op menu
        self._nPhysicalChannels = 8 # Number of physical channels
        self._ValidRanges = {'-10V:10V':0, '-5V:5V':1, '-2.5V:2.5V':2,'0V:10V':3}
        self._RangeMultipliers = [20, 10, 5, 10]
        self._RangeOffsets = [10, 5, 2.5, 0]
        self._InputRangeLimits = [[-10, 10], [-5, 5], [-2.5, 2.5], [0, 10]]
        self._rangeIndices = [0] * self._nPhysicalChannels # Integer code from 0 to 3 inclusive for voltage range (position in ValidRanges dictionary above)
        self._FirmwareVersion = 0
        self._Initialized = 0  # Set to 1 after object constructor is done running
        self._Streaming = 0  # Set to 1 if the oscope display is streaming
        self._chBits = 8192  # Bit width of ADC resolution which is 13 bits, so 2^13.
        self._USBstream2File = False  # True if data acquired with the scope() GUI is streamed to a file
        self._USBFile_SamplePos = 1
        self._USBFile_EventPos = 1
        self._Logging = 0
        self._EventReporting = 0
        self._USBStreamEnabled = 0
        self._ModuleStreamEnabled = 0
        self._nChannelsStreaming2USB = 0  # Number of channels that enabled USB streaming.

        # Public variables
        self.nActiveChannels = self._nPhysicalChannels  # Number of channels to sample (consecutive, beginning with channel 1)
        self.SamplingRate = 1000  # 1Hz-50kHz, affects all channels
        self.InputRange = ['-10V:10V'] * self._nPhysicalChannels  # A cell array of strings indicating voltage range for 12-bit conversion. Valid ranges are in ValidRanges (above). Default is '-10V:10V'.
        self.Thresholds = [10] * self._nPhysicalChannels    # Threshold (V) for each channel. Analog signal crossing the threshold generates an event. Initialized to max voltage of default range
        self.ResetVoltages = [-10] * self._nPhysicalChannels  # Voltage must cross ResetValue (V) before another threshold event can occur
        self.SMeventsEnabled = [0] * self._nPhysicalChannels  # Logical vector indicating channels that generate events
        self.Stream2Module = [0] * self._nPhysicalChannels  # Logical vector indicating channels to stream to output module (raw data)
        self.StreamPrefix = 'R'  # Prefix byte sent before each sample when streaming to output module
        self.nSamplesToLog = 'infinite'  # Number of samples to log on trigger, 0 = infinite
        self.Stream2USB = [0] * self._nPhysicalChannels  # Logical vector indicating channels to stream to USB when streaming is enabled
        self.USBStreamFile = ''  # Full path to file for data acquired with scope() GUI. If empty, scope() data is not saved.

    
        # Tell the analog input module that the USB initiated new connection so reset all state variables.
        msg = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('O')])
        self.Port.write_array(msg)
        time.sleep(0.1)
        HandShakeOkByte = self.Port.read_uint8()
        if (HandShakeOkByte == 161): # Correct handshake response
            self._FirmwareVersion = self.Port.read_uint32()
            
            if (self._FirmwareVersion < 3):  # LatestFirmware
                print('*********************************************************************')
                print('Warning: Old firmware detected: v', self._FirmwareVersion)
                print('The current version is: v 3')
                print('*********************************************************************')
            elif (self._FirmwareVersion > 3):  # LatestFirmware
                print('Analog Input Module with future firmware found. Please update your Bpod software from the Bpod_Gen2 repository.')
            else:
                print('Analog Input Module successfully paired.')
            
            self._Initialized = 1

        else:
            raise AnalogInException('Error: The serial port {0} returned an unexpected handshake signature.'.format(serial_port))


    def getSamplingRate(self):
        return self.SamplingRate

    def getChannelInputVoltageMax(self, channelNum):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error getting channel's max input voltage: Must use a value from 0-7 for channelNum")
        elif (self.InputRange[channelNum] == '-10V:10V'):
            return 10
        elif (self.InputRange[channelNum] == '-5V:5V'):
            return 5
        elif (self.InputRange[channelNum] == '-2.5V:2.5V'):
            return 2.5
        elif (self.InputRange[channelNum] == '0V:10V'):
            return 10

    def getChannelInputVoltageMin(self, channelNum):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error getting channel's min input voltage: Must use a value from 0-7 for channelNum")
        elif (self.InputRange[channelNum] == '-10V:10V'):
            return -10
        elif (self.InputRange[channelNum] == '-5V:5V'):
            return -5
        elif (self.InputRange[channelNum] == '-2.5V:2.5V'):
            return -2.5
        elif (self.InputRange[channelNum] == '0V:10V'):
            return 0

    def setNsamplesToLog(self, nSamples):
        if self._Initialized:
            nSamples2Send = nSamples
            if nSamples == 'infinte':
                nSamples2Send = 0
            # Used to acquire a fixed number of samples
            msgHeader = ArduinoTypes.get_uint8_array(array=[self._opMenuByte, ord('W')])
            msgBody = ArduinoTypes.get_uint32_array(array=[nSamples2Send])
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('nSamplesToLog')
            if nSamples == 0:
                nSamples = 'infinite'
        self.nSamplesToLog = nSamples
        

    def setSamplingRate(self, sf):
        if self._Initialized:
            if self._USBstream2File:
                raise AnalogInException('Error: The analog input module sampling rate cannot be changed while streaming to a file.')

            if (sf < 1) or (sf > 10000):
                raise AnalogInException('Error setting sampling rate: valid rates are in range: [1, 10000] Hz')

            msgHeader = ArduinoTypes.get_uint8_array(array=[self._opMenuByte, ord('F')])
            msgBody = ArduinoTypes.get_uint32_array(array=[sf])
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('samplingRate')

        self.SamplingRate = sf
       

    def setStreamPrefix(self, prefix):
        if self._Initialized:
            if (len(prefix) > 1):
                raise AnalogInException('Error setting prefix: the prefix must be a single byte.')
            
            msg = ArduinoTypes.get_uint8_array(array=[self._opMenuByte, ord('P'), prefix])            
            self.Port.write_array(msg)
            self._confirmTransmission('streamPrefix')
        
        self.StreamPrefix = prefix

        
    def setNactiveChannels(self, nChannels):
        if self._Initialized:
            if self._USBstream2File:
                raise AnalogInException('Error: The analog input module active channel set cannot be changed while streaming to a file.')
            
            if (nChannels < 1) or (nChannels > self._nPhysicalChannels):
                raise AnalogInException('Error setting active channel count: nChannels must be in the range 1: {0}'.format(self._nPhysicalChannels))
            
            msg = ArduinoTypes.get_uint8_array(array=[self._opMenuByte, ord('A'), nChannels])            
            self.Port.write_array(msg)
            self._confirmTransmission('activeChannels')
        
        self.nActiveChannels = nChannels
    
        
    def setInputRange(self, value):
        # 0: '-10V - 10V', 1: '-5V - 5V', 2: '-2.5V - 2.5V', 3: '0V - 10V'
        if self._Initialized:
            if self._USBstream2File:
                raise AnalogInException('Error: The analog input module voltage range cannot be changed while streaming to a file.')
            
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting input voltage ranges: The given list of input voltage ranges must be of length {0}'.format(self._nPhysicalChannels))

            InputRangeIndices = [0] * self._nPhysicalChannels  # Initializes all channels to default range of -10V:10V.
            for i in range(0, self._nPhysicalChannels):
                RangeString = value[i]
                if RangeString in self._ValidRanges:
                    RangeIndex = self._ValidRanges[RangeString]
                else:
                    raise AnalogInException("Invalid range specified: '{0}'. Valid ranges are: {1}".format(RangeString, self._ValidRanges))
                
                InputRangeIndices[i] = RangeIndex
            
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('R')])
            msgBody = ArduinoTypes.get_uint8_array(InputRangeIndices)
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('voltage range')
            oldRangeIndices = self._rangeIndices
            self._rangeIndices = InputRangeIndices
            # Set thresholds and reset values (expressed in voltages) to values in new range.
            # Thresholds that are out of range are set to the respective limits of the new range.
            NewThresholds = self.Thresholds
            NewResets = self.ResetVoltages
            for i in range(self._nPhysicalChannels):
                ThisRangeMin = self._InputRangeLimits[self._rangeIndices[i]][0]
                ThisRangeMax = self._InputRangeLimits[self._rangeIndices[i]][1]
                if NewThresholds[i] < ThisRangeMin:
                    NewThresholds[i] = ThisRangeMin
                elif NewThresholds[i] > ThisRangeMax:
                    NewThresholds[i] = ThisRangeMax
                
                if NewResets[i] < ThisRangeMin:
                    NewResets[i] = ThisRangeMin
                elif NewResets[i] > ThisRangeMax:
                    NewResets[i] = ThisRangeMax
                
                if (self.Thresholds[i] == self._InputRangeLimits[oldRangeIndices[i]][1]):
                    NewThresholds[i] = ThisRangeMax
                
                if (self.ResetVoltages[i] == self._InputRangeLimits[oldRangeIndices[i]][0]):
                    NewResets[i] = ThisRangeMin
                
            
            self.InputRange = value
            # Reset and threshold must be set simultanesously, since they
            # were changed simultaneously. Instead of calling
            # set.Thresholds, and set.ResetVoltages, the next 4 lines do both at once.
            ResetValueBits = self._Volts2Bits(NewResets, self._rangeIndices)
            ThresholdBits = self._Volts2Bits(NewThresholds, self._rangeIndices)
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('T')])
            msgBody = ArduinoTypes.get_uint16_array((ThresholdBits + ResetValueBits))
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('thresholds')
            self._Initialized = 0 # Disable updating to change the object
            self.Thresholds = NewThresholds
            self.ResetVoltages = NewResets
            self._Initialized = 1
        else:
            self.InputRange = value
    

    def setChannelInputRange(self, channelNum, rangeString):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel input voltage range: Must use a value from 0-7 for channelNum")
        
        else:
            listOfInputRanges = self.InputRange.copy()
            listOfInputRanges[channelNum] = rangeString
            self.setInputRange(listOfInputRanges)

        
    def setThresholds(self, value):
        if self._Initialized:
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting threshold voltages: The given list of threshold voltages must be of length {0}'.format(self._nPhysicalChannels))

            for i in range(self._nPhysicalChannels):
                if (value[i] < self._InputRangeLimits[self._rangeIndices[i]][0]) or (value[i] > self._InputRangeLimits[self._rangeIndices[i]][1]):
                    raise AnalogInException('Error setting threshold: the threshold for channel {0} is not within the channel\'s voltage range of: '.format(i, self.InputRange[i]))
            
            #Rescale thresholds according to voltage range.
            ResetValueBits = self._Volts2Bits(self.ResetVoltages, self._rangeIndices)
            ThresholdBits = self._Volts2Bits(value, self._rangeIndices)
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('T')])
            msgBody = ArduinoTypes.get_uint16_array((ThresholdBits + ResetValueBits))
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('thresholds')
        
        self.Thresholds = value
    

    def setChannelThreshold(self, channelNum, voltage):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel threshold voltage: Must use a value from 0-7 for channelNum")
        else:
            listOfThresholds = self.Thresholds.copy()
            listOfThresholds[channelNum] = voltage
            self.setThresholds(listOfThresholds)

        
    def setResetVoltages(self, value):
        if self._Initialized:
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting reset voltages: The given list of reset voltages must be of length {0}'.format(self._nPhysicalChannels))

            for i in range(self._nPhysicalChannels):
                if (value[i] < self._InputRangeLimits[self._rangeIndices[i]][0]) or (value[i] > self._InputRangeLimits[self._rangeIndices[i]][1]):
                    raise AnalogInException('Error setting threshold reset voltage: the value for channel {0} is not within the channel\'s voltage range: '.format(i, self.InputRange[i]))
            
            #Rescale thresholds according to voltage range.
            ResetValueBits = self._Volts2Bits(value, self._rangeIndices)
            ThresholdBits = self._Volts2Bits(self.Thresholds, self._rangeIndices)
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('T')])
            msgBody = ArduinoTypes.get_uint16_array((ThresholdBits + ResetValueBits))
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('reset values')
        
        self.ResetVoltages = value


    def setChannelResetVoltage(self, channelNum, voltage):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel reset voltage: Must use a value from 0-7 for channelNum")
        else:
            listOfResetVoltages = self.ResetVoltages.copy()
            listOfResetVoltages[channelNum] = voltage
            self.setResetVoltages(listOfResetVoltages)

        
    def setSMeventsEnabled(self, value):
        if self._Initialized:
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting events enabled: list given is not of length {0}'.format(self._nPhysicalChannels))

            sumOfVals = 0
            for i in range(self._nPhysicalChannels):
                if (value[i] == 0) or (value[i] == 1):
                    sumOfVals += 1

            if not (sumOfVals == self._nPhysicalChannels):
                raise AnalogInException('Error setting events enabled: enabled state must be 0 or 1')
            
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('K')])
            msgBody = ArduinoTypes.get_uint8_array(value)
            msgToSend = msgHeader + msgBody
            self.Port.write_array(msgToSend)
            self._confirmTransmission('events enabled')
        
        self.SMeventsEnabled = value


    def setChannelSMeventsEnabled(self, channelNum, value):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel SM events enabled: Must use a value from 0-7 for channelNum")
        else:
            listOfSMeventsEnabled = self.SMeventsEnabled.copy()
            listOfSMeventsEnabled[channelNum] = value
            self.setSMeventsEnabled(listOfSMeventsEnabled)

        
    def startModuleStream(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('S'), 1, 1])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('Module stream')

        self._ModuleStreamEnabled = 1

        
    def stopModuleStream(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('S'), 1, 0])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('Module stream')

        self._ModuleStreamEnabled = 0

        
    def startUSBStream(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('S'), 0, 1])
            self.Port.write_array(msgToSend)
            #self._confirmTransmission('USB stream')
        
        self._USBStreamEnabled = 1

        
    def stopUSBStream(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('S'), 0, 0])
            self.Port.write_array(msgToSend)
            self.USBStreamFile = [] # Stop writing to the current file
            # Do not confirm, data bytes in buffer may be expected by
            # another application
        
        self._USBStreamEnabled = 0

    def getSampleFromUSB(self):
        if self._Initialized and self._USBStreamEnabled:
            '''
            The analog input module sends 'R' byte before each sample of data when streaming to usb. This is the usbDataPrefix variable in the firmware.
            Then, it sends 0x00 byte relayed with each sync message. This is the usbSyncData variable in the firmware.
            The matlab documentation does not specify this, so you must read 2 bytes, one for 'R' and one for 0x00, before being able to read a sample.
            The result of read_uint16() should be 82 because this is the decimal ascii value of 'R' and also the decimal value of 0x5200 which is 2 bytes
            in size. The function converts the little endian bytes object to int.

            However, if the state machine sends the usbSyncByte '#' followed by another character for the usbSyncData, the analog module will replace the
            'R' and 0x00 with the '#' and usbSyncData byte, respectively, and then send the 2 byte values for the samples.
            '''
            # if (self.Port.read_uint16() == 82):
            prefix = self.Port.read_uint8_array(2)  # This the 2 byte prefix for 'R' and 0x00 when the bpod does not send a sync byte, or for '#' and usbSyncData when the bpod sends a sync byte and sync data to the analog input module.
            samples = self.Port.read_uint16_array(self._nChannelsStreaming2USB)  # Each sample is 'uint16' which is 2 bytes, so read from each streaming channel.
            return ([prefix] + [samples])

    # Reports threshold crossings to the state machine    
    def startReportingEvents(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('E'), 1, 1])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('event reporting')
        
        self._EventReporting = 1

        
    def stopReportingEvents(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('E'), 1, 0])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('event reporting')
        
        self._EventReporting = 0


    # Reports threshold crossings to the computer via USB    
    def startReportingEvents2USB(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('E'), 0, 1])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('USB event reporting')
        
        self._EventReporting = 1

        
    def stopReportingEvents2USB(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('E'), 0, 0])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('USB event reporting')
        
        self._EventReporting = 0
    
        
    def startLogging(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('L'), 1])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('start logging')
            self._Logging = 1


    def stopLogging(self):
        if self._Initialized:
            msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('L'), 0])
            self.Port.write_array(msgToSend)
            self._confirmTransmission('stop logging')
            self._Logging = 0


    def setStream2USB(self, value):
        if self._Initialized:
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting Stream2USB channels: value is not of length {0}'.format(self._nPhysicalChannels))

            sumOfVals = 0
            for i in range(self._nPhysicalChannels):
                if (value[i] == 0) or (value[i] == 1):
                    sumOfVals += 1

            if not (sumOfVals == self._nPhysicalChannels):
                raise AnalogInException('Error setting Stream2USB channels: enabled state must be 0 or 1')
            
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('C')])
            msgBody = ArduinoTypes.get_uint8_array((value + self.Stream2Module))  # Order matters here.
            msgToSend = msgHeader + msgBody  # Order matters.
            self.Port.write_array(msgToSend)
            self._confirmTransmission('stream to USB')

        self.Stream2USB = value
        self._nChannelsStreaming2USB = sum(value)

    
    def setChannelStream2USB(self, channelNum, value):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel Stream2USB: Must use a value from 0-7 for channelNum")
        else:
            listOfStream2USB = self.Stream2USB.copy()
            listOfStream2USB[channelNum] = value
            self.setStream2USB(listOfStream2USB)

        
    def setStream2Module(self, value):
        if self._Initialized:
            if not (len(value) == self._nPhysicalChannels):
                raise AnalogInException('Error setting Stream2Module channels: value is not of length {0}'.format(self._nPhysicalChannels))

            sumOfVals = 0
            for i in range(self._nPhysicalChannels):
                if (value[i] == 0) or (value[i] == 1):
                    sumOfVals += 1

            if not (sumOfVals == self._nPhysicalChannels):
                raise AnalogInException('Error setting Stream2Module channels: enabled state must be 0 or 1')
            
            msgHeader = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('C')])
            msgBody = ArduinoTypes.get_uint8_array((self.Stream2USB + value))  # Order matters here.
            msgToSend = msgHeader + msgBody  # Order matters.
            self.Port.write_array(msgToSend)
            self._confirmTransmission('stream to Module')
        
        self.Stream2Module = value


    def setChannelStream2Module(self, channelNum, value):
        if (channelNum < 0) or (channelNum > (self._nPhysicalChannels - 1)):
            raise AnalogInException("Error setting channel Stream2Module: Must use a value from 0-7 for channelNum")
        else:
            listOfStream2Module = self.Stream2Module.copy()
            listOfStream2Module[channelNum] = value
            self.setStream2Module(listOfStream2Module)


    def getFirmwareVersion(self):
        return self.FirmwareVersion

    '''
    def getData(self):
        if (self.Port.bytes_available() > 0):
            self.Port.read_bytes_array(self.Port.bytes_available()) # Clear buffer
        
        # Send 'Retrieve' command to the AM
        msgToSend = ArduinoTypes.get_uint8_array([self._opMenuByte, ord('D')])
        self.Port.write_array(msgToSend)
        nSamples = self.Port.read_uint32()
        nValues = self.nActiveChannels * nSamples
        # MaxReadSize = 50000
        bytesAvailable = self.Port.bytes_available()  # 16380 bytes seems to be the max input buffer size on my computer.
        MaxReadSize = int(bytesAvailable / 2)  # I divide by 2 to get the max number of 2-byte values.
        if nValues < MaxReadSize:
            RawData = self.Port.read_uint16_array(nValues)

        else:
            RawData = np.zeros(shape=nValues, dtype='uint16')
            nReads = int(nValues / MaxReadSize)  # round down to nearest integer.
            remainder = nValues % MaxReadSize
            Pos = 0
            for i in range(nReads):
                bytesAvailable = self.Port.bytes_available()  
                RawData[Pos : (Pos + MaxReadSize)] = self.Port.read_uint16_array(MaxReadSize)
                Pos = Pos + MaxReadSize

            bytesAvailable = self.Port.bytes_available()
            RawData[Pos : (Pos + remainder)] = self.Port.read_uint16_array(remainder)

        dataY = np.zeros(shape=(self.nActiveChannels, nSamples))
        ReshapedRawData = np.reshape(RawData, newshape=(self.nActiveChannels, nSamples))
        for i in range(self.nActiveChannels):
            thisMultiplier = self._RangeMultipliers[self._rangeIndices[i]]
            thisOffset = self._RangeOffsets[self._rangeIndices[i]]
            dataY[i, : ] = ((ReshapedRawData[i, : ] / 8192) * thisMultiplier) - thisOffset

        Period = 1 / self.SamplingRate
        dataX = np.zeros(shape=nSamples)
        for i in range(nSamples):
            dataX[i] = i * Period

        return (dataX, dataY)
    '''

    def setZero(self):
        msgToSend = ArduinoTypes.get_uint8_array([213, ord('Z')])
        self.Port.write_array(msgToSend)
    

    def close(self):
        self.Port.close()
    
    # Private methods
    def _confirmTransmission(self, paramName):
        Confirmed = self.Port.read_uint8()
        if Confirmed == 0:
            raise AnalogInException('Error setting {0}: the module denied your request.'.format(paramName))
        elif Confirmed != 1:
            raise AnalogInException('Error setting {0}: module did not acknowledge new value.'.format(paramName))
        

    def _Volts2Bits(self, VoltVector, RangeIndices):
        nElements = len(VoltVector)
        bits = [0] * nElements
        for i in range(nElements):
            thisMultiplier = self._RangeMultipliers[RangeIndices[i]]
            thisOffset = self._RangeOffsets[RangeIndices[i]]
            bits[i] = round(((VoltVector[i] + thisOffset) / thisMultiplier) * self._chBits)

        return bits
