# Some code snippets for when I was trying PWM.
#

import time
import board
import busio
import digitalio
import pwmio
import keypad

LED_BRIGHTNESS = 30000   # max is 65535

# Button LED PWM controls
#
# Originally I was going to PWM each LED, but I wasn't able to source enough current for each LED
# since the forward voltage of the diode is 3.3V. So I switched to a 58711 LED controller chip.
# Just leaving this in here for reference. 
#
# https://learn.adafruit.com/adafruit-feather-m4-express-atsamd51/circuitpython-pwm
# https://docs.circuitpython.org/en/latest/shared-bindings/pwmio/index.html 

button_LED_pins = [
    board.A1,
    board.A3,
    board.SCK,
    board.D4,
    board.SDA,
    board.SCL,
    board.D5,
    board.D9,
    board.D10,
    board.D11,
    board.D12,
    board.D13   
]

button_LEDs = [
    pwmio.PWMOut(board.A1, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.A3, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.SCK, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D4, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.SDA, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.SCL, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D5, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D9, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D10, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D11, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D12, frequency=5000, duty_cycle=LED_BRIGHTNESS),
    pwmio.PWMOut(board.D13, frequency=5000, duty_cycle=LED_BRIGHTNESS)
]

button_LEDs_on = [
    digitalio.DigitalInOut(board.A1),
    digitalio.DigitalInOut(board.A3),
    digitalio.DigitalInOut(board.SCK),
    digitalio.DigitalInOut(board.D4),
    digitalio.DigitalInOut(board.SDA),
    digitalio.DigitalInOut(board.SCL),
    digitalio.DigitalInOut(board.D5),
    digitalio.DigitalInOut(board.D9),
    digitalio.DigitalInOut(board.D10),
    digitalio.DigitalInOut(board.D11),
    digitalio.DigitalInOut(board.D12),
    digitalio.DigitalInOut(board.D13)
]

for button in button_LEDs_on:
    button.direction = digitalio.Direction.OUTPUT
    button.value = True

# Main event loop
while True:

    # Test code to cycle button brightness
    for i in range(100):
        # PWM LED up and down
        if i < 50:
            button_LEDs[0].duty_cycle = int(i * 2 * 65535 / 100)  # Up
        else:
            button_LEDs[0].duty_cycle = 65535 - int((i - 50) * 2 * 65535 / 100) 
        time.sleep(0.01)


    # TODO adjust as needed
    # time.sleep(0.02)
