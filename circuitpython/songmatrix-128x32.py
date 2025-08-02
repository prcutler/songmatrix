import socketpool
import ssl
import wifi
import adafruit_requests
import asyncio
import os
import time
import displayio
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException
import json
from adafruit_display_text.scrolling_label import ScrollingLabel


# This program uses two 64x32 LED matrices to display the current song title and artist that is playing.

# WIFI SETUP
def connect_wifi_mqtt():
    if wifi:
        while not wifi.radio.connected:
            print("Connecting to wifi...")
            wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
            time.sleep(1)
    else:
        while not esp.is_connected:
            print("Connecting to wifi...")
            esp.connect_AP(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
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

# NETWORK AND ADAFRUIT IO SETUP
time.sleep(3)  # wait for serial

mqtt_topic = "prcutler/feeds/audio"
aio_username = os.getenv("AIO_USERNAME")
aio_key = os.getenv("AIO_KEY")

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl.create_default_context())

displayio.release_displays()

matrix = rgbmatrix.RGBMatrix(
    width=128, bit_depth=2,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)

display = framebufferio.FramebufferDisplay(matrix, auto_refresh=False)

aio = IO_HTTP(aio_username, aio_key, requests)

try:
    data = aio.receive_data('audio')
    print(data, type(data))

    data_json = json.loads(data["value"])
    print(data_json)
    print("Song: ", data_json["title"] + " by " + data_json["artist"])

    song_title = data_json["title"]
    song_artist = data_json["artist"]

    song_length = len(song_title)
    artist_length = len(song_artist)

    song_spaces = ' ' * (21 - song_length)
    artist_spaces = ' ' * (21 - artist_length)

    song_title_scroll = song_title + song_spaces
    song_artist_scroll = song_artist + artist_spaces

    title_scroll = ScrollingLabel(
        terminalio.FONT,
        text=song_title_scroll,
        max_characters=20,
        color=0xff0000,
        animate_time=0.3
    )
    title_scroll.x = 1
    title_scroll.y = 8

    artist_scroll = ScrollingLabel(
        terminalio.FONT,
        text=song_artist_scroll,
        max_characters=20,
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

# MQTT
def connected(client, userdata, flags, rc):
    print("Subscribing to %s" % mqtt_topic)
    client.subscribe(mqtt_topic)


def disconnected(client, userdata, rc):
    print("Disconnected from MQTT Broker!")


def publish(client, userdata, topic, pid):
    print('Published to {0} with PID {1}'.format(topic, pid))


def message(client, topic, payload):
    print("mqtt msg:", topic, payload)

    payload_data = json.loads(payload)
    print(payload_data, type(payload_data))

    print("Song: ", payload_data["title"] + " by " + payload_data["artist"])

    song_title = payload_data["title"]
    song_artist = payload_data["artist"]

    song_length = len(song_title)
    artist_length = len(song_artist)

    song_spaces = ' ' * (21 - song_length)
    artist_spaces = ' ' * (21 - artist_length)

    song_title_scroll = song_title + song_spaces
    song_artist_scroll = song_artist + artist_spaces

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
        display.refresh(minimum_frames_per_second=0)
        await asyncio.sleep(0.1)


async def main():
    net_task = asyncio.create_task(update_network())
    ui_task = asyncio.create_task(update_ui())
    await asyncio.gather(net_task, ui_task)

asyncio.run(main())
