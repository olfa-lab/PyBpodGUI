import json
import logging
from PyQt5.QtWidgets import QDialog, QGraphicsScene, QGraphicsItem, QFileDialog
from PyQt5.QtCore import QRectF, Qt
from python_ui_files.protocol_editor_dialog_ui import Ui_Dialog


logging.basicConfig(format="%(message)s", level=logging.INFO)


class SimpleItem(QGraphicsItem):

    def __init__(self, x, y, num, name, timer, change_conditions, output_actions):
        super().__init__()
        self.x = x
        self.y = y
        self.name = name
        self.timer = timer
        self.changeConditions = change_conditions
        self.outputActions = output_actions
        self.num = num

    def boundingRect(self):
        penWidth = 1.0
        return QRectF(self.x, self.y, 150 + penWidth, 225 + penWidth)

    def paint(self, painter, option, widget):
        painter.drawRoundedRect(0 + self.x, 0 + self.y, 150, 225, 5, 5)
        painter.drawText(0 + self.x, 0 + self.y, 150, 25, Qt.TextWordWrap | Qt.AlignCenter, f'State {self.num}')
        painter.drawLine(0 + self.x, 25 + self.y, 150 + self.x, 25 + self.y)
        painter.drawText(2 + self.x, 25 + self.y, 150, 25, Qt.TextWordWrap, f'name: {self.name}')
        painter.drawLine(0 + self.x, 50 + self.y, 150 + self.x, 50 + self.y)
        painter.drawText(2 + self.x, 50 + self.y, 150, 25, Qt.TextWordWrap, f'timer: {self.timer}')
        painter.drawLine(0 + self.x, 75 + self.y, 150 + self.x, 75 + self.y)
        painter.drawText(2 + self.x, 75 + self.y, 150, 75, Qt.TextWordWrap, f'change conditions: \n  {self.changeConditions}')
        painter.drawLine(0 + self.x, 150 + self.y, 150 + self.x, 150 + self.y)
        painter.drawText(2 + self.x, 150 + self.y, 150, 75, Qt.TextWordWrap, f'output actions: \n  {self.outputActions}')


