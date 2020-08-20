import cv2 as cv
from image_utils.image_measurement import ImageMeasurement


class ImageInformation:

    def __init__(self, raw_img, find_img, measurement_obj: ImageMeasurement):
        self.raw_img = raw_img
        self.find_img = find_img
        self.measured_image: ImageMeasurement = measurement_obj


