#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time as time
import syslog
import os
import signal
from threading import Thread
from config import *
import morse
import re
import random

# topic to broadcast for key press/release 
topic = 'key'      # key press
interpret_topic  = 'interpret'
signals = []    # stores tuples of (time, event(up/down) )  to evaluate


last_press = time.perf_counter()


UP = GPIO.RISING
DOWN = GPIO.FALLING

# reverse if signal is grounding pin
if gpioInputGnd:
    UP = GPIO.FALLING
    DOWN = GPIO.RISING



def reconnect():
    # connect if not connected
    global CLIENTS
    for client in CLIENTS:
        if not client.is_connected():
            IP = client._host
            logmesg(syslog.LOG_INFO, f'reconnecting {IP}' )
            client.connect_async(IP)
    return 0



def showsignals():
    result = ''
    start_time = signals[0][0]
    for (time, event)  in signals:
        time  -= start_time
        result += f'{time:0.3f}  {event}\n'

    return result

def interpret(interval):
    """ 
    interpret  the key clicks to assign to a caracter

    """
    global CLIENTS

    if len(signals) < 2:
        return
    if len(CLIENTS) == 0: 
       return

    logmesg(syslog.LOG_INFO, '%6.4f interpret...' % (interval) )
    #logmesg(syslog.LOG_DEBUG, showsignals() )
    dot = morse.lengths['dotLength']
    dash = morse.lengths['dashLength']
    client  = CLIENTS[0]
    dotdash = []
    
    for i, (t, s) in enumerate(signals):
        if i > 0:
            (lt, ls ) = signals[i-1]  # last signal
            interval = t - lt  # time between up/down events

            if s == 0 and ls == 1:  # key down interval
                dotdash.append(interval)
            elif s == 1 and ls == 0:  # key up interval
                dotdash.append(-interval)
            else:
                logmesg(syslog.LOG_ERR, f'interpret long gap: {interval} from {ls} to {s}')

    #logmesg(syslog.LOG_DEBUG, f'dotdash {dotdash}' )
    morseChar = ''

    header =  ' time(ms) ideal(ms)  best fit          % error'

    actual_length = 1e-6  # avoid divide by zero
    ideal_length  = 1e-6

    for d  in dotdash:

        p = morse.matchLength(d)  # p is the name of the length, 'dotLength'
        correct = morse.lengths.get(p) + 1e-6
        if d < 0:
           guess = 'pause'
        else:
          guess = p

        err = 100.*(abs(d)-correct)/correct
        ideal_length += correct
        actual_length += abs(d)   # length
        keymsg = '% 5d    %5d %15s err: % 6.0f%%' % (int(1000*d), int(1000*correct), guess, err  )

        if d > 0.0:
            if p == 'dotLength':
                morseChar += '.'
            elif p == 'morseLLength':
                morseChar += 'L'
            elif p == 'morse0Length':
                morseChar += 'z'
            else:
                morseChar += '-'

        if d < 0.0:
            if p == 'dotLength':
                pass
            elif p == 'pauseLength' and morseChar[-1] == '.':
                morseChar += 'd'

    totalerr = (100.0*actual_length/ideal_length) - 100.0
    char = morse.morse2char(morseChar)
    result =   "%6s\t%s\t%4.0f" % (morseChar, char, totalerr)
    logmesg(syslog.LOG_INFO, result)

    if not char is None:
       for client in CLIENTS:
           publish(client, interpret_topic, char.encode('utf8'), qos)

    signals.clear()



def analyzer():
    """

    analyze the data collected so far

    """

    criteria =  2*morse.lengths['letterPauseLength'] 
    sleeptime = morse.lengths['dotLength']/4

    # loop awaiting signals
    while True:
        interval = time.perf_counter() - last_press
        if interval > criteria and len(signals) > 1 and len(signals) % 2 == 0:  # >1 cause need and up and down
            interpret(interval)

        time.sleep(sleeptime) # wait for data 


def publish(client, topic, status, qos=qos ):
 try:
    tries = 0
    ecode, count  = client.publish(topic, status, qos)

    if ecode != 0:
        logmesg(syslog.LOG_ERR, f'publish reports: {ecode} {count}')
        while client.reconnect() != 0:
             tries += 1
             if tries > 100: break
        
        ecode, count  = client.publish(topic, status, qos)
        logmesg(syslog.LOG_ERR, f'publish retry result: {ecode} {count} tries {tries} ')
        if ecode != 0:
            logmesg(syslog.LOG_ERR, f'publish error after recount: {ecode} {count}')

 except Exception as  err:
     logmesg(syslog.LOG_ERR, f'publish: {err}' )


def key_press(channel, status, now=0):

        """
         called when the key is pressed and when released
	"""
        status = int(status)
        # telegraph key pressed
        if gpioInputGnd:   # if grounding gpio pin for signal
            status = 1 - status

        signals.append( (now, status ) )
 
        for client in CLIENTS:
           publish(client, topic, status, qos)


def on_connect(client, userdata, flags, rc, properties):
     """
     called on connection to mqtt server 
     """
     if rc != 0:
         logmesg(syslog.LOG_ERR, f'key listener ERROR connecting: {rc} flags {flags}' )

     logmesg(syslog.LOG_INFO, f'on_connect: connected {client} {flags}' )




