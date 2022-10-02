"""
configure which pins the equipment is connected to
"""

import RPi.GPIO as GPIO
gpioMode = GPIO.BOARD
qos = 0
gpioOutputPin = 26

gpioInputPin = 19
gpioInputGnd = True 

# IP addresses for keys to send signals to

IPS = ['localhost', '192.168.20.115']