class ProtocolEditorDialog(QDialog, Ui_Dialog):

    def __init__(self, eventNamesList, outputChannelsList, protocolFileName=None, parent=None):
        super().__init__()
        self.setupUi(self)
        self.protocolFileName = protocolFileName
        if self.protocolFileName:
            with open(self.protocolFileName, 'r') as protocolFile:
                self.allStatesDict = json.load(protocolFile)
        else:
            self.allStatesDict = {'states': []}
        self.stateDict = {
            'stateName': '',
            'stateTimer': 0,
            'stateChangeConditions': {},
            'outputActions': {}  # The actual pybpod state machine uses list of two-tuples for output actions. But here, I will use dict for simplicity to avoid duplicates.
        }
        self.eventNames = ['Select...'] + eventNamesList
        '''[
            'Select...', 'Tup', 'Serial1_1', 'Serial1_2', 'Serial1_3', 'Serial1_4', 'Serial1_5', 'Serial1_6',
            'Serial1_7', 'Serial1_8', 'Serial1_9', 'Serial1_10', 'Serial1_11', 'Serial1_12', 'Serial1_13', 'Serial1_14', 'Serial1_15',
            'AnalogIn1_1', 'AnalogIn1_2', 'AnalogIn1_3', 'AnalogIn1_4', 'AnalogIn1_5', 'AnalogIn1_6', 'AnalogIn1_7', 'AnalogIn1_8',
            'AnalogIn1_9', 'AnalogIn1_10', 'AnalogIn1_11', 'AnalogIn1_12', 'AnalogIn1_13', 'AnalogIn1_14', 'AnalogIn1_15',
            'Serial3_1', 'Serial3_2', 'Serial3_3', 'Serial3_4', 'Serial3_5', 'Serial3_6', 'Serial3_7', 'Serial3_8', 'Serial3_9',
            'Serial3_10', 'Serial3_11', 'Serial3_12', 'Serial3_13', 'Serial3_14', 'Serial3_15', 'Serial4_1', 'Serial4_2', 'Serial4_3',
            'Serial4_4', 'Serial4_5', 'Serial4_6', 'Serial4_7', 'Serial4_8', 'Serial4_9', 'Serial4_10', 'Serial4_11', 'Serial4_12',
            'Serial4_13', 'Serial4_14', 'Serial4_15', 'Serial5_1', 'Serial5_2', 'Serial5_3', 'Serial5_4', 'Serial5_5', 'Serial5_6',
            'Serial5_7', 'Serial5_8', 'Serial5_9', 'Serial5_10', 'Serial5_11', 'Serial5_12', 'Serial5_13', 'Serial5_14', 'Serial5_15',
            'SoftCode1', 'SoftCode2', 'SoftCode3', 'SoftCode4', 'SoftCode5', 'SoftCode6', 'SoftCode7', 'SoftCode8', 'SoftCode9',
            'SoftCode10', 'SoftCode11', 'SoftCode12', 'SoftCode13', 'SoftCode14', 'SoftCode15', 'BNC1High', 'BNC1Low', 'BNC2High',
            'BNC2Low', 'Port1In', 'Port1Out', 'Port2In', 'Port2Out', 'Port3In', 'Port3Out', 'Port4In', 'Port4Out', 'GlobalTimer1_Start',
            'GlobalTimer2_Start', 'GlobalTimer3_Start', 'GlobalTimer4_Start', 'GlobalTimer5_Start', 'GlobalTimer6_Start', 'GlobalTimer7_Start',
            'GlobalTimer8_Start', 'GlobalTimer9_Start', 'GlobalTimer10_Start', 'GlobalTimer11_Start', 'GlobalTimer12_Start', 'GlobalTimer13_Start',
            'GlobalTimer14_Start', 'GlobalTimer15_Start', 'GlobalTimer16_Start', 'GlobalTimer1_End', 'GlobalTimer2_End', 'GlobalTimer3_End',
            'GlobalTimer4_End', 'GlobalTimer5_End', 'GlobalTimer6_End', 'GlobalTimer7_End', 'GlobalTimer8_End', 'GlobalTimer9_End',
            'GlobalTimer10_End', 'GlobalTimer11_End', 'GlobalTimer12_End', 'GlobalTimer13_End', 'GlobalTimer14_End', 'GlobalTimer15_End',
            'GlobalTimer16_End', 'GlobalCounter1_End', 'GlobalCounter2_End', 'GlobalCounter3_End', 'GlobalCounter4_End', 'GlobalCounter5_End',
            'GlobalCounter6_End', 'GlobalCounter7_End', 'GlobalCounter8_End', 'Condition1', 'Condition2', 'Condition3', 'Condition4', 'Condition5',
            'Condition6', 'Condition7', 'Condition8', 'Condition9', 'Condition10', 'Condition11', 'Condition12', 'Condition13', 'Condition14',
            'Condition15', 'Condition16'
        ]'''
        self.outputChannels = ['Select...', 'Olfactometer', 'LED', 'Valve'] + outputChannelsList
        '''[
            'Select...', 'Serial1', 'Serial2', 'Serial3', 'Serial4', 'Serial5', 'SoftCode',
            'BNC1', 'BNC2', 'PWM1', 'PWM2', 'PWM3', 'PWM4', 'Valve1', 'Valve2',
            'Valve3', 'Valve4', 'GlobalTimerTrig', 'GlobalTimerCancel', 'GlobalCounterReset'
        ]'''
        self.stateChangeEventComboBox.addItems(self.eventNames)
        self.stateChangeNameComboBox.addItems([
            'Select...', 'WaitForResponse', 'leftAction', 'rightAction', 'Correct', 'Wrong', 'NoResponse', 'NoSniff', 'ITI', 'exit'
        ])
        self.outputChannels.remove('SoftCode')  # Remove this until I figure out how to allow user to configure softcodes.
        self.outputChannelNameComboBox.addItems(self.outputChannels)
        self.stateTimerComboBox.addItems(['Select...', 'rewardDuration', 'itiDuration'])
        self.valvePorts = ['rewardValve', 'finalValve']
        self.LEDports = [1, 2, 3, 4]

        self.scene = QGraphicsScene(parent=self)
        self.graphicsView.setScene(self.scene)
        self.counter = 0
        self.xposition = 0
        self.displayFileContents()
        self.connectSignalsSlots()

    def connectSignalsSlots(self):
        self.stateNameComboBox.lineEdit().editingFinished.connect(self.recordStateName)
        self.stateNameComboBox.currentIndexChanged.connect(self.recordStateName)
        self.stateTimerComboBox.lineEdit().editingFinished.connect(self.recordStateTimer)
        # self.stateTimerComboBox.currentIndexChanged.connect(self.recordStateTimer)
        self.stateChangeEventComboBox.currentTextChanged.connect(self.recordStateChangeEvent)
        self.stateChangeNameComboBox.lineEdit().editingFinished.connect(self.recordStateChangeName)  # self.stateChangeNameComboBox is editable so I can use the editingFinished signal for QLineEdit.
        self.stateChangeNameComboBox.currentIndexChanged.connect(self.recordStateChangeName)
        self.outputChannelNameComboBox.currentTextChanged.connect(self.recordOutputChannelName)
        self.outputChannelValueComboBox.currentTextChanged.connect(self.recordOutputChannelValue)
        self.addStateChangeConditionButton.clicked.connect(self.addStateChangeCondition)
        self.addOutputActionButton.clicked.connect(self.addOutputAction)
        self.clearOutputActionsButton.clicked.connect(self.clearOutputActions)
        self.clearStateChangeConditionsButton.clicked.connect(self.clearStateChangeConditions)
        self.addStateButton.clicked.connect(self.addStateToView)
        self.removeStateButton.clicked.connect(self.removeStateFromView)
        self.cancelButton.clicked.connect(self.reject)
        self.saveButton.clicked.connect(self.saveFile)
        self.saveAsButton.clicked.connect(self.saveAsNewFileDialog)

    def displayFileContents(self):
        if (len(self.allStatesDict['states']) > 0):
            for state in self.allStatesDict['states']:
                stateItem = SimpleItem(
                    x=self.xposition,
                    y=0,
                    num=self.counter,
                    name=state['stateName'],
                    timer=state['stateTimer'],
                    change_conditions=str(state['stateChangeConditions']),  # I cast to string to avoid passing reference to the dict. Otherwise, the graphics items all get the same reference.
                    output_actions=str(state['outputActions'])
                )
                self.scene.addItem(stateItem)
                self.xposition += 200
                self.counter += 1

    def recordStateName(self, index=None):
        if index is None:
            stateName = self.stateNameComboBox.currentText()
        else:
            stateName = self.stateNameComboBox.itemText(index)

        self.stateDict['stateName'] = stateName
        if (self.stateNameComboBox.findText(stateName) == -1):  # -1 means the Text was not found in the combobox
            self.stateNameComboBox.addItem(stateName)  # Only add to combobox if not already in it to avoid duplicates.

    def recordStateTimer(self):
        try:
            self.stateDict['stateTimer'] = int(self.stateTimerComboBox.currentText())
        except ValueError:
            self.stateDict['stateTimer'] = self.stateTimerComboBox.currentText()

    def recordStateChangeEvent(self, eventName):
        # Check that user made a selection for both stateChangeEvent and stateChangeName first.
        # Index 0 is 'Select...' which is not a valid selection. Index -1 means no selection at all.
        if (self.stateChangeEventComboBox.currentIndex() > 0):
            if (self.stateChangeNameComboBox.currentIndex() > 0):
                self.addStateChangeConditionButton.setEnabled(True)  # Enable the button now since valid selections were made.

    def recordStateChangeName(self, index=None):
        if index is None:
            stateChangeName = self.stateChangeNameComboBox.currentText()
            findIndex = self.stateChangeNameComboBox.findText(stateChangeName)
            if (findIndex == -1):  # -1 means the Text was not found in the combobox
                self.stateChangeNameComboBox.addItem(stateChangeName)  # Only add to combobox if not already in it to avoid duplicates.
                length = self.stateChangeNameComboBox.count()
                self.stateChangeNameComboBox.setCurrentIndex(length - 1)  # set index to the last item in the combobox, which was just appended.
            else:
                self.stateChangeNameComboBox.setCurrentIndex(findIndex)  # item already in combobox so use its index.
        else:   
            # Check that user made a selection for both stateChangeEvent and stateChangeName first.
            # Index 0 is 'Select...' which is not a valid selection. Index -1 means no selection at all.
            if (self.stateChangeEventComboBox.currentIndex() > 0):
                if (index > 0):
                    self.addStateChangeConditionButton.setEnabled(True)  # Enable the button now since valid selections were made.

    def addStateChangeCondition(self):
        if (self.stateChangeEventComboBox.currentIndex() > 0):
            if (self.stateChangeNameComboBox.currentIndex() > 0):
                eventName = self.stateChangeEventComboBox.currentText()
                changeStateName = self.stateChangeNameComboBox.currentText()
                # Check if selection is already in stateChangeConditions. If so, then it also must be in ListWidget, but I do not want duplicates.
                # An eventName can only be used once which is why a dict is used to only hold one key for each eventName. 
                # So update the stateDict value for that key, clear the ListWidget, and populate it again with updated stateChangeConditions
                if eventName in self.stateDict['stateChangeConditions']:  
                    self.stateDict['stateChangeConditions'][eventName] = changeStateName
                    self.stateChangeConditionsListWidget.clear()
                    for key, value in self.stateDict['stateChangeConditions'].items():
                        itemToAdd = f"{key} --> {value}"
                        self.stateChangeConditionsListWidget.addItem(itemToAdd)
                
                # Otherwise add the new eventName key to the stateChangeConditions dict with changeStateName for the value.
                # And add the new key-value pair to the ListWidget.
                else:
                    self.stateDict['stateChangeConditions'][eventName] = changeStateName
                    itemToAdd = f"{eventName} --> {changeStateName}"
                    self.stateChangeConditionsListWidget.addItem(itemToAdd)

                    self.stateNameComboBox.addItem(changeStateName)  # Also add to the stateNameComboBox for convenience when creating the next state.
                
                self.addStateChangeConditionButton.setEnabled(False)  # Disable the button until new valid selections are made, to avoid adding duplicate to the listWidget.

    def clearStateChangeConditions(self):
        self.stateChangeConditionsListWidget.clear()
        # self.stateDict['stateChangeConditions'].clear()  # Instead of clearing, I reassign with empty dict below. This way any references to the information will not get deleted.
        self.stateDict['stateChangeConditions'] = {}
        self.stateChangeEventComboBox.setCurrentIndex(0)  # Helps to let user know to reselect valid selections before adding entry.
        self.stateChangeNameComboBox.setCurrentIndex(0)

    def recordOutputChannelName(self, channelName):
        if (self.outputChannelNameComboBox.currentIndex() <= 0):  # Index 0 is 'Select...' which is invalid. Index -1 is no selection at all.
            self.outputChannelValueComboBox.clear()  # Clear the value combobox to avoid mixing invalid output channel name with valid value.

        elif (channelName == 'Olfactometer'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItems(['Command...', 'set_stimulus', 'set_dummy_vials'])
        
        elif (channelName == 'LED'):
            self.outputChannelValueComboBox.clear()

            # Remove channel numbers that have already been added to stateDict['outputActions'], either with 'LED' or 'PWMx'.
            if len(self.LEDports) > 0:
                self.outputChannelValueComboBox.addItems(['Channel number...'] + [str(x) for x in self.LEDports])
            else:
                self.outputChannelValueComboBox.addItem('All used') 

        elif (channelName == 'Valve'):  # make sure to check for this before startswith('Valve').
            self.outputChannelValueComboBox.clear()

            # Remove channel numbers that have already been added to stateDict['outputActions'], either with 'Valve' or 'Valvex'.
            if len(self.valvePorts) > 0:
                self.outputChannelValueComboBox.addItems(['Channel number...'] + [x for x in self.valvePorts])
            else:
                self.outputChannelValueComboBox.addItem('All used')
        
        elif channelName.startswith('Serial'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItems(["Value...", 'SyncByte'])
            self.outputChannelValueComboBox.addItems([str(x) for x in range(1, 256)])  # Serial and Softcode allow output values from 1 to 255 inclusive.

        elif (channelName == 'SoftCode'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItem("Value...")
            self.outputChannelValueComboBox.addItems([str(x) for x in range(2, 256)])  # Softcode allow output values from 1 to 255 inclusive. But I reserve 1 for use by GUI.
        
        elif channelName.startswith('BNC') or channelName.startswith('Valve'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItems(['Value...', '0', '1'])

        elif channelName.startswith('PWM'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItem("Value...")
            self.outputChannelValueComboBox.addItems([str(x) for x in range(0, 256)])  # PWM allows output value from 0 to 255 inclusive.

        elif channelName.startswith('GlobalTimer'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItem("Timer ID...")
            self.outputChannelValueComboBox.addItems([str(x) for x in range(1, 17)])  # GlobalTimer can have id number from 1 to 16 inclusive.

        elif (channelName == 'GlobalCounterReset'):
            self.outputChannelValueComboBox.clear()
            self.outputChannelValueComboBox.addItem("Counter number...")
            self.outputChannelValueComboBox.addItems([str(x) for x in range(1, 9)])  # GlobalCounter can have id number from 1 to 8 inclusive.

    def recordOutputChannelValue(self, channelValue):
        # Check that user made a valid selection for both outputChannelName and outputChannelValue first.
        # Index 0 is 'Select...' which is not a valid selection. Index -1 means no selection at all.
        if (self.outputChannelNameComboBox.currentIndex() > 0):
            if (self.outputChannelValueComboBox.currentIndex() > 0):
                self.addOutputActionButton.setEnabled(True)  # Enable the button now since valid selections were made.

    def addOutputAction(self):
        if (self.outputChannelNameComboBox.currentIndex() > 0):
            if (self.outputChannelValueComboBox.currentIndex() > 0):
                channelName = self.outputChannelNameComboBox.currentText()
                try:
                    channelValue = int(self.outputChannelValueComboBox.currentText())
                except ValueError:
                    channelValue = self.outputChannelValueComboBox.currentText()
                # Check if selection is already in outputActions. If so, then it also must be in ListWidget, but I do not want duplicates.
                # An output channel can only be used once per state which is why a dict is used to only hold one key for each channelName. 
                # So update the outputActions dict value for that key, clear the ListWidget, and populate it again with updated outputActions.
                if channelName in self.stateDict['outputActions']:
                    # Check if its either 'LED' or 'Valve' and append to the list that should already be the value for that key.
                    # I append because when the channelName is either 'LED' or 'Valve', it can be used up to four times per state, once for each
                    # port number (i.e. it is possible to have [('LED', 1), ('LED', 2), ('LED', 3), ('LED', 4)] inside a single state's output actions.)
                    if (channelName == 'LED') or (channelName == 'Valve'):
                        self.stateDict['outputActions'][channelName].append(channelValue)
                        # Remove from combobox to avoid adding dupicate because the combobox items only get updated when the outputChannelNameComboBox currentText changes.
                        self.outputChannelValueComboBox.removeItem(self.outputChannelValueComboBox.currentIndex())
                        if channelName == 'LED':
                            item = 'PWM' + str(channelValue)
                            itemIndex = self.outputChannelNameComboBox.findText(item)
                            self.outputChannelNameComboBox.removeItem(itemIndex)  # For example, remove PWM1 if LED channel 1 was used already.
                            self.LEDports.remove(channelValue)  # Remove from list so doesnt show up again when combobox index changes.
                        else:
                            # item = 'Valve' + str(channelValue)
                            # itemIndex = self.outputChannelNameComboBox.findText(item)
                            # self.outputChannelNameComboBox.removeItem(itemIndex)  # For example, remove Valve1 if Valve channel 1 was used already.
                            self.valvePorts.remove(channelValue)  # Remove from list so doesnt show up again when combobox index changes.
                    
                    else:
                        if channelName.startswith('PWM'):
                            # Last character in the string is the port number (i.e 'PWM1' and 'Valve1') so remove that port number so it does not get added to the outputChannelValueComboBox.
                            # This will prevent the user from duplicating the port. For example, if 'PWM2' was used already, do not allow the user to select 'LED' channel 2.
                            self.LEDports.remove(int(channelName[-1]))  # self.LEDports is list of ints.
                        # elif channelName.startswith('Valve'):
                        #     # Last character in the string is the port number (i.e 'PWM1' and 'Valve1') so remove that port number so it does not get added to the outputChannelValueComboBox.
                        #     # This will prevent the user from duplicating the port. For example, if 'Valve2' was used already, do not allow the user to select 'Valve' channel 2.
                        #     self.valvePorts.remove(int(channelName[-1]))  # self.valvePorts is list of ints.

                        self.stateDict['outputActions'][channelName] = channelValue
                        # remove from combobox to avoid errors if user selects it again after it was already added (i.e. ValueError when removing twice from self.LEDports)
                        self.outputChannelNameComboBox.removeItem(self.outputChannelNameComboBox.currentIndex())
                    
                    self.outputActionsListWidget.clear()
                    for key, value in self.stateDict['outputActions'].items():
                        itemToAdd = f"{key} --> {value}"
                        self.outputActionsListWidget.addItem(itemToAdd)
                
                # Otherwise add the new channelName key to the outputActions dict with channelValue for the value.
                # And add the new key-value pair to the ListWidget.
                else:
                    # Again, check if channelName is either 'LED' or 'Valve' and then create the list as the key's value for the fist time before appending.
                    if (channelName == 'LED') or (channelName == 'Valve'):
                        self.stateDict['outputActions'][channelName] = []
                        self.stateDict['outputActions'][channelName].append(channelValue)
                        # Remove from combobox to avoid adding dupicate because the combobox items only get updated when the outputChannelNameComboBox currentText changes.
                        self.outputChannelValueComboBox.removeItem(self.outputChannelValueComboBox.currentIndex()) 
                        if channelName == 'LED':
                            item = 'PWM' + str(channelValue)
                            itemIndex = self.outputChannelNameComboBox.findText(item)
                            self.outputChannelNameComboBox.removeItem(itemIndex)  # For example, remove PWM1 if LED channel 1 was used already.
                            self.LEDports.remove(channelValue)  # Remove from list so doesnt show up again when combobox index changes.
                        else:
                            # item = 'Valve' + str(channelValue)
                            # itemIndex = self.outputChannelNameComboBox.findText(item)
                            # self.outputChannelNameComboBox.removeItem(itemIndex)  # For example, remove Valve1 if Valve channel 1 was used already.
                            self.valvePorts.remove(channelValue)  # Remove from list so doesnt show up again when combobox index changes.

                    else:
                        if channelName.startswith('PWM'):
                            # Last character in the string is the port number (i.e 'PWM1' and 'Valve1') so remove that port number so it does not get added to the outputChannelValueComboBox.
                            # This will prevent the user from duplicating the port. For example, if 'PWM2' was used already, do not allow the user to select 'LED' channel 2.
                            self.LEDports.remove(int(channelName[-1]))  # self.LEDports is list of ints.
                        # elif channelName.startswith('Valve'):
                        #     # Last character in the string is the port number (i.e 'PWM1' and 'Valve1') so remove that port number so it does not get added to the outputChannelValueComboBox.
                        #     # This will prevent the user from duplicating the port. For example, if 'Valve2' was used already, do not allow the user to select 'Valve' channel 2.
                        #     self.valvePorts.remove(int(channelName[-1]))  # self.valvePorts is list of ints.
                        
                        self.stateDict['outputActions'][channelName] = channelValue
                        # remove from combobox to avoid errors if user selects is again after it was already added (i.e. ValueError when removing twice from self.LEDports)
                        self.outputChannelNameComboBox.removeItem(self.outputChannelNameComboBox.currentIndex())
                    
                    itemToAdd = f"{channelName} --> {channelValue}"
                    self.outputActionsListWidget.addItem(itemToAdd)
                
                self.addOutputActionButton.setEnabled(False)  # Disable the button until new valid selections are made, to avoid adding duplicate to the listWidget.

    def clearOutputActions(self):
        self.outputActionsListWidget.clear()
        # self.stateDict['outputActions'].clear()  # Instead of clearing, I reassign with empty dict below. This way any references to the information will not get deleted.
        self.stateDict['outputActions'] = {}
        self.outputChannelNameComboBox.clear()  # Clear combobox and then re-add all values from self.outputChannels. I do this in case one or more channel Names were removed.
        self.outputChannelNameComboBox.addItems(self.outputChannels)
        self.LEDports.clear()  # Clear the list and re-add the port numbers in case one or more ports were removed.
        self.LEDports = [1, 2, 3, 4]
        self.valvePorts.clear()  # Clear the list and re-add the port numbers in case one or more ports were removed.
        self.valvePorts = ['rewardValve', 'finalValve']
        self.outputChannelNameComboBox.setCurrentIndex(0)  # Helps to make user realize that the add button will reactivate when a new valid selection is made.

    def addStateToView(self):
        # Only the state name and state change conditions are required for a state to be valid.
        # The timer defaults to zero and output actions are not required.
        if self.stateDict['stateName'] and self.stateDict['stateChangeConditions']:
            
            self.allStatesDict['states'].append(self.stateDict.copy())  # I used copy() to preserve the contents of stateChangeConditions and outputActions because their references get deleted after adding a state.

            stateItem = SimpleItem(
                x=self.xposition,
                y=0,
                num=self.counter,
                name=self.stateDict['stateName'],
                timer=self.stateDict['stateTimer'],
                change_conditions=str(self.stateDict['stateChangeConditions']),  # I cast to string to avoid passing reference to the dict. Otherwise, the graphics items all get the same reference.
                output_actions=str(self.stateDict['outputActions'])
            )
            self.scene.addItem(stateItem)
            self.xposition += 200
            self.counter += 1

            self.stateNameComboBox.lineEdit().clear()
            self.stateTimerComboBox.setCurrentIndex(0)
            
            self.clearStateChangeConditions()
            self.clearOutputActions()
    
    def removeStateFromView(self):
        stateItems = self.scene.items()
        self.scene.removeItem(stateItems[0])  # first element is the most recent item added.
        self.xposition -= 200  # decrement to account for the state that was removed.
        self.counter -= 1  # decrement to account for the state that was removed.
        self.allStatesDict['states'].pop()  # remove the most recently added state (which will be the last item in the list).
    
    def saveFile(self):
        if self.protocolFileName:
            with open(self.protocolFileName, 'w') as protocolFile:
                json.dump(self.allStatesDict, protocolFile, indent=4)
                    
            self.accept()  # Closes the dialog window.
    
    def saveAsNewFileDialog(self):
        if (len(self.allStatesDict['states']) > 0):
            options = QFileDialog.Options()
            options |= QFileDialog.DontUseNativeDialog
            fileName, _ = QFileDialog.getSaveFileName(parent=self, caption="Save As New Protocol File", directory="protocol_files", filter="JSON Files (*.json)", options=options)
            if fileName:
                with open(fileName, 'w') as fname:
                    json.dump(self.allStatesDict, fname, indent=4)
                    
                self.accept()  # Closes the dialog window.
