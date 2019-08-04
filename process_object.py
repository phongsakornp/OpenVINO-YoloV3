import cv2
import time
import sys

this = sys.modules[__name__]
this.out = None
this.timeout = None

def process_object(obj, image):
    label = obj.class_id
    confidence = obj.confidence
    # print(cv2.__version__)

    if confidence > 0.5:
        if label == 15:
            print(label, confidence)

            if this.out is None:
                print('Create Writer')
                # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                fps = 3
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
