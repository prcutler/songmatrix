# SongMatrix

## Overview

SongMatrix uses a Raspberry Pi with a microphone to listen to the background music every few minutes. It then uses [`shazamio`](https://github.com/dotX12/ShazamIO) to identify the song and sends a MQTT message to the Adafruit IO MQTT broker.  The message is received on an Adafruit MatrixPortal and displays the artist and song title.

## Checklist

In addition to a little Python knowledge, you will need:

- [ ] Raspberry Pi single board computer (Any will do, I'm using an older Raspberry Pi 2 without issue)
- [ ] USB Microphone ([Adafruit](https://www.adafruit.com/product/3367))
- [ ] Adafruit MatrixPortal (Should work on either the newer [S3](https://www.adafruit.com/product/5778) or older [M4](https://www.adafruit.com/product/4745))
- [ ] Adafruit 32x64 RGB Matrix panel (I'm using a [2.5 pitch panel](https://www.adafruit.com/product/5036))
- [ ] [Adafruit IO](https://io.adafruit.com) account

## Demo

![A 32x64 Matrix displaying the song Breathing Underwater on the top row and the artist, Metric, on the bottom row](images/480p.gif)

## Installation

1. With your Raspberry Pi, clone the repo
2. In the `python` directory, create a `config.py` file with two fields:
* aio_username = "yourAdafruitIOusername"
* aio+key = "YourAPIKey"

3. Run `python record-identify.py` which starts an unending `while` loop. (`systemd` service coming soon)
4. In the `circuitpython` directory copy `songmatrix.py` to your MatrixPortal as `code.py`
5. Make sure your MatrixPortal's `settings.toml` includes your WiFi information and Adafruit IO credentials
