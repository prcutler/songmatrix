wifi = None

import socketpool
import ssl
import wifi
import adafruit_requests
import random
import asyncio
import os
import time
import displayio
import json
from adafruit_matrixportal.matrix import Matrix
import terminalio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException
from adafruit_display_text.scrolling_label import ScrollingLabel
import json


mqtt_topic = "prcutler/feeds/audio"


def connect_wifi_mqtt():
    if wifi:
        while not wifi.radio.connected:
            print("Connecting to wifi...")
            wifi.radio.connect(secrets["ssid"], secrets["password"])
            time.sleep(1)
    else:
        while not esp.is_connected:
            print("Connecting to wifi...")
            esp.connect_AP(secrets["ssid"], secrets["password"])
            time.sleep(1)
    while not mqtt_client.is_connected():
        print(f"Connecting to AIO...")
        mqtt_client.connect()
        time.sleep(1)


def reset():
    if wifi:
        pass
    else:
        esp.reset()
        # pass


# NETWORK SETUP

time.sleep(3)  # wait for serial

aio_username = os.getenv("AIO_USERNAME")
aio_key = os.getenv("AIO_KEY")

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl.create_default_context())

# DISPLAYIO SETUP

displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display

aio = IO_HTTP(aio_username, aio_key, requests)

try:
    data2 = aio.receive_data('audio')
    print(data2)
    print('receive_data ' + data2['value'], type(data2))

    song_data = str(data2['value'])
    print(song_data)

    song_string = song_data.split(" by ", 1)

    song_title = song_string[0]
    song_artist = song_string[1]

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
        color=0xFFFFFF,
        animate_time=0.3
    )
    artist_scroll.x = 1
    artist_scroll.y = 24

    g = displayio.Group()
    g.append(title_scroll)
    g.append(artist_scroll)
    display.root_group = g

except:
    print("Adafruit IO reports 404 Error - is your feed empty?  Start recording.")


# MQTT SETUP

def connected(client, userdata, flags, rc):
    print("Subscribing to %s" % mqtt_topic)
    client.subscribe(mqtt_topic)


def disconnected(client, userdata, rc):
    print("Disconnected from MQTT Broker!")


def publish(client, userdata, topic, pid):
    print('Published to {0} with PID {1}'.format(topic, pid))


def message(client, topic, payload):
    print("mqtt msg:", topic, payload)

    # payload_data = json.loads(payload)
    # print(payload_data, type(payload_data))

    song_data = str(payload)

    song_string = song_data.split(" by ", 1)

    song_title = song_string[0]
    song_artist = song_string[1]

    song_title_scroll = song_title + '        '
    song_artist_scroll = song_artist + '         '

    title_scroll.text = song_title_scroll
    artist_scroll.text = song_artist_scroll
    time.sleep(3)


if wifi:
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
else:
    mqtt_client = MQTT.MQTT(
        broker="io.adafruit.com",
        username=os.getenv('AIO_USERNAME'),
        password=os.getenv('AIO_KEY'),
        socket_timeout=0.01  # apparently socket recvs even block asyncio
    )
    MQTT.set_socket(socket, esp)

mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message
mqtt_client.on_publish = publish

while True:
    try:
        connect_wifi_mqtt()
        break
    except Exception or OSError as ex:
        print(f"Exception: {ex} Resetting wifi...")
        reset()
        time.sleep(1)


# ASYNC

async def update_network():
    while True:
        try:
            connect_wifi_mqtt()
            mqtt_client.loop(0.2)
        except (RuntimeError, ConnectionError, MMQTTException) as ex:
            print(f"Exception: {ex} Resetting wifi...")
            reset()
            time.sleep(1)
        await asyncio.sleep(1)


async def update_ui():
    while True:
        title_scroll.update()  # optional: force=True
        artist_scroll.update()
        await asyncio.sleep(0.1)


async def main():
    net_task = asyncio.create_task(update_network())
    ui_task = asyncio.create_task(update_ui())
    await asyncio.gather(net_task, ui_task)

asyncio.run(main())
