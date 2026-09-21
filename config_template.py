"""
configure which pins the equipment is connected to
"""

import syslog
import RPi.GPIO as GPIO

message_client_name = 'telegraph'

gpioMode = GPIO.BOARD
qos = 0

gpioOutputPin=   12
gpioInputPin =   18
gpioInputGnd = False  # signal is grounding gpio pin, vs connecting to 3.3v

wpm = 20
MAX_WPM = 100
SERVER = 'drmatthewclark.com'

randomAmount = 0.02

# IP addresses for keys to send signals to
IPS = [('localhost', 1883) ]

# wrapper to allow printing to console etc
def logmesg(log_level, msg):
    print(log_level, msg)
    syslog.syslog(eval(f'syslog.{log_level}'), msg)
