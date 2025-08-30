"""
configure which pins the equipment is connected to
"""

import syslog
import RPi.GPIO as GPIO
import syslog

gpioMode = GPIO.BOARD
qos = 0

gpioOutputPin = 10
gpioInputPin =   16
gpioInputGnd = True  # signal is grounding gpio pin, vs connecting to 3.3v

wpm = 19
randomAmount = 0.02 
log_level = syslog.LOG_INFO

# IP addresses for keys to send signals to

IPS = ['localhost']


loglevels = { 'LOG_EMERG':0, 'LOG_ALERT':1, 'LOG_CRIT' : 2, 'LOG_ERR': 3, 'LOG_WARNING':4, 'LOG_NOTICE':5, 'LOG_INFO':6, 'LOG_DEBUG' : 7 }
