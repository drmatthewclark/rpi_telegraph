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

# ips addresses to broacast telegraph messages to
# is now in config file
#IPS = ['localhost']


# topic to broadcast for key press/release 
topic = 'key'

pubtopic = 'code'

signals = []

last_press = time.perf_counter()
keepalive=30
setLoglevel(log_level)

UP = GPIO.RISING
DOWN = GPIO.FALLING

# reverse if signal is grounding pin
if gpioInputGnd:
    UP = GPIO.FALLING
    DOWN = GPIO.RISING


def mesg(log_level, msg):
    syslog.syslog(log_level, msg)
    print(msg)


def reconnect():
    # connect if not connected
    for client, IP in clients:
        if not client.is_connected():
            if client.connect(IP, keepalive=keepalive) != 0:
                mesg(syslog.LOG_ERROR, 'failed to reconnect' )
                return 0
    return 0



def interpret(interval):
    """ 
    interpret  the key clicks to assign to a caracter

    """
    if len(clients) == 0:
         setup_clients()
    if len(clients) == 0:
         return
 
    if len(signals) < 2:
        return

    mesg(syslog.LOG_INFO, '%6.4f interpret...' % (interval) )
    dot = lengths['dotLength']
    dash = lengths['dashLength']
    c, ip = clients[0]
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

    #mesg(syslog.LOG_DEBUG, str(dotdash) )
    morseChar = ''

    header =  ' time(ms) ideal(ms)  best fit          % error'
    c.publish('code', header.encode('utf8'), qos)
    #mesg(syslog.LOG_INFO, header)

    actual_length = 0
    ideal_length = 0

    for d  in dotdash:

        p = matchLength(d)  # p is the name of the length, 'dotLength'
        correct = lengths.get(p)
        if d < 0:
           guess = 'pause'
        else:
          guess = p

        err = 100.*(abs(d)-correct)/correct
        ideal_length += correct
        actual_length += abs(d)   # length
        keymsg = '% 5d    %5d %15s err: % 6.0f%%' % (int(1000*d), int(1000*correct), guess, err  )
        c.publish('code', keymsg.encode('utf8'), qos )

        #mesg(syslog.LOG_INFO,  keymsg )
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
    c.publish('code', result.encode('utf8'), qos)
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

        # telegraph key pressed

        if gpioInputGnd:   # if grounding gpio pin for signal
            status = 1 - status

        signals.append( (now, status ) )

        reconnect()

        #mesg(syslog.LOG_DEBUG, 'about to publish  ' + str(status) )
        for clientr in clients:
                client, IP = clientr
                #mesg(syslog.LOG_DEBUG, 'published  ' + str(status) )
                ecode, count  = client.publish(topic, status, qos)
                if ecode != 0:
                    mesg(syslog.LOG_ERR, 'publish error ' + str(ecode) )


def on_connect(client, userdata, flags, rc):
	"""
	called on connection to mqtt server 

	"""
	if rc != 0:
		mesg(syslog.LOG_ERR, 'key listener ERROR connecting: ' + str(rc) )

	mesg(syslog.LOG_INFO, 'key listener connected' )


def on_disconnect(client, userdata, rs):
    """
    called on disconnect
    """

    mesg(syslog.LOG_INFO, 'on_disconnect ' + str(client) + ' ' + str(rs) + ' disconnected')

    if reconnect() == 0:
        mesg(syslog.LOG_INFO, 'reconnected ' + str(client))
    else:
        mesg(syslog.LOG_ERR, 'failed to reconnect ' + str(client))

def on_connectionlost():
	print('connection lost')

def setup_clients():
    """
    set up the connections

    """
    clients = []
    for IP in IPS:
        try:
            client = mqtt.Client(topic + str(IP) )
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.on_connectionlost = on_connectionlost
            client.connect(IP, keepalive=keepalive)
            clients.append( (client, IP) )
            mesg(log_level, 'client ' + IP + ' connected' )

        except Exception as exp:
            mesg(syslog.LOG_ERR, 'error connecting to ' + str(IP) )
 
    return clients
    
 
def setup():

        GPIO.setmode(gpioMode) 
        print('setup gpio')

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1
        else:
            pud = GPIO.PUD_DOWN
            last_status = 0
 
        GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud)
        print('setup gpio done')

        clients = setup_clients()
        # announce startup
        mesg(syslog.LOG_INFO, 'key listener started' )
        print('setup done')
        return clients


def gpio_listener():
    """ 
    main listening loop for key presses
    """
    global last_press
    while True:
        level = GPIO.input(gpioInputPin)
        while GPIO.input(gpioInputPin) == level:
            time.sleep(0.008)

        # the following does not always work
        #GPIO.wait_for_edge(gpioInputPin,GPIO.BOTH, timeout=65535)

        last_press=time.perf_counter()
        # not level because it changed
        key_press(gpioInputPin, not level, now=last_press)
       

def daemonize( func ):
	worker = Thread(target=func, name=str(func), daemon=True)
	worker.start()
	return worker


if __name__ == '__main__':

   mesg(log_level, 'key listener starting' )
   clients = setup()
   print('setup done')

   ana = daemonize(analyzer)
   gpl = daemonize(gpio_listener)
   gpl.join()
   ana.join()
