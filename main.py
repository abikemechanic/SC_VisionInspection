from PyQt5 import QtWidgets
import sys
from PIL import Image
import cv2 as cv
import numpy as np
import time
import datetime
import pytesseract
import UI.main_window

app = QtWidgets.QApplication(sys.argv)
window = UI.main_window.MainWindow()
window.show()
sys.exit(app.exec_())



def transform_image(image):
    # img_h = int(image.shape[0] * 0.35)
    # img_w = int(image.shape[1] * 0.35)
    #
    # image = cv.resize(image, (img_w, img_h), interpolation=cv.INTER_AREA)

    # blur image
    image = cv.bilateralFilter(image, 3, 75, 75)

    # threshold image
    image = cv.adaptiveThreshold(image, 255, cv.ADAPTIVE_THRESH_GAUSSIAN_C,
                                 cv.THRESH_BINARY, 7, 4)

    # filter horizontal lines
    vert_size = 5
    vert_struct = cv.getStructuringElement(cv.MORPH_RECT, (1, vert_size))
    image = cv.erode(image, vert_struct)
    image = cv.dilate(image, vert_struct)

    # enlarge spring edges
    kernel_size = 3
    ker = np.ones((kernel_size, kernel_size), np.uint8)
    image = cv.erode(image, ker, iterations=1)
    # image = cv.dilate(image, ker, iterations=3)

    return image


def calculate_threshold(image):
    max_pix = image.shape[0] * image.shape[1]
    return (cv.countNonZero(image) / max_pix) * 100


# if __name__ == '__main__':
#     last_image_time = time.time()
#     img_count = 0
#     vw = cv.VideoWriter('small_coil.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 32, (4000, 2000))
#     vid_frames = 0
#     record = False
#
#     flir_camera = flir_camera_controller.CameraController()
#     flir_camera.start()
#
#     threshold_level = 0
#     time_delta = 0
#     i = 0
#
#     while 1:
#         img = flir_camera.current_image
#         if img is None:
#             continue
#
#         inspection_area = img[700:1000, 2800:2850]
#
#         cv.rectangle(img, (2800, 700), (2850, 1000), (255, 255, 255), 3)
#
#         img_h = int(img.shape[0] * 0.35)
#         img_w = int(img.shape[1] * 0.35)
#
#         inspection_area = transform_image(inspection_area)
#
#         current_level = calculate_threshold(inspection_area)
#
#         # TESSERACT INFORMATION
#
#         # boxes = pytesseract.image_to_data(img)
#         # box_list = boxes.split('\n')
#         # for b in box_list[1:]:
#         #     b = b.split('\t')
#         #     if len(b) > 11:
#         #         t = b[-1].split()
#         #         if len(t) <= 0:
#         #             continue
#         #         img = cv.rectangle(img, (int(b[6]), int(b[7])), (int(b[6]) + int(b[8]), int(b[7]) + int(b[9])),
#         #                            (0, 0, 255), 3)
#
#         _img = cv.copyTo(img, None)
#         _img[700:1000, 2800:2850] = inspection_area
#         _img = cv.resize(_img, (img_w, img_h), interpolation=cv.INTER_AREA)
#
#         k = cv.waitKey(1)
#         cv.imshow('raw image', _img)
#         # cv.imshow('inspection image', inspection_area)
#         if k == ord('q'):
#             break
#         elif k == ord('s'):
#             cv.imwrite('save_img_{}.jpg'.format(img_count), img)
#             img_count += 1
#         elif k == ord('a') or record:
#             record = True
#             if vid_frames < 250:
#                 vid_frames += 1
#                 vw.write(img)
#                 print('recording, frame: {}'.format(vid_frames))
#             if vid_frames == 250:
#                 record = False
#                 vw.release()
#                 print('finished recording')
#         elif k == ord('l'):
#             threshold_level = current_level
#
#         if current_level <= threshold_level:
#             print('found spring')
#
#         i += 1
#         image_time = time.time()
#         time_delta += image_time - last_image_time
#         last_image_time = image_time
#         if i > 100:
#             time_delta = time_delta / 100
#             print('fps: {:.3f}'.format(1 / time_delta))
#             i = 0
#
#         del img
#
#     flir_camera.end_camera = True
#     cv.destroyAllWindows()



