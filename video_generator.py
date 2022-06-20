import random
from threading import Lock

import googleapiclient.errors
from googleapiclient.discovery import build

DEVELOPER_KEY = 'AIzaSyDSykfiYC_Q2FcCGORdBs3QuV9DshT_MDc'
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
    """
    We now have a lock object that will be used to synchronize threads during
    first access to the Singleton.
    """

    def __call__(cls, *args, **kwargs):
        """
        Possible changes to the value of the `__init__` argument do not affect
        the returned instance.
        """
        # Now, imagine that the program has just been launched. Since there's no
        # Singleton instance yet, multiple threads can simultaneously pass the
        # previous conditional and reach this point almost at the same time. The
        # first of them will acquire lock and will proceed further, while the
        # rest will wait here.
        with cls._lock:
            # The first thread to acquire the lock, reaches this conditional,
            # goes inside and creates the Singleton instance. Once it leaves the
            # lock block, a thread that might have been waiting for the lock
            # release may then enter this section. But since the Singleton field
            # is already initialized, the thread won't create a new object.
            if cls not in cls._instances:
                instance = super().__call__(*args, **kwargs)
                cls._instances[cls] = instance
        return cls._instances[cls]


class YouTubeSingleton(metaclass=YouTubeSingletonMeta):
    """
    We'll use this property to prove that our Singleton really works.
    """

    def __init__(self) -> None:
        self.youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=DEVELOPER_KEY)
        self.video_mutex = Lock()
        self.video_mutex.acquire()
        self.videos = []
        with open("video.txt", 'r') as fp:
            for line in fp:
                # remove linebreak from a current name
                # linebreak is the last character of each line
                x = line[:-1]

                # add current item to the list
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
            with open("video.txt", 'a') as fp:
                for video in videos:
                    # write each item on a new line
                    fp.write("%s\n" % video)
            self.video_mutex.release()
        #
        # except googleapiclient.errors.HttpError:
        #     # open file and read the content in a list
        #     videos = self.videos

        except Exception as e:
            videos = self.videos

        return videos[random.randint(0, len(videos) - 1)]
