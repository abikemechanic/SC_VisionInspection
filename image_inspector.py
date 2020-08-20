from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QSettings
import cv2 as cv
import numpy as np

import flir_camera_controller
from json_settings import JsonSettings


class ImageInspector(QObject):
    new_image_available: pyqtSignal = pyqtSignal()
    inspection_alert: pyqtSignal = pyqtSignal(bool)

    def __init__(self, settings: dict):
        super(ImageInspector, self).__init__()

        self.image_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')
        self.settings = JsonSettings()

        self.inspection_area = None
        self.raw_image = None
        self.final_image = None
        self.detection_img = None
        self.measurement_img = None
        self._settings = settings
        self._resize_factor = .25
        self._resize_image_width = 0
        self._resize_image_height = 0
        self._current_image = None
        self._vert_size = self.settings.get_value('spring_finder.vert_size', 7)
        self._inspection_threshold_value = self.settings.get_value('spring_finder.inspection_threshold_value', 120)
        self._threshold_value = self.settings.get_value('spring_finder.threshold_value', 20)
        self.current_threshold_value = 0
        self._morph_kernel_size = self.settings.get_value('spring_finder.morph_kernel_size', 5)
        self._inspection_alert_value = False
        self._setting_inspection_area = False

        self._temp_x1 = 0
        self._temp_x2 = 0
        self._temp_y1 = 0
        self._temp_y2 = 0
        self.inspection_pt1_x = 0
        self.inspection_pt1_y = 0
        self.inspection_pt2_x = 0
        self.inspection_pt2_y = 0
        self._inspection_pt1_x = self.settings.get_value('spring_finder.inspection_pt1_x', int(310 * 4))
        self._inspection_pt1_y = self.settings.get_value('spring_finder.inspection_pt1_y', int(470 * 4))
        self._inspection_pt2_x = self.settings.get_value('spring_finder.inspection_pt2_x', int(340 * 4))
        self._inspection_pt2_y = self.settings.get_value('spring_finder.inspection_pt2_y', int(540 * 4))
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
        # return self.image_settings.value('image/resize_factor', .25)
        return self.settings.get_value('spring_finder/resize_factor', .25)

    @resize_factor.setter
    def resize_factor(self, value):
        # self.image_settings.setValue('image/resize_factor', float(value))
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
        # self.image_settings.setValue('image/vert_size', int(value))
        self.settings.set_value('spring_finder.vert_size', int(value))

    @property
    def inspection_threshold_value(self):
        return self._inspection_threshold_value

    @inspection_threshold_value.setter
    def inspection_threshold_value(self, value):
        self._inspection_threshold_value = value
        # self.image_settings.setValue('image/inspection_threshold_value', int(value))
        self.settings.set_value('spring_finder.inspection_threshold_value', int(value))

    @property
    def morph_kernel_size(self):
        return self._morph_kernel_size

    @morph_kernel_size.setter
    def morph_kernel_size(self, value):
        self._morph_kernel_size = value
        # self.image_settings.setValue('image/morph_kernel_size', int(value))
        self.settings.set_value('spring_finder.morph_kernel_size', int(value))

    @property
    def threshold_value(self):
        return self._threshold_value

    @threshold_value.setter
    def threshold_value(self, value):
        self._threshold_value = value
        # self.image_settings.setValue('image/threshold_value', float(value))
        self.settings.set_value('spring_finder.threshold_value', float(value))

    @property
    def inspection_alert_value(self):
        return self._inspection_alert_value

    @inspection_alert_value.setter
    def inspection_alert_value(self, value):
        if value != self.inspection_alert_value:
            self._inspection_alert_value = value
            self.inspection_alert.emit(value)

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

        if self.current_threshold_value > (float(self.threshold_value) * 0.9):
            # check for 90% of threshold value to indicate spring found
            self.inspection_alert_value = True
        else:
            self.inspection_alert_value = False

    def update_camera_status(self, status):
        pass

    def _analyze_inspection_area(self):
        try:
            img = self.inspection_area
            img = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
            # cv.imshow('t', img)
            # cv.waitKey(0)
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

        # move measurement to trigger when spring found
        if self.current_threshold_value > (float(self.threshold_value) * 0.9):
            self._measure_spring_end()

    def _measure_spring_end(self):
        raw_img = self.inspection_area
        img = cv.cvtColor(self.inspection_area, cv.COLOR_BGR2GRAY)
        img = cv.medianBlur(img, 5)
        r, img = cv.threshold(img, self.inspection_threshold_value, 255, cv.THRESH_BINARY_INV)
        cnt, h = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

        if len(cnt) < 1:
            self.inspection_area = raw_img
            self.measurement_img = img
            return

        max_area, max_cont = 0, None

        for c in cnt:
            if cv.contourArea(c) > max_area:
                max_area = cv.contourArea(c)
                max_cont = c

        try:
            cv.drawContours(raw_img, [max_cont], 0, (0, 0, 0), 1)
            cv.drawContours(img, [max_cont], 0, (0, 0, 0), 1)

            max_x_point = max_cont[0][0][0]
            min_x_point = max_cont[0][0][0]
            y_max = raw_img.shape[0]

            for pt in max_cont:
                pt_x = pt[0][0]
                if pt_x > max_x_point:
                    max_x_point = pt_x
                elif pt_x <= min_x_point:
                    min_x_point = pt_x

            print(f'max x: {max_x_point}, min x: {min_x_point}')

            cv.line(raw_img, (max_x_point, 0), (max_x_point, y_max), (255, 0, 255), 2)
            cv.line(raw_img, (min_x_point, 0), (min_x_point, y_max), (0, 255, 0), 2)
            cv.line(raw_img, (max_x_point, int(y_max/2)), (min_x_point, int(y_max/2)), (255, 0, 0), 2)

        except (cv.error, SystemError):
            print('error')

        self.inspection_area = raw_img
        self.measurement_img = img
        print('')

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

            # self.image_settings.setValue('image/inspection_pt1_x', self._inspection_pt1_x)
            # self.image_settings.setValue('image/inspection_pt1_y', self._inspection_pt1_y)
            # self.image_settings.setValue('image/inspection_pt2_x', self._inspection_pt2_x)
            # self.image_settings.setValue('image/inspection_pt2_y', self._inspection_pt2_y)
        #     self.settings.set_value('spring_finder.inspection_pt1_x', self._inspection_pt1_x)
        #     self.settings.set_value('spring_finder.inspection_pt1_y', self._inspection_pt1_y)
        #     self.settings.set_value('')
        # self._inspection_pt1_x = self.settings.get_value('spring_finder.inspection_pt1_x', int(310 * 4))
        # self._inspection_pt1_y = self.settings.get_value('spring_finder.inspection_pt1_y', int(470 * 4))
        # self._inspection_pt2_x = self.settings.get_value('spring_finder.inspection_pt2_x', int(340 * 4))
        # self._inspection_pt2_y = self.settings.get_value('spring_finder.inspection_pt2_y', int(540 * 4))

            self._setting_point = 0
            self._temp_x1 = 0
            self._temp_x2 = 0
            self._temp_y1 = 0
            self._temp_y2 = 0
            self._setting_inspection_area = False
