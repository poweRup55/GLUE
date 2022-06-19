import math
import os
import os.path
import random
import shutil
import subprocess
from os import listdir
from os.path import isfile, join

from multiprocessing import Process

import cv2
import ffmpeg
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
import moviepy.editor as mp
from pafy import pafy

from multiprocessing import Pool, TimeoutError

import video_generator

OUTPUT_DIRECOTRY = "output\\with_story"
FPS = 25
VIDEO_SIZE = (1920, 1080)
MAX_BYTE_SIZE = 255
MINUTES = 0
SECONDS = 5
TOTAL_TIME = MINUTES * 60 + SECONDS
TEMP_DIRECTORY = OUTPUT_DIRECOTRY + "\\temp"
UPDATED_DIRECTORY = OUTPUT_DIRECOTRY + "\\updated"


def main():
    make_temp_videos()
    concatenate(UPDATED_DIRECTORY, OUTPUT_DIRECOTRY + '\\final' + str(
        len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + '.mp4')


def make_temp_videos():
    count = 0
    with Pool(processes=8) as pool:
        while choose_video_time.story_percentage < 100:
            os.makedirs(TEMP_DIRECTORY)
            os.makedirs(UPDATED_DIRECTORY)
            file_name = str(count) + ".mp4"

            temp_filename = TEMP_DIRECTORY + "\\" + file_name
            time_of_video = choose_video_time()
            job = pool.apply_async(start_sub_process, (file_name, temp_filename, time_of_video,))
            job.get()
            count += 1
        pool.close()
        pool.join()
    print("done!")


def start_sub_process(file_name, out_filename, time_of_video):
    # add_job_name(file_name)
    print(out_filename + " started and is " + str(time_of_video) + " seconds long")
    finished = False
    while not finished:
        finished = start_sub_process_helper(out_filename, time_of_video)
        if not finished:
            print("retrying " + out_filename)
            continue
        p =
        try:


        except Exception as e:

    # job_finished(file_name)
    file = open(out_filename, 'r')
    file.close()
    print(out_filename + " finished")


def start_sub_process_helper(out_filename, time_of_video):
    youtube_url = "https://www.youtube.com/watch?v=" + video_generator.YouTubeSingleton().youtube_search()
    stream_url = pafy.new(youtube_url).getbest().url
    download_video_from_youtube = (ffmpeg.input(stream_url, t=time_of_video).output(out_filename, f='mp4', acodec='aac',
                                                                                    vcodec='libx264',
                                                                                    loglevel="quiet").overwrite_output().run_async())
    try:
        download_video_from_youtube.wait(min(time_of_video * 10, 20))
        return True
    except subprocess.TimeoutExpired:
        return False


def concatenate(video_clips_path, output_path):
    # create VideoFileClip object for each video file
    files_in_temp = [video_clips_path + "\\" + f for f in listdir(video_clips_path)]
    clips = [VideoFileClip(c) for c in files_in_temp]
    final_clip = concatenate_videoclips(clips, method="compose")
    # write the output video file
    final_clip.write_videofile(output_path, codec='libx264')


def choose_video_time():
    if 0 <= choose_video_time.story_percentage <= 80:
        time = quarter(10 * math.exp((-1 / 25) * choose_video_time.story_percentage))
        time = max(0.25, quarter(random.uniform(time - 3, time + 3)))
    else:
        time = quarter(random.uniform(5, 10))
    choose_video_time.story_percentage += time * 100 / TOTAL_TIME
    return time


def quarter(x):
    return math.ceil(x * 4) / 4


#
# def add_job_name(job_name):
#     with ThreadsPoolFiles.ThreadPoolSingelton().process_files_list_mutex:
#         ThreadsPoolFiles.ThreadPoolSingelton().process_files_list.append(job_name)
#         print(ThreadsPoolFiles.ThreadPoolSingelton().process_files_list, len(
#             ThreadsPoolFiles.ThreadPoolSingelton().process_files_list))
#
#
# def job_finished(job_name):
#     with ThreadsPoolFiles.ThreadPoolSingelton().process_files_list_mutex:
#         ThreadsPoolFiles.ThreadPoolSingelton().process_files_list.remove(job_name)


if __name__ == '__main__':
    # try:
        choose_video_time.story_percentage = 0
        main()
    # finally:
    #     shutil.rmtree(TEMP_DIRECTORY)
    #     shutil.rmtree(UPDATED_DIRECTORY)

"""
    
    THIS CODE USES OPEN CV
    
    video = cv2.VideoCapture(stream_url)
    if not video.isOpened():
        print("\nError opening video stream or file")
        exit(1)
    result = cv2.VideoWriter(out_filename,
                             cv2.VideoWriter_fourcc(*'avc1'),
                             FPS, VIDEO_SIZE)
    frame_count = 0
    while video.isOpened() and frame_count != 100:
        ret, in_frame = video.read()
        if ret:
            in_frame = in_frame.astype(np.float32) / MAX_BYTE_SIZE
            out_frame = cv2.resize(in_frame, VIDEO_SIZE)
            out_frame = np.round(np.clip(out_frame, 0, 1) * MAX_BYTE_SIZE).astype(np.uint8)
            result.write(out_frame)
            cv2.imshow('frame', out_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
            frame_count += 1

        else:
            break
    video.release()
    result.release()
    # Closes all the frames
    cv2.destroyAllWindows()
    
    THIS CODE USES BAD FFMPEG
       

    # output_directory = "output\\with_story"
    # out_filename = output_directory + "\\" + str(
    #     len(os.listdir(output_directory)) + 1) + ".mp4"
    # # url of the video
    # youtube_url = "https://www.youtube.com/watch?v=" + video_generator.youtube_search()
    #
    # stream_url = pafy.new(youtube_url).getbest().url
    #
    # stream = ffmpeg.input(stream_url, t=10)
    # audio = stream.audio
    # video = stream.video
    # stream = ffmpeg.output(audio, video, out_filename, f='mp4', acodec='aac', vcodec='libx264')
    # ffmpeg.run(stream)
    # exit(0)
"""
