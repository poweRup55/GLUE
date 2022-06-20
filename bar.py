from subprocess import TimeoutExpired

import ffmpeg
from moviepy.video.fx.resize import resize
from moviepy.video.io.VideoFileClip import VideoFileClip
from pafy import pafy

import video_generator
from constants import *


def start_sub_process(file_name, out_filename, video_length):
    # add_job_name(file_name)
    # print(file_name + " started and is " + str(time_of_video) + " seconds long")
    try:
        finished = False
        while not finished:
            finished = start_sub_process_helper(out_filename, video_length)
            if not finished:
                # print("retrying " + file_name)
                continue
            # print(file_name + 'downloaded successfully! Starting conversion')
            convert_video_file(file_name, out_filename)
        # job_finished(file_name)
        file = open(out_filename, 'r')
        file.close()
    except Exception as e:
        start_sub_process(file_name, out_filename, video_length)
    # print(out_filename + " finished")


def convert_video_file(file_name, out_filename):
    clip = VideoFileClip(out_filename)
    clip = resize(clip, height=1080)
    clip.write_videofile(CONVERTED_DIRECTORY + '\\' + file_name, verbose=False, logger=None)
    clip.close()


def start_sub_process_helper(out_filename, time_of_video):
    youtube_url = "https://www.youtube.com/watch?v=" + video_generator.YouTubeSingleton().youtube_search()
    stream_url = pafy.new(youtube_url).getbest().url
    download_video_from_youtube = (ffmpeg.input(stream_url, t=time_of_video).output(out_filename, f='mp4', acodec='aac',
                                                                                    vcodec='libx264',
                                                                                    loglevel="quiet").overwrite_output().run_async())
    try:
        download_video_from_youtube.wait(20)
        return True
    except TimeoutExpired:
        # print("Timeout " + out_filename)
        return False
