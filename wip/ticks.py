# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import os
import ssl
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import socketpool
import wifi
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
import json
import adafruit_requests
from adafruit_matrixportal.matrixportal import MatrixPortal
import terminalio
import displayio
from adafruit_matrixportal.matrix import Matrix
import adafruit_display_text.label
import time
import asyncio
from adafruit_ticks import ticks_ms, ticks_add, ticks_diff

### WiFi ###

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    if os.getenv("AIO_USERNAME") and os.getenv("AIO_KEY"):
        secrets = {
            "aio_username": os.getenv("AIO_USERNAME"),
            "aio_key": os.getenv("AIO_KEY"),
            "ssid": os.getenv("CIRCUITPY_WIFI_SSID"),
            "password": os.getenv("CIRCUITPY_WIFI_PASSWORD"),
        }
    else:
        from secrets import secrets
except ImportError:
    print(
        "WiFi + Adafruit IO secrets are kept in secrets.py or settings.toml, please add them there!"
    )
    raise

# Set your Adafruit IO Username and Key in secrets.py
# (visit io.adafruit.com if you need to create an account,
# or if you need your Adafruit IO key.)
aio_username = secrets["aio_username"]
aio_key = secrets["aio_key"]

if not wifi.radio.connected:
    print("Connecting to %s" % secrets["ssid"])
    wifi.radio.connect(secrets["ssid"], secrets["password"])
    print("Connected to %s!" % secrets["ssid"])


displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display

mqtt_topic = "prcutler/feeds/audio"

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

requests = adafruit_requests.Session(pool, ssl.create_default_context())

# Initialize a new MQTT Client object
mqtt_client = MQTT.MQTT(
    broker="io.adafruit.com",
    port=8883,
    username=secrets["aio_username"],
    password=secrets["aio_key"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
    is_ssl=True,
)

# Initialize an Adafruit IO MQTT Client
io = IO_MQTT(mqtt_client)

aio = IO_HTTP(aio_username, aio_key, requests)
io.connect()

data2 = aio.receive_data('audio')
print('receive_data ' + data2['value'], type(data2))

data_string = data2['value']
print(data_string, type(data_string))

json_data = json.loads(data_string)
print(json_data, type(json_data))

song_title = json_data['title']
song_artist = json_data['artist']

text_color = 0xff0000
# how often to check for a new trigger from ToF
pause_time = 30  # seconds
# speed for scrolling the text on the matrix
scroll_time = 0.1  # seconds

line1 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=text_color,
    text=song_title)
line1.x = 1
line1.y = 8

line2 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0x0080ff,
    text=song_artist)
line2.x = 1
line2.y = 24


def scroll(line):
    line.x = line.x - 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width


g = displayio.Group()
g.append(line1)
g.append(line2)

display.show(g)


def get_song_data():
    data_string = data2['value']
    print(data_string, type(data_string))

    json_data = json.loads(data_string)
    print(json_data, type(json_data))

    song_artist = json_data['title']
    song_title = json_data['artist']

    # Create two lines of text to scroll. Besides changing the text, you can also
    # customize the color and font (using Adafruit_CircuitPython_Bitmap_Font).
    # To keep this demo simple, we just used the built-in font.
    # The Y coordinates of the two lines were chosen so that they looked good
    # but if you change the font you might find that other values work better.
    line1 = adafruit_display_text.label.Label(
        terminalio.FONT,
        color=0xff0000,
        text=song_artist)
    line1.x = display.width
    line1.y = 8

    line2 = adafruit_display_text.label.Label(
        terminalio.FONT,
        color=0x0080ff,
        text=song_title)
    line2.x = display.width
    line2.y = 24

    # Put each line of text into a Group, then show that group.
    g = displayio.Group()
    g.append(line1)
    g.append(line2)
    display.show(g)


clock = ticks_ms()
the_time = 5000
x = 0
scroll_clock = ticks_ms()
scroll_time = int(scroll_time * 1000)
pause_clock = ticks_ms()
pause_time = pause_time * 1000
pause = False

# You can add more effects in this loop. For instance, maybe you want to set the
# color of each label to a different value.
while True:
    if ticks_diff(ticks_ms(), scroll_clock) >= scroll_time:
        print("Scroll line 1")
        scroll(line1)
        print("Scroll line 2")
        scroll(line2)
        display.refresh(minimum_frames_per_second=0)
        scroll_clock = ticks_add(scroll_clock, scroll_time)
