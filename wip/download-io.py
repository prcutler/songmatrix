import asyncio
from Adafruit_IO import Client
import config
import json

aio = Client(config.aio_username, config.aio_key)

# Get the last value of the feed.
data = aio.receive('audio')

print(data)
