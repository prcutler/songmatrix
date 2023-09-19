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

# Set up RGB Matrix display
displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display

# data_string = {"title": "Flowin' Prose", "artist": "Beastie Boys"}
#data = json.dumps(data_string)

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


### Code ###
# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Subscribing to %s" % mqtt_topic)
    client.subscribe(mqtt_topic)


def subscribe(client, userdata, topic, granted_qos):
    # This method is called when the client subscribes to a new feed.
    print("Subscribed to {0} with QOS level {1}".format(topic, granted_qos))


def unsubscribe(client, userdata, topic, pid):
    # This method is called when the client unsubscribes from a feed.
    print("Unsubscribed from {0} with PID {1}".format(topic, pid))


def disconnected(client, userdata, rc):
    # This method is called when the client is disconnected
    print("Disconnected from MQTT Broker!")


def message(client, topic, payload):
    """Method called when a client's subscribed feed has a new
    value.
    :param str topic: The topic of the feed with a new value.
    :param str payload: The new value
    """
    print(topic, payload)

    # payload = {"title": "Flowin' Prose", "artist": "Beastie Boys"}
    # data = json.dumps(payload)

    print(g[0])
    # g = displayio.Group()
    g.pop(1)
    g.pop(0)

    time.sleep(3)

    json_data = json.loads(payload)
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

    g.append(title_scroll)
    g.append(artist_scroll)
    # display.show(g)
    title_scroll.update()
    artist_scroll.update()


# Set up the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected
mqtt_client.on_message = message

print("Connecting to MQTT broker...")
mqtt_client.connect()

while True:
    title_scroll.update()
    artist_scroll.update()
    mqtt_client.loop()
