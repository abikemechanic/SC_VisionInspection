from PyQt5.QtCore import pyqtSignal, QObject, QTimer, QSettings
import cv2 as cv
import numpy as np
import time


class ImageMeasurement:

    def __init__(self, image):
        self.raw_image = image
        cur_time = time.localtime()
        self.img_id = f'SmallCoil_{cur_time.tm_year}_{cur_time.tm_mon}_{cur_time.tm_mday}_ ' +\
                      f'{cur_time.tm_hour}_{cur_time.tm_min}_{cur_time.tm_sec}'

    def _format_and_measure(self):
        img = cv.cvtColor(self.raw_image, cv.COLOR_BGR2GRAY)
        img = cv.medianBlur(img, 5)
        # r, img = cv.threshold(img, )
