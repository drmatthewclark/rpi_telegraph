"""
configure which pins the equipment is connected to
and other variables.  
"""

import syslog
import RPi.GPIO as GPIO

gpioMode = GPIO.BOARD
gpioOutputPin=   12
gpioInputPin =   18
gpioInputGnd = False  # signal is grounding gpio pin, vs connecting to 3.3v

# this gets the unique local station name from a file so everyone is reading
# from the same consistent place
#
with open('/usr/local/rpi_telegraph/local_name', 'r') as file:
    message_client_name = file.read().strip()
    print(f'local name >{message_client_name}<' )


# MQTT settings.  the authentication is mostly to 
# stop bot scanners at this point. 

qos = 0   # mqtt QOS level
uname = message_client_name
pword = message_client_name + '-t7f+&0mE9wg,_?D'
SERVER = 'drmatthewclark.com'

# telegraph settings
keepalive = 10
wpm = 20       # default speed
MAX_WPM = 100  # upper limit for speed
randomAmount = 0.02   # make sending slightly imperfect

# wrapper to allow printing to console etc
def logmesg(log_level, msg):
    #print(log_level, msg)
    syslog.syslog(eval(f'syslog.{log_level}'), msg)

