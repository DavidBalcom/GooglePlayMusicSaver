# GooglePlaySaver #

This is a command line tool to download songs from your playlists on Google Play Music. It's perfect if you have an ipod nano that you like to use for running, and you want to get your Google Play playlists on it. It works by getting a list of all your songs from the playlist, searching for the song on YouTube, downloading it as an mp4, and then converting it to an mp3.

### Usage ###

Run the script from the command line and follow the prompts. Alternatively, add arguments to the function calls at the end of the script to run it without user input.

### Requirements ###

Python 2.7

This requires ffmpeg to be installed and in the path, or at least the same directory as the script. 

also requires:

beautifulsoup4==4.5.1
eyeD3==0.7.11
gmusicapi==10.1.2
pytube==6.2.2
requests==2.11.1
retrying==1.3.3

## Author

* **David Balcom** [LinkedIn](https://www.linkedin.com/in/djbalcom)