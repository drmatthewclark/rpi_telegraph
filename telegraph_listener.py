#!/usr/bin/python

import paho.mqtt.client as mqtt
from queue import Queue
from threading import Thread
import time
from datetime import datetime
import morse
import syslog

qos = 2
IP = 'localhost'
message_client_name = 'telegraph'
msg_topic = 'telegraph'
key_topic = 'key'
log_level = syslog.LOG_INFO

# global message queue
message_queue = Queue()
key_queue     = Queue()
message_threads = {}

def check_threads():
	for t in message_threads:
		thred = message_threads[t]	
		if not thred.is_alive():
			syslog.syslog(syslog.LOG_ERR,  t + ' monitor thread is dead' )
			exit(1)
			 


def now():
	return str(datetime.now())


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

	if msg.topic == key_topic:
		key_queue.put(m)

	elif msg.topic == msg_topic:	
		message_queue.put(m)

	check_threads()

def setup_message_listener():
	worker = Thread(target=process_messages, args=(message_queue,) )
	message_threads[setup_message_listener] = worker
	worker.setDaemon(True)
	worker.start()
	
def setup_key_listener():
	worker = Thread(target=process_key, args=(key_queue,) )
	message_threads[setup_key_listener] = worker
	worker.setDaemon(True)
	worker.start()

def setup():
	morse.setup()
	setup_message_listener()
	setup_key_listener()

	message_client = mqtt.Client(message_client_name)
	message_client.on_message = on_message 
	message_client.connect(IP)
	message_client.subscribe( [(msg_topic, qos), (key_topic, qos)] )

	syslog.syslog(log_level, 'telegraph listener started')
	message_client.loop_forever()  # Start networking daemon

setup()

