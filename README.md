# SongMatrix

## Overview

SongMatrix uses a Raspberry Pi with a microphone to listen to the background music every few minutes. It then uses shazamio to identify the song and sends a MQTT message to the Adafruit IO MQTT broker.  The message is received on an Adafruit MatrixPortal and displays the artist and song title.

# Checklist

[ ] Raspberry Pi single board computer (Any will do, I'm using an older Raspberry Pi 2 without issue)

[ ] USB Microphone 

[ ] Adafruit MatrixPortal (Should work on either the newer S3 or older M4)
