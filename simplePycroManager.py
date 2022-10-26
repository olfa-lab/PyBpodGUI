save_dir = r'H:\\repos\\PyBpodGUI\\camera_data'
save_name = r'Acquisition_test'
acq_settings_file = r'H:\\repos\\PyBpodGUI\\img_acq_simple.txt'

from time import sleep
from pycromanager import Bridge, Core, start_headless

mm_app_path = r'C:\Program Files\Micro-Manager-2.0'
config_file = mm_app_path + r'\MMConfig_Prime95B_600.cfg'

# start the Java process for headless mode
start_headless(mm_app_path, config_file, timeout=5000)

bridge = Bridge()
core = bridge.get_core()
core = Core()
camera_name = core.get_camera_device()

# core.set_property(camera_name, 'TriggerMode', 'Trigger first') # this is a Prime 95B property
# core.set_property(camera_name, 'ClearMode', 'Pre-Exposure')

studio = bridge.get_studio()
acquisitions = studio.acquisitions()
settings = acquisitions.load_sequence_settings(acq_settings_file)
settings.shouldDisplayImages = False

settings._set_field('root', save_dir)
settings._set_field('numFrames', 100)
acquisitions.set_acquisition_settings(settings)

trial = 0
nTrials = 2
for trial in range(nTrials):

    settings._set_field('prefix', r'Trial_{:03d}'.format(trial))
    print('Acquiring trial {0}\n'.format(trial))
    acquisitions.set_acquisition_settings(settings)
    # print(dir(acquisitions.get_acquisition_settings()))
    current_acquisition = acquisitions.run_acquisition()

    sleep(5)