"""
configure which pins the equipment is connected to
"""

import RPi.GPIO as GPIO
gpioMode = GPIO.BOARD
qos = 0

gpioOutputPin = 12
gpioInputPin = 18
gpioInputGnd = False

randomAmount = 0.05 

# IP addresses for keys to send signals to

IPS = ['localhost']
