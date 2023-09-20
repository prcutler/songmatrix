# mqtt_asyncio_test.py -- try to run mqtt_client.loop() in asyncio without blocking other tasks
# 2 Sep 2023 - @todbot / Tod Kurt
# Note: looks like you need to set "socket_timemout" when creating mqtt_client
#       otherwise it blocks other asyncio tasks
import asyncio
import os
import socketpool
import ssl
import time
import wifi
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
import displayio
import adafruit_requests
import json
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_display_text.label
import terminalio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_display_text.scrolling_label import ScrollingLabel


mqtt_topic = "prcutler/feeds/audio"

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


# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()

requests = adafruit_requests.Session(pool, ssl.create_default_context())

displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display

aio = IO_HTTP(aio_username, aio_key, requests)

data2 = aio.receive_data('audio')
print('receive_data ' + data2['value'], type(data2))

data_string = data2['value']
print(data_string, type(data_string))

json_data = json.loads(data_string)
print(json_data, type(json_data))

song_artist = json_data['title']
song_title = json_data['artist']

song_title_scroll = song_title + '        '
song_artist_scroll = song_artist + '         '

title_scroll = ScrollingLabel(
    terminalio.FONT,
    text=song_title_scroll,
    max_characters=10,
    color=0xff0000,
    animate_time=0.3
)
title_scroll.x = 1
title_scroll.y = 8

artist_scroll = ScrollingLabel(
    terminalio.FONT,
    text=song_artist_scroll,
    max_characters=10,
    color=0x0080ff,
    animate_time=0.3
)
artist_scroll.x = 1
artist_scroll.y = 24

g = displayio.Group()
g.append(title_scroll)
g.append(artist_scroll)
display.show(g)


def connected(client, userdata, flags, rc):
    print("Subscribing to %s" % mqtt_topic)
    client.subscribe(mqtt_topic)


def disconnected(client, userdata, rc):
    print("Disconnected from MQTT Broker!")


def message(client, topic, payload):
    print("mqtt msg:", topic, payload)

    payload_data = json.loads(payload)
    print(payload_data, type(payload_data))

    song_artist = json_data['title']
    song_title = json_data['artist']

    time.sleep(3)
    artist_scroll.text = "Loading"
    time.sleep(3)

    song_title_scroll = song_title + '        '
    song_artist_scroll = song_artist + '         '

    title_scroll.text = song_title_scroll
    artist_scroll.text = song_artist_scroll
    time.sleep(3)


async def update_network():
    mqtt_client = MQTT.MQTT(
        broker="io.adafruit.com",
        port=1883,
        username=os.getenv('AIO_USERNAME'),
        password=os.getenv('AIO_KEY'),
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
        await asyncio.sleep(0.5)


async def update_ui():
    # this is where you'd update your screen at a regular framerate
    while True:
        title_scroll.update()
        artist_scroll.update()
        # print("hello:", time.monotonic())
        await asyncio.sleep(0.05)  # 20 Hz update rate


async def main():
    net_task = asyncio.create_task(update_network())
    ui_task = asyncio.create_task(update_ui())
    await asyncio.gather(net_task, ui_task)

asyncio.run(main())