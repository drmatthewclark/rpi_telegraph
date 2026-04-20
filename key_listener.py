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
from threading import Event

# topic to broadcast for key press/release 
topic = 'key'      # key press
interpret_topic  = 'interpret'
signals = []    # stores tuples of (time, event(up/down) )  to evaluate

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
           Thread(target=publish, args=(client, interpret_topic, char.encode('utf8'), qos), daemon=True ).start()

    signals.clear()



def analyzer():

    """
    analyze the data collected so far
    """
    criteria =  morse.lengths['letterPauseLength'] 
    sleeptime = morse.lengths['dotLength']/2
    cycles = 0
    ping_interval = int(sleeptime * 100000 )

    # loop awaiting signals
    while True:
        cycles += 1
        try:
            num_signals = len(signals)
            interval = time.perf_counter() - signals[-1][0]
    
            if interval > criteria and num_signals % 2 == 0:  # >1 cause need and up and down
                interpret(interval)
    
            elif cycles % ping_interval == 0: 
              cycles = 0 # prevent getting too large after a long time
              for client in CLIENTS:
                  Thread(target=publish, args=(client, 'x', 1), daemon=True ).start()
        except:
            pass
        finally:
            time.sleep(sleeptime) # wait for data 


#
# wrapper for mqtt publish
#
def publish(client, topic, status, qos=qos ):
 try:
    reconnect_tries = 0
    max_tries = 10

    ecode, count  = client.publish(topic, status, qos)

    if ecode != 0:
        logmesg(syslog.LOG_ERR, f'publish reports failed: {ecode} {count}')
        while client.reconnect() != 0:
             reconnect_tries += 1
             time.sleep(0.5)
             if reconnect_tries > max_tries:
                  logmesg(syslog.LOG_ERR, f'publish reconnect failed after {max_tries} attempts')
                  break
        
        ecode, count  = client.publish(topic, status, qos)
        logmesg(syslog.LOG_ERR, f'publish retry result: {ecode} {count} tries {tries} ')
        if ecode != 0:
            logmesg(syslog.LOG_ERR, f'publish error after recount: {ecode} {count}')

 except Exception as  err:
     logmesg(syslog.LOG_ERR, f'publish: {err}' )



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




def setup_client(IP):
        client = None
        logmesg(syslog.LOG_INFO, f'setup_client: client {IP} try connect{client}' )
        try: 
            client_id = f'{IP}{random.random()}'
            client = mqtt.Client(protocol=mqtt.MQTTv5, client_id=client_id )
            client.user_data_set(IP)
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.connect( IP )
            logmesg(syslog.LOG_INFO, f'setup_client: client {IP} connected {client} id {client_id}' )
            
        except Exception as exp:
            logmesg(syslog.LOG_ERR, f'setup_client: error connecting to {IP} err: {exp}' )
        finally:
            return client

def setup_clients():
    """
    set up the connections
    """
    clients = []

    for IP in IPS:  # list of configured IP addresses to broadcast to
        client = setup_client( IP )  
        if client is None:  # if none, make a second try
            time.sleep(10)
            client = setup_client( IP )
            if not client is None:
                 clients.append( client )
        else:
            clients.append( client ) 

    return clients
   
 
 
def setup_gpio():
        try:
           GPIO.setmode(gpioMode) 

           GPIO.cleanup(gpioInputPin) 
           GPIO.setmode(gpioMode) 
           GPIO.setwarnings(False)
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
          GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud )
        except Exception as err:
           logmesg(syslog.LOG_ERR, f'setup_gpio setup: {err}')


def signal(arg):
    # called on key press or release 
    now =  time.perf_counter()
    level = int( GPIO.input(gpioInputPin) )

    if gpioInputGnd:   # if grounding gpio pin for signal
         level = 1 - level 

    signals.append( (now, level ) )
 
    for client in CLIENTS:
         Thread(target=publish, args=(client, topic, level, qos), daemon=True ).start()


def gpio_listener():
    """ 
    main listening loop for key presses
    """
    setup_gpio() 
    GPIO.add_event_detect(gpioInputPin, GPIO.BOTH, signal, 1 )
    Event().wait()  # wait here forever


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
   morse.setActivecode('morseIMC')  # default code

   setup_listener()

   ana = daemonize( analyzer )  # figures out the letters
   gpio_listener()  # listens to local key waits here forever

   logmesg(syslog.LOG_ERR, 'gpio_listener ended unexpectedly' )

   gpl.join()
   ana.join()
