"""
An experiment.
Can a computer generate a movie from random youtube videos and it will still have a narrative?
"""

import json
import os
import shutil
import sys
from multiprocessing import freeze_support, Pool, Lock, Process
from random import randint, choice
from subprocess import TimeoutExpired
from time import sleep

import ffmpeg
from googleapiclient.discovery import build
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from pafy import pafy
from random_word import RandomWords
from tqdm import tqdm

from constants import *


class YouTubeSingleton():

    def __init__(self):
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        self.video_links = {}
        # Add video links from video txt file
        if os.path.exists(VIDEO_DATABASE):
            if os.stat(VIDEO_DATABASE).st_size != 0:
                with open(VIDEO_DATABASE, 'r') as f:
                    self.video_links = json.load(f)
        else:
            with open(VIDEO_DATABASE, 'w+') as f:
                pass

    def youtube_search(self, word):
        """
        Generates a random word and searches it on YouTube. Picks one video from the search query randomly
        :return: A YouTube video link suffix
        """
        videos = []
        if word in self.video_links:
            video_log_lock.acquire()
            videos = self.video_links[word]
            video_log_lock.release()
        else:
            try:
                search_response = self.youtube.search().list(
                    part=SNIPPET,
                    maxResults=MAX_RESULTS,
                    type=VIDEO,
                    q=word
                ).execute()

                # Filters - only videos
                for search_result in search_response.get('items', []):
                    if search_result['id']['kind'] == 'youtube#video':
                        videos.append('%s' % (search_result['id']['videoId']))

                video_log_lock.acquire()
                # open file in append mode
                with open(VIDEO_DATABASE, 'w+') as fp:
                    self.video_links[word] = self.video_links.get(word, []) + videos
                    json.dump(self.video_links, fp)
                video_log_lock.release()

            except Exception as e:
                print("inside youtube_search")  # TODO Add more precise exceptions!
                print(e)
                # When an execution is made - use the database of videos
                video_log_lock.acquire()
                word, videos = choice(list(self.video_links.values()))
                video_log_lock.release()

        return videos[randint(0, len(videos) - 1)]


# def choose_video_length(elapsed_percentage):
#     """
#     Chooses a video length according to custom mathematical function according to the already elapsed percentage
#     :param elapsed_percentage: int - the elapsed percentage of the video length that was sent to the process pool
#     :return: video_length - float, updated elapsed percentage - float
#     """
#     if 0 <= elapsed_percentage <= FIRST_PHASE_PRECENTAGE:
#         video_length = -0.2 * elapsed_percentage + 15
#         video_length = max(FIRST_PHASE_MIN_LENGTH, video_length)
#     elif FIRST_PHASE_PRECENTAGE < elapsed_percentage <= SECOND_PHASE_PERCENTAGE:
#         video_length = uniform(MIN_SECOND_PHASE_LEN, MAX_SECOND_PHASE_LEN)
#     else:
#         video_length = uniform(MIN_THIRD_PHASE_LEN, MAX_THIRD_PHASE_LEN)
#     elapsed_percentage += video_length * 100 / TOTAL_TIME
#     return video_length, elapsed_percentage


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


def download_youtube_video(video_file_name, video_file_path, video_length, word=None):
    """
    Downloads and resizes a YouTube video.
    :param video_file_name: video file name - string
    :param video_file_path: video file path - string
    :param video_length: Length of video in seconds - float
    """
    youtube_url = YOUTUBE_PREFIX + youtube_singleton.youtube_search(word)
    stream_url = pafy.new(youtube_url).getbest().url
    retry_count = 0
    while retry_count <= MAX_RETRY_COUNT:
        try:
            if not ffmpeg_download(stream_url, video_file_path, video_length):
                retry_count += 1
                continue
            check_file_integrity(video_file_name, TEMP_DIRECTORY)
            resize_video_file(video_file_name, video_file_path)
            check_file_integrity(video_file_name, CONVERTED_DIRECTORY)
            break
        except Exception as e:  # TODO check for type of exceptions!!!! There are a lot of them
            print("inside download_youtube_video")
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


def ffmpeg_download(stream_url, video_file_path, time_of_video):
    """
    Picks and downloads a YouTube video with ffmpeg until timeout
    :param video_file_path: YouTube video download file name as a string
    :param time_of_video: length of the video in float
    :return: True if downloaded successfully, false otherwise.
    """
    download_video_from_youtube = (
        ffmpeg.input(stream_url, t=time_of_video).output(video_file_path, f=VIDEO_CONTAINER, acodec=ACODEC,
                                                         vcodec=OUTPUT_CODEC,
                                                         loglevel=LOGLEVEL).overwrite_output().run_async())
    try:
        download_video_from_youtube.wait(MAX_TIMEOUT_LEN)
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
    videos_in_folder = [video_clips_path + "\\" + f for f in os.listdir(video_clips_path)]
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


# def create_video_download_jobs(pool, func):
#     """
#     Picks the video length and creates download jobs for the process pool.
#     :param pool: Process pool instance
#     :return: A list of all the jobs that were made, the total number of videos that will be downloaded
#     """
#     num_of_video = 0
#     total_per = 0
#     working_jobs = []
#     while total_per < 100:
#         video_file_name = str(num_of_video) + VIDEO_EXTENSION
#         video_length, total_per = choose_video_length(total_per)
#         video_file_path = TEMP_DIRECTORY + "\\" + video_file_name
#         working_jobs.append(pool.apply_async(func, (video_file_name, video_file_path, video_length)))
#         num_of_video += 1
#         video_length_choose_progress_bar(num_of_video, total_per)
#     return working_jobs, num_of_video

def create_video_download_jobs(pool, func):
    """
    Picks the video length and creates download jobs for the process pool.
    :param pool: Process pool instance
    :return: A list of all the jobs that were made, the total number of videos that will be downloaded
    """
    num_of_video = 0
    working_jobs = []
    words = RandomWords().get_random_words(limit=10)
    num = str(len([name for name in os.listdir(OUTPUT_DIRECOTRY)]))
    with open(OUTPUT_DIRECOTRY + 'sentence' + str(len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + '.txt',
              'w+') as f:
        for word in words:
            f.write(word)
            f.write(" ")
    for word in words:
        video_file_name = str(num_of_video) + VIDEO_EXTENSION
        video_length = 0.5 * len(word)
        video_file_path = TEMP_DIRECTORY + "\\" + video_file_name
        working_jobs.append(pool.apply_async(func, (video_file_name, video_file_path, video_length, word)))
        num_of_video += 1

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


def init_child(lock_, youtube_singleton_):
    global video_log_lock, youtube_singleton
    video_log_lock = lock_
    youtube_singleton = youtube_singleton_


def start_process_pool():
    """
    Starts a process pool and gives it videos to download
    """
    create_output_dir()
    lock = Lock()
    youtube_singleton_ = YouTubeSingleton()

    with Pool(processes=NUM_OF_PROCESSES, initializer=init_child, initargs=(lock, youtube_singleton_)) as pool:
        working_jobs, num_of_video = create_video_download_jobs(pool, download_youtube_video)
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
    print(START_MSG)
    download_videos()
    print(MAKING_MASTER_VIDEO_TXT)
    concatenate(CONVERTED_DIRECTORY, OUTPUT_DIRECOTRY + NAME_OF_FINAL_PRODUCT + str(
        len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + VIDEO_EXTENSION)
    print(FINISHED_MESSAGE)
    path = os.path.realpath(OUTPUT_DIRECOTRY)
    os.startfile(path)
    exit(0)
