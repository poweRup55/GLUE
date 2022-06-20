import os
import shutil
import sys
from math import exp, ceil
from multiprocessing import Pool
from random import uniform
from time import sleep

from tqdm import tqdm

import bar
from constants import *


def make_temp_videos():
    count = 0
    if os.path.exists(TEMP_DIRECTORY):
        shutil.rmtree(TEMP_DIRECTORY)
    os.makedirs(TEMP_DIRECTORY)
    if os.path.exists(CONVERTED_DIRECTORY):
        shutil.rmtree(CONVERTED_DIRECTORY)
    os.makedirs(CONVERTED_DIRECTORY)
    total_per = 0
    working_jobs = []
    with Pool(processes=8) as pool:
        while total_per < 100:
            file_name = str(count) + ".mp4"
            video_length, total_per = choose_video_time(total_per)
            temp_filename = TEMP_DIRECTORY + "\\" + file_name
            working_jobs.append(pool.apply_async(bar.start_sub_process, (file_name, temp_filename, video_length)))
            count += 1
            progress_bar(count, total_per)
        print('\n')
        sys.stdout.flush()
        timeout_time = 5 * 60
        num_of_finished_jobs = 0
        sec_count = 0
        with tqdm(total=count, desc="Number of videos downloaded") as pbar:
            while True:
                if sec_count >= timeout_time:
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
        pool.terminate()
        pool.join()


def choose_video_time(elapsed_percentage):
    if 0 <= elapsed_percentage <= 60:
        time = -0.2 * elapsed_percentage +15
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
    # the exact output you're looking for:
    sys.stdout.write("Downloading queue: " + str(i) + " which are: " + str(j) +' of the video')
    sys.stdout.flush()
