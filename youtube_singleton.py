"""

IMPORTANT - ADD YOUR DEVELOPER KEY HERE FOR THIS TO WORK

"""
import os
import random
from os.path import exists
from threading import Lock

from googleapiclient.discovery import build
from random_word import RandomWords

from constants import *

DEVELOPER_KEY = os.environ['DEVELOPER_KEY']

MAX_RESULTS = 50
VIDEO = 'video'
SNIPPET = 'snippet'
APPEND_MODE = 'a+'
DATABASE_TXT = "youtube_video_database.txt"
VIDEO_DATABASE_TXT = "youtube_video_database.txt"
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


class YouTubeSingletonMeta(type):
    """
    This is a thread-safe implementation of Singleton. Metaclass.
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
    """
    This is a thread-safe implementation of Singleton.
    """

    def __init__(self) -> None:
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        self.video_mutex = Lock()
        self.video_mutex.acquire()
        self.video_links = set()
        # Add video links from video txt file
        if exists(VIDEO_DATABASE_TXT):
            with open(VIDEO_DATABASE_TXT, READ_MODE) as fp:
                for line in fp:
                    x = line[:-1]
                    self.video_links.add(x)
        self.video_mutex.release()
        self.random_word_gen = RandomWords()

    def youtube_search(self):
        """
        Generates a random word and searches it on YouTube. Picks one video from the search query randomly
        :return: A YouTube video link suffix
        """
        videos = []
        try:

            search_response = self.youtube.search().list(
                part=SNIPPET,
                maxResults=MAX_RESULTS,
                type=VIDEO,
                q=self.random_word_gen.get_random_word()
            ).execute()

            # Filters - only videos
            for search_result in search_response.get('items', []):
                if search_result['id']['kind'] == 'youtube#video':
                    videos.append('%s' % (search_result['id']['videoId']))

            self.video_mutex.acquire()
            # open file in append mode
            with open(DATABASE_TXT, APPEND_MODE) as fp:
                for video in videos:
                    if video not in self.video_links:
                        # write each item on a new line
                        self.video_links.add(video)
                        fp.write("%s\n" % video)
            self.video_mutex.release()

        except Exception as e:  # TODO Add more precise exceptions!
            # print(e)
            # When an execution is made - used the database of videos
            self.video_mutex.acquire()
            videos = list(self.video_links)
            self.video_mutex.release()

        return videos[random.randint(0, len(videos) - 1)]
