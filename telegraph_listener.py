#!/usr/bin/python


import paho.mqtt.client as mqtt
from queue import Queue
from threading import Thread
import time
import random
from datetime import datetime
from config import *
import morse
import signal 
import sys
from multiprocessing.connection import Listener

IP = 'localhost'
#message_client_name = 'telegraph'  in config
msg_topic = 'telegraph'

control_topics = ['telegraph', 'speed', 'code' ] 
server_client = None
message_client = None

# global message queues
message_queue = Queue()


def process_messages(message_queue):
       """
       process the queue of messages to transmit because one could come in while another is still in progress
       """
       
       try:
          while True:
              msg = message_queue.get(block=True)
              morse.message(msg)

       except Exception as err:
           logmesg('LOG_ERR', f'Error in process_messages: {err}' )

           

def on_message(message_client, userdata, msg):
       """
        called when a message is recieved; one of
        1) a key press or release 
        2) a text message to transmit
        3) an alteration of parameters, speed, code, loglevel

       """
       logmesg('LOG_DEBUG', f'on_message: {message_client._client_id} {userdata}  msg: {msg}')
       m = msg.payload.decode('utf-8')   # the actual message
       topic = msg.topic

       if topic == msg_topic:       
              message_queue.put(m)

       elif topic in control_topics:
            if topic == 'speed':
              try:
                 speed = float(m)
                 morse.setSpeed( speed )
                 logmesg('LOG_INFO', f'listener setting speed to {speed}')
              except Exception as err:
                 logmesg('LOG_ERR', f'listener error setting speed to {m}:  {err}')

            elif topic == 'code':
               logmesg('LOG_INFO', f'listener setting active code to {m}' )
               morse.setActivecode(m)
               logmesg('LOG_INFO', f'listener set active code to {morse.getActiveCode()}' )
  
       else: 
          logmesg('LOG_ERR', f'listener topic  {topic}, {m} not understood' )


           
def daemonize( func, args ):
        """
        deamonize a function to run asynchronously
        """
        if args is None:
           worker = Thread(target=func, name=str(func), daemon=True)
        else:
           worker = Thread(target=func, name=str(func), args=args, daemon=True)
    
        worker.start()
        return worker



def on_server_connect(client, userdata, flags, rc, properties):
       """
       called on connection to the server
       subcribe to the server on connections.
       """
       options = mqtt.SubscribeOptions( noLocal=True, qos=qos )
       for topic in control_topics:
           
          result, count = client.subscribe( topic=topic, options = options )

          if result != 0:
              logmesg('LOG_ERR', f'error: {result} telegraph_listener "{client._client_id.decode()}" error subscribing to client' )
              exit(7)

       logmesg('LOG_INFO', 'telegraph_listener connected' )



def on_connect(client, userdata, flags, rc, properties):
       """
       called on connection to the server
       subcribe to the server on connections.
       """
       options = mqtt.SubscribeOptions( noLocal=True, qos=qos )
       for topic in control_topics:
           
          result, count = client.subscribe( topic=topic, options = options )

          if result != 0:
              logmesg('LOG_ERR', f'error: {result} telegraph_listener "{client._client_id.decode()}" error subscribing to client' )
              exit(7)

       logmesg('LOG_INFO', 'telegraph_listener connected' )



def on_disconnect(client, userdata, rs, properties):

    """
    called when the server disconnects
    """
    host = client._host
    logmesg('LOG_ERR', f'on_disconnect: {client} {rs} {host}  disconnected')

    ret = client.connect( host=host )

    if ret == 0:
        logmesg('LOG_INFO', f'on_disconnect: reconnected {host}')
    else:
        logmesg('LOG_ERR', f'on_disconnect: failed to reconnect {host}' )


def listen_for_interpret():

   address = ('127.0.5.1', 16321)

   while True:
     logmesg('LOG_INFO', f'telegraph interpreter socket listener starting' )
     listener = Listener(address, authkey=b'x')
     conn = listener.accept()
     try: 
       while True:
          msg = conn.recv()
          logmesg('LOG_INFO', f'interpret recieve message  {msg}'  )
          message_client.publish('telegraph', msg, qos )
          server_client.publish('telegraph', msg, qos )
         
          listener.close() 
     except Exception as err:
        logmesg('LOG_ERR', f'telegraph socket listener err {err}, closing' )
        listener.close()
    
   logmesg('LOG_INFO', 'telegraph interpreter socket listener ending')


def listen_for_key():

   address = ('127.0.5.1', 16320)

   while True:
     logmesg('LOG_INFO', f'telegraph socket listener starting' )
     listener = Listener(address, authkey=b'x')
     conn = listener.accept()
     try: 
       while True:
          msg = conn.recv()
          morse.key( msg )
       
     except Exception as err:
        logmesg('LOG_ERR', f'telegraph socket listener err {err}, closing' )
        listener.close()
    
   logmesg('LOG_INFO', 'telegraph socket listener ending')
     
     
def setup():
       global server_client
       global message_client

       morse.setup()
       logmesg('LOG_INFO', 'telegraph listener starting')
       morse.setSpeed(wpm) # set to config file value

       lis  = daemonize( listen_for_key, None  ) 
       intr = daemonize( listen_for_interpret, None  ) 
       msq =  daemonize(process_messages, (message_queue,) )

       logmesg('LOG_INFO', f'server is {SERVER}' )
       # listen for messages to server
       server_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                                    protocol=mqtt.MQTTv5, client_id=f'server {SERVER} {random.random()} ')
       server_client.user_data_set(SERVER) # store ip
       server_client.on_message = on_message
       server_client.on_connect = on_server_connect
       server_client.on_disconnect = on_disconnect
       server_client.connect( host=SERVER, keepalive = 30 )
       server_client.loop_start()  # Start networking daemon
  
       message_client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                                   protocol=mqtt.MQTTv5, client_id=f'message_client_name {random.random()}')
       message_client.user_data_set(IP) # store ip
       message_client.on_message = on_message 
       message_client.on_connect = on_connect
       message_client.on_disconnect = on_disconnect
       message_client.connect( host=IP )
       message_client.loop_start()  # Start networking daemon

       # this function should not return 
       msq.join()
  
       logmesg('LOG_ERR', 'telegraph listener finished' )

if __name__ == '__main__':
     setup()
