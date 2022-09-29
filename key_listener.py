#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time as time
import syslog

IP = 'localhost'

qos = 2
gpioPin = 18

bounce = 2  # milliseconds
topic = 'key'
client = None
down = 1
up =   0

log_level = syslog.LOG_INFO

syslog.syslog(log_level, 'key listener starting' )


def key_press(channel):
	# telegraph key pressed
	status = GPIO.input(channel)
	client.publish(topic, status, qos)


def on_connect(client, userdata, flags, rc):
	if rc != 0:
		syslog.syslog(syslog.LOG_ERR, 'key listener ERROR connecting: ' + str(rc) )

	client.publish(topic, up, qos)  # return to up
	syslog.syslog(log_level, 'key listener connected' )


def setup():

	GPIO.setmode(GPIO.BOARD) 
	GPIO.setup(gpioPin, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)
	GPIO.add_event_detect(gpioPin, GPIO.BOTH,  callback=key_press,   bouncetime=bounce)

	client = mqtt.Client(topic)
	client.on_connect = on_connect
	client.connect(IP)

	# announce startup
	client.publish('telegraph', 'CQ', qos)
	syslog.syslog(log_level, 'key listener started' )
	return client

	
client = setup()
client.loop_forever()
