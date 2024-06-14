# Onkyo serial-based input remote control.
#
# This is a simple 4x3 keypad control for selecting the most common inputs on my Onkyo
# TX-RZ800 receiver. This receiver is a few years old and has a DB9 (gasp!) serial 
# port on the back for sending commands to and receiving status messages from the
# receiver. This protocol also works over WiFi to the receiver, but I thought I'd
# build it old-school using serial instead. The project uses the Adafruit Feather 
# ItsyBitsy M4 board, a TTL-to-RS232 line driver, 12 NKK lighted momentarily-on 
# pushbutton switches, 59711 LED controller for the switch LEDs, and a capacitive
# touch sensor.
# 
# The 59711 library seems to map the pins backwards from the 58711 chip. Here's the mapping.
#
# leds[0] channels 0, 1, 2   == RGB3
# leds[1] channels 3, 4, 5   == RGB2
# leds[2] channels 6, 7, 8   == RGB1
# leds[3] channels 9, 10, 11 == RGB0
#
# leds.set_channel(0, 65535) # R3
# leds.set_channel(1, 65535) # G3
# leds.set_channel(2, 65535) # B3
# leds.set_channel(3, 65535) # R2
# leds.set_channel(4, 65535) # G2
# leds.set_channel(5, 65535) # B2
# leds.set_channel(6, 65535) # R1
# leds.set_channel(7, 65535) # G1
# leds.set_channel(8, 65535) # B1
# leds.set_channel(9, 65535) # R0
# leds.set_channel(10, 65535//6) # G0
# leds.set_channel(11, 65535) # B0
#
# LED states
# * All LED off: receiver is off
# * One LED on: receiver is on the indicated channel
# * All LEDs on: prox sensor tripped
#
# There's also a dimmer button on the bottom to control the LED brightness.
# 
# (c) Doug Gaff 2023, All Rights Reserved

import time
import board
import busio
import digitalio
import keypad
import adafruit_tlc59711
from adafruit_debouncer import Debouncer

# Create the keypad
# https://learn.adafruit.com/key-pad-matrix-scanning-in-circuitpython/keymatrix
km = keypad.KeyMatrix(
    row_pins=(board.A0, board.A1, board.A2, board.A3),
    column_pins=(board.D7, board.D9, board.D10),
)

# Create the UART
uart = busio.UART(board.TX, board.RX, baudrate=9600)

# Create SPI bus for LED control
spi = busio.SPI(clock=board.SCK, MOSI=board.MOSI)
leds = adafruit_tlc59711.TLC59711(spi)

# Setup prox sensor input pin
prox_trigger = digitalio.DigitalInOut(board.D11)
prox_trigger.direction = digitalio.Direction.INPUT

# Setup dimmer button
dim_pin = digitalio.DigitalInOut(board.D12)
dim_pin.direction = digitalio.Direction.INPUT
dim_pin.pull = digitalio.Pull.DOWN
dim_button = Debouncer(dim_pin)

# Dim levels
dim_levels = [65535, 20000, 2000]  # Don't go below 1000 or the fade out will throw an error
dim_index = 0

# Serial status codes for the various inputs. Variable name matches button on the
# front of the receiver. The comment reflects how it's actually wired in my setup.
DVD = '1SLI10'       # CD/DVD/BlueRay
CBL = '1SLI01'       # Apple TV
STM = '1SLI11'       # Switch
PC = '1SLI05'        # WII
G1 = '1SLI02'        # Turntable
G2 = '1SLI04'        # Namco old school game controller
AUX = '1SLI03'       # Front aux input
CD  = '1SLI23'       # Cassette tape deck
PHN = '1SLI22'       # (not used by me) Phono -- no way to bypass the internal preamp
TV = '1SLI12'        # TV
TUN = '1SLI26'       # AM/FM - goes to the last selected tuner
FM = '1SLI24'        # FM tuner
AM = '1SLI25'        # AM tuner
NET = '1SLI2B'       # Spotify/Airplay/Etc.
BLUETOOTH = '1SLI2E' # (not used by me) Bluetooth -- I use airplay instead
PWR_OFF = '1PWR00'   # I monitor for power off to turn off the button lights.

# Button command mapping. This is how the keypad is laid out.
#   +-------+-------+--------+
#   |  TV   | PHONO |  TAPE  |
#   +-------+-------+--------+
#   |  CD   |  NET  | SWITCH |
#   +-------+-------+--------+
#   |  WII  | NAMCO | APPLE  |
#   +-------+-------+--------+
#   |  AUX  |  TUN  |  OFF   |
#   +-------+-------+--------+

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

# Button LED state.
last_button_id = -1

# Serial receive data buffer.
data_buffer = ''

