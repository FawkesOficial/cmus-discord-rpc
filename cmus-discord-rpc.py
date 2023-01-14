#!/usr/bin/env python3

# This script implements a discord rich presence for cmus.
# This was honestly developed for my very personal use case (i.e. download using youtube-dl which embeds YT urls in the files metadata).
# If you can make any use of this, great. If not, you could always try to contact me to question me about this script.

from pypresence import Presence
import time
from pycmus import remote
from mutagen.id3 import ID3
import requests
from os import getenv

REFRESH_RATE = 0.99

RATE_LIMIT_RETRY_TIMEOUT = 6

RETRY = True
RETRY_TIMEOUT = 10

# Replace this with your OAuth2 CLIENT ID. If you don't have one you can get it by creating a new application in https://discord.com/developers/applications
CLIENT_ID = getenv("CMUS_DISCORD_RPC_TOKEN")

try:
    while RETRY:
        try:
            CMUS = remote.PyCmus()
            RPC = Presence(CLIENT_ID)
            RPC.connect()

            print()
            print("[+] Connected to Discord and cmus!")
            while True:
                cmus_status = CMUS.get_status_dict()

                if cmus_status["status"] == "playing":
                    song_name = cmus_status["tag"]["title"]
                    song_artist = cmus_status["tag"]["artist"]
                    album_name = (cmus_status["tag"]).get("album", song_name)
                    song_path = cmus_status["file"]
                    audio_file = ID3(song_path)
                    song_url = str(audio_file["TXXX:comment"])
                    song_id = song_url.replace("https://www.youtube.com/watch?v=", "")
                    elapsed = int(cmus_status["position"])
                    play_song_button = {"label": "Play on YouTube", "url": song_url}

                    youtube_thumbnail_qualities = [
                        "maxresdefault.jpg",
                        "sddefault.jpg",
                        "hqdefault.jpg",
                        "0.jpg",
                        "mqdefault.jpg",
                        "1.jpg",
                        "2.jpg",
                        "3.jpg",
                        "default.jpg"
                    ]
                    # Get the best quality thumbnail
                    for quality in youtube_thumbnail_qualities:
                        album_cover_url = f"https://img.youtube.com/vi/{song_id}/{quality}"
                        album_cover_request = requests.get(album_cover_url)
                        if album_cover_request.status_code == 200:
                            album_cover = album_cover_url
                            break
                        else:
                            print()
                            print(f"[X] No thumbnails were found for {song_name} ({song_url})")
                            
                            # Default asset uploaded to https://discord.com/developers/applications. If you want this to work, you have to upload "assets/vinyl-icon.png"
                            album_cover = "vinyl-icon"

                    try:
                        RPC.update(
                            details = song_name,
                            state = f"by {song_artist}",
                            large_image = album_cover,
                            large_text = album_name,
                            start = time.time()-elapsed,
                            buttons = [play_song_button]
                        )
                    except:
                        print()
                        print("[X] Got rate limited in RPC.update() (probably bc of changing songs too fast)")
                        RPC.close()
                        time.sleep(RATE_LIMIT_RETRY_TIMEOUT)
                        break
                else:
                    try:
                        RPC.clear()
                        # RPC.update() # Default App assests
                    except:
                        print()
                        print("[X] Got rate limited in RPC.clear() (probably bc of changing songs too fast)")
                        RPC.close()
                        time.sleep(RATE_LIMIT_RETRY_TIMEOUT)
                        break

                time.sleep(REFRESH_RATE)

        except:
            print()
            print("[X] Either Discord or cmus is not running. Checking again in 10 seconds ...")
            try:
                RPC.close()
            except:
                pass

            time.sleep(RETRY_TIMEOUT)
except:
    try:
        RPC.close()
    except:
        pass
