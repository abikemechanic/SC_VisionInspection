from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QSettings
import cv2 as cv
import numpy as np

import flir_camera_controller
from json_settings import JsonSettings
from image_utils.image_measurement import ImageMeasurement


class ImageInspector(QObject):
    new_image_available: pyqtSignal = pyqtSignal()
    new_measurement_available: pyqtSignal = pyqtSignal()
    inspection_alert: pyqtSignal = pyqtSignal(bool)

    def __init__(self, settings: dict):
        super(ImageInspector, self).__init__()

        # self.image_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')
        self.settings = JsonSettings()

        self.inspection_area = None
        self.raw_image = None
        self.final_image = None
        self.detection_img = None
        self.measurement_img = None
        self._settings = settings
        self._resize_factor = float(self.settings.get_value('spring_finder.resize_factor', .25))
        self._resize_image_width = 0
        self._resize_image_height = 0
        self._current_image = None
        self._vert_size = int(self.settings.get_value('spring_finder.vert_size', 7))
        self._inspection_threshold_value = int(self.settings.get_value('spring_finder.inspection_threshold_value', 120))
        self._threshold_value = float(self.settings.get_value('spring_finder.threshold_value', .20))
        self.current_threshold_value = 0
        self._morph_kernel_size = int(self.settings.get_value('spring_finder.morph_kernel_size', 5))
        self._inspection_alert_value = None
        self._setting_inspection_area = False
        self.spring_diameter = 0

        self._temp_x1 = 0
        self._temp_x2 = 0
        self._temp_y1 = 0
        self._temp_y2 = 0
        self._inspection_pt1_x = int(self.settings.get_value('spring_finder.inspection_pt1_x', int(310 * 4)))
        self._inspection_pt1_y = int(self.settings.get_value('spring_finder.inspection_pt1_y', int(470 * 4)))
        self._inspection_pt2_x = int(self.settings.get_value('spring_finder.inspection_pt2_x', int(340 * 4)))
        self._inspection_pt2_y = int(self.settings.get_value('spring_finder.inspection_pt2_y', int(540 * 4)))
        self.inspection_pt1_x = self._inspection_pt1_x
        self.inspection_pt1_y = self._inspection_pt1_y
        self.inspection_pt2_x = self._inspection_pt2_x
        self.inspection_pt2_y = self._inspection_pt2_y
        self._setting_point = 0

        self.camera = flir_camera_controller.CameraController()
        self.camera.new_frame_available.connect(self.analyze_new_image)
        self.camera.camera_connection_event.connect(self.update_camera_status)

        self.image_timer = QTimer()
        self.image_timer.timeout.connect(self.analyze_new_image)
        self.image_timer.start(5)

    # region Properties

    @property
    def resize_factor(self):
        return self._resize_factor

    @resize_factor.setter
    def resize_factor(self, value):
        self._resize_factor = value
        self.settings.set_value('spring_finder.resize_factor', float(value))

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
        self.settings.set_value('spring_finder.vert_size', int(value))

    @property
    def inspection_threshold_value(self):
        return self._inspection_threshold_value

    @inspection_threshold_value.setter
    def inspection_threshold_value(self, value):
        self._inspection_threshold_value = value
        self.settings.set_value('spring_finder.inspection_threshold_value', int(value))

    @property
    def morph_kernel_size(self):
        return self._morph_kernel_size

    @morph_kernel_size.setter
    def morph_kernel_size(self, value):
        self._morph_kernel_size = value
        self.settings.set_value('spring_finder.morph_kernel_size', int(value))

    @property
    def threshold_value(self):
        return self._threshold_value

    @threshold_value.setter
    def threshold_value(self, value):
        self._threshold_value = value
        self.settings.set_value('spring_finder.threshold_value', float(value))

    @property
    def inspection_alert_value(self):
        return self._inspection_alert_value

    @inspection_alert_value.setter
    def inspection_alert_value(self, value):
        if value != self.inspection_alert_value:
            self._inspection_alert_value = value
            self.inspection_alert.emit(value)
            if value:
                self._measure_spring()

    @property
    def inspection_points(self):
        return [(self._inspection_pt1_x, self._inspection_pt1_y),
                (self._inspection_pt2_x, self._inspection_pt2_y)]

    @property
    def inspection_pt1_x(self):
        return self._inspection_pt1_x

    @inspection_pt1_x.setter
    def inspection_pt1_x(self, value):
        self._inspection_pt1_x = value
        self.settings.set_value('spring_finder.inspection_pt1_x', int(value))

    @property
    def inspection_pt1_y(self):
        return self._inspection_pt1_y

    @inspection_pt1_y.setter
    def inspection_pt1_y(self, value):
        self._inspection_pt1_y = value
        self.settings.set_value('spring_finder.inspection_pt1_y', value)

    @property
    def inspection_pt2_x(self):
        return self._inspection_pt2_x

    @inspection_pt2_x.setter
    def inspection_pt2_x(self, value):
        self._inspection_pt2_x = value
        self.settings.set_value('spring_finder.inspection_pt2_x', value)

    @property
    def inspection_pt2_y(self):
        return self._inspection_pt2_y

    @inspection_pt2_y.setter
    def inspection_pt2_y(self, value):
        self._inspection_pt2_y = value
        self.settings.set_value('spring_finder.inspection_pt2_y', value)

    # endregion

    def begin(self):
        pass

    def stop(self):
        self.camera.close_camera()
        self.image_timer.stop()

    def analyze_new_image(self):
        del self.raw_image
        self.raw_image = self.camera.current_image

        self.inspection_area = self.raw_image[self.inspection_pt1_x: self.inspection_pt2_x,
                                              self.inspection_pt1_y: self.inspection_pt2_y]

        self._analyze_inspection_area()

        _img = cv.copyTo(self.raw_image, None)
        rect_pt_1 = (self.inspection_pt2_y, self.inspection_pt2_x)
        rect_pt_2 = (self.inspection_pt1_y, self.inspection_pt1_x)
        _img = cv.rectangle(_img, rect_pt_1, rect_pt_2, (0, 255, 0), 3)

        _img_w = int(_img.shape[1] * self._resize_factor)
        _img_h = int(_img.shape[0] * self._resize_factor)
        _img = cv.resize(_img, (_img_w, _img_h), interpolation=cv.INTER_AREA)

        self.current_image = _img
        self.new_image_available.emit()

        if self.current_threshold_value > (float(self.threshold_value) * 0.93):
            # check for 93% of threshold value to indicate spring found
            self.inspection_alert_value = True
        else:
            self.inspection_alert_value = False

    def update_camera_status(self, status):
        pass

    def _analyze_inspection_area(self):
        try:
            img = self.inspection_area
            img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
        except cv.error:
            return

        img = cv.bilateralFilter(img, 3, 75, 75)

        r, img = cv.threshold(img, self.inspection_threshold_value, 255, cv.THRESH_BINARY_INV)

        # noise reduction
        kernel_size = self.morph_kernel_size
        ker = np.ones((kernel_size, kernel_size), np.uint8)
        img = cv.erode(img, ker, iterations=2)
        img = cv.dilate(img, ker, iterations=2)

        max_pix = img.shape[0] * img.shape[1]
        self.current_threshold_value = (cv.countNonZero(img) / max_pix)
        self.detection_img = img

    def set_threshold_value(self):
        self.threshold_value = self.current_threshold_value

    def set_inspection_area(self):
        if not self._setting_inspection_area:
            self._setting_inspection_area = True
            self._setting_point = 1

        else:
            self._setting_inspection_area = False
            self._temp_x1 = 0
            self._temp_x2 = 0
            self._temp_y1 = 0
            self._temp_y2 = 0
            self._setting_point = 0

    def set_inspection_point(self, x, y):
        if self._setting_point == 1:
            self._temp_x1 = int(y * (1 / self._resize_factor))
            self._temp_y1 = int(x * (1 / self._resize_factor))
            self._setting_point = 2

        elif self._setting_point == 2:
            self._temp_x2 = int(y * (1 / self._resize_factor))
            self._temp_y2 = int(x * (1 / self._resize_factor))

            self.inspection_pt1_x = min(self._temp_x1, self._temp_x2)
            self.inspection_pt2_x = max(self._temp_x1, self._temp_x2)
            self.inspection_pt1_y = min(self._temp_y1, self._temp_y2)
            self.inspection_pt2_y = max(self._temp_y1, self._temp_y2)

            self._setting_point = 0
            self._temp_x1 = 0
            self._temp_x2 = 0
            self._temp_y1 = 0
            self._temp_y2 = 0
            self._setting_inspection_area = False

    def _measure_spring(self):
        img_meas = ImageMeasurement(self.inspection_area)
        img_meas.finished_measurement.connect(self.measurement_complete)

    def measurement_complete(self, img_obj):
        self.measurement_img = img_obj.final_image
        self.spring_diameter = img_obj.spring_diameter_inch
        self.new_measurement_available.emit()
        # save image to file for future use
        # record measurment data for charting
