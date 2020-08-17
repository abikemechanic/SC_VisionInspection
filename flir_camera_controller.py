from simple_pyspin import Camera
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QSettings
import time


class CameraController(QThread):
    new_frame_available = pyqtSignal(object)
    camera_connection_event = pyqtSignal(bool)

    settings_directory = ''

    def __init__(self):
        super(CameraController, self).__init__()

        self.cam = Camera(index=0)
        self.end_camera = False
        self._current_image = None

        self.cam_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')

        # Camera setup
        self.cam.init()

        self.cam.Width = self.cam_width
        self.cam.Height = self.cam_height
        self.cam.OffsetX = 0
        self.cam.OffsetY = 0

        self.cam.GainAuto = 'Off'
        self.cam.Gain = 9
        self.cam.ExposureAuto = 'Off'
        self.cam.ExposureTime = 10000

        if 'Bayer' in self.cam.PixelFormat:
            self.cam.PixelFormat = 'BGR8'

        self.cam.start()

    # region Properties

    @property
    def current_image(self):
        self._current_image = None
        return self.cam.get_array()

    @current_image.setter
    def current_image(self, value):
        self._current_image = self.cam.get_array()

    @property
    def cam_width(self):
        return self.cam_settings.value('cam/width', 4000)

    @cam_width.setter
    def cam_width(self, value):
        self.cam_settings.setValue('cam/width', int(value))

    @property
    def cam_height(self):
        return self.cam_settings.value('cam/height', 2000)

    @cam_height.setter
    def cam_height(self, value):
        self.cam_settings.setValue('cam/height', int(value))

    # endregion

    def get_next_image(self):
        return self.cam.get_array()

    def close_camera(self):
        self.cam.close()
        del self.cam
