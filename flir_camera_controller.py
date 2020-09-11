from simple_pyspin import Camera, CameraError
from PyQt5.QtCore import pyqtSignal, QObject, QThread, QSettings
import time

from json_settings import JsonSettings


class CameraController(QThread):
    new_frame_available = pyqtSignal(object)
    camera_connection_event = pyqtSignal(bool)

    settings_directory = ''

    def __init__(self, camera_index=0):
        super(CameraController, self).__init__()

        self.cam = Camera(index=camera_index)
        self.end_camera = False
        self._current_image = None

        self.cam_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')
        self.settings = JsonSettings()

        self._cam_width = int(self.settings.get_value('camera.width', 1200))
        self._cam_height = int(self.settings.get_value('camera.height', 600))
        self._x_offset = int(self.settings.get_value('camera.x_offset', 800))
        self._y_offset = int(self.settings.get_value('camera.y_offset', 700))
        self._pixel_format = self.settings.get_value('camera.pixel_format', 'BGR8')
        self._exposure_auto = self.settings.get_value('camera.exposure_auto', 'Off')
        self._exposure_time = int(self.settings.get_value('camera.exposure_time', 2000))
        self._gain_auto = self.settings.get_value('camera.gain_auto', 'Off')
        self._gain = int(self.settings.get_value('camera.gain', 9))

        # Camera setup
        self.cam.init()
        self._init_camera()
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
        return self._cam_width

    @cam_width.setter
    def cam_width(self, value):
        self.settings.set_value('camera.width', int(value))

    @property
    def cam_height(self):
        return self._cam_height

    @cam_height.setter
    def cam_height(self, value):
        self.settings.set_value('camera.height', int(value))

    @property
    def x_offset(self):
        return self._x_offset

    @x_offset.setter
    def x_offset(self, value):
        self.settings.set_value('camera.x_offset', int(value))

    @property
    def y_offset(self):
        return self._y_offset

    @y_offset.setter
    def y_offset(self, value):
        self.settings.set_value('camera.y_offset', int(value))

    @property
    def pixel_format(self):
        return self._pixel_format

    @pixel_format.setter
    def pixel_format(self, value):
        self.settings.set_value('camera.pixel_format', value)

    @property
    def exposure_auto(self):
        return self._exposure_auto

    @exposure_auto.setter
    def exposure_auto(self, value):
        self.settings.set_value('camera.exposure_auto', value)
        self._exposure_auto = value

    @property
    def exposure_time(self):
        return self._exposure_time

    @exposure_time.setter
    def exposure_time(self, value):
        self.settings.set_value('camera.exposure_time', int(value))
        self._exposure_time = value

    @property
    def gain_auto(self):
        return self._gain_auto

    @gain_auto.setter
    def gain_auto(self, value):
        self.settings.set_value('camera.gain_auto', value)
        self._gain_auto = value

    @property
    def gain(self):
        return self._gain

    @gain.setter
    def gain(self, value):
        self.settings.set_value('camera.gain', int(value))
        self._gain = value

    # endregion

    def _init_camera(self):
        try:
            self.cam.Width = self.cam_width
            self.cam.Height = self.cam_height
            self.cam.OffsetX = self.x_offset
            self.cam.OffsetY = self.y_offset

            self.cam.GainAuto = 'Off'
            self.cam.Gain = 9
            self.cam.ExposureAuto = self.exposure_auto
            self.cam.ExposureTime = self.exposure_time
            self.cam.GainAuto = self.gain_auto
            self.cam.Gain = self.gain
            self.cam.PixelFormat = self.pixel_format
        except CameraError as ex:
            print(ex)
            self.cam.start()
            self.cam.stop()
            self._init_camera()

    def get_next_image(self):
        return self.cam.get_array()

    def close_camera(self):
        self.cam.close()
        del self.cam
