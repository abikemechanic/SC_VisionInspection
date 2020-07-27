from simple_pyspin import Camera
from PyQt5.QtCore import pyqtSignal, QObject, QThread
import time


class CameraController(QThread):
    new_frame_available = pyqtSignal(object)
    camera_connection_event = pyqtSignal(bool)

    def __init__(self):
        super(CameraController, self).__init__()

        self.cam = Camera(index=0)
        self.end_camera = False
        self._current_image = None

        # Camera setup
        self.cam.init()

        self.cam.Width = 4000
        self.cam.Height = 2000
        self.cam.OffsetX = 0
        self.cam.OffsetY = 250

        self.cam.GainAuto = 'Off'
        self.cam.Gain = 9
        self.cam.ExposureAuto = 'Off'
        self.cam.ExposureTime = 10000

    @property
    def current_image(self):
        img = self._current_image
        self._current_image = None
        return img

    @current_image.setter
    def current_image(self, value):
        self._current_image = value
        # self.new_frame_available.emit()

    def run(self):
        self.cam.start()

        while 1:
            self.current_image = self.cam.get_array()
            self.new_frame_available.emit(self.current_image)
            time.sleep(1/100)

            if self.end_camera:
                self.close_camera()
                break

    def get_next_image(self):
        return self.cam.get_array()

    def close_camera(self):
        self.cam.close()
