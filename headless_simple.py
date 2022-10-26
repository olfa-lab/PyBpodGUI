from pycromanager import start_headless, Core, Studio, Bridge

save_dir = r'H:\\repos\\PyBpodGUI\\camera_data\\headless'
save_name = r'Headless_test'
acq_settings_file = r'H:\\repos\\PyBpodGUI\\img_acq_simple.txt'

mm_app_path = r'C:\Program Files\Micro-Manager-2.0'
config_file = mm_app_path + r'\MMConfig_Prime95B_600.cfg'
java_loc = r"C:\Program Files\Micro-Manager-2.0\jre\bin\java.exe"
start_headless(mm_app_path, config_file, java_loc=java_loc, timeout=5000)

core = Core()
print('loaded core')
bridge = Bridge()
print('loaded bridge')

camera_name = core.get_camera_device()

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

    with Acquisition(directory=save_dir, name="tcz_acq", show_display=True,
                 ) as acq:
        # Generate the events for a single z-stack
        events = multi_d_acquisition_events(
            num_time_points=5,
            time_interval_s=0,
        )
        acq.acquire(events)