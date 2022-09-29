#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time as time
import syslog
from config import *

# ips addresses to broacast telegraph messages to
# is now in config file
#IPS = ['localhost']

# clients
clients = []

qos = 2

bounce = 2  # milliseconds
topic = 'key'


log_level = syslog.LOG_INFO

syslog.syslog(log_level, 'key listener starting' )


def key_press(channel):
	# telegraph key pressed
	status = GPIO.input(channel)
	for client in clients:
		client.publish(topic, status, qos)


def on_connect(client, userdata, flags, rc):
	if rc != 0:
		syslog.syslog(syslog.LOG_ERR, 'key listener ERROR connecting: ' + str(rc) )

	syslog.syslog(log_level, 'key listener connected' )


def setup():

	GPIO.setmode(gpioMode) 
	GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
	GPIO.add_event_detect(gpioInputPin, GPIO.BOTH,  callback=key_press,   bouncetime=bounce)

	for IP in IPS:
		try:
			client = mqtt.Client(topic + str(IP) )
			client.on_connect = on_connect
			client.connect(IP)
			clients.append(client)
			syslog.syslog(log_level, 'client ' + IP + ' connected' )

		except Exception as exp:
			syslog.syslog(syslog.LOG_ERR, 'error connecting to ' + str(IP) )

	# announce startup
	syslog.syslog(log_level, 'key listener started' )
	return clients

	
clients = setup()
clients[0].loop_forever()
