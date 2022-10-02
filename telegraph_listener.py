#!/usr/bin/python


import paho.mqtt.client as mqtt
from queue import Queue
from threading import Thread
import time
from datetime import datetime
import morse
import syslog
from config import *

IP = 'localhost'
message_client_name = 'telegraph'
msg_topic = 'telegraph'
key_topic = 'key'
control_topic = 'control'

INFO = syslog.LOG_INFO
ERR  = syslog.LOG_ERR
DEBUG = syslog.LOG_DEBUG
loglevels = { 'LOG_EMERG':0, 'LOG_ALERT':1, 'LOG_CRIT' : 2, 'LOG_ERR': 3, 'LOG_WARNING':4, 'LOG_NOTICE':5, 'LOG_INFO':6, 'LOG_DEBUG' : 7 }

# global message queue
message_queue = Queue()
key_queue     = Queue()
message_threads = {}

def check_threads():
	for t in message_threads:
		thred = message_threads[t]	
		if not thred.is_alive():
			syslog.syslog(syslog.LOG_ERR,  str(t) + ' monitor thread is dead' )
			exit(1)
			 


def process_messages(message_queue):
	"""
	process the queue of messages to transmit because one could come in while another is still in progress
	"""
	active = True
	while active:
		msg = message_queue.get(block=True)
		if msg is not None:
			morse.message(msg)
			

def process_key(key_queue):
	"""
	process the queue of key presses to transmit because one could come in while another is still in progress
	"""
	active = True
	while active:
		msg = key_queue.get(block=True)
		if msg is not None:
			morse.key(msg)


def on_message(message_client, userdata, msg):
	m = msg.payload.decode('utf-8')
	syslog.syslog(DEBUG, 'message: ' + str(message_client) + ' ' + str(msg))
	if msg.topic == key_topic:
		key_queue.put(m)

	elif msg.topic == msg_topic:	
		message_queue.put(m)

	elif msg.topic == control_topic:
		try:
			data = m.split(':')
			if data[0] == 'speed':
				syslog.syslog(INFO, 'listener setting speed to ' + data[1])
				morse.setSpeed(float(data[1]))
			if data[0] == 'code':
				syslog.syslog(INFO, 'listener setting active code to ' + str(data[1]))
				morse.setActivecode(data[1])

			if data[0] == 'loglevel':
				if data[1].strip() in loglevels:
					lvl = loglevels[data[1]]
				else:
					lvl = data[1]

				syslog.syslog(INFO, 'listener setting log level to ' + str(lvl) )
				morse.setLoglevel(int(lvl))

		except Exception as err: 
			syslog.syslog(ERR,'bad control message: ' + m + ' Err: ' + str(err) ) 

	check_threads()

def setup_message_listener():
	worker = Thread(target=process_messages, args=(message_queue,) )
	message_threads['setup_message_listener'] = worker
	worker.setDaemon(True)
	worker.start()

	
def setup_key_listener():
	worker = Thread(target=process_key, args=(key_queue,) )
	message_threads['setup_key_listener'] = worker
	worker.setDaemon(True)
	worker.start()


def on_connect(client, userdata, flags, rc):
	result = client.subscribe( [(msg_topic, qos), (key_topic, qos), (control_topic, qos)] )
	if result != (0,1):
		syslog.syslog(ERR, 'error:' + str(result) + ' telegraph_listener error subscribing' )
		exit(7)

	syslog.syslog(INFO, str(client) + ' connected' )

def setup():
	morse.setup()
	setup_message_listener()
	setup_key_listener()

	message_client = mqtt.Client(message_client_name)
	message_client.on_message = on_message 
	message_client.on_connect = on_connect
	message_client.connect(IP)

	syslog.syslog(INFO, 'telegraph listener started')
	message_client.loop_forever()  # Start networking daemon

setup()

