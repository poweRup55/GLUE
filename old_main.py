"""
An experiment.
Can a computer generate a movie from random youtube videos and it will still have a narrative?
"""
import datetime
import json
import random
import re
import shutil
import string
from multiprocessing import Lock
from multiprocessing.pool import ThreadPool
from random import choice
from time import sleep

import yt_dlp
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from moviepy.editor import *
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from random_word import RandomWords
from tqdm import tqdm

from constants import *

VIDEO_TO_BE_IN_SECONDS_ = "How long would you like the video to be? (in seconds)\n"


class YouTubeSingleton:

    def __init__(self):
        # print("Creating youtube singelton\n")
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        self.video_links = {}
        self.video_database_lock = Lock()
        # Add video links from video txt file
        if os.path.exists(VIDEO_DATABASE):
            if os.stat(VIDEO_DATABASE).st_size != 0:
                with open(VIDEO_DATABASE, READ_MODE) as f:
                    self.video_links = json.load(f)

    def youtube_search(self, word):
        """
        Generates a random word and searches it on YouTube. Picks one video from the search query randomly
        :return: A YouTube video link suffix
        """
        video_links = []
        word_in_database = False
        self.video_database_lock.acquire()
        if word in self.video_links:
            word_in_database = True
            video_links = self.video_links[word]
        self.video_database_lock.release()
        if not word_in_database:
            video_links = self.search_youtube(video_links, word)

        return choice(video_links)

    def search_youtube(self, video_links, word):
        try:
            # print("searching {} on youtube\n".format(word))
            search_response = self.youtube.search().list(
                part=SNIPPET,
                maxResults=MAX_RESULTS,
                type=VIDEO,
                q=word
            ).execute()

            # Filters - only videos
            for search_result in search_response.get('items', []):
                if search_result['id']['kind'] == 'youtube#video':
                    video_links.append('%s' % (search_result['id']['videoId']))

            self.video_database_lock.acquire()
            with open(VIDEO_DATABASE, 'w+') as fp:
                self.video_links[word] = video_links
                json.dump(self.video_links, fp)
            self.video_database_lock.release()

        except HttpError as e:
            print("OUT OF QUOTA! Picking a random video\n")
            # When an execution is made - use the database of videos
            self.video_database_lock.acquire()
            pick = list(self.video_links.values())
            video_links = choice(pick)
            self.video_database_lock.release()
        return video_links


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

#
# def video_length_choose_progress_bar(v_counter, per_total_len):
#     """
#     A progress bar for the video length selector.
#     :param v_counter: Counter of how many videos were sent to download - int
#     :param per_total_len: total elapsed percentage of the length of the videos - float
#     """
#     sleep(0.1)
#     sys.stdout.write('\r')
#     sys.stdout.write(PROGRESS_BAR_FORMAT_TXT.format(v_counter, per_total_len))
#     sys.stdout.flush()


def get_callable_range_video(length):
    def video_length_call(info_dict, ydl):
        video_duration = info_dict['duration']
        if video_duration > length:
            time_pick = random.uniform(0, video_duration - length)
            yield {'start_time': time_pick, 'end_time': time_pick + length}
        else:
            yield {'start_time': 0, 'end_time': video_duration}

    return video_length_call


def download_youtube_video(youtube_singleton, temp_video_file_name, temp_video_file_path, video_length, word):
    """
    Downloads and resizes a YouTube video.
    :param temp_video_file_name: video file name - string
    :param temp_video_file_path: video file path - string
    :param video_length: Length of video in seconds - float
    """
    while not os.path.exists(temp_video_file_path):
        get_and_down_youtube_vid(youtube_singleton, temp_video_file_path, video_length, word)
    resize_video_file(temp_video_file_name, temp_video_file_path, word)
    # stream_url = pafy.new(youtube_url).getbest().url

    retry_count = 0
    # while retry_count <= MAX_RETRY_COUNT:
    #     try:
    #         if not ffmpeg_download(stream_url, video_file_path, video_length):
    #             retry_count += 1
    #             continue
    #         check_file_integrity(video_file_name, TEMP_DIRECTORY)
    #         resize_video_file(video_file_name, video_file_path)
    #         check_file_integrity(video_file_name, CONVERTED_DIRECTORY)
    #         break
    #     except Exception as e:  # TODO check for type of exceptions!!!! There are a lot of them
    #         print("inside download_youtube_video")
    #         print(e)
    #         retry_count += 1
    #         continue


def get_and_down_youtube_vid(youtube_singleton, video_file_path, video_length, word):
    youtube_url = YOUTUBE_PREFIX + youtube_singleton.youtube_search(word)
    ydl_opts = {'ignoreerrors': True,
                'quiet': True,
                'format': 'mp4',
                'outtmpl': video_file_path,
                'download_ranges': get_callable_range_video(video_length),
                'noprogress': True}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([youtube_url])


def check_file_integrity(file_name, folder_path):
    """
    A basic check for a file - see if it opens.
    :param file_name: file name - string
    :param folder_path: folder path - string
    """
    file = open(folder_path + '\\' + file_name, READ_MODE)
    file.close()


