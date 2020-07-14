import PyQt5
import pyspin.PySpin as PySpin
from PIL import Image


if __name__ == '__main__':
    pyspin_sys = PySpin.System.GetInstance()
    cam_list = pyspin_sys.GetCameras()
    cam_dict = []
    node_map = ''
    node_map_tl_device = ''
    last_image_capture_time = 0
    current_image_capture_time = 0

    for i, c in enumerate(cam_list):
        cam_dict[i] = c

    if len(cam_list) > 1:
        cam: PySpin.Camera = cam_dict[0]
        cam.Init()
        node_map_tl_device = cam.GetTLDeviceNodeMap()
        node_map = cam.GetNodeMap()

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

            node_pixel_format_value = node_pixel_format.GetEntryByName('RGB8Packed')
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

            node_width_value = 2000
            node_height_value = 1500
            node_width.SetValue(node_width_value)
            node_height.SetValue(node_height_value)

            # set ROI offset area
            node_offset_x = PySpin.CIntegerPtr(self.node_map.GetNode('OffsetX'))
            node_offset_y = PySpin.CIntegerPtr(self.node_map.GetNode('OffsetY'))

            if not PySpin.IsAvailable(node_offset_x) or not PySpin.IsWritable(node_offset_x):
                raise PySpin.SpinnakerException('x offset node not available')

            if not PySpin.IsAvailable(node_offset_y) or not PySpin.IsWritable(node_offset_y):
                raise PySpin.SpinnakerException('y offset node not available')

            node_offset_x_value = int(node_width_value / 2)
            node_offset_y_value = int(node_height_value / 2)
            node_offset_x.SetValue(node_offset_x_value)
            node_offset_y.SetValue(node_offset_y_value)

        except PySpin.SpinnakerException as ex:
            print(ex)
            cam.DeInit()
            pass


