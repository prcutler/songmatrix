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
from adafruit_display_text.scrolling_label import ScrollingLabel


# This program uses two 64x32 LED matrices to display the current song title and artist playing on ListenBrainz.

LISTENBRAINZ_USER = "silwenae"
LISTENBRAINZ_API = "https://api.listenbrainz.org/1"
POLL_INTERVAL = 30  # seconds


# WIFI SETUP
def connect_wifi():
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


def reset():
    if wifi:
        pass
    else:
        esp.reset()
        # pass

# NETWORK SETUP
time.sleep(3)  # wait for serial

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


# LISTENBRAINZ
def get_now_playing():
    """Return the currently playing track for LISTENBRAINZ_USER, falling back
    to their most recent listen if nothing is playing right now."""
    try:
        response = requests.get(f"{LISTENBRAINZ_API}/user/{LISTENBRAINZ_USER}/playing-now")
        data = response.json()
        response.close()
        listens = data.get("payload", {}).get("listens", [])
        if listens:
            return listens[0]

        response = requests.get(f"{LISTENBRAINZ_API}/user/{LISTENBRAINZ_USER}/listens?count=1")
        data = response.json()
        response.close()
        listens = data.get("payload", {}).get("listens", [])
        if listens:
            return listens[0]
    except Exception as ex:
        print(f"ListenBrainz request failed: {ex}")

    return None


def scroll_text(text):
    spaces = ' ' * (21 - len(text))
    return text + spaces


song_title = "Loading..."
song_artist = "ListenBrainz"

try:
    connect_wifi()
    listen = get_now_playing()
    if listen:
        metadata = listen.get("track_metadata", {})
        song_title = metadata.get("track_name", "Unknown track")
        song_artist = metadata.get("artist_name", "Unknown artist")
        print("Song: ", song_title + " by " + song_artist)
except Exception as ex:
    print(f"Exception: {ex}")

# Baseline y-position of each line. base_alignment anchors to the text
# baseline instead of the glyph bounding box, so title/artist line up the
# same way regardless of which letters (ascenders/descenders) each one has.
TITLE_Y = 14
ARTIST_Y = 30

title_scroll = ScrollingLabel(
    terminalio.FONT,
    text=scroll_text(song_title),
    max_characters=20,
    color=0xff0000,
    animate_time=0.3,
    base_alignment=True
)
title_scroll.x = 1
title_scroll.y = TITLE_Y

artist_scroll = ScrollingLabel(
    terminalio.FONT,
    text=scroll_text(song_artist),
    max_characters=20,
    color=0xFFFFFF,
    animate_time=0.3,
    base_alignment=True
)
artist_scroll.x = 1
artist_scroll.y = ARTIST_Y

g = displayio.Group()
g.append(title_scroll)
g.append(artist_scroll)
display.root_group = g

while True:
    try:
        connect_wifi()
        break
    except Exception or OSError as ex:
        print(f"Exception: {ex} Resetting wifi...")
        reset()
        time.sleep(1)


# ASYNC

async def update_now_playing():
    global song_title, song_artist
    while True:
        try:
            connect_wifi()
            listen = get_now_playing()
            if listen:
                metadata = listen.get("track_metadata", {})
                new_title = metadata.get("track_name", "Unknown track")
                new_artist = metadata.get("artist_name", "Unknown artist")
                if new_title != song_title or new_artist != song_artist:
                    print("Song: ", new_title + " by " + new_artist)
                    song_title = new_title
                    song_artist = new_artist
                    title_scroll.text = scroll_text(song_title)
                    artist_scroll.text = scroll_text(song_artist)
        except (RuntimeError, ConnectionError) as ex:
            print(f"Exception: {ex} Resetting wifi...")
            reset()
        await asyncio.sleep(POLL_INTERVAL)


async def update_ui():
    while True:
        title_scroll.update()  # optional: force=True
        artist_scroll.update()
        display.refresh(minimum_frames_per_second=0)
        await asyncio.sleep(0.1)


async def main():
    now_playing_task = asyncio.create_task(update_now_playing())
    ui_task = asyncio.create_task(update_ui())
    await asyncio.gather(now_playing_task, ui_task)

asyncio.run(main())
