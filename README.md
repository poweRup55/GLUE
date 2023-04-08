# Glue
The purpose of this program is to experiment with generating a movie from random YouTube videos and determining whether it still has a narrative.

The user has to specify the desired length of the output video in seconds. He then can choose to write his own prompt or ask the program to choose random words.

The program uses the prompt or random words and searches for videos related to those words on YouTube. From the search results, the program chooses a random video and downloads it, resizes it, and cuts it according to the desired length.

To avoid running out of quota for the YouTube Data API, the program stores the video links in a JSON file and retrieves videos from the local database instead of calling the API.

The program uses the moviepy library to concatenate and resize the downloaded videos and create the final movie. also it uses the multiprocessing and threading modules in Python to download and process multiple videos in parallel.
## How to run

1 . You can download the latest releast and run "main.exe"


2 . run the main.py file and follow the prompts.
  required libraries: yt_dlp, google-api-python-client, moviepy, random_word, and tqdm. Also a developer key needes to the be added to the DEVELOPER_KEYS list in the program.


