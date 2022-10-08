#!/usr/bin/python3

import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time as time
import syslog
from threading import Thread
from config import *
from morse import *
import re

# ips addresses to broacast telegraph messages to
# is now in config file
#IPS = ['localhost']

# clients
clients = []

# topic to broadcast for key press/release 
topic = 'key'

pubclient = None
pubtopic = 'code'

signals = []

last_press = time.perf_counter()
last_status = 0

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


def interpret(interval):
    """ 
    interpret  the key clicks to assign to a caracter

    """
 
    if len(signals) < 2:
        return

    mesg(syslog.LOG_INFO, '%6.4f interpret...' % (interval) )
    dot = lengths['dotLength']
    dash = lengths['dashLength']

    dotdash = []

    for i, (t, s) in enumerate(signals):
        if i > 0:
            (lt, ls ) = signals[i-1]
            interval = t - lt
            if s == 0 and ls == 1:
                dotdash.append(interval)
            if s == 1 and ls == 0:
                dotdash.append(-interval)

    #mesg(syslog.LOG_DEBUG, str(dotdash) )
    morseChar = ''

    #    0.0235 0.0800 code       dotLength err: -70.651%
    mesg(syslog.LOG_INFO, ' time     ideal           best fit         % error')
    totalerr = 0

    for d  in dotdash:

        p = matchLength(d)  # p is the name of the length, 'dotLength'
        correct = lengths.get(p)
        if d < 0:
          guess = 'pause'
        else:
          guess = p

        err = 100.*(abs(d)-correct)/correct
        totalerr += err
        mesg(syslog.LOG_INFO, '% 5.4f %5.4f code %15s err: % 6.3f%%' % (d, correct, guess, err  ))
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

    totalerr /= len(dotdash)
    char = morse2char(morseChar)
    result =   "%s\t%s\t%4.2f" % (morseChar, char, totalerr)
    mesg(syslog.LOG_INFO, result)
    c, ip = clients[0]
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


def key_press(channel, now=0):

        """
         called when the key is pressed and when released

	"""

        global last_status, last_press

        #mesg(syslog.LOG_DEBUG, 'key pressed pin' + str(channel)  )
        #now = time.perf_counter()

        last_press = now

        status = GPIO.input(channel)

        # telegraph key pressed

        if gpioInputGnd:   # if grounding gpio pin for signal
            status = 1 - status

        if status == last_status:
            return

        last_status = status

        signals.append( (now, status ) )

        #mesg(syslog.LOG_DEBUG, 'about to publish  ' + str(status) )
        for clientr in clients:
                client, IP = clientr
                #mesg(syslog.LOG_DEBUG, 'published  ' + str(status) )
                ecode, count  = client.publish(topic, status, qos)
                if ecode != 0:
                    mesg(syslog.LOG_ERR, 'publish error ' + str(ecode) )
                    client.connect(IP)



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

    mesg(syslog.LOG_INFO, str(client) + ' ' + str(rs) + ' disconnected')
    for d in clients:
        c, ip = d
        if c == client:
            ret = client.connect(ip)
            if ret == 0:
                mesg(syslog.LOG_INFO, 'reconnected ' + str(ip))
            else:
                mesg(syslog.LOG_ERR, 'failed to reconnect ' + str(ip))


def setup_clients():
    """
    set up the connections

    """

    for IP in IPS:
        try:
            client = mqtt.Client(topic + str(IP) )
            client.on_connect = on_connect
            client.on_disconnect = on_disconnect
            client.connect(IP)
            clients.append( (client, IP) )
            mesg(log_level, 'client ' + IP + ' connected' )

        except Exception as exp:
            mesg(syslog.LOG_ERR, 'error connecting to ' + str(IP) )

    return pubclient
 
def setup():

        GPIO.setmode(gpioMode) 
        pud = GPIO.PUD_DOWN
        last_status = 0

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1

        GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud)

        pubclient = setup_clients()
        # announce startup
        mesg(syslog.LOG_INFO, 'key listener started' )
        return clients


def gpio_listener():
    """ 
    main listening loop for key presses
    """

    while True:
        GPIO.wait_for_edge(gpioInputPin,GPIO.BOTH)
        key_press(gpioInputPin, now=time.perf_counter())
       

def daemonize( func ):
	worker = Thread(target=func, name=str(func), daemon=True)
	worker.start()
	return worker


mesg(log_level, 'key listener starting' )
clients = setup()

daemonize(analyzer)
gpl = daemonize(gpio_listener)
gpl.join()

