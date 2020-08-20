from PyQt5.QtCore import Qt, pyqtSignal, QObject, QTimer, QSettings, QThread
import cv2 as cv
import numpy as np
import time

from json_settings import JsonSettings


class ImageMeasurement(QThread):
    finished_measurement = pyqtSignal(object)

    def __init__(self, image):
        super().__init__()
        self.raw_image = image
        self._final_image = None
        cur_time = time.localtime()
        self.img_id = f'SmallCoil_{cur_time.tm_year}_{cur_time.tm_mon}_{cur_time.tm_mday}_ ' +\
                      f'{cur_time.tm_hour}_{cur_time.tm_min}_{cur_time.tm_sec}'
        self.settings = JsonSettings()

        self._transform_threshold = int(self.settings.get_value('spring_measure.transform_threshold', 120))
        self._blur_kernel_size = int(self.settings.get_value('spring_measure.blur_kernel_size', 5))
        self._pixel_per_inch = int(self.settings.get_value('spring_measure.pixels_per_inch', int(181 / .170)))
        # width in pixels / width in inches
        self._calibration_date = self.settings.get_value('spring_measure.calibration_date', '01/01/2000')

        self._max_x_point = 0
        self._min_x_point = 0
        self._x_difference = 0
        self.spring_diameter_inch = 0

        self.start()

    # region Properties
        
    @property
    def max_x_point(self):
        return self._max_x_point

    @max_x_point.setter
    def max_x_point(self, value):
        self._max_x_point = value

    @property
    def min_x_point(self):
        return self._min_x_point

    @min_x_point.setter
    def min_x_point(self, value):
        self._min_x_point = value

    @property
    def x_difference(self):
        return self._x_difference

    @x_difference.setter
    def x_difference(self, value):
        self._x_difference = value

    @property
    def final_image(self):
        return self._final_image

    @final_image.setter
    def final_image(self, value):
        self._final_image = value

    # endregion

    def run(self):
        self._format_and_measure()
        self.finished_measurement.emit(self)

    def _format_and_measure(self):
        img = cv.cvtColor(self.raw_image, cv.COLOR_BGR2GRAY)
        img = cv.medianBlur(img, self._blur_kernel_size)
        r, img = cv.threshold(img, self._transform_threshold, 255, cv.THRESH_BINARY_INV)
        cnt, h = cv.findContours(img, cv.RETR_TREE, cv.CHAIN_APPROX_NONE)

        if len(cnt) < 1:
            raise AttributeError('No Contours Found In Image')

        max_area, max_cont = 0, None

        for c in cnt:
            if cv.contourArea(c) > max_area:
                max_area = cv.contourArea(c)
                max_cont = c

        try:
            cv.drawContours(self.raw_image, [max_cont], 0, (0, 0, 0), 2)

            self.max_x_point = max_cont[0][0][0]
            self.min_x_point = max_cont[0][0][0]
            y_max = img.shape[0]

            for pt in max_cont:
                pt_x = pt[0][0]
                self.max_x_point = max(pt_x, self.max_x_point)
                self.min_x_point = min(pt_x, self.min_x_point)

            cv.line(self.raw_image, (self.max_x_point, 0), (self.max_x_point, y_max), (0, 0, 255), 1)
            cv.line(self.raw_image, (self.min_x_point, 0), (self.min_x_point, y_max), (0, 0, 255), 1)
            cv.line(self.raw_image, (self.max_x_point, int(y_max / 2)), (self.min_x_point, int(y_max / 2)), (0, 255, 0), 1)

            self.x_difference = self.max_x_point - self.min_x_point
            self.spring_diameter_inch = 1 / (self._pixel_per_inch * 1 / self.x_difference)
            self.final_image = self.raw_image
            print(self.x_difference)

        except (cv.error, SystemError):
            raise AttributeError('Cannot Define Contour Of Image')
