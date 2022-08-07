"""

An experiment.
Can a computer generate a movie from random youtube videos and it will still have a narrative?

"""

import os
import os.path
import shutil
import sys
from multiprocessing import Pool
from multiprocessing import Process
from multiprocessing import freeze_support
from os import listdir
from random import uniform
from subprocess import TimeoutExpired
from time import sleep

import ffmpeg
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from pafy import pafy
from tqdm import tqdm

import youtube_singleton
from constants import *


def choose_video_length(elapsed_percentage):
    """
    Chooses a video length according to custom mathematical function according to the already elapsed percentage
    :param elapsed_percentage: int - the elapsed percentage of the video length that was sent to the process pool
    :return: video_length - float, updated elapsed percentage - float
    """
    if 0 <= elapsed_percentage <= FIRST_PHASE_PRECENTAGE:
        video_length = -0.2 * elapsed_percentage + 15
        video_length = max(FIRST_PHASE_MIN_LENGTH, video_length)
    elif FIRST_PHASE_PRECENTAGE < elapsed_percentage <= SECOND_PHASE_PERCENTAGE:
        video_length = uniform(MIN_SECOND_PHASE_LEN, MAX_SECOND_PHASE_LEN)
    else:
        video_length = uniform(MIN_THIRD_PHASE_LEN, MAX_THIRD_PHASE_LEN)
    elapsed_percentage += video_length * 100 / TOTAL_TIME
    return video_length, elapsed_percentage


def video_length_choose_progress_bar(v_counter, per_total_len):
    """
    A progress bar for the video length selector.
    :param v_counter: Counter of how many videos were sent to download - int
    :param per_total_len: total elapsed percentage of the length of the videos - float
    """
    sleep(0.1)
    sys.stdout.write('\r')
    sys.stdout.write(PROGRESS_BAR_FORMAT_TXT.format(v_counter, per_total_len))
    sys.stdout.flush()


def download_youtube_video(video_file_name, video_file_path, video_length):
    """
    Downloads and resizes a yotube video.
    :param video_file_name: video file name - string
    :param video_file_path: video file path - string
    :param video_length: Length of video in seconds - float
    """
    retry_count = 0
    while retry_count <= MAX_RETRY_COUNT:
        try:
            if not pick_n_down_video(video_file_path, video_length):
                retry_count += 1
                continue
            check_file_integrity(video_file_name, TEMP_DIRECTORY)
            resize_video_file(video_file_name, video_file_path)
            check_file_integrity(video_file_name, CONVERTED_DIRECTORY)
            break
        except Exception as e:  # TODO check for type of exceptions!!!! There are a lot of them
            print(e)
            retry_count += 1
            continue


def check_file_integrity(file_name, folder_path):
    """
    A basic check for a file - see if it opens.
    :param file_name: file name - string
    :param folder_path: folder path - string
    """
    file = open(folder_path + '\\' + file_name, READ_MODE)
    file.close()


def resize_video_file(video_file_name, video_file_path):
    """
    Resize a video file and saves it.
    :param video_file_name: video file name - string
    :param video_file_path: video file path - string
    """
    clip = VideoFileClip(video_file_path)
    clip = resize(clip, height=RESIZE_HEIGHT)
    clip.write_videofile(CONVERTED_DIRECTORY + '\\' + video_file_name, verbose=False, logger=None)
    clip.close()


def pick_n_down_video(video_file_path, time_of_video):
    """
    Picks and downloads a YouTube video with ffmpeg until timeout
    :param video_file_path: YouTube video download file name as a string
    :param time_of_video: length of the video in float
    :return: True if downloaded successfully, false otherwise.
    """
    youtube_url = YOUTUBE_PREFIX + youtube_singleton.YouTubeSingleton().youtube_search()
    stream_url = pafy.new(youtube_url).getbest().url
    download_video_from_youtube = (
        ffmpeg.input(stream_url, t=time_of_video).output(video_file_path, f=VIDEO_CONTAINER, acodec=ACODEC,
                                                         vcodec=OUTPUT_CODEC,
                                                         loglevel=LOGLEVEL).overwrite_output().run_async())
    try:
        download_video_from_youtube.wait(max(MIN_TIMEOUT_LEN, time_of_video * 5))
        file = open(video_file_path, READ_MODE)  # Used to check if corrupted download
        file.close()
        return True
    except TimeoutExpired:
        # print("Timeout " + out_filename)
        return False
    except FileNotFoundError:
        return False


