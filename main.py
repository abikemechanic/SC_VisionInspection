import PyQt5
from PIL import Image
import cv2 as cv
import time
import datetime
import pytesseract
from simple_pyspin import Camera

if __name__ == '__main__':
    # cam = Camera()
    # cam.start()
    last_image_time = time.time()
    # pytesseract.pytesseract.tesseract_cmd = 'E:\\Tesseract\\tesseract'
    #
    # while cam.current_image is None:
    #     print('no image yet')
    #     time.sleep(1)

    cam = Camera()
    cam.init()
    print(cam.SensorWidth)
    print(cam.SensorHeight)

    cam.PixelFormat = 'BayerRG8'

    cam.Width = 4000
    cam.Height = 2000
    cam.OffsetX = 0
    cam.OffsetY = 250

    cam.GainAuto = 'Off'
    cam.Gain = min(7, cam.get_info('Gain')['max'])
    cam.ExposureAuto = 'Off'
    cam.ExposureTime = 10000

    cam.start()
    img_count = 0
    vw = cv.VideoWriter('small_coil.avi', cv.VideoWriter_fourcc('M', 'J', 'P', 'G'), 32, (4000, 2000))
    vid_frames = 0
    record = False
    while 1:
        img = cam.get_array()
        new_img_height = int(img.shape[0] * 0.3)
        new_img_width = int(img.shape[1] * 0.3)

        img = cv.resize(img, (new_img_width, new_img_height), interpolation=cv.INTER_AREA)
        # img = cv.Canny(img, 100, 101)

        # boxes = pytesseract.image_to_data(img)
        # box_list = boxes.split('\n')
        # for b in box_list[1:]:
        #     b = b.split('\t')
        #     if len(b) > 11:
        #         t = b[-1].split()
        #         if len(t) <= 0:
        #             continue
        #         img = cv.rectangle(img, (int(b[6]), int(b[7])), (int(b[6]) + int(b[8]), int(b[7]) + int(b[9])),
        #                            (0, 0, 255), 3)

        k = cv.waitKey(1)
        cv.imshow('test image', img)
        if k == ord('q'):
            break
        elif k == ord('s'):
            cv.imwrite('save_img_{}.jpg'.format(img_count), img)
            img_count += 1
        elif k == ord('a') or record:
            record = True
            if vid_frames < 250:
                vid_frames += 1
                vw.write(img)
                print('recording, frame: {}'.format(vid_frames))
            if vid_frames == 250:
                record = False
                vw.release()
                print('finished recording')

        image_time = time.time()
        time_delta = image_time - last_image_time
        last_image_time = image_time

    cam.close()
    cv.destroyAllWindows()