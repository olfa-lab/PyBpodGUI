save_dir = r'H:\\repos\\PyBpodGUI\\camera_data'
save_name = r'Acquisition_test'
acq_settings_file = r'H:\\repos\\PyBpodGUI\\.default_acq'

# import logging
# import atexit
# my_bpod=None
# def close():
#     if my_bpod:
#         try:
#             my_bpod.stop_trial()
#         except:
#             pass
#         try:
#             my_bpod.close()
#         except:
#             pass
# atexit.register(close)
# from pybpodapi.protocol import Bpod, StateMachine
# from pybpodapi.exceptions.bpod_error import BpodErrorException
# logging.basicConfig(format="%(message)s", level=logging.INFO)
# logger = logging.getLogger(__name__)

# my_bpod = Bpod()
# sma = StateMachine(my_bpod)
 
# sma.add_state(
#     state_name='BNC1On',
#     state_timer=1,
#     state_change_conditions={
#         'Tup': 'BNC1Off'
#         },
#     output_actions= [('BNC1', 1 )]
        
# )
# sma.add_state(
# state_name='BNC1Off',
# state_timer=10,
# state_change_conditions={
#     'Tup': 'BNC1On',
# },
# output_actions=[('BNC1', 0)]
# )

# my_bpod.send_state_machine(sma)

# my_bpod.run_state_machine(sma)
# my_bpod.close()

from time import sleep
from pycromanager import Bridge, Acquisition, multi_d_acquisition_events

bridge = Bridge()
core = bridge.get_core()
camera_name = core.get_camera_device()

core.set_property(camera_name, 'TriggerMode', 'Trigger first') # this is a Prime 95B property
core.set_property(camera_name, 'ClearMode', 'Pre-Exposure')

nTrials = 10
trial = 0
# pass in the function as a post_hardware_hook


#     with Acquisition(directory=save_dir, name=save_name
#         ) as acq:
        
#         events = multi_d_acquisition_events(num_time_points=100)

#         print('About to start acquire')

#         acq.acquire(events)
#         trial += 1

studio = bridge.get_studio()
acquisitions = studio.acquisitions()
settings = acquisitions.load_sequence_settings(acq_settings_file)
settings.shouldDisplayImages = False

settings._set_field('root', save_dir)
settings._set_field('numFrames', 100)
acquisitions.set_acquisition_settings(settings)

trial = 0
nTrials = 6
while trial < nTrials:

    settings._set_field('prefix', r'Trial_{:03d}'.format(trial))
    print(settings)
    acquisitions.set_acquisition_settings(settings)
    print(dir(acquisitions.get_acquisition_settings()))
    current_acquisition = acquisitions.run_acquisition()

    sleep(5)
    trial += 1
# my_bpod.close()