def concatenate(video_clips_path, output_path):
    """
    Concatenate video together
    :param video_clips_path: Path to folder of videos
    :param output_path: output path of the final video
    """
    # create VideoFileClip object for each video file
    videos_in_folder = [video_clips_path + "\\" + f for f in listdir(video_clips_path)]
    clips = []
    for video in videos_in_folder:
        try:
            clip = VideoFileClip(video)
            clips.append(clip)
        except OSError as e:  # Skips broken videos
            continue
    final_clip = concatenate_videoclips(clips, method=CONCATENATE_METHOD)
    # write the output video file
    final_clip.write_videofile(output_path, codec=OUTPUT_CODEC)


def download_progress_bar(num_of_video, working_jobs):
    """
    A progress bar of all the video downloads.
    As a timeout of MASTER_DOWNLOAD_TIMEOUT length.
    :param num_of_video: Total number of video that will be downloaded
    :param working_jobs: A list of all the jobs in the process pool
    """
    num_of_finished_jobs = 0
    sec_count = 0
    with tqdm(total=num_of_video, desc=TQDM_DOWNLOAD_DESC) as pbar:
        while True:
            if sec_count >= MASTER_DOWNLOAD_TIMEOUT:
                print(TERMINATING_DOWN_MESSAGE)
                break
            finished_jobs = [job for job in working_jobs if job.ready()]
            num_of_finished_len = len(finished_jobs)
            pbar.update(num_of_finished_len - num_of_finished_jobs)
            num_of_finished_jobs = num_of_finished_len
            if len(working_jobs) == num_of_finished_jobs:
                print(FINISHED_DOWNLOAD_MSG)
                break
            sleep(TQDM_SLEEP_DUR)
            sec_count += TQDM_SLEEP_DUR


def create_video_download_jobs(pool):
    """
    Picks the video length and creates download jobs for the process pool.
    :param pool: Process pool instance
    :return: A list of all the jobs that were made, the total number of videos that will be downloaded
    """
    num_of_video = 0
    total_per = 0
    working_jobs = []
    while total_per < 100:
        video_file_name = str(num_of_video) + VIDEO_EXTENSION
        video_length, total_per = choose_video_length(total_per)
        video_file_path = TEMP_DIRECTORY + "\\" + video_file_name
        working_jobs.append(pool.apply_async(download_youtube_video, (video_file_name, video_file_path, video_length)))
        num_of_video += 1
        video_length_choose_progress_bar(num_of_video, total_per)
    return working_jobs, num_of_video


def create_output_dir():
    """
    Creates a temp directory and a converted video directory.
    """
    if os.path.exists(TEMP_DIRECTORY):
        shutil.rmtree(TEMP_DIRECTORY)
    os.makedirs(TEMP_DIRECTORY)
    if os.path.exists(CONVERTED_DIRECTORY):
        shutil.rmtree(CONVERTED_DIRECTORY)
    os.makedirs(CONVERTED_DIRECTORY)


def start_process_pool():
    """
    Starts a process pool and gives it videos to download
    """
    create_output_dir()
    with Pool(processes=NUM_OF_PROCESSES) as pool:
        working_jobs, num_of_video = create_video_download_jobs(pool)
        print('\n')
        sys.stdout.flush()
        download_progress_bar(num_of_video, working_jobs)
        pool.terminate()
        pool.join()


def download_videos():
    """
    Opens a subprocess that downloads YouTube videos
    """
    video_from_internet_method = Process(target=start_process_pool, daemon=False)
    video_from_internet_method.start()
    video_from_internet_method.join()
    video_from_internet_method.terminate()


if __name__ == '__main__':
    freeze_support()  # used for multiprocessing
    # load_dotenv()  # used for API key
    print(START_MSG)
    download_videos()
    print(MAKING_MASTER_VIDEO_TXT)
    concatenate(CONVERTED_DIRECTORY, OUTPUT_DIRECOTRY + NAME_OF_FINAL_PRODUCT + str(
        len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + VIDEO_EXTENSION)
    print(FINISHED_MESSAGE)
    # input('WRITE ME A STORY TO FINISH AND PRESS ENTER: ')
    path = os.path.realpath(OUTPUT_DIRECOTRY)
    os.startfile(path)
    exit(0)
