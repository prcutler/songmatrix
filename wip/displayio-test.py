import time
import displayio
from adafruit_matrixportal.matrix import Matrix
from adafruit_matrixportal.matrixportal import MatrixPortal
import adafruit_display_text.label
import terminalio
import json


displayio.release_displays()
matrix = Matrix(width=64, height=32, bit_depth=3)
display = matrix.display

data_string = {"title": "Flowin' Prose", "artist": "Beastie Boys"}
data = json.dumps(data_string)

print(data, type(data))

json_data = json.loads(data)
print(json_data, type(json_data))

song_artist = json_data['title']
song_title = json_data['artist']


line1 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xff0000,
    text=song_artist)
line1.x = 1
line1.y = 8

line2 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0x0080ff,
    text=song_title)
line2.x = 1
line2.y = 24

# Put each line of text into a Group, then show that group.
g = displayio.Group()
g.append(line1)
g.append(line2)
display.show(g)

time.sleep(5)

g.pop(1)
g.pop(0)

line3 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0x0080ff,
    text=song_title)
line3.x = 1
line3.y = 8

line4 = adafruit_display_text.label.Label(
    terminalio.FONT,
    color=0xff0000,
    text=song_artist)
line4.x = 1
line4.y = 24

g.append(line3)
g.append(line4)
display.show(g)

time.sleep(5)


def scroll(line):
    line.x = line.x - 1
    line_width = line.bounding_box[2]
    if line.x < -line_width:
        line.x = display.width


while True:
    scroll(line3)
    scroll(line4)
    time.sleep(0.1)