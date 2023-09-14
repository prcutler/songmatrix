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


# Define callback functions which will be called when certain events happen.
# pylint: disable=unused-argument
def connected(client):
    # Connected function will be called when the client is connected to Adafruit IO.
    # This is a good place to subscribe to feed changes.  The client parameter
    # passed to this function is the Adafruit IO MQTT client so you can make
    # calls against it easily.
    print("Connected to Adafruit IO!  Listening for DemoFeed changes...")
    # Subscribe to changes on a feed named DemoFeed.
    client.subscribe("audio")


def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


# pylint: disable=unused-argument
def disconnected(client):
    # Disconnected function will be called when the client disconnects.
    print("Disconnected from Adafruit IO!")


# pylint: disable=unused-argument
def message(client, feed_id, payload):
    # Message function will be called when a subscribed feed has a new value.
    # The feed_id parameter identifies the feed, and the payload parameter has
    # the new value.
    print("Feed {0} received new value: {1}".format(feed_id, payload))

    json_data = json.loads(payload)
    print(json_data)
    title = json_data['title']
    artist = json_data['artist']
    print(artist, title)


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

requests = adafruit_requests.Session(pool, ssl.create_default_context())

aio = IO_HTTP(aio_username, aio_key, requests)

data2 = aio.receive_data('audio')
print('receive_data ' + data2['value'], type(data2))


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


get_song_data()


# This function will scoot one label a pixel to the left and send it back to
# the far right if it's gone all the way off screen. This goes in a function
# because we'll do exactly the same thing with line1 and line2 below.
def scroll(line):
    line.x = line.x - 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width


# You can add more effects in this loop. For instance, maybe you want to set the
# color of each label to a different value.
#while True:
#    scroll(line1)
#    scroll(line2)
#    display.refresh(minimum_frames_per_second=0)
#    time.sleep(0.02)
 #   io.loop()


async def update_network():
    mqtt_client = MQTT.MQTT(
        broker="io.adafruit.com",
        port=1883,
        username = os.getenv('AIO_USERNAME'),
        password = os.getenv('AIO_KEY'),
        socket_pool=pool,
        ssl_context=ssl_context,
        is_ssl=False,
        socket_timeout=0.01  # apparently socket recvs even block asyncio
    )

    mqtt_client.on_connect = connected
    mqtt_client.on_disconnect = disconnected
    mqtt_client.on_message = message

    print("Connecting to MQTT broker...")
    mqtt_client.connect()

    while True:
        try:
            mqtt_client.loop()
        except RuntimeError or ConnectionError:
            await asyncio.sleep(10)
            mqtt_client.connect()
            mqtt_client.loop()
        await asyncio.sleep(0.1)


async def update_ui():
    # this is where you'd update your screen at a regular framerate
    while True:
        print("hello:", time.monotonic())
        await asyncio.sleep(0.05) # 20 Hz update rate


async def main():
    net_task = asyncio.create_task(update_network())
    ui_task = asyncio.create_task(update_ui())
    await asyncio.gather(net_task, ui_task)


asyncio.run(main())