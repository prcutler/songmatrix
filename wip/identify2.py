import asyncio
from Adafruit_IO import Client
from shazamio import Shazam
import config
import json
import sounddevice as sd
from scipy.io.wavfile import write


async def main():
    shazam = Shazam()
    out = await shazam.recognize_song('output.wav')
    track_title = out['track']['title']
    artist = out['track']['subtitle']
    print(track_title + ' by ' + artist)

    payload = {"title": track_title, "artist": artist}
    payload_json = json.dumps(payload)
    print(payload_json)

    # payload = track_title + " by " + artist

    aio = Client(config.aio_username, config.aio_key)
    aio.send_data('jsontest', payload_json)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
