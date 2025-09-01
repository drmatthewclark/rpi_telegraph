#!/usr/bin/python


import paho.mqtt.client as mqtt
from queue import Queue
from threading import Thread
import time
from datetime import datetime
from config import *
import morse
import signal 
import sys
import syslog

IP = 'localhost'
message_client_name = 'telegraph'
msg_topic = 'telegraph'
key_topic = 'key'
control_topic = 'control'

# global message queues
message_queue = Queue()
key_queue     = Queue()


def process_messages(message_queue):
       """
       process the queue of messages to transmit because one could come in while another is still in progress
       """
       
       try:
          while True:
              msg = message_queue.get(block=True)
              morse.message(msg)
       except Exception as err:
           print('process_messages', err)

           
       print('process_messages ending' )

def process_key(key_queue):
       """
       process the queue of key presses to transmit because one could come in while another is still in progress
       """

       while True:
              msg = key_queue.get(block=True)
              #syslog.syslog(syslog.LOG_DEBUG, 'process_key message, queue = ' + str(key_queue) )
              morse.key(msg)

       print('process_key ending' )

def on_message(message_client, userdata, msg):

       """
        called when a message is recieved; one of
        1) a key press or release 
        2) a text message to transmit
        3) an alteration of parameters, speed, code, loglevel

       """
       m = msg.payload.decode('utf-8')   # the actual message

       #syslog.syslog(syslog.LOG_DEBUG, 'message recieved  topic: ' + msg.topic + ' message ' + str(msg))

       if msg.topic == key_topic:
              key_queue.put(m)

       elif msg.topic == msg_topic:       
              message_queue.put(m)

       elif msg.topic == control_topic:
              try:
                     data = m.split(':')
                     if data[0] == 'speed':
                            syslog.syslog(syslog.LOG_INFO, 'listener setting speed to ' + data[1])
                            morse.setSpeed(float(data[1]))
                     if data[0] == 'code':
                            syslog.syslog(syslog.LOG_INFO, 'listener setting active code to ' + str(data[1]))
                            morse.setActivecode(data[1])

                     if data[0] == 'loglevel':
                            if data[1].strip() in loglevels:
                                   lvl = loglevels[data[1]]
                            else:
                                   lvl = data[1]

                            syslog.syslog(syslog.LOG_INFO, 'listener setting log level to ' + str(lvl) )
                            morse.setLoglevel(int(lvl))

              except Exception as err: 
                     syslog.syslog(ERR,'bad control message: ' + m + ' Err: ' + str(err) ) 


def daemonize( func, args ):
        """
        deamonize a function to run asynchronously
        """
       
        worker = Thread(target=func, name=str(func), args=args, daemon=True)
        worker.start()
        return worker


def on_connect(client, userdata, flags, rc):
       """
       called on connection to the server
       subcribe to the server on connections.
       """

       result, count = client.subscribe( [(msg_topic, qos), (key_topic, qos), (control_topic, qos)] )
       if result != 0:
              syslog.syslog(syslog.LOG_ERR, 'error:' + str(result) + ' telegraph_listener error subscribing' )
              exit(7)

       syslog.syslog(syslog.LOG_INFO, 'telegraph_listener connected' )


def on_disconnect(client, userdata, rs):

    """
    called when the server disconnects
    """
    syslog.syslog(syslog.LOG_ERR, str(client) + ' ' + str(rs) + ' disconnected')
    ret = client.connect(IP)
    if ret == 0:
        syslog.syslog(log_level, 'reconnected ' + str(IP))
    else:
        syslog.syslog(syslog.LOG_ERR, 'failed to reconnect ' + str(IP))


def setup():
       syslog.syslog(syslog.LOG_INFO, 'telegraph listener starting')
       morse.setup()

       msq =  daemonize(process_messages, (message_queue,) )
       keyq = daemonize(process_key, (key_queue,) )

       message_client = mqtt.Client(message_client_name)
       message_client.on_message = on_message 
       message_client.on_connect = on_connect
       message_client.on_disconnect = on_disconnect
       message_client.connect(IP)
       message_client.loop_forever()  # Start networking daemon
       
       keyq.join() 
       msq.join()
 
       syslog.syslog(syslog.LOG_ERR, 'telegraph listener finished' )


if __name__ == '__main__':
   setup()
