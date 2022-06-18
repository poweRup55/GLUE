import random
from os import listdir
from os.path import isfile, join

import cv2
import numpy as np
from scipy.signal import fftconvolve

VIDEO_SIZE = (1920, 1080)

FPS = 25

MAX_BYTE_SIZE = 255
REMEMBER_COEFFICIENT = 25
INPUT_PATH = "input"
COEFFCIENT_DECAY = 0.2
STEPS = 12
MAX_FRAMES = 500
TEST_FRAME = REMEMBER_COEFFICIENT * STEPS
RANDOM = True
CHANCE = 1 / 12
GLOW = True

STORY = True
VIDEO_LENGTH = 4  # In minutes
VIDEO_LENGTH_IN_FRAMES = int(VIDEO_LENGTH * 60 * FPS)


# def timing(f):
#     @wraps(f)
#     def wrap(*args, **kw):
#         ts = time()
#         result = f(*args, **kw)
#         te = time()
#         print('func:%r took: %2.4f sec' % (f.__name__, te - ts))
#         return result
#
#     return wrap


def choose_input_file():
    files = [f for f in listdir(INPUT_PATH) if isfile(join(INPUT_PATH, f))]
    print("Choose a file to do the thingy\\n")
    for i in range(len(files)):
        print(str(i + 1) + '. ' + files[i])
    while True:
        choice = input("Enter the number of the file: ")
        if choice.isdigit():
            choice = int(choice) - 1
            if 0 <= choice <= len(files) - 1:
                return files[choice]
            print("WRONG INPUT MOFO")


def main_loop(video, result):
    shape_of_image_in_vid = VIDEO_SIZE
    remember_mat = np.zeros(shape_of_image_in_vid).astype(np.float32)
    if COEFFCIENT_DECAY == 0:
        remember_coefficient_mat = np.repeat(1, REMEMBER_COEFFICIENT).astype(np.float32)
    else:
        remember_coefficient_mat = np.arange(0, COEFFCIENT_DECAY,
                                             float(1 / REMEMBER_COEFFICIENT) * COEFFCIENT_DECAY, dtype=np.float32)
    prev_pics = np.zeros((shape_of_image_in_vid + (REMEMBER_COEFFICIENT,))).astype(np.float32)
    frame_count = 0
    while video.isOpened() and frame_count != MAX_FRAMES:
        ret, in_frame = video.read()
        if ret:
            # Display the resulting frame
            in_frame = in_frame.astype(np.float32) / MAX_BYTE_SIZE
            out_frame = in_frame + remember_mat
            if GLOW:
                out_frame = fftconvolve(out_frame, (1 / 15) * np.random.random((5, 5, 3)), 'same')
            out_frame = np.round(np.clip(out_frame, 0, 1) * MAX_BYTE_SIZE).astype(np.uint8)
            result.write(out_frame)
            cv2.imshow('frame', out_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            if RANDOM:
                if random.randint(0, int(1 / CHANCE)) == int(1 / CHANCE):
                    remember_mat, prev_pics = add_to_output(in_frame, prev_pics, remember_coefficient_mat)
            else:
                if frame_count % STEPS == 0:
                    remember_mat, prev_pics = add_to_output(in_frame, prev_pics, remember_coefficient_mat)
            frame_count += 1
        # Break the loop
        else:
            break
    video.release()


def add_to_output(in_frame, prev_pics, remember_coefficient_mat):
    if COEFFCIENT_DECAY == 0:
        prev_pics = change_last(in_frame, prev_pics)
        prev_pics = roll(prev_pics)
        remember_mat = np.sum(prev_pics, axis=3)
    else:
        prev_pics = change_last(in_frame, prev_pics)
        prev_pics = roll(prev_pics)
        remember_mat = remember_mat_create(prev_pics, remember_coefficient_mat)
    return remember_mat, prev_pics


# @timing
def remember_mat_create(prev_pics, remember_coefficient_mat):
    remember_mat = np.matmul(prev_pics, np.flip(remember_coefficient_mat))
    return remember_mat


# @timing
def change_last(in_frame, prev_pics):
    prev_pics[:, :, :, -1] = in_frame
    return prev_pics


# @timing
def roll(prev_pics):
    prev_pics = np.roll(prev_pics, 1)
    return prev_pics


def main():
    out_filename = str(COEFFCIENT_DECAY) + "_" + str(REMEMBER_COEFFICIENT) + '_' + str(
        STEPS) + ("Rand" if RANDOM else "") + ("Glow" if GLOW else "") + '.mp4'

    if not STORY:
        in_filename = choose_input_file()
        out_filename = in_filename[0:10] + "_" + out_filename
        in_filename_path = INPUT_PATH + "\\" + in_filename
        video = cv2.VideoCapture(in_filename_path)
        if not video.isOpened():
            print("\nError opening video stream or file")
            exit(1)
        result = cv2.VideoWriter(out_filename,
                                 cv2.VideoWriter_fourcc(*'avc1'),
                                 FPS, VIDEO_SIZE)
        main_loop(video, result)
        result.release()
        # Closes all the frames
        cv2.destroyAllWindows()
        exit(0)


if __name__ == '__main__':
    main()