# Proximity and fade-out variables.
prox_fadeout = False
power_off_fadeout = False
led_fade_timer_ns = 0
led_fade_level = 0

# Reboot flag to request channel and receiver status
first_boot = True

# Main event loop
while True:
    # Sending these two commands on boot will make sure the right button lights up. If the power is off,
    # the last mode will light up and then will turn off. If the power is on, the appropriate channel
    # light will stay lit.
    if first_boot:
        uart.write(bytes("!1SLIQSTN\r",'ascii'))
        uart.write(bytes("!1PWRQSTN\r",'ascii'))
        first_boot = False

    # Process any button events. See https://docs.circuitpython.org/en/latest/shared-bindings/keypad/index.html
    event = km.events.get()
    if event:
        # print(event)    
        if event.pressed:
            if event.key_number in button_mapping:
                send_str = '!' + button_mapping[event.key_number] + '\r'
                send_bytes = bytes(send_str, 'ascii') 
                uart.write(send_bytes)

    # Prox triggered. Light up everything. The prox will keep resetting the fade out timer until
    # proximity is no longer detected.
    if prox_trigger.value:
        # Hold all the lights on for 3 seconds before starting the fade out.
        led_fade_timer_ns = time.monotonic_ns() + 3000000000  
        led_fade_level = dim_levels[dim_index]
        prox_fadeout = True

        # All lights on.    
        for i in range(12): leds.set_channel(i, dim_levels[dim_index]) 
        leds.show()

    # Handle a fadeout until it's done.
    if (power_off_fadeout or (prox_fadeout and not prox_trigger.value)) and time.monotonic_ns() > led_fade_timer_ns:
        # Go to the next fade level
        led_fade_level -= 1000
        if led_fade_level < 1000: led_fade_level = 0

        # If this is a power off fade out, only fade out the power button.
        if power_off_fadeout:
            leds.set_channel(11, led_fade_level)
        # Otherwise this is a prox fade-out, fade out all buttons except selected one.
        else:
            for i in range(12): 
                # if last_button_id == 11 or i != last_button_id:
                if i != last_button_id:
                    leds.set_channel(i, led_fade_level)
        leds.show()

        # Are we done fading?
        if led_fade_level == 0:
            if last_button_id == 11 and prox_fadeout:
                power_off_fadeout = True
                led_fade_timer_ns = time.monotonic_ns() + 1000000000 
                led_fade_level = dim_levels[dim_index]
                prox_fadeout = False
            else:
                power_off_fadeout = False            
                prox_fadeout = False            
                led_fade_timer_ns = 0
        else:
            led_fade_timer_ns = time.monotonic_ns() + 15000000  # 15 ms fade interval

    # Handle dimming button. 
    dim_button.update()
    if dim_button.fell:
        # Move to next dim level
        dim_index += 1
        if dim_index == 3: dim_index = 0

        # Change button brightness unless the power is off.
        if last_button_id != 11: 
            leds.set_channel(last_button_id, dim_levels[dim_index])
            leds.show()

    # Process UART communications.
    if uart.in_waiting > 0:
        num_bytes = uart.in_waiting
        data = uart.read(num_bytes)  
        # print("raw data ")
        # print (data)  # this is a bytearray type

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
                    # if len(command) > 0: print("command message " + command)

                    # remove EOF 
                    cmd_str = command.replace((b'\x1a').decode('ascii'),'')

                    # is this command mapped to a button?
                    if cmd_str in status_mapping:
                        # get the new button id based on the command string
                        # todo current_button_id
                        last_button_id = int(status_mapping[cmd_str])

                        # Special power off case. When power off is pressed, it lights up for one second and
                        # then fades out to a fully off keypad.
                        if cmd_str == PWR_OFF:
                            # Turn out all lights and turn on the power off light.
                            for i in range(12): 
                                leds.set_channel(i, 0)
                            leds.set_channel(11, dim_levels[dim_index])
                            leds.show()

                            # Setup a fadeout for the power off button. Reset prox fadeout if it was in progress.
                            power_off_fadeout = True
                            led_fade_timer_ns = time.monotonic_ns() + 1000000000 
                            led_fade_level = dim_levels[dim_index]
                            prox_fadeout = False
                        # All other button cases when the power is on.
                        else: 
                            # Turn off all buttons except the one selected.
                            for i in range(12): 
                                if i != last_button_id: leds.set_channel(i, 0)

                            # Turn on the new button.
                            # print("button to light " + str(last_button_id + 1))
                            leds.set_channel(last_button_id, dim_levels[dim_index])
                            leds.show()

                            # Reset the prox sensor fadeout if it was in progress.
                            prox_fadeout = False
                            led_fade_timer_ns = 0

                # clear the buffer
                data_buffer = ""
