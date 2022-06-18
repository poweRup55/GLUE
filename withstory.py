import math
import os
import os.path
import random
import shutil
import subprocess
from os import listdir
from os.path import isfile, join

import ffmpeg
from moviepy.video.compositing.concatenate import concatenate_videoclips
from moviepy.video.io.VideoFileClip import VideoFileClip
from pafy import pafy

import ThreadsPoolFiles
import video_generator

OUTPUT_DIRECOTRY = "output\\with_story"
FPS = 25
VIDEO_SIZE = (1920, 1080)
MAX_BYTE_SIZE = 255
MINUTES = 0
SECONDS = 30
TOTAL_TIME = MINUTES * 60 + SECONDS
TEMP_DIRECTORY = OUTPUT_DIRECOTRY + "\\temp"


def main():
    make_temp_videos()
    concatenate(TEMP_DIRECTORY, OUTPUT_DIRECOTRY + '\\final.mp4')


def make_temp_videos():
    count = 0
    executor = ThreadsPoolFiles.ThreadPoolSingelton(3)
    while choose_video_time.story_percentage < 100:
        if not os.path.isdir(TEMP_DIRECTORY): os.mkdir(TEMP_DIRECTORY)
        out_filename = TEMP_DIRECTORY + "\\" + str(count) + ".mp4"
        time_of_video = choose_video_time()
        executor.add_job(start_sub_process, out_filename, time_of_video)
        count += 1
    executor.wait()
    print("done!")


def start_sub_process(out_filename, time_of_video):
    file_name = out_filename.removesuffix('.mp4').split('\\')[-1]
    ThreadsPoolFiles.ThreadPoolSingelton().add_job_name(file_name)
    # print(out_filename + " started and is " + str(time_of_video) + " seconds long")
    start_sub_process_helper(out_filename, time_of_video)
    ThreadsPoolFiles.ThreadPoolSingelton().job_finished(file_name)
    # print(out_filename + " finished")


def start_sub_process_helper(out_filename, time_of_video):
    youtube_url = "https://www.youtube.com/watch?v=" + video_generator.YouTubeSingleton().youtube_search()
    stream_url = pafy.new(youtube_url).getbest().url
    try:
        process = (
            ffmpeg
            .input(stream_url, t=time_of_video)
            .output(out_filename, f='mp4', acodec='aac', vcodec='libx264', loglevel="quiet")
            .overwrite_output()
            .run_async()
        )
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        process.kill()
        start_sub_process_helper(out_filename, time_of_video)


def concatenate(video_clips_path, output_path):
    # create VideoFileClip object for each video file
    files_in_temp = [video_clips_path + "\\" + f for f in listdir(video_clips_path) if
                     isfile(join(video_clips_path, f))]
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


if __name__ == '__main__':
    choose_video_time.story_percentage = 0
    main()
    shutil.rmtree(TEMP_DIRECTORY)

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
