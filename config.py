"""
configure which pins the equipment is connected to
"""

import RPi.GPIO as GPIO
gpioMode = GPIO.BOARD

gpioOutputPin = 12
gpioInputPin = 18


# IP addresses for keys to send signals to

IPS = ['localhost', '10.0.0.1']
