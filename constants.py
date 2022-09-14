MAX_THIRD_PHASE_LEN = 7
MIN_THIRD_PHASE_LEN = 5
MAX_SECOND_PHASE_LEN = 0.12
MIN_SECOND_PHASE_LEN = 0.04
SECOND_PHASE_PERCENTAGE = 80
FIRST_PHASE_PRECENTAGE = 60
FIRST_PHASE_MIN_LENGTH = 3

READ_MODE = 'r'
RESIZE_HEIGHT = 1080
LOGLEVEL = "quiet"
ACODEC = 'aac'
YOUTUBE_PREFIX = "https://www.youtube.com/watch?v="
OUTPUT_CODEC = 'libx264'
CONCATENATE_METHOD = "compose"
TQDM_SLEEP_DUR = 1
TQDM_DOWNLOAD_DESC = "Number of videos downloaded"
VIDEO_EXTENSION = ".mp4"
VIDEO_CONTAINER = 'mp4'
NUM_OF_PROCESSES = 8
MASTER_DOWNLOAD_TIMEOUT = 10 * 60
VIDEO_SIZE = (1920, 1080)
OUTPUT_DIRECOTRY = "output"
TEMP_DIRECTORY = OUTPUT_DIRECOTRY + "\\temp"
CONVERTED_DIRECTORY = OUTPUT_DIRECOTRY + "\\conversion"
NAME_OF_FINAL_PRODUCT = '\\final'
FINISHED_MESSAGE = '\n \n  FINISHED! \n \n'
START_MSG = 'Making A Very Coherent Video'
MAKING_MASTER_VIDEO_TXT = "Finished downloading videos! Making master video"
FINISHED_DOWNLOAD_MSG = "finished downloading all videos!"
TERMINATING_DOWN_MESSAGE = "Terminating because it is taking too long. Making video now"
PROGRESS_BAR_FORMAT_TXT = "Downloading queue: {} which are: {:%} of the video"
MAX_TIMEOUT_LEN = 20





MAX_RESULTS = 50
VIDEO = 'video'
SNIPPET = 'snippet'
APPEND_MODE = 'a+'
VIDEO_DATABASE = "youtube_video_database.json"
YOUTUBE_API_SERVICE_NAME = 'youtube'
YOUTUBE_API_VERSION = 'v3'


# Change this to change the final video length
MINUTES = 1
SECONDS = 0


TOTAL_TIME = MINUTES * 60 + SECONDS
