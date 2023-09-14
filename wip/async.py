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

mqtt_topic = "prcutler/feeds/audio"

wifi.radio.connect(os.getenv('CIRCUITPY_WIFI_SSID'),
                   os.getenv('CIRCUITPY_WIFI_PASSWORD'))
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
print("Connected to wifi, my IP:", wifi.radio.ipv4_address)

displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display


def connected(client, userdata, flags, rc):
    print("Subscribing to %s" % mqtt_topic)
    client.subscribe(mqtt_topic)


def disconnected(client, userdata, rc):
    print("Disconnected from MQTT Broker!")


def message(client, topic, payload):
    print("mqtt msg:", topic, payload)


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