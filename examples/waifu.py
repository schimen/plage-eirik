#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Adafruit_GPIO as GPIO
import Adafruit_GPIO.SPI as SPI

import ST7789 as TFT

from PIL import Image, ImageDraw, ImageFont, ImageColor

import numpy as np

# Raspberry Pi pin configuration:
RST = 25
DC  = 24
LED = 27
SPI_PORT = 0
SPI_DEVICE = 0
SPI_MODE = 0b11
SPI_SPEED_HZ = 40000000


disp = TFT.ST7789(spi=SPI.SpiDev(SPI_PORT, SPI_DEVICE, max_speed_hz=SPI_SPEED_HZ),
       mode=SPI_MODE, rst=RST, dc=DC, led=LED)

# Initialize display.
disp.begin()

# Clear display.
disp.clear()

# Analogue clock setting
width = 240
height = 240


# Initial screen (Demonstration for displaying images)
image = Image.open('waifu.jpg').resize((width, height))
disp.display(image)
