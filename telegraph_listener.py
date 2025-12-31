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
keepalive = 5

control_topics = ['telegraph', 'key', 'speed', 'code', 'loglevel' ] 

# global message queues
message_queue = Queue()
key_queue     = Queue()

def logmsg(loglevel, msg ):
      syslog.syslog(loglevel, msg )
      #print(loglevel, msg )


def process_messages(message_queue):
       """
       process the queue of messages to transmit because one could come in while another is still in progress
       """
       
       try:
          while True:
              msg = message_queue.get(block=True)
              logmsg(syslog.LOG_DEBUG, f'message processed: {msg}' )
              morse.message(msg)
       except Exception as err:
           logmsg(syslog.LOG_ERR, f'process message {err}' )

           
       logmsg(syslog.LOG_INFO, 'process_messages ending' )

def process_key(key_queue):
       """
       process the queue of key presses to transmit because one could come in while another is still in progress
       """

       while True:
              msg = key_queue.get(block=True)
              morse.key( int(msg) )

       logmsg(syslog.LOG_INFO, 'process key ended' )

 

def on_message(message_client, userdata, msg):

       """
        called when a message is recieved; one of
        1) a key press or release 
        2) a text message to transmit
        3) an alteration of parameters, speed, code, loglevel

       """
       m = msg.payload.decode('utf-8')   # the actual message
       topic = msg.topic

       logmsg(syslog.LOG_DEBUG, f'message recieved  topic: {topic} message: {m}  {msg.info}')

       if topic == key_topic:
              key_queue.put(m)

       elif topic == msg_topic:       
              message_queue.put(m)

       elif topic in control_topics:
            if topic == 'speed':
              try:
                 speed = float(m)
                 morse.setSpeed( speed )
                 logmsg(syslog.LOG_INFO, f'listener setting speed to {speed}')
              except Exception as err:
                 logmsg(syslog.LOG_ERR, f'listener error setting speed to {m}:  {err}')


            elif topic == 'loglevel':
              try:
                 loglevel = int(m)
                 morse.setLoglevel( loglevel )
                 logmsg(syslog.LOG_INFO, f'listener setting log level to {loglevel}')
              except Exception as err:
                 logmsg(syslog.LOG_ERR, f'listener error setting loglevel to {m}:  {err}')

            elif topic == 'code':
               logmsg(syslog.LOG_INFO, f'listener setting active code to {m}' )
               morse.setActivecode(m)
  
       else: 
          logmsg(syslog.LOG_ERR, f'listener topic  {topic}, {m} not understood' )


           
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
       #result, count = client.subscribe( [(msg_topic, qos), (key_topic, qos), (control_topics, qos)] )

       for topic in control_topics:
          result, count = client.subscribe( (topic, qos) )

          if result != 0:
              logmsg(syslog.LOG_ERR, f'error: {result} telegraph_listener error subscribing' )
              exit(7)

       logmsg(syslog.LOG_INFO, 'telegraph_listener connected' )



def on_disconnect(client, userdata, rs):

    """
    called when the server disconnects
    """
    host = client._host
    logmsg(syslog.LOG_ERR, f'on_disconnect: {client} {rs} {host}  disconnected')

    ret = client.connect(host, keepalive=keepalive)

    if ret == 0:
        logmsg(log_level, f'on_disconnect: reconnected {host}')
    else:
        logmsg(syslog.LOG_ERR, f'on_disconnect: failed to reconnect {host}' )



def keep_connection(client):
        while True:
          time.sleep(600)
          ret = client.connect(IP, keepalive=keepalive)
          if ret != 0:
             logmsg(syslog.LOG_ERR, f'on_disconnect: failed to reconnect {IP}' )


          
def setup():

       logmsg(syslog.LOG_INFO, 'telegraph listener starting')
       morse.setup()

       msq =  daemonize(process_messages, (message_queue,) )
       keyq = daemonize(process_key, (key_queue,) )

       message_client = mqtt.Client(message_client_name)
       message_client.on_message = on_message 
       message_client.on_connect = on_connect
       message_client.on_disconnect = on_disconnect
       message_client.connect_async(IP, keepalive=keepalive)

       keep = daemonize( keep_connection( message_client ))
       message_client.loop_forever()  # Start networking daemon

       logmsg(syslog.LOG_ERR, 'message_client loop_forever ended' )

       keyq.join() 
       msq.join()
       keep.join()
  
       logmsg(syslog.LOG_ERR, 'telegraph listener finished' )


if __name__ == '__main__':
     setup()
