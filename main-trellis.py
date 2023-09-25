# SPDX-FileCopyrightText: 2022 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import board
from adafruit_neotrellis.neotrellis import NeoTrellis

import board
import busio
import digitalio

# Create the i2c object for the trellis
i2c_bus = board.I2C()  # uses board.SCL and board.SDA
# i2c_bus = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

# Create the trellis object
trellis = NeoTrellis(i2c_bus)

# Set the brightness value (0 to 1.0)
trellis.brightness = 0.5

# Some color definitions
OFF = (0, 0, 0)
RED = (255, 0, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
CYAN = (0, 255, 255)
BLUE = (0, 0, 255)
PURPLE = (180, 0, 255)
WHITE = (255, 255, 255)

# Serial status codes for the various inputs. Variable name matches button on receiver.
# Comment is how it's actually wired.
DVD = '1SLI10' # CD/DVD/BlueRay
CBL = '1SLI01' # Apple TV
STM = '1SLI11' # Switch
PC = '1SLI05'  # WII
G1 = '1SLI02'  # Turntable
G2 = '1SLI04'  # Namco  ## !!!CHECK THIS!!!
AUX = '1SLI03' # Front Input
CD  = '1SLI23' # Tape
PHN = '1SLI22' # (not used) Phono -- no way to bypass internal preamp
TV = '1SLI12'  # TV
TUN = '1SLI26' # AM/FM
FM = '1SLI24'
AM = '1SLI25'
NET = '1SLI2B' # Spotify/Airplay/Etc.
BLUETOOTH = '1SLI2E' # (not used) Bluetooth -- I use airplay rather than bluetooth
PWR_OFF = '1PWR00'

# Button command mapping
button_mapping = {
    0: TV,
    1: G1,
    2: CD,
    3: DVD,
    4: NET,
    5: STM,
    6: PC,
    7: G2,
    8: CBL,
    9: AUX,
    10: TUN,
    11: PWR_OFF
}

# Status messages mapping to button lights. Map extra channels to existing buttons.
status_mapping = {y: x for x, y in button_mapping.items()}
status_mapping[FM] = 10        # TUN
status_mapping[AM] = 10        # TUN
status_mapping[PHN] = 11       # PWR_OFF
status_mapping[BLUETOOTH] = 11 # PWR_OFF

# Create the UART
uart = busio.UART(board.TX, board.RX, baudrate=9600)

# This will be called when button events are received
def button_press(event):
    # turn the LED on when a rising edge is detected
    if event.edge == NeoTrellis.EDGE_RISING:
        # trellis.pixels[event.number] = CYAN
        if event.number in button_mapping:
            send_str = '!' + button_mapping[event.number] + '\r'
            send_bytes = bytes(send_str, 'ascii') 
            uart.write(send_bytes)

        print("You pressed button # " + str(event.number))
    # turn the LED off when a falling edge is detected
    # elif event.edge == NeoTrellis.EDGE_FALLING:
    #     trellis.pixels[event.number] = OFF

# Startup sequence
for i in range(16):
    # activate rising edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_RISING)
    # activate falling edge events on all keys
    trellis.activate_key(i, NeoTrellis.EDGE_FALLING)
    # set all keys to trigger the blink callback
    trellis.callbacks[i] = button_press

    # cycle the LEDs on startup
    trellis.pixels[i] = PURPLE
    time.sleep(0.05)

# Turn everything off
for i in range(16):
    trellis.pixels[i] = OFF
    time.sleep(0.05)

# Button light state
last_button_id = -1

# Serial receive data buffer.
data_buffer = ''

# Main event loop
while True:
    # Process any button events
    trellis.sync()

    # Process UART communications
    if uart.in_waiting > 0:
        num_bytes = uart.in_waiting
        data = uart.read(num_bytes)  
        print("raw data ")
        print (data)  # this is a bytearray type

        if data is not None:
            # add the received data to the buffer
            data_buffer += ''.join([chr(b) for b in data]) 

            # only process the data buffer when we've received an EOF. This handles the case when
            # the receive buffer is still filling up.
            if len(data_buffer) > 0 and data_buffer[len(data_buffer)-1] == (b'\x1a').decode('ascii'):
                # split the string into individual commands and process each one
                commands = data_buffer.split('!')
                for command in commands:
                    # print all the commands we receive
                    if len(command) > 0: print("command message " + command)

                    # remove EOF 
                    cmd_str = command.replace((b'\x1a').decode('ascii'),'')

                    # is this command mapped to a button?
                    if cmd_str in status_mapping:
                        # get the new button id based on the command string
                        button_id = int(status_mapping[cmd_str])

                        # turn the last button off if it's different
                        if last_button_id != -1 and last_button_id != button_id: trellis.pixels[last_button_id] = OFF

                        # turn on the new button. handle special case for the PWR_OFF button when it used to indicate
                        # a mode not mapped to a button on the panel
                        print("button to light " + str(button_id + 1))
                        if cmd_str != PWR_OFF: trellis.pixels[button_id] = WHITE

                        # store the light we just turned on
                        last_button_id = button_id

                # clear the buffer
                data_buffer = ""

    # the trellis can only be read every 17 milliseconds or so
    time.sleep(0.02)
