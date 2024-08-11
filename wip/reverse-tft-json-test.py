# SPDX-FileCopyrightText: 2024 Liz Clark for Adafruit Industries
#
# SPDX-License-Identifier: MIT

import os
import time
import wifi
import board
import displayio
import socketpool
import ssl
import adafruit_requests
import asyncio
import microcontroller
from adafruit_bitmap_font import bitmap_font
from adafruit_display_text import bitmap_label
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_io.adafruit_io import IO_MQTT, IO_HTTP
import json


wifi.radio.connect(os.getenv("CIRCUITPY_WIFI_SSID"), os.getenv("CIRCUITPY_WIFI_PASSWORD"))
pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(pool, ssl.create_default_context())

display = board.DISPLAY
group = displayio.Group()

mqtt_topic = "prcutler/feeds/jsontest"
aio_username = os.getenv("AIO_USERNAME")
aio_key = os.getenv("AIO_KEY")

aio = IO_HTTP(aio_username, aio_key, requests)

data = aio.receive_data('jsontest')
print(data, type(data))

data_json = json.loads(data["value"])
print(data_json)
print("Song: ", data_json["title"] + " by " + data_json["artist"])
