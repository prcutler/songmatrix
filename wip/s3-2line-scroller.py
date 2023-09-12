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

# Create two lines of text to scroll. Besides changing the text, you can also
# customize the color and font (using Adafruit_CircuitPython_Bitmap_Font).
# To keep this demo simple, we just used the built-in font.
# The Y coordinates of the two lines were chosen so that they looked good
# but if you change the font you might find that other values work better.
line1 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xff0000,
    text="This scroller is brought to you by CircuitPython RGBMatrix")
line1.x = display.width
line1.y = 8

line2 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0x0080ff,
    text="Hello to all CircuitPython contributors worldwide <3")
line2.x = display.width
line2.y = 24

# Put each line of text into a Group, then show that group.
g = displayio.Group()
g.append(line1)
g.append(line2)
display.show(g)

# This function will scoot one label a pixel to the left and send it back to
# the far right if it's gone all the way off screen. This goes in a function
# because we'll do exactly the same thing with line1 and line2 below.
def scroll(line):
    line.x = line.x - 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width

# This function scrolls lines backwards.  Try switching which function is
# called for line2 below!
def reverse_scroll(line):
    line.x = line.x + 1
    line_width = line.bounding_box[2]
    if line.x >= display.width:
        line.x = -line_width

# You can add more effects in this loop. For instance, maybe you want to set the
# color of each label to a different value.
while True:
    scroll(line1)
    scroll(line2)
    #reverse_scroll(line2)
    display.refresh(minimum_frames_per_second=0)

