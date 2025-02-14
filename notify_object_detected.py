import sys, os, datetime, time
import cv2
import pygame
import asyncio
from threading import Thread
import boto3
from botocore.exceptions import ClientError
from linebot import (LineBotApi)
from linebot.models import (
    TextSendMessage, ImageSendMessage
)
import yaml

secret = None
settings = None

with open("secret.yaml", "r") as stream:
    try:
      secret = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

with open("settings.yaml", 'r') as stream:
    try:
        settings = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

print("Settings", settings)

# parser = argparse.ArgumentParser()
# parser.add_argument(
        # '-classes',
        # '--proceedobjectclasses',
        # dest='proceed_object_classes',
        # type=int,
        # default=15,
        # help='List of object class to be processed (Default=15)',
        # nargs='+'
# )
# args = parser.parse_args()
# proceed_object_classes = args.proceed_object_classes
# print('Proceed Object Classes', proceed_object_classes)

this = sys.modules[__name__]
this.out = None
this.timeout = None
this.captured_folder = 'captured/'
this.capturing = False
this.line_bot_api = LineBotApi(secret["linebot"]["channel_access_token"])
this.my_line_user_id = secret["linebot"]["my_user_id"]
this.s3_client = boto3.client(
        's3',
        aws_access_key_id=secret["s3"]["aws_access_key_id"],
        aws_secret_access_key=secret["s3"]["aws_secret_access_key"])
this.s3_bucket_name = secret["s3"]["bucket_name"]
this.notify_object_labels = settings["notify"]["labels"]

# print(cv2.__version__)
# print(os.uname(), os.uname()[4])

async def sleep(sec):
    await asyncio.sleep(sec)

async def start_capturing_done_in(sec):
    print("Start Capturing..")
    this.capturing = True
    await sleep(sec)
    this.capturing = False
    print("End Capturing")

def start_caturing_cat_loop(image):
    # loop = asyncio.get_event_loop()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = [
            loop.create_task(start_capturing_done_in(10)),
            loop.create_task(play_sound()),
            loop.create_task(save_image_and_notify(image, 'Cat detected!!!'))
    ]

    loop.run_until_complete(asyncio.wait(tasks))

def start_caturing_person_loop(image):
    # loop = asyncio.get_event_loop()

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    tasks = [
            loop.create_task(start_capturing_done_in(30)),
            loop.create_task(save_image_and_notify(image, 'Person detected!'))
    ]

    loop.run_until_complete(asyncio.wait(tasks))

def notify(obj, image):
    label = obj.class_id
    confidence = obj.confidence

    if confidence > 0.5:
        if label in notify_object_labels:
            print(label, confidence)

            if label == 15:
                if not this.capturing:
                    # PhongsakornP. 5 Aug 2019
                    # I had a problem with write video on rasberry pi, it was hang.
                    # Todo: Will solve it later, maybe using async or threads
                    # save_video()

                    this.capturing = True

                    t = Thread(target=start_caturing_cat_loop, args=(image,))
                    t.start()

                # if this.out is None:
                    # print('Create Writer')
                    # # fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                    # fourcc = cv2.VideoWriter_fourcc('M', 'J', 'P', 'G')
                    # this.out = cv2.VideoWriter('output.mp4', fourcc, fps, (320, 240), isColor=True)
                    # this.timeout = time.time() + 5
            elif label == 0:

                if not this.capturing:
                    this.capturing = True
                    t = Thread(target=start_caturing_person_loop, args=(image,))
                    t.start()


async def save_image_and_notify(image, message):
    image_file_name = await save_image(image)
    image_url = await upload_image_s3(image_file_name, image_file_name)
    await send_notify_message(image_url, image_url, message)

async def upload_image_s3(image_file_name, object_name):
    try:
        response = this.s3_client.upload_file(image_file_name, this.s3_bucket_name, object_name)
        presigned_response = await create_presigned_url(this.s3_bucket_name, object_name)

        print("Done > Upload Image To S3")

        return presigned_response;
    except ClientError as e:
        print(e)
        return None

async def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    try:
        response = this.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
        )
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response

async def play_sound():
    pygame.mixer.init()
    pygame.mixer.music.load('sound/dog.mp3')
    pygame.mixer.music.play()
    print('Done > Play Sound')

async def save_image(image):
    date = datetime.datetime.now().strftime("%Y%m%d_%H-%M-%S")
    image_file_name = os.path.join(this.captured_folder, 'image_%s_.jpg' %date)
    cv2.imwrite(image_file_name, image)

    print("Done > Save Image")

    return image_file_name

async def send_notify_message(original_url, preview_url, message):
    imageMessage = ImageSendMessage(original_content_url=original_url, preview_image_url=preview_url)
    textMessage = TextSendMessage(text=message)
    this.line_bot_api.push_message('Ub6d6b3173fd1c3539da659dd58321c72', [textMessage, imageMessage])
    print("Done > Send Notify Message")


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

'''
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
'''
