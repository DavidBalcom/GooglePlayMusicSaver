#!/usr/bin/env python

import base64
import subprocess
import os
import getpass
from multiprocessing.dummy import Pool as ThreadPool
import time
import copy
import traceback

import gmusicapi
import requests
import bs4
from pytube import YouTube
import eyed3
from retrying import retry

__author__ = "David Balcom"

"""
cmd line tool to download playlists from Google Play. Can also be used in a script by adding arguements to the function calls. 

This will pull the playlists for a user from Google Play Music and then allow the user to select a playlist.
It then searchs Youtube for the songs in the playlist and downloads them as mp4 videos, then it uses ffmpeg to convert them to an mp3. 
"""


class GooglePlayGetter(object):


    def __init__(self):
        super(GooglePlayGetter, self).__init__()
        self.base_url = 'https://www.youtube.com'
        self.query_url = self.base_url+'/results'
        self.playlist_contents = None
        self.tracklist = []
        self.playlist_name = None
        self.playlist = None
        self.dest_dir = None


    def _get_playlists(self, email=None, pw=None):

        if not all([email, pw]):
            email = raw_input('email:')
            pw = getpass.getpass('password:')

        print('\nlogging in...\n')

        api = gmusicapi.Mobileclient(debug_logging=False)
        api.login(email, pw, gmusicapi.Mobileclient.FROM_MAC_ADDRESS)
        playlist_contents = api.get_all_user_playlist_contents()
        self.playlist_contents = playlist_contents
        print '\nselect a playlist:\n'
        counter = 0
        for playlist in playlist_contents:
            counter += 1
            print str(counter)+': '+playlist['name']
        print '\n'


    def _set_playlist(self, playlist_name=None):
        if not playlist_name:
            playlist_from_user = raw_input('Playlist:')

            try:
                playlist_from_user = int(playlist_from_user)
                self.playlist = self.playlist_contents[playlist_from_user-1]

            except ValueError:
                for playlist in self.playlist_contents:
                    if playlist['name'].strip() == playlist_from_user:
                        self.playlist = playlist
                        break

            if not self.playlist:
                print "\nPlaylist not found. Please enter selection again:\n"
                self._set_playlist()

        else:
            for playlist in self.playlist_contents:
                if playlist['name'].strip() == playlist_name:
                    self.playlist = playlist
                    break
                
            print 'playlist name not set'



    def _set_dest_dir(self, dest_dir=None):
        if not dest_dir:
            dest_dir = raw_input('Destination Directory:')

        try:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            self.dest_dir = dest_dir

        except:
            print '\nCouldnt make that directory, please try again\n'
            self._set_dest_dir()



    def _get_song_list(self):
        tracks = self.playlist['tracks']
        new_tracklist = []
        for track in tracks:
            try:
                track_tuple = (track['track']['artist'], track['track']['title'])
                new_tracklist.append(track_tuple)
            except KeyError:
                # track doesn't have title or artist, maybe was added by user
                pass

        self.tracklist = copy.deepcopy(new_tracklist)


    @retry(stop_max_attempt_number=3)
    def _download_track(self, track_tuple):
        
        try:
            search_string = track_tuple[0]+' '+track_tuple[1]
            print "Downloading "+search_string
            params = {"search_query": search_string}
            r = requests.get(self.query_url, params)

            # search youtube and parse response
            soup = bs4.BeautifulSoup(r.content, 'html.parser')
            try:
                ols = soup.find_all('ol', class_='item-section')
                item = ols[0].li.div.div.find_all('h3')
                vid_url_extension = item[0].a.get('href')
                html_parsed = True
            except Exception as e:
                print 'WARNING: Couldn\'t parse html for '+search_string
                print r.url
                html_parsed = False

            if html_parsed:

                # download video
                vid_url = self.base_url+vid_url_extension

                try:
                    yt = YouTube(vid_url)
                    filename = yt.filename
                    video = yt.get('mp4', '360p')
                    video.download(self.dest_dir)
                    video_downloaded = True
                except Exception as VideoDownloadException:
                    print "WARNING: unable to download video: "+search_string
                    print str(VideoDownloadException)
                    video_downloaded = False

                if video_downloaded:
                    # convert video to mp3
                    video_filename = filename+'.mp4'
                    mp3_filename = filename+'.mp3'

                    video_path = os.path.join(self.dest_dir, video_filename)
                    mp3_path = os.path.join(self.dest_dir, mp3_filename)

                    argsList = ['ffmpeg', '-loglevel', 'panic', '-i', video_path, '-f', 'mp3', mp3_path]
                    subprocess.check_call(argsList)

                    # tag song
                    song = eyed3.load(mp3_path)
                    song.tag.artist = track_tuple[0]
                    song.tag.title = track_tuple[1]
                    try:
                        song.tag.save()
                    except:
                        try:
                            time.sleep(5)
                            song.tag.save()
                        except:
                            print "WARNING: Couldn't save ID3 tags for "+search_string
                    
                    try:
                        os.remove(video_path)
                    except:
                        time.sleep(5)
                        try:
                            os.remove(video_path)
                        except:
                            print "WARNING: Couldn't delete "+video_filename
                

        except Exception as e:
            print '\nEXCEPTION:\n'
            print traceback.print_exc()
            print '\n'
            raise e



    def _get_all_the_tracks(self, tracklist, threads=4):
        pool = ThreadPool(threads)
        pool.map(self._download_track, tracklist)
        pool.close()
        pool.join()




if __name__ == '__main__':

    g = GooglePlayGetter()

    g._get_playlists()

    g._set_playlist()

    g._set_dest_dir()

    g._get_song_list()

    g._get_all_the_tracks(g.tracklist, threads=4)
