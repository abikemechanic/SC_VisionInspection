from PyQt5 import QtWidgets, uic
from PyQt5.QtGui import QKeyEvent, QPixmap, QCloseEvent, QShowEvent, QImage
from PyQt5.QtWidgets import QLabel, QMainWindow, QGraphicsView
from PIL import Image

from flir_camera_controller import CameraController as Camera


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        uic.loadUi('UI/mainwindow.ui', self)

        self.lbl_VideoFeed: QLabel = self.lbl_VideoFeed
        self.lbl_InspectionFeed: QLabel = self.lbl_InspectionFeed

        self.camera = Camera()
        self.camera.new_frame_available.connect(self.new_image_available)
        self.camera.camera_connection_event.connect(self.update_camera_connection)
        self.camera.start()

    def new_image_available(self, img_data):
        # img_data = self.camera.current_image
        h, w = img_data.shape
        bytes_per_line = 3 * w
        q_img = QImage(img_data.data, w, h, bytes_per_line, QImage.Format_Grayscale8)
        q_pix = QPixmap()
        # q_pix.convertFromImage(q_img)
        # q_pix = QPixmap(q_img)

        self.lbl_VideoFeed.setPixmap(q_pix)

    def update_camera_connection(self, val):
        pass
