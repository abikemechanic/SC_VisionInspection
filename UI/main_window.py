from PyQt5 import QtWidgets, uic, QtGui
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QKeyEvent, QPixmap, QCloseEvent, QShowEvent
from PyQt5.QtWidgets import QLabel, QMainWindow, QSpinBox
from PIL import Image
import numpy as np

# from flir_camera_controller import CameraController as Camera
from image_inspector import ImageInspector as Camera


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        uic.loadUi('UI/mainwindow.ui', self)
        self.app_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')

        self.lbl_VideoFeed: QLabel = self.lbl_VideoFeed
        self.lbl_InspectionFeed: QLabel = self.lbl_InspectionFeed

        self.camera = Camera(None)
        self.camera.new_image_available.connect(self.new_image_available)
        self.camera.begin()

        self.spinBox_ThresholdValue: QSpinBox = self.spinBox_ThresholdValue
        self.spinBox_ThresholdValue.valueChanged.connect(self.update_morphology_kernel)
        self.spinBox_ThresholdValue.setValue(self.app_settings.value('image/morph', 3))

        self.spinBox_VertSize: QSpinBox = self.spinBox_VertSize
        self.spinBox_VertSize.valueChanged.connect(self.update_vert_size)
        self.spinBox_VertSize.setValue(self.app_settings.value('image/vert_size', 7))

    def closeEvent(self, a0):
        self.camera.stop()

    def new_image_available(self):
        pil_img = Image.fromarray(self.camera.current_image)
        self.lbl_VideoFeed.setPixmap(pil_img.toqpixmap())

        pil_insp = Image.fromarray(self.camera.inspection_area)
        self.lbl_InspectionFeed.setPixmap(pil_insp.toqpixmap().scaledToHeight(self.lbl_InspectionFeed.height()))

    def update_camera_connection(self, val):
        pass

    def update_vert_size(self, value):
        self.camera.vert_size = value

    def update_morphology_kernel(self, value):
        self.camera.morph_kernel_size = value
