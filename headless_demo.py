from pycromanager import Acquisition, multi_d_acquisition_events, Core, start_headless
import numpy as np
import time

mm_app_path = r'C:\Program Files\Micro-Manager-2.0'

config_file = mm_app_path + r'\MMConfig_Prime95B_600.cfg'

#Optional: specify your own version of java to run with
# java_loc = "/Library/Java/JavaVirtualMachines/zulu-8.jdk/Contents/Home/bin/java"
java_loc = r"C:\Program Files\Micro-Manager-2.0\jre\bin\java.exe"
start_headless(mm_app_path, config_file, java_loc=java_loc, timeout=5000)

core = Core()
core.snap_image()
print(core.get_image())

# save_dir = "/Users/henrypinkard/tmp"
save_dir = r"H:\repos\PyBpodGUI\camera_data\headless_demo"

def image_saved_fn(axes, dataset):
    pixels = dataset.read_image(**axes)
    print(np.mean(pixels))

with Acquisition(directory=save_dir, name="tcz_acq", show_display=True,
                image_saved_fn=image_saved_fn
                 ) as acq:
    # Generate the events for a single z-stack
    events = multi_d_acquisition_events(
        num_time_points=5,
        time_interval_s=0,
        z_start=0,
        order="tcz",
    )
    acq.acquire(events)
d = acq.get_dataset()
pass