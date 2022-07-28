"""

An experiment.
Can a computer generate a movie from random youtube videos and it will still have a narrative?

"""

import os
import os.path
import shutil
import sys
from math import ceil
from multiprocessing import Pool
from multiprocessing import Process
from multiprocessing import freeze_support
from os import listdir
from random import uniform
from subprocess import TimeoutExpired
from time import sleep

import ffmpeg
from dotenv import load_dotenv
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from pafy import pafy
from tqdm import tqdm

import youtube_singleton

MASTER_DOWNLOAD_TIMEOUT = 5 * 60

OUTPUT_DIRECOTRY = "output"
FPS = 25
VIDEO_SIZE = (1920, 1080)
MAX_BYTE_SIZE = 255
MINUTES = 1
SECONDS = 30
TOTAL_TIME = MINUTES * 60 + SECONDS
TEMP_DIRECTORY = OUTPUT_DIRECOTRY + "\\temp"
CONVERTED_DIRECTORY = OUTPUT_DIRECOTRY + "\\conversion"


def choose_video_time(elapsed_percentage):
    if 0 <= elapsed_percentage <= 60:
        time = -0.2 * elapsed_percentage + 15
        time = max(0.04, time)
    elif 60 < elapsed_percentage <= 80:
        time = uniform(0.04, 0.12)
    else:
        time = quarter(uniform(5, 7))
    elapsed_percentage += time * 100 / TOTAL_TIME
    return time, elapsed_percentage


def quarter(x):
    return ceil(x * 4) / 4


def progress_bar(i, j):
    sleep(0.1)
    sys.stdout.write('\r')
    sys.stdout.write("Downloading queue: " + str(i) + " which are: " + str(j) + ' of the video')
    sys.stdout.flush()


def start_sub_process(file_name, out_filename, video_length):
    """

    :param file_name:
    :param out_filename:
    :param video_length:
    :return:
    """
    retry_count = 0
    while retry_count >= 10:
        try:
            if not get_video_from_youtube(out_filename, video_length):
                retry_count += 1
                continue
            convert_video_file(file_name, out_filename)
            check_file_integrity(file_name)
        except Exception as e:  # TODO check for type of exceptions!!!!
            # print(e, "\n ....................................Retrying!")
            retry_count += 1
            continue


def check_file_integrity(file_name):
    file = open(CONVERTED_DIRECTORY + '\\' + file_name, 'r')
    file.close()


def convert_video_file(file_name, out_filename):
    clip = VideoFileClip(out_filename)
    clip = resize(clip, height=1080)
    clip.write_videofile(CONVERTED_DIRECTORY + '\\' + file_name, verbose=False, logger=None)
    clip.close()


def get_video_from_youtube(out_filename, time_of_video):
    youtube_url = "https://www.youtube.com/watch?v=" + youtube_singleton.YouTubeSingleton().youtube_search()
    stream_url = pafy.new(youtube_url).getbest().url
    download_video_from_youtube = (
        ffmpeg.input(stream_url, t=time_of_video).output(out_filename, f='mp4', acodec='aac', vcodec='libx264',
                                                         loglevel="quiet").overwrite_output().run_async())
    try:
        download_video_from_youtube.wait(max(20, time_of_video * 3))
        file = open(out_filename, 'r')
        file.close()
        return True
    except TimeoutExpired:
        # print("Timeout " + out_filename)
        return False
    except FileNotFoundError:
        return False


OPENING_SCRIPT = 'Making A Very Coherent Video'


def concatenate(video_clips_path, output_path):
    # create VideoFileClip object for each video file
    files_in_temp = [video_clips_path + "\\" + f for f in listdir(video_clips_path)]
    clips = []
    for file in files_in_temp:
        try:
            clip = VideoFileClip(file)
            clips.append(clip)
        except OSError as e:
            continue
    final_clip = concatenate_videoclips(clips, method="compose")
    # write the output video file
    final_clip.write_videofile(output_path, codec='libx264')


def download_youtube_videos():
    create_output_dir()
    with Pool(processes=8) as pool:
        working_jobs, num_of_video = create_video_download_jobs(pool)
        print('\n')
        sys.stdout.flush()
        download_progress_bar(num_of_video, working_jobs)
        pool.terminate()
        pool.join()


def download_progress_bar(num_of_video, working_jobs):
    num_of_finished_jobs = 0
    sec_count = 0
    with tqdm(total=num_of_video, desc="Number of videos downloaded") as pbar:
        while True:
            if sec_count >= MASTER_DOWNLOAD_TIMEOUT:
                print("Terminating because it is taking too long. Making video now")
                break
            finished_jobs = [job for job in working_jobs if job.ready()]
            num_of_finished_len = len(finished_jobs)
            pbar.update(num_of_finished_len - num_of_finished_jobs)
            num_of_finished_jobs = num_of_finished_len
            if len(working_jobs) == num_of_finished_jobs:
                print("finished downloading all videos!")
                break
            sleep(1)
            sec_count = +1


def create_video_download_jobs(pool):
    num_of_video = 0
    total_per = 0
    working_jobs = []
    while total_per < 100:
        file_name = str(num_of_video) + ".mp4"
        video_length, total_per = choose_video_time(total_per)
        temp_filename = TEMP_DIRECTORY + "\\" + file_name
        working_jobs.append(pool.apply_async(start_sub_process, (file_name, temp_filename, video_length)))
        num_of_video += 1
        progress_bar(num_of_video, total_per)
    return working_jobs, num_of_video


def create_output_dir():
    if os.path.exists(TEMP_DIRECTORY):
        shutil.rmtree(TEMP_DIRECTORY)
    os.makedirs(TEMP_DIRECTORY)
    if os.path.exists(CONVERTED_DIRECTORY):
        shutil.rmtree(CONVERTED_DIRECTORY)
    os.makedirs(CONVERTED_DIRECTORY)


def download_videos():
    video_from_internet_method = Process(target=download_youtube_videos, daemon=False)
    video_from_internet_method.start()
    video_from_internet_method.join()
    video_from_internet_method.terminate()
    print("Finished downloading videos! Making master video")


if __name__ == '__main__':
    freeze_support()  # used for multiprocessing
    load_dotenv()  # loading API key
    print(OPENING_SCRIPT)
    download_videos()
    concatenate(CONVERTED_DIRECTORY, OUTPUT_DIRECOTRY + '\\final' + str(
        len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + '.mp4')
    print('\n \n  FINISHED! \n \n')
    input('WRITE ME A STORY TO FINISH AND PRESS ENTER: ')
    path = os.path.realpath(OUTPUT_DIRECOTRY)
    os.startfile(path)
