# import simple_pyspin
from PIL import Image
import pyspin.PySpin as PySpin
import os
from PyQt5.QtCore import pyqtSignal, QThread
from PyQt5.QtGui import QPixmap, QImage, qRgb
import time
import ctypes.wintypes


class Camera(QThread):
    new_image_available = pyqtSignal(QPixmap)
    fps_rate = pyqtSignal(str)

    def __init__(self, picture_directory=''):
        QThread.__init__(self)

        self.pyspin_system = PySpin.System.GetInstance()
        self.cam_dict = {}
        self.cam: PySpin.Camera = None
        self.node_map = ''
        self.node_map_tl_device = ''
        self.capture_image = False
        self.last_image_capture_time = 0
        self.current_image_capture_time = 0

        self.current_image = None
        self._save_image = False
        self.CSIDL_PICTURES = 295
        self._picture_save_directory = picture_directory

        self.end_camera = False
        self.wait_to_end = True

    @property
    def save_image(self):
        return self._save_image

    @save_image.setter
    def save_image(self, value):
        if self._save_image != value:
            self._save_image = value

    @property
    def picture_save_directory(self):
        return self._picture_save_directory

    @picture_save_directory.setter
    def picture_save_directory(self, value):
        if self._picture_save_directory != value:
            self._picture_save_directory = value

        if not os.path.exists(self._picture_save_directory):
            os.mkdir(self._picture_save_directory)

    def run(self):
        try:
            i = 0
            self.cam = self._setup_camera()
            while self.cam is None or not self.cam:
                i += 1
                if i < 5:
                    print(i)
                    self.cam = self._setup_camera()
                    time.sleep(1)
                else:
                    print('unable to start camera, power cycle')
        except PySpin.SpinnakerException as ex:
            raise ex

        self.cam.BeginAcquisition()
        # end acquisition at the end of the program...

        while not self.end_camera:
            try:
                img_result = self.cam.GetNextImage()
                if img_result.IsIncomplete():
                    continue
                else:
                    img_data = img_result.GetNDArray()
                    self.current_image = img_data

            except PySpin.SpinnakerException as ex:
                self.cam.EndAcquisition()
                raise ex

            except MemoryError:
                pass

        self.cam.GetNextImage()
        self.cam.EndAcquisition()
        self.wait_to_end = False

    def _setup_camera(self):
        cam_list = self.pyspin_system.GetCameras()
        for i, c in enumerate(cam_list):
            # there will only be one camera for time being
            self.cam_dict[i] = c

        if len(cam_list) == 1:
            cam: PySpin.Camera = self.cam_dict[0]
            cam.Init()
            self.node_map_tl_device = cam.GetTLDeviceNodeMap()
            self.node_map = cam.GetNodeMap()
            # return cam
        elif len(cam_list) < 1:
            return None
        else:
            pass
            # set up event to have user choose camera
            # or have multiple outputs...

        try:  # try the setup, if unsuccessful DeInit() camera to save from power cycling

            # set bufferhandling to NewestOnly
            s_node_map = cam.GetTLStreamNodeMap()
            node_bufferhandling_mode = PySpin.CEnumerationPtr(s_node_map.GetNode('StreamBufferHandlingMode'))
            if not PySpin.IsAvailable(node_bufferhandling_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
                raise PySpin.SpinnakerException('unable to set stream buffer handling mode')

            node_newest_only = node_bufferhandling_mode.GetEntryByName('NewestOnly')
            if not PySpin.IsAvailable(node_newest_only) or not PySpin.IsReadable(node_newest_only):
                raise PySpin.SpinnakerException('unable to set stream buffer handling mode')

            # retrieve and set value from entry node
            node_newest_only_mode = node_newest_only.GetValue()
            node_bufferhandling_mode.SetIntValue(node_newest_only_mode)

            # set camera acquisition mode
            # single frame, multiple frames, continuous
            node_acquisition_mode = PySpin.CEnumerationPtr(self.node_map.GetNode('AcquisitionMode'))
            if not PySpin.IsAvailable(node_acquisition_mode) or not PySpin.IsWritable(node_bufferhandling_mode):
                raise PySpin.SpinnakerException('unable to set acquisition mode to continuous (enum retrieval)')

            node_acquisition_mode_continuous = node_acquisition_mode.GetEntryByName('Continuous')
            if not PySpin.IsAvailable(node_acquisition_mode_continuous) or not PySpin.IsReadable(
                    node_acquisition_mode_continuous):
                raise PySpin.SpinnakerException('unable to set acquisition mode to continuous (entry retieval)')

            # retrieve and set integer value from entry node
            acquisition_mode_continuous = node_acquisition_mode_continuous.GetValue()
            node_acquisition_mode.SetIntValue(acquisition_mode_continuous)

            # set camera pixel format - for color images
            node_pixel_format = PySpin.CEnumerationPtr(self.node_map.GetNode('PixelFormat'))
            if not PySpin.IsAvailable(node_pixel_format) or not PySpin.IsWritable(node_pixel_format):
                raise PySpin.SpinnakerException('unable to set pixel format to BayerRG8')

            node_pixel_format_value = node_pixel_format.GetEntryByName('BGR8')
            # node_pixel_format_value = node_pixel_format.GetEntryByName('Mono8')
            if not PySpin.IsAvailable(node_pixel_format_value) or not PySpin.IsReadable(node_pixel_format_value):
                raise PySpin.SpinnakerException('unable to set pixel format to BayerRG8')

            pixel_format_value = node_pixel_format_value.GetValue()
            node_pixel_format.SetIntValue(pixel_format_value)

            # set height and width value to ROI
            node_width = PySpin.CIntegerPtr(self.node_map.GetNode('Width'))
            node_height = PySpin.CIntegerPtr(self.node_map.GetNode('Height'))

            if not PySpin.IsAvailable(node_height) or not PySpin.IsAvailable(node_width):
                raise PySpin.SpinnakerException('height and width nodes not available')

            if not PySpin.IsWritable(node_height) or not PySpin.IsWritable(node_width):
                raise PySpin.SpinnakerException('height or width nodes not writable')

            node_width_value = 1024
            node_height_value = 760
            node_width.SetValue(node_width_value)
            node_height.SetValue(node_height_value)

            # set ROI offset area
            node_offset_x = PySpin.CIntegerPtr(self.node_map.GetNode('OffsetX'))
            node_offset_y = PySpin.CIntegerPtr(self.node_map.GetNode('OffsetY'))

            if not PySpin.IsAvailable(node_offset_x) or not PySpin.IsWritable(node_offset_x):
                raise PySpin.SpinnakerException('x offset node not available')

            if not PySpin.IsAvailable(node_offset_y) or not PySpin.IsWritable(node_offset_y):
                raise PySpin.SpinnakerException('y offset node not available')

            # node_offset_x_value = int(node_width_value / 2)
            # node_offset_y_value = int(node_height_value / 2)
            node_offset_x_value = int((4000 - node_width_value) / 2)
            node_offset_y_value = int((3000 - node_height_value) / 2)
            node_offset_x.SetValue(node_offset_x_value)
            node_offset_y.SetValue(node_offset_y_value)

            return cam

        except PySpin.SpinnakerException as ex:
            print(ex)
            cam.DeInit()

            return False
