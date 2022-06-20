from multiprocessing import freeze_support

freeze_support()
import cv2
from ffpyplayer.player import MediaPlayer
from moviepy.video.compositing.concatenate import concatenate_videoclips
from os import listdir
import Fo
from multiprocessing import Process
import os
import os.path

from moviepy.video.io.VideoFileClip import VideoFileClip
from constants import *


def main():
    video_from_internet_method = Process(target=Fo.make_temp_videos, daemon=False)
    video_from_internet_method.start()
    video_from_internet_method.join()
    video_from_internet_method.terminate()

    print("Finished downloading videos! Making master video")
    concatenate(CONVERTED_DIRECTORY, OUTPUT_DIRECOTRY + '\\final' + str(
        len([name for name in os.listdir(OUTPUT_DIRECOTRY)])) + '.mp4')


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
    PlayVideo(output_path)


def PlayVideo(video_path):
    video = cv2.VideoCapture(video_path)
    player = MediaPlayer(video_path)
    while True:
        grabbed, frame = video.read()
        audio_frame, val = player.get_frame()
        if not grabbed:
            print("End of video")
            break
        if cv2.waitKey(28) & 0xFF == ord("q"):
            break
        cv2.imshow("Video", frame)
        if val != 'eof' and audio_frame is not None:
            # audio
            img, t = audio_frame
    video.release()
    cv2.destroyAllWindows()


if __name__ == '__main__':
    freeze_support()
    print('Making A Very Coherent Video')
    main()
