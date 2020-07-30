from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QSettings
import cv2 as cv
import numpy as np

import flir_camera_controller


class ImageInspector(QObject):
    new_image_available: pyqtSignal = pyqtSignal()

    settings_file = 'image_inspection_settings.json'

    def __init__(self, settings: dict):
        super(ImageInspector, self).__init__()

        self.image_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')

        self.inspection_area = None
        self.raw_image = None
        self.final_image = None
        self._settings = settings
        self._resize_factor = .25
        self._resize_image_width = 0
        self._resize_image_height = 0
        self._current_image = None
        self._vert_size = 7

        self.camera = flir_camera_controller.CameraController()
        self.camera.new_frame_available.connect(self.analyze_new_image)
        self.camera.camera_connection_event.connect(self.update_camera_status)

        self.inspection_points = [(850, 2800), (1150, 2850)]

        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.analyze_new_image)
        self.image_timer.start(5)

    # region Properties

    @property
    def resize_factor(self):
        return self.image_settings.value('image/resize_factor', .25)

    @resize_factor.setter
    def resize_factor(self, value):
        self.image_settings.setValue('image/resize_factor', float(value))

    @property
    def current_image(self):
        return self._current_image

    @current_image.setter
    def current_image(self, value):
        del self._current_image
        self._current_image = value

    @property
    def vert_size(self):
        return self._vert_size

    @vert_size.setter
    def vert_size(self, value):
        self._vert_size = value
        self.image_settings.setValue('image/vert_size', int(value))

    # endregion

    def begin(self):
        pass

    def stop(self):
        self.camera.close_camera()
        self.image_timer.stop()

    def analyze_new_image(self):
        del self.raw_image
        self.raw_image = self.camera.current_image

        self.inspection_area = self.raw_image[self.inspection_points[0][0]: self.inspection_points[1][0],
                                              self.inspection_points[0][1]: self.inspection_points[1][1]]

        self._analyze_inspection_area()

        _img = cv.copyTo(self.raw_image, None)
        _img[self.inspection_points[0][0]: self.inspection_points[1][0],
             self.inspection_points[0][1]: self.inspection_points[1][1]] = self.inspection_area

        _img_w = int(_img.shape[1] * self._resize_factor)
        _img_h = int(_img.shape[0] * self._resize_factor)
        _img = cv.resize(_img, (_img_w, _img_h), interpolation=cv.INTER_AREA)

        self.current_image = _img
        self.new_image_available.emit()

    def update_camera_status(self, status):
        pass

    def _analyze_inspection_area(self):
        img = cv.bilateralFilter(self.inspection_area, 3, 75, 75)
        img = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY, 3, 4)

        # filter horizontal lines
        vert_struct = cv.getStructuringElement(cv.MORPH_RECT, (1, self.vert_size))
        img = cv.erode(img, vert_struct)
        img = cv.dilate(img, vert_struct)

        # noise reduction
        kernel_size = 3
        ker = np.ones((kernel_size, kernel_size), np.uint8)

        self.inspection_area = img
