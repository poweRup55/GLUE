import os
import random
from threading import Lock

from googleapiclient.discovery import build

YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'

prefix = ['IMG ', 'IMG_', 'IMG-', 'DSC ']
postfix = [' MOV', '.MOV', ' .MOV']


class YouTubeSingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton.
    """

    _instances = {}

    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class YouTubeSingleton(metaclass=YouTubeSingletonMeta):
    def __init__(self) -> None:
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=os.getenv('DEVELOPER_KEY'))
        self.video_mutex = Lock()
        self.video_mutex.acquire()
        self.videos = []
        with open("youtube_video_database.txt", 'r') as fp:
            for line in fp:
                x = line[:-1]
                self.videos.append(x)
        self.video_mutex.release()

    def youtube_search(self):
        videos = []
        try:
            search_response = self.youtube.search().list(
                q=random.choice(prefix) + str(random.randint(999, 9999)) + random.choice(postfix),
                part='snippet',
                maxResults=5
            ).execute()

            for search_result in search_response.get('items', []):
                if search_result['id']['kind'] == 'youtube#video':
                    videos.append('%s' % (search_result['id']['videoId']))

            self.video_mutex.acquire()
            # open file in write mode
            with open("youtube_video_database.txt", 'a') as fp:
                for video in videos:
                    # write each item on a new line
                    fp.write("%s\n" % video)
            self.video_mutex.release()

        except Exception as e:  # TODO Add more precise exceptions!
            videos = self.videos

        return videos[random.randint(0, len(videos) - 1)]
