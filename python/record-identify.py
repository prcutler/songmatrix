import asyncio
import json
import time

import config
import requests
import sounddevice as sd
from Adafruit_IO import Client
from scipy.io.wavfile import write
from shazamio import Shazam

LB_SUBMIT_URL = "https://api.listenbrainz.org/1/submit-listens"


def submit_listenbrainz(artist, title):
    payload = {
        "listen_type": "single",
        "payload": [
            {
                "listened_at": int(time.time()),
                "track_metadata": {
                    "artist_name": artist,
                    "track_name": title,
                },
            }
        ],
    }
    headers = {"Authorization": f"Token {config.lb_api}"}
    response = requests.post(LB_SUBMIT_URL, json=payload, headers=headers)
    if response.status_code == 200:
        print("Submitted to ListenBrainz")
    else:
        print(f"ListenBrainz error: {response.status_code} {response.text}")


async def main():
    while True:
        # Try / Except to catch if a song is not identified or there is silence and will try again
        try:
            print("Starting...")

            fs = 44100  # Sample rate
            seconds = 30  # Duration of recording

            my_recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()  # Wait until recording is finished
            write("output.wav", fs, my_recording)  # Save as WAV file
            print("Recording complete")

            shazam = Shazam()
            out = await shazam.recognize_song("output.wav")
            track_title = out["track"]["title"]
            artist = out["track"]["subtitle"]

            payload = {"title": track_title, "artist": artist}
            payload_json = json.dumps(payload)
            print(payload_json)

            aio = Client(config.aio_username, config.aio_key)
            aio.send_data("audio", payload_json)

            submit_listenbrainz(artist, track_title)

        except KeyError:
            print("Song not identified")
            pass

        # How long to wait before recording another sample in seconds
        time.sleep(180)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