def resize_video_file(video_file_name, video_file_path, word):
    """
    Resize a video file and saves it.
    :param video_file_name: video file name - string
    :param video_file_path: video file path - string
    """
    try:
        clip = VideoFileClip(video_file_path)
        clip = resize(clip, height=RESIZE_HEIGHT)
        # Generate a text clip
        txt_clip = TextClip(txt=str(word).upper(), fontsize=100, font='lane', color='black',
                            bg_color='white').set_position(("left", "bottom")).set_duration(clip.duration)

        video = CompositeVideoClip([clip, txt_clip])
        video.write_videofile(CONVERTED_DIRECTORY + '\\' + video_file_name, verbose=False, logger=None)
    except Exception as e:
        print(e)


# def ffmpeg_download(stream_url, video_file_path, time_of_video):
#     """
#     Picks and downloads a YouTube video with ffmpeg until timeout
#     :param video_file_path: YouTube video download file name as a string
#     :param time_of_video: length of the video in float
#     :return: True if downloaded successfully, false otherwise.
#     """
#     download_video_from_youtube = (
#         ffmpeg.input(stream_url, t=time_of_video).output(video_file_path, f=VIDEO_CONTAINER, acodec=ACODEC,
#                                                          vcodec=OUTPUT_CODEC,
#                                                          loglevel=LOGLEVEL).overwrite_output().run_async())
#     try:
#         download_video_from_youtube.wait(MAX_TIMEOUT_LEN)
#         file = open(video_file_path, READ_MODE)  # Used to check if corrupted download
#         file.close()
#         return True
#     except TimeoutExpired:
#         # print("Timeout " + out_filename)
#         return False
#     except FileNotFoundError:
#         return False


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
            print(video + ' is broken. SKIPPING')
            print('\n')
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

def create_video_download_jobs(pool, words, total_video_length, youtube_singleton, func):
    """
    Picks the video length and creates download jobs for the process pool.
    :param pool: Process pool instance
    :return: A list of all the jobs that were made, the total number of videos that will be downloaded
    """
    working_jobs = []
    for i in range(len(words)):
        temp_video_file_name = str(i) + VIDEO_EXTENSION
        temp_video_file_path = TEMP_DIRECTORY + "\\" + temp_video_file_name
        working_jobs.append(
            pool.apply_async(func,
                             (youtube_singleton, temp_video_file_name, temp_video_file_path,
                              get_video_length(total_video_length, words), words[i])))
    return working_jobs


def get_video_length(total_video_length, words):
    return total_video_length / len(words)


def get_sentence_input():
    while True:
        print("For random words, enter 1\n")
        print("to type words, enter 2\n")
        print("to get words from input file, enter 3\n")
        try:
            choice_input = int(input())
            if choice_input == 1:
                words_input = RandomWords().get_random_words(hasDictionaryDef="true",
                                                             limit=int(input("How many random words?")))
                break
            elif choice_input == 2:
                words_input = input("Please write something. Anything.\n")
            elif choice_input == 3:
                with open('input', READ_MODE) as fp:
                    words_input = fp.read()
            else:
                raise ValueError
            words_input = re.sub("\\n+|\\t+", ' ',
                                 words_input.translate(str.maketrans('', '', string.punctuation))).split(' ')
            break
        except ValueError as e:
            print("wrong input.\n")
    repeat = int(input("How many times do you want to repeat input?:\n"))
    if repeat:
        words_input = words_input * repeat
    return words_input


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


def start_thread_pool(total_video_length, words):
    """
    Starts a process pool and gives it videos to download
    """

    youtube_singleton = YouTubeSingleton()
    with ThreadPool(NUM_OF_PROCESSES) as pool:
        # Gives jobs to pool
        working_jobs = create_video_download_jobs(pool, words, total_video_length, youtube_singleton,
                                                  download_youtube_video)
        print('\n')
        sys.stdout.flush()
        download_progress_bar(len(words), working_jobs)
        pool.terminate()
        pool.join()


def main():
    print_words_in_database()
    sentence_input = get_sentence_input()
    total_video_length = int(input(VIDEO_TO_BE_IN_SECONDS_))
    create_output_dir()
    start_thread_pool(total_video_length, sentence_input)
    print(MAKING_MASTER_VIDEO_TXT)
    output_name = OUTPUT_DIRECOTRY + '\\' + str(datetime.datetime.now()).replace('-', '_').replace(' ', '_').replace(
        ':', '_')
    concatenate(CONVERTED_DIRECTORY, output_name + VIDEO_EXTENSION)
    with open(output_name + '.txt', 'w+') as f:
        for word in sentence_input:
            f.write(word)
            f.write(" ")
    print(FINISHED_MESSAGE)
    open_folder_in_explorer()
    exit(0)


def open_folder_in_explorer():
    path = os.path.realpath(OUTPUT_DIRECOTRY)
    os.startfile(path)


def print_words_in_database():
    print("WORDS IN DATABASE")
    print('________________________________')
    if os.path.exists(VIDEO_DATABASE):
        if os.stat(VIDEO_DATABASE).st_size != 0:
            with open(VIDEO_DATABASE, 'r') as f:
                words_in_database = json.load(f)
    for word in words_in_database.keys():
        print(word)
    print('________________________________\n')


if __name__ == '__main__':
    main()
