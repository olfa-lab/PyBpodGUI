from unicodedata import name
from shutil import copy2  # preserve metadata
import os

def migrateSessionData():

    # destination in R drive
    destination = r'R:\\rinberglabspace\\Users\\Joshua\\1Prig'

    # get all camera tifs and h5
    folder = self.camera.camera_data_dir
    list_of_tifs = []
    while not bool(list_of_tifs):
        list_of_tifs = glob.glob(folder +'\\*\\*.tif')

    for tif in list_of_tifs:
        copy2(tif, destination)

    # copy h5 from experiment
    h5folder = r'H:\\repos\\PyBpodGUI\\results'
    list_of_h5s = []
    while not bool(list_of_tifs):
        list_of_h5s = glob.glob(folder +'\\*.tif')

    latest_h5 = max(list_of_h5s, key=os.path.getctime)
    copy2(latest_h5, destination)
    pass


if __name__ == "__main__":
    migrateSessionData()