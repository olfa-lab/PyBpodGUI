# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'olfa_editor_dialog.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Dialog(object):
    def setupUi(self, Dialog):
        Dialog.setObjectName("Dialog")
        Dialog.resize(702, 679)
        self.buttonBox = QtWidgets.QDialogButtonBox(Dialog)
        self.buttonBox.setGeometry(QtCore.QRect(500, 630, 181, 41))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Save)
        self.buttonBox.setCenterButtons(True)
        self.buttonBox.setObjectName("buttonBox")
        self.vialsGroupBox = QtWidgets.QGroupBox(Dialog)
        self.vialsGroupBox.setGeometry(QtCore.QRect(20, 220, 661, 241))
        self.vialsGroupBox.setObjectName("vialsGroupBox")
        self.gridLayoutWidget = QtWidgets.QWidget(self.vialsGroupBox)
        self.gridLayoutWidget.setGeometry(QtCore.QRect(10, 30, 641, 165))
        self.gridLayoutWidget.setObjectName("gridLayoutWidget")
        self.vialsGridLayout = QtWidgets.QGridLayout(self.gridLayoutWidget)
        self.vialsGridLayout.setContentsMargins(0, 0, 0, 0)
        self.vialsGridLayout.setObjectName("vialsGridLayout")
        self.vialFormLayout_5 = QtWidgets.QFormLayout()
        self.vialFormLayout_5.setObjectName("vialFormLayout_5")
        self.vialNumLabel_5 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_5.setObjectName("vialNumLabel_5")
        self.vialFormLayout_5.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_5)
        self.vialNumLineEdit_5 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_5.setReadOnly(True)
        self.vialNumLineEdit_5.setObjectName("vialNumLineEdit_5")
        self.vialFormLayout_5.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_5)
        self.vialOdorNameLabel_5 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_5.setObjectName("vialOdorNameLabel_5")
        self.vialFormLayout_5.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_5)
        self.vialOdorNameLineEdit_5 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_5.setObjectName("vialOdorNameLineEdit_5")
        self.vialFormLayout_5.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_5)
        self.vialConcLabel_5 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_5.setObjectName("vialConcLabel_5")
        self.vialFormLayout_5.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_5)
        self.vialConcLineEdit_5 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_5.setObjectName("vialConcLineEdit_5")
        self.vialFormLayout_5.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_5)
        self.vialsGridLayout.addLayout(self.vialFormLayout_5, 2, 0, 1, 1)
        self.line_3 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_3.setObjectName("line_3")
        self.vialsGridLayout.addWidget(self.line_3, 0, 5, 1, 1)
        self.vialFormLayout_8 = QtWidgets.QFormLayout()
        self.vialFormLayout_8.setObjectName("vialFormLayout_8")
        self.vialNumLabel_8 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_8.setObjectName("vialNumLabel_8")
        self.vialFormLayout_8.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_8)
        self.vialNumLineEdit_8 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_8.setReadOnly(True)
        self.vialNumLineEdit_8.setObjectName("vialNumLineEdit_8")
        self.vialFormLayout_8.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_8)
        self.vialOdorNameLabel_8 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_8.setObjectName("vialOdorNameLabel_8")
        self.vialFormLayout_8.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_8)
        self.vialOdorNameLineEdit_8 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_8.setObjectName("vialOdorNameLineEdit_8")
        self.vialFormLayout_8.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_8)
        self.vialConcLabel_8 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_8.setObjectName("vialConcLabel_8")
        self.vialFormLayout_8.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_8)
        self.vialConcLineEdit_8 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_8.setObjectName("vialConcLineEdit_8")
        self.vialFormLayout_8.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_8)
        self.vialsGridLayout.addLayout(self.vialFormLayout_8, 2, 6, 1, 1)
        self.vialFormLayout_4 = QtWidgets.QFormLayout()
        self.vialFormLayout_4.setObjectName("vialFormLayout_4")
        self.vialNumLabel_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_4.setObjectName("vialNumLabel_4")
        self.vialFormLayout_4.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_4)
        self.vialNumLineEdit_4 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_4.setReadOnly(True)
        self.vialNumLineEdit_4.setObjectName("vialNumLineEdit_4")
        self.vialFormLayout_4.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_4)
        self.vialOdorNameLabel_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_4.setObjectName("vialOdorNameLabel_4")
        self.vialFormLayout_4.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_4)
        self.vialOdorNameLineEdit_4 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_4.setObjectName("vialOdorNameLineEdit_4")
        self.vialFormLayout_4.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_4)
        self.vialConcLabel_4 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_4.setObjectName("vialConcLabel_4")
        self.vialFormLayout_4.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_4)
        self.vialConcLineEdit_4 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_4.setObjectName("vialConcLineEdit_4")
        self.vialFormLayout_4.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_4)
        self.vialsGridLayout.addLayout(self.vialFormLayout_4, 0, 6, 1, 1)
        self.line_2 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.vialsGridLayout.addWidget(self.line_2, 0, 3, 1, 1)
        self.line = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.vialsGridLayout.addWidget(self.line, 0, 1, 1, 1)
        self.vialFormLayout_6 = QtWidgets.QFormLayout()
        self.vialFormLayout_6.setObjectName("vialFormLayout_6")
        self.vialNumLabel_6 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_6.setObjectName("vialNumLabel_6")
        self.vialFormLayout_6.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_6)
        self.vialNumLineEdit_6 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_6.setReadOnly(True)
        self.vialNumLineEdit_6.setObjectName("vialNumLineEdit_6")
        self.vialFormLayout_6.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_6)
        self.vialOdorNameLabel_6 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_6.setObjectName("vialOdorNameLabel_6")
        self.vialFormLayout_6.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_6)
        self.vialOdorNameLineEdit_6 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_6.setObjectName("vialOdorNameLineEdit_6")
        self.vialFormLayout_6.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_6)
        self.vialConcLabel_6 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_6.setObjectName("vialConcLabel_6")
        self.vialFormLayout_6.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_6)
        self.vialConcLineEdit_6 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_6.setObjectName("vialConcLineEdit_6")
        self.vialFormLayout_6.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_6)
        self.vialsGridLayout.addLayout(self.vialFormLayout_6, 2, 2, 1, 1)
        self.valFormLayout_3 = QtWidgets.QFormLayout()
        self.valFormLayout_3.setObjectName("valFormLayout_3")
        self.vialNumLabel_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_3.setObjectName("vialNumLabel_3")
        self.valFormLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_3)
        self.vialNumLineEdit_3 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_3.setReadOnly(True)
        self.vialNumLineEdit_3.setObjectName("vialNumLineEdit_3")
        self.valFormLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_3)
        self.vialOdorNameLabel_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_3.setObjectName("vialOdorNameLabel_3")
        self.valFormLayout_3.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_3)
        self.vialOdorNameLineEdit_3 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_3.setObjectName("vialOdorNameLineEdit_3")
        self.valFormLayout_3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_3)
        self.vialConcLabel_3 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_3.setObjectName("vialConcLabel_3")
        self.valFormLayout_3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_3)
        self.vialConcLineEdit_3 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_3.setObjectName("vialConcLineEdit_3")
        self.valFormLayout_3.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_3)
        self.vialsGridLayout.addLayout(self.valFormLayout_3, 0, 4, 1, 1)
        self.vialFormLayout_1 = QtWidgets.QFormLayout()
        self.vialFormLayout_1.setObjectName("vialFormLayout_1")
        self.vialNumLabel_1 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_1.setObjectName("vialNumLabel_1")
        self.vialFormLayout_1.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_1)
        self.vialNumLineEdit_1 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_1.setReadOnly(True)
        self.vialNumLineEdit_1.setObjectName("vialNumLineEdit_1")
        self.vialFormLayout_1.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_1)
        self.vialOdorNameLabel_1 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_1.setObjectName("vialOdorNameLabel_1")
        self.vialFormLayout_1.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_1)
        self.vialOdorNameLineEdit_1 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_1.setObjectName("vialOdorNameLineEdit_1")
        self.vialFormLayout_1.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_1)
        self.vialConcLabel_1 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_1.setObjectName("vialConcLabel_1")
        self.vialFormLayout_1.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_1)
        self.vialConcLineEdit_1 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_1.setObjectName("vialConcLineEdit_1")
        self.vialFormLayout_1.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_1)
        self.vialsGridLayout.addLayout(self.vialFormLayout_1, 0, 0, 1, 1)
        self.vialFormLayout_2 = QtWidgets.QFormLayout()
        self.vialFormLayout_2.setObjectName("vialFormLayout_2")
        self.vialNumLabel_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_2.setObjectName("vialNumLabel_2")
        self.vialFormLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_2)
        self.vialNumLineEdit_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_2.setReadOnly(True)
        self.vialNumLineEdit_2.setObjectName("vialNumLineEdit_2")
        self.vialFormLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_2)
        self.vialOdorNameLabel_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_2.setObjectName("vialOdorNameLabel_2")
        self.vialFormLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_2)
        self.vialOdorNameLineEdit_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_2.setObjectName("vialOdorNameLineEdit_2")
        self.vialFormLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_2)
        self.vialConcLabel_2 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_2.setObjectName("vialConcLabel_2")
        self.vialFormLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_2)
        self.vialConcLineEdit_2 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_2.setObjectName("vialConcLineEdit_2")
        self.vialFormLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_2)
        self.vialsGridLayout.addLayout(self.vialFormLayout_2, 0, 2, 1, 1)
        self.vialFormLayout_7 = QtWidgets.QFormLayout()
        self.vialFormLayout_7.setObjectName("vialFormLayout_7")
        self.vialNumLabel_7 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialNumLabel_7.setObjectName("vialNumLabel_7")
        self.vialFormLayout_7.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.vialNumLabel_7)
        self.vialNumLineEdit_7 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialNumLineEdit_7.setReadOnly(True)
        self.vialNumLineEdit_7.setObjectName("vialNumLineEdit_7")
        self.vialFormLayout_7.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.vialNumLineEdit_7)
        self.vialOdorNameLabel_7 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialOdorNameLabel_7.setObjectName("vialOdorNameLabel_7")
        self.vialFormLayout_7.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.vialOdorNameLabel_7)
        self.vialOdorNameLineEdit_7 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialOdorNameLineEdit_7.setObjectName("vialOdorNameLineEdit_7")
        self.vialFormLayout_7.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.vialOdorNameLineEdit_7)
        self.vialConcLabel_7 = QtWidgets.QLabel(self.gridLayoutWidget)
        self.vialConcLabel_7.setObjectName("vialConcLabel_7")
        self.vialFormLayout_7.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.vialConcLabel_7)
        self.vialConcLineEdit_7 = QtWidgets.QLineEdit(self.gridLayoutWidget)
        self.vialConcLineEdit_7.setObjectName("vialConcLineEdit_7")
        self.vialFormLayout_7.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.vialConcLineEdit_7)
        self.vialsGridLayout.addLayout(self.vialFormLayout_7, 2, 4, 1, 1)
        self.line_8 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_8.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_8.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_8.setObjectName("line_8")
        self.vialsGridLayout.addWidget(self.line_8, 1, 0, 1, 7)
        self.line_9 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_9.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_9.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_9.setObjectName("line_9")
        self.vialsGridLayout.addWidget(self.line_9, 2, 1, 1, 1)
        self.line_10 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_10.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_10.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_10.setObjectName("line_10")
        self.vialsGridLayout.addWidget(self.line_10, 2, 3, 1, 1)
        self.line_11 = QtWidgets.QFrame(self.gridLayoutWidget)
        self.line_11.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_11.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_11.setObjectName("line_11")
        self.vialsGridLayout.addWidget(self.line_11, 2, 5, 1, 1)
        self.label = QtWidgets.QLabel(self.vialsGroupBox)
        self.label.setGeometry(QtCore.QRect(10, 210, 181, 16))
        self.label.setObjectName("label")
        self.mfcGroupBox = QtWidgets.QGroupBox(Dialog)
        self.mfcGroupBox.setGeometry(QtCore.QRect(20, 20, 461, 181))
        self.mfcGroupBox.setObjectName("mfcGroupBox")
        self.formLayoutWidget_5 = QtWidgets.QWidget(self.mfcGroupBox)
        self.formLayoutWidget_5.setGeometry(QtCore.QRect(10, 20, 211, 141))
        self.formLayoutWidget_5.setObjectName("formLayoutWidget_5")
        self.mfcFormLayout_1 = QtWidgets.QFormLayout(self.formLayoutWidget_5)
        self.mfcFormLayout_1.setContentsMargins(0, 0, 0, 0)
        self.mfcFormLayout_1.setObjectName("mfcFormLayout_1")
        self.mfcTypeLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.mfcTypeLabel_1.setObjectName("mfcTypeLabel_1")
        self.mfcFormLayout_1.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.mfcTypeLabel_1)
        self.mfcTypeComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_5)
        self.mfcTypeComboBox_1.setObjectName("mfcTypeComboBox_1")
        self.mfcFormLayout_1.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.mfcTypeComboBox_1)
        self.mfcAddressLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.mfcAddressLabel_1.setObjectName("mfcAddressLabel_1")
        self.mfcFormLayout_1.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.mfcAddressLabel_1)
        self.mfcAddressComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_5)
        self.mfcAddressComboBox_1.setObjectName("mfcAddressComboBox_1")
        self.mfcFormLayout_1.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.mfcAddressComboBox_1)
        self.mfcArduinoPortNumLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.mfcArduinoPortNumLabel_1.setObjectName("mfcArduinoPortNumLabel_1")
        self.mfcFormLayout_1.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.mfcArduinoPortNumLabel_1)
        self.mfcArduinoPortNumComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_5)
        self.mfcArduinoPortNumComboBox_1.setObjectName("mfcArduinoPortNumComboBox_1")
        self.mfcFormLayout_1.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.mfcArduinoPortNumComboBox_1)
        self.mfcCapacityLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.mfcCapacityLabel_1.setObjectName("mfcCapacityLabel_1")
        self.mfcFormLayout_1.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.mfcCapacityLabel_1)
        self.mfcCapacityComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_5)
        self.mfcCapacityComboBox_1.setObjectName("mfcCapacityComboBox_1")
        self.mfcFormLayout_1.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.mfcCapacityComboBox_1)
        self.mfcGasLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_5)
        self.mfcGasLabel_1.setObjectName("mfcGasLabel_1")
        self.mfcFormLayout_1.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.mfcGasLabel_1)
        self.mfcGasComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_5)
        self.mfcGasComboBox_1.setObjectName("mfcGasComboBox_1")
        self.mfcFormLayout_1.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.mfcGasComboBox_1)
        self.formLayoutWidget_6 = QtWidgets.QWidget(self.mfcGroupBox)
        self.formLayoutWidget_6.setGeometry(QtCore.QRect(240, 20, 211, 141))
        self.formLayoutWidget_6.setObjectName("formLayoutWidget_6")
        self.mfcFormLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_6)
        self.mfcFormLayout_2.setContentsMargins(0, 0, 0, 0)
        self.mfcFormLayout_2.setObjectName("mfcFormLayout_2")
        self.mfcTypeLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_6)
        self.mfcTypeLabel_2.setObjectName("mfcTypeLabel_2")
        self.mfcFormLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.mfcTypeLabel_2)
        self.mfcTypeComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_6)
        self.mfcTypeComboBox_2.setObjectName("mfcTypeComboBox_2")
        self.mfcFormLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.mfcTypeComboBox_2)
        self.mfcAddressLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_6)
        self.mfcAddressLabel_2.setObjectName("mfcAddressLabel_2")
        self.mfcFormLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.mfcAddressLabel_2)
        self.mfcAddressComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_6)
        self.mfcAddressComboBox_2.setObjectName("mfcAddressComboBox_2")
        self.mfcFormLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.mfcAddressComboBox_2)
        self.mfcArduinoPortNumLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_6)
        self.mfcArduinoPortNumLabel_2.setObjectName("mfcArduinoPortNumLabel_2")
        self.mfcFormLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.mfcArduinoPortNumLabel_2)
        self.mfcArduinoPortNumComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_6)
        self.mfcArduinoPortNumComboBox_2.setObjectName("mfcArduinoPortNumComboBox_2")
        self.mfcFormLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.mfcArduinoPortNumComboBox_2)
        self.mfcCapacityLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_6)
        self.mfcCapacityLabel_2.setObjectName("mfcCapacityLabel_2")
        self.mfcFormLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.mfcCapacityLabel_2)
        self.mfcGasLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_6)
        self.mfcGasLabel_2.setObjectName("mfcGasLabel_2")
        self.mfcFormLayout_2.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.mfcGasLabel_2)
        self.mfcGasComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_6)
        self.mfcGasComboBox_2.setObjectName("mfcGasComboBox_2")
        self.mfcFormLayout_2.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.mfcGasComboBox_2)
        self.mfcCapacityComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_6)
        self.mfcCapacityComboBox_2.setObjectName("mfcCapacityComboBox_2")
        self.mfcFormLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.mfcCapacityComboBox_2)
        self.line_4 = QtWidgets.QFrame(self.mfcGroupBox)
        self.line_4.setGeometry(QtCore.QRect(220, 20, 20, 141))
        self.line_4.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_4.setObjectName("line_4")
        self.settingsGroupBox = QtWidgets.QGroupBox(Dialog)
        self.settingsGroupBox.setGeometry(QtCore.QRect(499, 19, 181, 181))
        self.settingsGroupBox.setObjectName("settingsGroupBox")
        self.formLayoutWidget_7 = QtWidgets.QWidget(self.settingsGroupBox)
        self.formLayoutWidget_7.setGeometry(QtCore.QRect(10, 20, 160, 152))
        self.formLayoutWidget_7.setObjectName("formLayoutWidget_7")
        self.settingsFormLayout = QtWidgets.QFormLayout(self.formLayoutWidget_7)
        self.settingsFormLayout.setContentsMargins(0, 0, 0, 0)
        self.settingsFormLayout.setObjectName("settingsFormLayout")
        self.cassetteSNLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.cassetteSNLabel_1.setObjectName("cassetteSNLabel_1")
        self.settingsFormLayout.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.cassetteSNLabel_1)
        self.cassetteSNLineEdit_1 = QtWidgets.QLineEdit(self.formLayoutWidget_7)
        self.cassetteSNLineEdit_1.setObjectName("cassetteSNLineEdit_1")
        self.settingsFormLayout.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.cassetteSNLineEdit_1)
        self.cassetteSNLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.cassetteSNLabel_2.setObjectName("cassetteSNLabel_2")
        self.settingsFormLayout.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.cassetteSNLabel_2)
        self.cassetteSNLineEdit_2 = QtWidgets.QLineEdit(self.formLayoutWidget_7)
        self.cassetteSNLineEdit_2.setObjectName("cassetteSNLineEdit_2")
        self.settingsFormLayout.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.cassetteSNLineEdit_2)
        self.comPortLabel = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.comPortLabel.setObjectName("comPortLabel")
        self.settingsFormLayout.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.comPortLabel)
        self.comPortLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget_7)
        self.comPortLineEdit.setObjectName("comPortLineEdit")
        self.settingsFormLayout.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.comPortLineEdit)
        self.interfaceLabel = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.interfaceLabel.setObjectName("interfaceLabel")
        self.settingsFormLayout.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.interfaceLabel)
        self.interfaceComboBox = QtWidgets.QComboBox(self.formLayoutWidget_7)
        self.interfaceComboBox.setObjectName("interfaceComboBox")
        self.settingsFormLayout.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.interfaceComboBox)
        self.masterSNLabel = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.masterSNLabel.setObjectName("masterSNLabel")
        self.settingsFormLayout.setWidget(4, QtWidgets.QFormLayout.LabelRole, self.masterSNLabel)
        self.masterSNLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget_7)
        self.masterSNLineEdit.setObjectName("masterSNLineEdit")
        self.settingsFormLayout.setWidget(4, QtWidgets.QFormLayout.FieldRole, self.masterSNLineEdit)
        self.slaveIndexLabel = QtWidgets.QLabel(self.formLayoutWidget_7)
        self.slaveIndexLabel.setObjectName("slaveIndexLabel")
        self.settingsFormLayout.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.slaveIndexLabel)
        self.slaveIndexLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget_7)
        self.slaveIndexLineEdit.setObjectName("slaveIndexLineEdit")
        self.settingsFormLayout.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.slaveIndexLineEdit)
        self.saveAsButton = QtWidgets.QPushButton(Dialog)
        self.saveAsButton.setGeometry(QtCore.QRect(430, 640, 75, 23))
        self.saveAsButton.setObjectName("saveAsButton")
        self.dilutorsGroupBox = QtWidgets.QGroupBox(Dialog)
        self.dilutorsGroupBox.setGeometry(QtCore.QRect(20, 480, 661, 141))
        self.dilutorsGroupBox.setObjectName("dilutorsGroupBox")
        self.formLayoutWidget_8 = QtWidgets.QWidget(self.dilutorsGroupBox)
        self.formLayoutWidget_8.setGeometry(QtCore.QRect(200, 20, 211, 111))
        self.formLayoutWidget_8.setObjectName("formLayoutWidget_8")
        self.dilutorFormLayout_2 = QtWidgets.QFormLayout(self.formLayoutWidget_8)
        self.dilutorFormLayout_2.setContentsMargins(0, 0, 0, 0)
        self.dilutorFormLayout_2.setObjectName("dilutorFormLayout_2")
        self.dilutorMFCTypeLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.dilutorMFCTypeLabel_1.setObjectName("dilutorMFCTypeLabel_1")
        self.dilutorFormLayout_2.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCTypeLabel_1)
        self.dilutorMFCTypeComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.dilutorMFCTypeComboBox_1.setObjectName("dilutorMFCTypeComboBox_1")
        self.dilutorFormLayout_2.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCTypeComboBox_1)
        self.dilutorMFCAddressLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.dilutorMFCAddressLabel_1.setObjectName("dilutorMFCAddressLabel_1")
        self.dilutorFormLayout_2.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCAddressLabel_1)
        self.dilutorMFCAddressComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.dilutorMFCAddressComboBox_1.setObjectName("dilutorMFCAddressComboBox_1")
        self.dilutorFormLayout_2.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCAddressComboBox_1)
        self.dilutorMFCCapacityLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.dilutorMFCCapacityLabel_1.setObjectName("dilutorMFCCapacityLabel_1")
        self.dilutorFormLayout_2.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCCapacityLabel_1)
        self.dilutorMFCCapacityComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.dilutorMFCCapacityComboBox_1.setObjectName("dilutorMFCCapacityComboBox_1")
        self.dilutorFormLayout_2.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCCapacityComboBox_1)
        self.dilutorMFCGasLabel_1 = QtWidgets.QLabel(self.formLayoutWidget_8)
        self.dilutorMFCGasLabel_1.setObjectName("dilutorMFCGasLabel_1")
        self.dilutorFormLayout_2.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCGasLabel_1)
        self.dilutorMFCGasComboBox_1 = QtWidgets.QComboBox(self.formLayoutWidget_8)
        self.dilutorMFCGasComboBox_1.setObjectName("dilutorMFCGasComboBox_1")
        self.dilutorFormLayout_2.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCGasComboBox_1)
        self.formLayoutWidget_9 = QtWidgets.QWidget(self.dilutorsGroupBox)
        self.formLayoutWidget_9.setGeometry(QtCore.QRect(430, 20, 211, 111))
        self.formLayoutWidget_9.setObjectName("formLayoutWidget_9")
        self.dilutorFormLayout_3 = QtWidgets.QFormLayout(self.formLayoutWidget_9)
        self.dilutorFormLayout_3.setContentsMargins(0, 0, 0, 0)
        self.dilutorFormLayout_3.setObjectName("dilutorFormLayout_3")
        self.dilutorMFCTypeLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_9)
        self.dilutorMFCTypeLabel_2.setObjectName("dilutorMFCTypeLabel_2")
        self.dilutorFormLayout_3.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCTypeLabel_2)
        self.dilutorMFCTypeComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_9)
        self.dilutorMFCTypeComboBox_2.setObjectName("dilutorMFCTypeComboBox_2")
        self.dilutorFormLayout_3.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCTypeComboBox_2)
        self.dilutorMFCAddressLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_9)
        self.dilutorMFCAddressLabel_2.setObjectName("dilutorMFCAddressLabel_2")
        self.dilutorFormLayout_3.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCAddressLabel_2)
        self.dilutorMFCAddressComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_9)
        self.dilutorMFCAddressComboBox_2.setObjectName("dilutorMFCAddressComboBox_2")
        self.dilutorFormLayout_3.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCAddressComboBox_2)
        self.dilutorMFCCapacityLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_9)
        self.dilutorMFCCapacityLabel_2.setObjectName("dilutorMFCCapacityLabel_2")
        self.dilutorFormLayout_3.setWidget(2, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCCapacityLabel_2)
        self.dilutorMFCCapacityComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_9)
        self.dilutorMFCCapacityComboBox_2.setObjectName("dilutorMFCCapacityComboBox_2")
        self.dilutorFormLayout_3.setWidget(2, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCCapacityComboBox_2)
        self.dilutorMFCGasLabel_2 = QtWidgets.QLabel(self.formLayoutWidget_9)
        self.dilutorMFCGasLabel_2.setObjectName("dilutorMFCGasLabel_2")
        self.dilutorFormLayout_3.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.dilutorMFCGasLabel_2)
        self.dilutorMFCGasComboBox_2 = QtWidgets.QComboBox(self.formLayoutWidget_9)
        self.dilutorMFCGasComboBox_2.setObjectName("dilutorMFCGasComboBox_2")
        self.dilutorFormLayout_3.setWidget(3, QtWidgets.QFormLayout.FieldRole, self.dilutorMFCGasComboBox_2)
        self.formLayoutWidget = QtWidgets.QWidget(self.dilutorsGroupBox)
        self.formLayoutWidget.setGeometry(QtCore.QRect(20, 20, 160, 61))
        self.formLayoutWidget.setObjectName("formLayoutWidget")
        self.dilutorFormLayout_1 = QtWidgets.QFormLayout(self.formLayoutWidget)
        self.dilutorFormLayout_1.setContentsMargins(0, 0, 0, 0)
        self.dilutorFormLayout_1.setObjectName("dilutorFormLayout_1")
        self.dilutorComPortLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.dilutorComPortLabel.setObjectName("dilutorComPortLabel")
        self.dilutorFormLayout_1.setWidget(0, QtWidgets.QFormLayout.LabelRole, self.dilutorComPortLabel)
        self.dilutorComPortLineEdit = QtWidgets.QLineEdit(self.formLayoutWidget)
        self.dilutorComPortLineEdit.setObjectName("dilutorComPortLineEdit")
        self.dilutorFormLayout_1.setWidget(0, QtWidgets.QFormLayout.FieldRole, self.dilutorComPortLineEdit)
        self.dilutorTypeLabel = QtWidgets.QLabel(self.formLayoutWidget)
        self.dilutorTypeLabel.setObjectName("dilutorTypeLabel")
        self.dilutorFormLayout_1.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.dilutorTypeLabel)
        self.dilutorTypeComboBox = QtWidgets.QComboBox(self.formLayoutWidget)
        self.dilutorTypeComboBox.setObjectName("dilutorTypeComboBox")
        self.dilutorFormLayout_1.setWidget(1, QtWidgets.QFormLayout.FieldRole, self.dilutorTypeComboBox)
        self.line_5 = QtWidgets.QFrame(self.dilutorsGroupBox)
        self.line_5.setGeometry(QtCore.QRect(180, 20, 20, 111))
        self.line_5.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_5.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_5.setObjectName("line_5")
        self.line_6 = QtWidgets.QFrame(self.dilutorsGroupBox)
        self.line_6.setGeometry(QtCore.QRect(410, 20, 20, 111))
        self.line_6.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_6.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_6.setObjectName("line_6")
        self.clearDilutorButton = QtWidgets.QPushButton(self.dilutorsGroupBox)
        self.clearDilutorButton.setGeometry(QtCore.QRect(40, 100, 111, 23))
        self.clearDilutorButton.setObjectName("clearDilutorButton")

        self.retranslateUi(Dialog)
        self.buttonBox.rejected.connect(Dialog.reject)
        QtCore.QMetaObject.connectSlotsByName(Dialog)

    def retranslateUi(self, Dialog):
        _translate = QtCore.QCoreApplication.translate
        Dialog.setWindowTitle(_translate("Dialog", "Dialog"))
        self.vialsGroupBox.setTitle(_translate("Dialog", "Vials"))
        self.vialNumLabel_5.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_5.setText(_translate("Dialog", "5"))
        self.vialOdorNameLabel_5.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_5.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_8.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_8.setText(_translate("Dialog", "8"))
        self.vialOdorNameLabel_8.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_8.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_4.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_4.setText(_translate("Dialog", "4"))
        self.vialOdorNameLabel_4.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_4.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_6.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_6.setText(_translate("Dialog", "6"))
        self.vialOdorNameLabel_6.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_6.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_3.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_3.setText(_translate("Dialog", "3"))
        self.vialOdorNameLabel_3.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_3.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_1.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_1.setText(_translate("Dialog", "1"))
        self.vialOdorNameLabel_1.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_1.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_2.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_2.setText(_translate("Dialog", "2"))
        self.vialOdorNameLabel_2.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_2.setText(_translate("Dialog", "Concentration"))
        self.vialNumLabel_7.setText(_translate("Dialog", "Vial num"))
        self.vialNumLineEdit_7.setText(_translate("Dialog", "7"))
        self.vialOdorNameLabel_7.setText(_translate("Dialog", "Odor name"))
        self.vialConcLabel_7.setText(_translate("Dialog", "Concentration"))
        self.label.setText(_translate("Dialog", "Note: Vial 4 is the dummy vial."))
        self.mfcGroupBox.setTitle(_translate("Dialog", "MFCs"))
        self.mfcTypeLabel_1.setText(_translate("Dialog", "MFC Type"))
        self.mfcAddressLabel_1.setText(_translate("Dialog", "Address"))
        self.mfcArduinoPortNumLabel_1.setText(_translate("Dialog", "Arduino Port Number"))
        self.mfcCapacityLabel_1.setText(_translate("Dialog", "Capacity"))
        self.mfcGasLabel_1.setText(_translate("Dialog", "Gas"))
        self.mfcTypeLabel_2.setText(_translate("Dialog", "MFC Type"))
        self.mfcAddressLabel_2.setText(_translate("Dialog", "Address"))
        self.mfcArduinoPortNumLabel_2.setText(_translate("Dialog", "Arduino Port Number"))
        self.mfcCapacityLabel_2.setText(_translate("Dialog", "Capacity"))
        self.mfcGasLabel_2.setText(_translate("Dialog", "Gas"))
        self.settingsGroupBox.setTitle(_translate("Dialog", "Settings"))
        self.cassetteSNLabel_1.setText(_translate("Dialog", "Cassette 1 SN"))
        self.cassetteSNLabel_2.setText(_translate("Dialog", "Cassette 2 SN"))
        self.comPortLabel.setText(_translate("Dialog", "COM Port"))
        self.interfaceLabel.setText(_translate("Dialog", "Interface"))
        self.masterSNLabel.setText(_translate("Dialog", "Master SN"))
        self.slaveIndexLabel.setText(_translate("Dialog", "Slave Index"))
        self.saveAsButton.setText(_translate("Dialog", "Save As"))
        self.dilutorsGroupBox.setTitle(_translate("Dialog", "Dilutors"))
        self.dilutorMFCTypeLabel_1.setText(_translate("Dialog", "MFC Type"))
        self.dilutorMFCAddressLabel_1.setText(_translate("Dialog", "Address"))
        self.dilutorMFCCapacityLabel_1.setText(_translate("Dialog", "Capacity"))
        self.dilutorMFCGasLabel_1.setText(_translate("Dialog", "Gas"))
        self.dilutorMFCTypeLabel_2.setText(_translate("Dialog", "MFC Type"))
        self.dilutorMFCAddressLabel_2.setText(_translate("Dialog", "Address"))
        self.dilutorMFCCapacityLabel_2.setText(_translate("Dialog", "Capacity"))
        self.dilutorMFCGasLabel_2.setText(_translate("Dialog", "Gas"))
        self.dilutorComPortLabel.setText(_translate("Dialog", "COM Port"))
        self.dilutorTypeLabel.setText(_translate("Dialog", "Dilutor Type"))
        self.clearDilutorButton.setText(_translate("Dialog", "Clear Dilutor"))
