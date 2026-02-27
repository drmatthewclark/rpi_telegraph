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


# topic to broadcast for key press/release 
topic = 'key'      # key press
interpret_topic  = 'interpret'
signals = []

last_press = time.perf_counter()
keepalive=30

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
            client.connect_async(IP, keepalive=keepalive)
    return 0


def checkCode():
    # codenamefile is in config
    if os.path.exists(codenamefile):
        with open(codenamefile, 'r') as fle:
             codename = fle.read()
        morse.setActivecode(codename)
        os.remove(codenamefile)


def interpret(interval):
    """ 
    interpret  the key clicks to assign to a caracter

    """
    global CLIENTS

    if len(signals) < 2:
        return
    if len(CLIENTS) == 0: 
       return

    checkCode()
    logmesg(syslog.LOG_INFO, '%6.4f interpret...' % (interval) )
    dot = morse.lengths['dotLength']
    dash = morse.lengths['dashLength']
    client  = CLIENTS[0]
    dotdash = []

    for i, (t, s) in enumerate(signals):
        if i > 0:
            (lt, ls ) = signals[i-1]
            interval = t - lt
            if s == 0 and ls == 1:  # key down interval
                dotdash.append(interval)
            elif s == 1 and ls == 0:  # pause interval
                dotdash.append(-interval)
            else:
                logmesg(syslog.LOG_ERR, 'interpret: %f %d,  %f %d' %( t,s, lt, ls ) )

    morseChar = ''

    header =  ' time(ms) ideal(ms)  best fit          % error'
    #publish(client, interpret_topic, header.encode('utf8'), qos)

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
        #publish(client, interpret_topic, guess.encode('utf8'), qos )

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

    sleeptime = morse.lengths['dotLength']/4
    criteria =  2*morse.lengths['letterPauseLength'] 
    while True:
        interval = (time.perf_counter() - last_press)
        if interval > criteria and len(signals) > 0:
            interpret(interval)

        time.sleep(sleeptime)



def publish(client, topic, status, qos=qos ):
 try:
    ecode, count  = client.publish(topic, status, qos)

    if ecode != 0:
        client.reconnect()
        ecode, count  = client.publish(topic, status, qos)
        if ecode != 0:
            logmesg(syslog.LOG_ERR, f'key_press error: {ecode} {client}')
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


def on_connect(client, userdata, flags, rc):
     """
     called on connection to mqtt server 
     """
     if rc != 0:
         logmesg(syslog.LOG_ERR, f'key listener ERROR connecting: {rc} flags {flags}' )

     logmesg(syslog.LOG_INFO, f'on_connect: connected {client} {flags}' )




def on_disconnect(client, userdata, rc):
    """
    called on disconnect
    """

    logmesg(syslog.LOG_INFO, f'on_disconnect: {client} {rc} disconnected')
 
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
            client = mqtt.Client(f'{topic}{IP}' )
            client.user_data_set(IP)
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.connect(IP, keepalive=keepalive)
            clients.append( client )
            logmesg(syslog.LOG_INFO, f'setup_clients: client {IP} connected {client}' )

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


def pin_change(channel):
    # used with 
    # #GPIO.add_event_detect(gpioInputPin, GPIO.BOTH, callback=pin_change )
    # but that is not as efficient as a loop unfortunately

    global last_press
    last_press =  time.perf_counter()
    level = GPIO.input(channel)
    key_press(channel, level, now=last_press )




def gpio_listener():
    """ 
    main listening loop for key presses
    """
    global last_press
    setup_gpio() 
    wait = 0.005
    waiting = 0
    fast_wait = 0.0001 # increase accuracy during messages
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
         
        if wait == slow_wait:  # skeeps first message after waiting 
            key_press(gpioInputPin, not level, now=last_press )

        wait = fast_wait
        time.sleep(wait)
        waiting = 0
      except Exception as err:
          pass
          #logmesg(syslog.LOG_ERR, f'gpio_listener {err}')

    logmesg(syslog.LOG_ERR, 'gpio_listener loop ended')
    
   

def daemonize( func, args=None ):
        if args is None:
            worker = Thread(target=func, name=str(func), daemon=True )
        else:
            worker = Thread(target=func, name=str(func), daemon=True, args=args)

        worker.start()
        return worker

# publish some stuff to keep awake
def keep(sleeptime=10):

  time.sleep(sleeptime)
  while True:
    for client in CLIENTS:
        publish(client, 'k', '' )

    time.sleep(sleeptime)


if __name__ == '__main__':

   logmesg(syslog.LOG_INFO, 'key listener starting' )
   setup_gpio()
   CLIENTS = setup_clients()
   logmesg(syslog.LOG_INFO, 'clients ' + str(CLIENTS) )
   morse.setActivecode('morseIMC')

   ana = daemonize(analyzer )  # figures out the letters
   gpl = daemonize(gpio_listener) # listens to local key
   keep = daemonize(keep(10))

   gpl.join()
   ana.join()
   keep.join()
