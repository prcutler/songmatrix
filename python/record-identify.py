import asyncio
from Adafruit_IO import Client
from shazamio import Shazam
import config
import json
import sounddevice as sd
from scipy.io.wavfile import write
import time


async def main():

    while True:

        # Try / Except to catch if a song is not identified or there is silence and will try again
        try:
            fs = 44100  # Sample rate
            seconds = 30  # Duration of recording

            my_recording = sd.rec(int(seconds * fs), samplerate=fs, channels=2)
            sd.wait()  # Wait until recording is finished
            write('output.wav', fs, my_recording)  # Save as WAV file

            shazam = Shazam()
            out = await shazam.recognize_song('output.wav')
            track_title = out['track']['title']
            artist = out['track']['subtitle']

            payload = {"title": track_title, "artist": artist}
            payload_json = json.dumps(payload)
            print(payload_json)

            aio = Client(config.aio_username, config.aio_key)
            aio.send_data('audio', payload_json)

        except KeyError:
            pass

        # How long to wait before recording another sample in seconds
        time.sleep(180)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
