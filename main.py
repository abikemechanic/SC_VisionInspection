import PyQt5
import pyspin.PySpin as PySpin
from PIL import Image
from image_acquisition import Camera
import cv2 as cv
import time
import pytesseract

if __name__ == '__main__':
    cam = Camera()
    cam.start()
    last_image_time = time.time()
    pytesseract.pytesseract.tesseract_cmd = 'E:\\Tesseract\\tesseract'

    while cam.current_image is None:
        print('no image yet')
        time.sleep(1)

    while 1:
        img = cam.current_image
        cam.current_image = None
        if img is None:
            time.sleep(.02)
            continue

        boxes = pytesseract.image_to_data(img)
        box_list = boxes.split('\n')
        for b in box_list[1:]:
            b = b.split('\t')
            print(b)
            if len(b) > 11:
                img = cv.rectangle(img, (int(b[6]), int(b[7])), (int(b[6]) + int(b[8]), int(b[7]) + int(b[9])),
                                   (0, 0, 255), 3)

        cv.imshow('test image', img)
        if cv.waitKey(1) == ord('q'):
            break

        image_time = time.time()
        time_delta = image_time - last_image_time
        print('fps = {:.0f}'.format(1 / time_delta))
        last_image_time = image_time

    cam.end_camera = True
