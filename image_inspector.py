from PyQt5.QtCore import pyqtSignal, QObject
import cv2 as cv
import numpy as np

import flir_camera_controller


class ImageInspector(QObject):
    new_image_available: pyqtSignal = pyqtSignal()

    settings_file = 'image_inspection_settings.json'

    def __init__(self, settings: dict):
        super(ImageInspector, self).__init__()

        self.inspection_area = None
        self.raw_image = None
        self.final_image = None
        self._settings = settings
        self._resize_factor = 1
        self._resize_image_width = 0
        self._resize_image_height = 0

        self.camera = flir_camera_controller.CameraController()
        self.camera.new_frame_available.connect(self.analyze_new_imagse)
        self.camera.camera_connection_event.connect(self.update_camera_status)
        self.camera.start()

        self.inspection_points = [(700, 2800), (1000, 2850)]

    # region Properties

    @property
    def resize_factor(self):
        return self._resize_factor

    @resize_factor.setter
    def resize_factor(self, value):
        self._resize_factor = value
        self._resize_image_width = self.raw_image.shape[1] * value
        self._resize_image_height = self.raw_image.shape[0] * value

    # endregion

    def analyze_new_image(self):
        self.raw_image = self.camera.current_image
        self.inspection_area = self.raw_image[self.inspection_points[0][0]: self.inspection_points[0][1],
                                              self.inspection_points[1][0]: self.inspection_points[1][1]]

        self._analyze_inspection_area()

        _img = cv.copyTo(self.raw_image, None)
        _img[self.inspection_points[0][0]: self.inspection_points[0][1],
             self.inspection_points[1][0]: self.inspection_points[1][1]] = self.inspection_area

        # set final image

    def update_camera_status(self, status):
        print(status)

    def _analyze_inspection_area(self):
        img = cv.bilateralFilter(self.inspection_area, 3, 75, 75)
        img = cv.adaptiveThreshold(img, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C, cv.THRESH_BINARY, 7, 4)

        # filter horizontal lines
        vert_size = 5
        vert_struct = cv.getStructuringElement(cv.MORPH_RECT, (1, vert_size))
        img = cv.erode(img, vert_struct)
        img = cv.dilate(img, vert_struct)

        # noise reduction
        kernel_size = 3
        ker = np.ones((kernel_size, kernel_size), np.uint8)

        self.inspection_area = img
