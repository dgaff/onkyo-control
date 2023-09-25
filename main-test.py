# SPDX-FileCopyrightText: 2022 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from adafruit_neotrellis.neotrellis import NeoTrellis

import board
import busio
import digitalio


# create the i2c object for the trellis
i2c_bus = board.I2C()  # uses board.SCL and board.SDA
# i2c_bus = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# create the trellis
trellis = NeoTrellis(i2c_bus)

# Set the brightness value (0 to 1.0)
trellis.brightness = 0.5

# some color definitions
OFF = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)


# this will be called when button events are received
def blink(event):
    # turn the LED on when a rising edge is detected
    if event.edge == NeoTrellis.EDGE_RISING:
        trellis.pixels[event.number] = CYAN
        print("You pressed button # " + str(event.number))
    # turn the LED off when a falling edge is detected
    elif event.edge == NeoTrellis.EDGE_FALLING:
        trellis.pixels[event.number] = OFF

def rainbow():
    for i_color in range(8):
        for i in range(16):
            if i_color == 0: trellis.pixels[i] = OFF
            elif i_color == 1: trellis.pixels[i] = RED
            elif i_color == 2: trellis.pixels[i] = YELLOW
            elif i_color == 3: trellis.pixels[i] = GREEN
            elif i_color == 4: trellis.pixels[i] = CYAN
            elif i_color == 5: trellis.pixels[i] = BLUE
            elif i_color == 6: trellis.pixels[i] = PURPLE
            elif i_color == 7: trellis.pixels[i] = WHITE
        time.sleep(0.5)

def full_cycle():
    for r in range(0, 256, 20):
        for g in range(0, 256, 20):
            for b in range(0, 256, 20):
                trellis.pixels[0] = (r, g, b)

# Startup sequence
for i in range(16):
    # activate rising edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    # activate falling edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    # set all keys to trigger the blink callback
    trellis.callbacks[i] = blink

    # cycle the LEDs on startup
    trellis.pixels[i] = PURPLE
    time.sleep(0.05)

# Turn everything off
for i in range(16):
    trellis.pixels[i] = OFF
    time.sleep(0.05)

# From UART code to blink the LED
# For most CircuitPython boards:
# led = digitalio.DigitalInOut(board.LED)
# For QT Py M0:
# led = digitalio.DigitalInOut(board.SCK)
# led.direction = digitalio.Direction.OUTPUT

uart = busio.UART(board.TX, board.RX, baudrate=9600)

while True:
    # Rainbow display test
    # rainbow()

    # Full color cycle test
    # full_cycle()

    # Input test
    # call the sync function call any triggered callbacks
    trellis.sync()

    # UART test
    if uart.in_waiting > 0:
        num_bytes = uart.in_waiting
        data = uart.read(num_bytes)  
        # print(data)  # this is a bytearray type

        if data is not None:
            # led.value = True

            # convert bytearray to string
            data_string = ''.join([chr(b) for b in data])
            print(data_string, end="")

            # echo the typing
            send_bytes = bytes(data_string, 'ascii') # 'utf-8'
            uart.write(send_bytes)

            # led.value = False

    # the trellis can only be read every 17 milliseconds or so
    time.sleep(0.02)
