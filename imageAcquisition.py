import time

import numpy as np
from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, QTimer
from pycromanager.zmq_bridge._bridge import _Bridge
from pycromanager import Core, Studio
from pycromanager import Acquisition, multi_d_acquisition_events
from time import sleep

import logging


class DeviceException(Exception):
    pass


class MicroManagerPrime95B:  # here we define the 'camera' object used in app.py
    bridge = None
    core = None
    studio = None
    acquisitions = None
    camera_name = None

    settings = None
    current_acquisition = None
    camera_data_dir = None

    def __init__(self, acq_settings_file=None):
        self.bridge = _Bridge()
        #self.core = self.bridge.get_core()
        self.core = Core()
        #self.studio = self.bridge.get_studio()
        self.studio = Studio()
        self.acquisitions = self.studio.acquisitions()
        dir(self.acquisitions)
        self.camera_name = self.core.get_camera_device()
        
        # Set camera properties for 80Hz imaging
        self.core.set_property(self.camera_name, 'Exposure', 7)
        self.core.set_property(self.camera_name, 'ClearMode', 'Pre-Sequence')
        self.core.set_property(self.camera_name, 'ReadoutRate', '200MHz 12bit')
        self.core.set_property(self.camera_name, 'TriggerMode', 'Trigger first')
        self.core.set_property(self.camera_name, 'MetadataEnabled', 'Yes')
        self.core.set_property(self.camera_name, 'Binning', '2x2')

        if acq_settings_file:
            self.settings = self.acquisitions.load_sequence_settings(acq_settings_file)
        else:
            self.settings = self.acquisitions.get_acquisition_settings()

        self.settings.intervalMs = 0
        self.settings.shouldDisplayImages = False

        self.acquisitions.set_acquisition_settings(self.settings)

    def update_settings(self):
        self.settings._set_field('save', True)
        self.settings._set_field('shouldDisplayImages', False)
        self.acquisitions.set_acquisition_settings(self.settings)

    def set_binning(self, binning='2x2'):
        if binning not in ['1x1', '2x2']:
            binning = '2x2'

        self.core.set_property(self.camera_name, 'Binning', binning)

    def set_clearmode(self, mode='Pre-Sequence'):
        self.core.set_property(self.camera_name, 'ClearMode', mode)

    def set_readout_rate(self, rate='200MHz 12bit'):
        self.core.set_property(self.camera_name, 'ReadoutRate', rate)

    def set_trigger_mode(self, mode='Trigger first'):
        self.core.set_property(self.camera_name, 'TriggerMode', mode)

    def set_metadata_mode(self, mode='Yes'):
        self.core.set_property(self.camera_name, 'MetadataEnabled', mode)

    def set_exposure(self, exposure_ms=7):
        self.core.set_property(self.camera_name, 'Exposure', exposure_ms)

    def set_interval(self, interval_ms=0):
        self.settings.intervalMs = interval_ms
        self.update_settings()

    def set_frame_num(self, frame_num):
        self.settings.numFrames = frame_num
        self.update_settings()

    def set_camera_data_dir(self, camera_data_dir):
        self.settings._set_field('root', camera_data_dir)
        self.camera_data_dir = camera_data_dir
        self.update_settings()

    def set_prefix(self, prefix):
        self.settings._set_field('prefix', prefix)
        self.update_settings()

    def set_camera_data_name(self, camera_data_name):
        self.settings._set_field('prefix', camera_data_name)
        self.camera_data_name = camera_data_name
        self.update_settings()

    def start_acquisition(self):
        self.update_settings()
        
        print('\n\nStarting camera acquisition\n\n')


        check_settings = self.acquisitions.get_acquisition_settings()

        self.current_acquisition = self.acquisitions.run_acquisition_nonblocking() # has to be started for every trial, _nonblocking?
        self.acquisitions.get_acquisition_settings()

    def stop_acquisition(self):
        self.acquisitions.halt_acquisition()  # guessing here

    def is_acquisition_running(self):
        return self.acquisitions.is_acquisition_running()