def on_disconnect(client, userdata, reason, properties):
    """
    called on disconnect
    """

    logmesg(syslog.LOG_INFO, f'on_disconnect: {client} {reason} disconnected')
 
    if client.reconnect() == 0:
        logmesg(syslog.LOG_INFO, f'on_disconnect: reconnected {client}' )
    else:
        logmesg(syslog.LOG_ERR, f'on_disconnect: failed to reconnect {client}' )



def setup_clients():
    """
    set up the connections
    """
    clients = []

    for IP in IPS:  # list of configured IP addresses to broadcast to
        logmesg(syslog.LOG_INFO, f'setup_clients: connecting to client {IP}' )
        try: 
            client_id = f'{topic}{IP}{random.random()}'
            client = mqtt.Client(protocol=mqtt.MQTTv5, client_id=client_id )
            client.user_data_set(IP)
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.connect( IP )
            clients.append( client )
            logmesg(syslog.LOG_INFO, f'setup_clients: client {IP} connected {client} id {client_id}' )

        except Exception as exp:
            logmesg(syslog.LOG_ERR, f'setup_clients: error connecting to {IP} err: {exp}' )
 
    return clients
    
 
def setup_gpio():
        try:
           GPIO.setmode(gpioMode) 
           logmesg(syslog.LOG_INFO, f'setup_gpio success')
        except Exception as err:
           logmesg(syslog.LOG_ERR, f'setup_gpio setmode: {err}')

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1
        else:
            pud = GPIO.PUD_DOWN
            last_status = 0
        try: 
          GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud)
        except Exception as err:
           logmesg(syslog.LOG_ERR, f'setup_gpio setup: {err}')


def gpio_listener():
    """ 
    main listening loop for key presses
    """
    global last_press
    setup_gpio() 
    wait = 0.005
    waiting = 0
    fast_wait = 0.001 # increase accuracy during messages
    slow_wait = 0.01   # less accurate timing between messages

    while True:
      try:
        level = GPIO.input(gpioInputPin)
        # innner loop waiting for in change
        while GPIO.input(gpioInputPin) == level:
            time.sleep(wait)
            waiting += wait
            if waiting > 10:  # swich to slower loop after 10 sec inactivity
                 wait = slow_wait

        # 'not level'  because it changed
        last_press =  time.perf_counter()
        key_press(gpioInputPin, not level, now=last_press )
         
        #if wait == slow_wait:  # skeeps first message after waiting 
        #    key_press(gpioInputPin, not level, now=last_press )

        wait = fast_wait
        time.sleep(wait)
        waiting = 0
      except Exception as err:
          pass
          logmesg(syslog.LOG_ERR, f'gpio_listener {err}')
     

    logmesg(syslog.LOG_ERR, 'gpio_listener loop ended')
    
   

def daemonize( func, args=None ):
        if args is None:
            worker = Thread(target=func, name=str(func), daemon=True )
        else:
            worker = Thread(target=func, name=str(func), daemon=True, args=args)

        worker.start()
        return worker



def setup_listener():
       logmesg(syslog.LOG_INFO, 'setup_listener started' )
       message_client = mqtt.Client(protocol=mqtt.MQTTv5, client_id='key_listener')
       message_client.on_message = on_listen_message
       message_client.on_connect = on_listen_connect
       message_client.on_disconnect = on_listen_disconnect
       message_client.connect_async( '127.0.0.1' )
       message_client.loop_start()  # Start networking daemon

def on_listen_connect(client, userdata, flags, rc, properties):
      topic = 'code'
      qos = 0
      logmesg(syslog.LOG_INFO, 'subscribing to listen to code, and speed' )
      suboptions = mqtt.SubscribeOptions( qos = 0)
      result, count = client.subscribe( topic='code' , options = suboptions )
      result, count = client.subscribe( topic='speed', options = suboptions  )

      if result != 0:
              logmesg(syslog.LOG_ERR, f'error: {result} key_listener error subscribing' )
              exit(7)


def on_listen_message(message_client, userdata, msg):
      
       message = msg.payload.decode('utf-8')   # the actual message
       topic = msg.topic
       logmesg(syslog.LOG_INFO, f'on_listen_message recieved {topic} {message}' )
       if topic == 'code':
          morse.setActivecode(message)
       if topic == 'speed':
          morse.setSpeed(message) 

def on_listen_disconnect(client, userdata, reason, properties):
      logmesg(syslog.LOG_INFO, f'on_listen_disconnect' )
      setup_listener()



if __name__ == '__main__':

   logmesg(syslog.LOG_INFO, 'key listener starting' )
   setup_gpio()
   CLIENTS = setup_clients()
   logmesg(syslog.LOG_INFO, 'clients ' + str(CLIENTS) )
   morse.setActivecode('morseIMC')

   setup_listener()

   ana = daemonize(analyzer )  # figures out the letters
   gpl = daemonize(gpio_listener) # listens to local key

   gpl.join()
   ana.join()
   keep.join()
