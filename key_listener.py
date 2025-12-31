#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time as time
import syslog
import signal
from threading import Thread
from config import *
from morse import *
import re

# topic to broadcast for key press/release 
topic = 'key'      # key press
pubtopic = 'code'  # change settings

signals = []

last_press = time.perf_counter()
keepalive=65534
setLoglevel(log_level)

UP = GPIO.RISING
DOWN = GPIO.FALLING
CLIENTS = []    # list of clients

# reverse if signal is grounding pin
if gpioInputGnd:
    UP = GPIO.FALLING
    DOWN = GPIO.RISING


def mesg(log_level, msg):
    syslog.syslog(log_level, msg)
    print(msg)

def publish(client, code, msg, qos):
    try:
       return client.publish(code, msg, qos) # returns ecode, count
    except Exception as err:
       mesg(syslog.LOG_ERR, f'publish error:  {err}' )

    return -1, -1

def reconnect():
    # connect if not connected
    for client in CLIENTS:
        if not client.is_connected():
            IP = client._host
            mesg(syslog.LOG_INFO, f'reconnecting {IP}' )
            client.connect_async(IP, keepalive=keepalive)
    return 0



def interpret(interval):
    """ 
    interpret  the key clicks to assign to a caracter

    """
    if len(signals) < 2:
        return

    mesg(syslog.LOG_INFO, '%6.4f interpret...' % (interval) )
    dot = lengths['dotLength']
    dash = lengths['dashLength']
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
                mesg(syslog.LOG_ERR, 'interpret: %f %d,  %f %d' %( t,s, lt, ls ) )

    morseChar = ''

    header =  ' time(ms) ideal(ms)  best fit          % error'
    publish(client, 'code', header.encode('utf8'), qos)

    actual_length = 1e-6  # avoid divide by zero
    ideal_length  = 1e-6

    for d  in dotdash:

        p = matchLength(d)  # p is the name of the length, 'dotLength'
        correct = lengths.get(p) + 1e-6
        if d < 0:
           guess = 'pause'
        else:
          guess = p

        err = 100.*(abs(d)-correct)/correct
        ideal_length += correct
        actual_length += abs(d)   # length
        keymsg = '% 5d    %5d %15s err: % 6.0f%%' % (int(1000*d), int(1000*correct), guess, err  )
        publish(client, 'code', keymsg.encode('utf8'), qos )

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
    char = morse2char(morseChar)
    result =   "%6s\t%s\t%4.0f" % (morseChar, char, totalerr)
    mesg(syslog.LOG_INFO, result)
    publish(client, 'code', result.encode('utf8'), qos)
    signals.clear()



def analyzer():
    """

    analyze the data collected so far

    """

    sleeptime = lengths['dotLength']/2
    criteria =  3*lengths['letterPauseLength'] 
    while True:
        interval = (time.perf_counter() - last_press)
        if interval > criteria and len(signals) > 0:
            interpret(interval)

        time.sleep(sleeptime)


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
           ecode, count  = client.publish(topic, status, qos)
           if ecode != 0:
              client.reconnect()
              ecode, count = client.publish(topic, status, qos) # retry
              if ecode != 0:
                  mesg(syslog.LOG_ERR, f'key_press error: {ecode} {client}')

def on_connect(client, userdata, flags, rc):
     """
     called on connection to mqtt server 
     """
     if rc != 0:
         mesg(syslog.LOG_ERR, f'key listener ERROR connecting: {rc} flags {flags}' )

     mesg(syslog.LOG_INFO, f'on_connect: connected {client} {flags}' )




def on_disconnect(client, userdata, rc):
    """
    called on disconnect
    """

    mesg(syslog.LOG_INFO, f'on_disconnect: {client} {rc} disconnected')
 
    if client.reconnect() == 0:
        mesg(syslog.LOG_INFO, f'reconnected {client}' )
    else:
        mesg(syslog.LOG_ERR, f'failed to reconnect {client}' )



def setup_clients():
    """
    set up the connections
    """
    clients = []

    for IP in IPS:  # list of configured IP addresses to broadcast to
        try:
            client = mqtt.Client(f'{topic}{IP}' )
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.connect_async(IP, keepalive=keepalive)
            clients.append( client )
            mesg(syslog.LOG_INFO, f'client {IP} connected {client}' )

        except Exception as exp:
            mesg(syslog.LOG_ERR, f'error connecting to {IP} err: {exp}' )
 
    return clients
    
 
def setup():

        GPIO.setmode(gpioMode) 

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1
        else:
            pud = GPIO.PUD_DOWN
            last_status = 0
 
        GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud)

        return setup_clients()



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
    
    wait = 0.005
    waiting = 0
    fast_wait = 0.0001 # increase accuracy during messages
    slow_wait = 0.05   # less accurate timing between messages

    while True:
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
        wait = fast_wait
        waiting = 0
          
    mesg(syslog.LOG_ERR, 'gpio_listener loop ended')
    
   

def daemonize( func, args=None ):
        if args is None:
            worker = Thread(target=func, name=str(func), daemon=True )
        else:
            worker = Thread(target=func, name=str(func), daemon=True, args=args)

        worker.start()
        return worker




if __name__ == '__main__':

   mesg(log_level, 'key listener starting' )
   CLIENTS = setup()

   ana = daemonize(analyzer )
   gpl = daemonize(gpio_listener)
   gpl.join()
   ana.join()
