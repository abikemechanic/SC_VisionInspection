from PyQt5 import uic
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QLabel, QMainWindow, QSpinBox, QPushButton
from PIL import Image

# from flir_camera_controller import CameraController as Camera
from image_utils.image_inspector import ImageInspector as Camera
from json_settings import JsonSettings


# noinspection PyUnresolvedReferences
class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()

        uic.loadUi('UI/mainwindow.ui', self)
        self.app_settings = QSettings('Motion Dynamics', 'SC Vision Inspection')

        self.settings = JsonSettings()
        self.settings.file_name = 'SC_Vision_Inspection_Settings.json'

        self.lbl_VideoFeed: QLabel = self.lbl_VideoFeed
        self.lbl_InspectionFeed: QLabel = self.lbl_InspectionFeed

        self.camera = Camera(None)
        self.camera.new_image_available.connect(self.new_image_available)
        self.camera.new_measurement_available.connect(self.on_new_measurement)
        self.camera.inspection_alert.connect(self.inspection_alert)
        self.camera.begin()

        self.spinBox_ThresholdValue: QSpinBox = self.spinBox_ThresholdValue
        self.spinBox_ThresholdValue.valueChanged.connect(self.update_morphology_kernel)

        self.spinBox_VertSize: QSpinBox = self.spinBox_VertSize
        self.spinBox_VertSize.valueChanged.connect(self.update_vert_size)

        self.spinBox_InspectionThresholdValue: QSpinBox = self.spinBox_InspectionThresholdValue
        self.spinBox_InspectionThresholdValue.valueChanged.connect(self.update_inspection_threshold_value)

        self.btn_TrainThreshold: QPushButton = self.btn_TrainThreshold
        self.btn_TrainThreshold.clicked.connect(self.update_threshold_value)

        self.btn_SetInspectionArea: QPushButton = self.btn_SetInspectionArea
        self.btn_SetInspectionArea.clicked.connect(self.set_inspection_area)

        self.label_ThresholdLevel: QLabel = self.label_ThresholdLevel
        self.label_Notifier: QLabel = self.label_Notifier
        self.label_SpringDiameter: QLabel = self.label_SpringDiameter

        self.setup_ui()

    def setup_ui(self):
        self.spinBox_ThresholdValue.setValue(self.app_settings.value('image/morph_kernel_size'))
        self.spinBox_VertSize.setValue(self.app_settings.value('image/vert_size'))
        self.spinBox_InspectionThresholdValue.setValue(self.app_settings.value('image/inspection_threshold_value'))

        self.lbl_VideoFeed.mousePressEvent = self.lbl_VideoFeed_clicked

    def closeEvent(self, a0):
        self.camera.stop()

    def new_image_available(self):
        pil_img = Image.fromarray(self.camera.current_image)
        self.lbl_VideoFeed.setPixmap(pil_img.toqpixmap())

        if self.camera.measurement_img is not None:
            pil_insp = Image.fromarray(self.camera.measurement_img)
            if pil_insp is not None:
                self.lbl_InspectionFeed.setPixmap(pil_insp.toqpixmap().scaledToWidth(self.lbl_InspectionFeed.width()))

        self.label_ThresholdLevel.setText('{:4.2f}'.format(self.camera.current_threshold_value * 100.0))

    def on_new_measurement(self):
        pil_meas = Image.fromarray(self.camera.measurement_img)
        self.lbl_InspectionFeed.setPixmap(pil_meas.toqpixmap().scaledToWidth(self.lbl_InspectionFeed.width()))

        self.label_SpringDiameter.setText('{:4.5f}'.format(self.camera.spring_diameter))

    def update_camera_connection(self, val):
        pass

    def update_vert_size(self, value):
        self.camera.vert_size = value

    def update_inspection_threshold_value(self, value):
        self.camera.inspection_threshold_value = value

    def update_morphology_kernel(self, value):
        self.camera.morph_kernel_size = value

    def update_threshold_value(self):
        self.camera.set_threshold_value()

    def set_inspection_area(self):
        self.camera.set_inspection_area()

    def inspection_alert(self, signal):
        if signal:
            txt = 'Spring Found: Yes'
        else:
            txt = 'Spring Found: No'

        self.label_Notifier.setText(txt)

    def lbl_VideoFeed_clicked(self, event):
        x = event.pos().x()
        y = event.pos().y()

        self.camera.set_inspection_point(x, y)
