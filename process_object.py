import cv2
import time
import sys
import os
import datetime

this = sys.modules[__name__]
this.out = None
this.timeout = None
this.captured_folder = 'captured/'
this.capturing = False

# print(cv2.__version__)
# print(os.uname(), os.uname()[4])

def process_object(obj, image, fps=3):
    label = obj.class_id
    confidence = obj.confidence

    if confidence > 0.5:
        if label == 15:
            print(label, confidence)

            if this.out is None:
                print('Create Writer')
                # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                this.out = cv2.VideoWriter('output.mp4', fourcc, fps, (320, 240), isColor=True)
                this.timeout = time.time() + 5

    if this.out is not None:
        if time.time() > timeout:
            print('Done')
            this.out.release()
            this.out = None
            this.timeout = None
        else:
            print('Write Image')
            this.out.write(image)

def process_object_2(obj, image):
    label = obj.class_id
    confidence = obj.confidence

    if confidence > 0.5:
        if label == 15:
            print(label, confidence)

            if not this.capturing:
                this.capturing = True
                save_image(image)
                save_video()
                this.capturing = False

            # if this.out is None:
                # print('Create Writer')
                # # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                # this.out = cv2.VideoWriter('output.mp4', fourcc, fps, (320, 240), isColor=True)
                # this.timeout = time.time() + 5

def save_image(image):
    date = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    cv2.imwrite(os.path.join(this.captured_folder, 'image_%s_.jpg' %date), image)
    print("Done: Save Image")

def save_video():
    camera_width = 640
    camera_height = 480

    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FPS, 30)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, camera_width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, camera_height)

    fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
    date = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    fps = 30

    this.out = cv2.VideoWriter(os.path.join(this.captured_folder, 'cap_%s_.mp4' %date), fourcc, fps, (camera_width, camera_height), isColor=True)
    this.timeout = time.time() + 5

    if cap.isOpened:
        print('Write Video')

        while time.time() < this.timeout:
            ret, image = cap.read()
            this.out.write(image)

        print('Done')
        this.out.release()
        this.out = None
        this.timeout = None
