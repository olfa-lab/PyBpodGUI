from pycromanager import Bridge
bridge = Bridge()
studio = bridge.get_studio()
acq = studio.acquisitions()
settings = acq.get_acquisition_settings()
acq.set_acquisition_settings(settings)

print('should_display_images is set to {0}'.format(settings.should_display_images()))


settings._set_field('shouldDisplayImages', False)
acq.set_acquisition_settings(settings)
check_settings = acq.get_acquisition_settings()

print('should_display_images is set to {0}'.format(check_settings.should_display_images()))
