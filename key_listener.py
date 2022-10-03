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
 
topic = 'key'
signals = []

last_press = time.perf_counter()
last_status = 0

log_level = syslog.LOG_INFO

UP = GPIO.RISING
DOWN = GPIO.FALLING

if gpioInputGnd:
    UP = GPIO.FALLING
    DOWN = GPIO.RISING


dot = lengths['dotLength']
dash = lengths['dashLength']
letterPause = lengths['letterPauseLength']

def mesg(log_level, msg):
    syslog.syslog(log_level, msg)
    print(msg)

def msg(message):
    mesg(log_level, message)

def interpret():
    
    if len(signals) < 2:
        return

    msg('interpret...')
    #       0.0235 0.0800 code       dotLength err: -70.651%
    msg('time     ideal        best fit            % error')
    global dot
    lens = []
    dotdash = []
    dash = 3*dot

    for i, (t, s) in enumerate(signals):
        if i > 0:
            (lt, ls ) = signals[i-1]
            interval = t - lt
            if s == 0 and ls == 1:
                dotdash.append(interval)
            if s == 1 and ls == 0:
                dotdash.append(-interval)

    morseChar = ''
    oldmorse = activecode == 'morse1920'

    for d  in dotdash:
        dotdist = abs(abs(d)-dot)
        dashdist = abs(abs(d)-dash)
        p = matchLength(d)
        correct = lengths.get(p)
        msg('% 5.4f %5.4f code %15s err: % 6.3f%%' % (d, correct, p, 100.*(abs(d)-correct)/correct  ))
        if d > 0.0:
            if p == 'dotLength':
                morseChar += '.'
            elif p == 'morseLLength' and oldmorse:
                morseChar += 'L'
            elif p == 'morse0Length' and oldmorse:
                morseChar += 'z'
            else:
                morseChar += '-'

        if d < 0.0:
            if p == 'dotLength':
                pass
            elif oldmorse and p == 'pauseLength' and morseChar[-1] == '.':
                morseChar += 'd'

    char = morse2char(morseChar)
    msg("'" + morseChar + "'" +  ' : ' + char )
    signals.clear()



def analyzer():
    sleeptime =  0.20
    while True:
        now = time.perf_counter()
        if (now - last_press) > 0.5:
            interpret()

        time.sleep(sleeptime)


def key_press(channel):

        global last_status, last_press

        now = time.perf_counter()
        status = GPIO.input(channel)

        # telegraph key pressed

        if gpioInputGnd:   # if grounding gpio pin for signal
            status = 1 - status

        if status == last_status:
            return

        last_status = status

        signals.append( (now, status ) )
        last_press = now

        for clientr in clients:
                client, IP = clientr
                ecode, count  = client.publish(topic, status, qos)
                if ecode != 0:
                    mesg(syslog.LOG_ERR, 'publish error ' + str(ecode) )
                    client.connect(IP)


def on_connect(client, userdata, flags, rc):
        if rc != 0:
                mesg(syslog.LOG_ERR, 'key listener ERROR connecting: ' + str(rc) )

        mesg(log_level, 'key listener connected' )


def on_disconnect(client, userdata, rs):
    mesg(log_level, str(client) + ' ' + str(rs) + ' disconnected')
    for d in clients:
        c, ip = d
        if c == client:
            ret = client.connect(ip)
            if ret == 0:
                mesg(log_level, 'reconnected ' + str(ip))
            else:
                mesg(syslog.LOG_ERR, 'failed to reconnect ' + str(ip))


def setup_clients():

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

def setup():

        GPIO.setmode(gpioMode) 
        pud = GPIO.PUD_DOWN
        last_status = 0

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1

        GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud)

        setup_clients()
        # announce startup
        mesg(log_level, 'key listener started' )
        return clients

def gpio_listener():
    while True:
        GPIO.wait_for_edge(gpioInputPin,GPIO.BOTH)
        key_press(gpioInputPin)
       

mesg(log_level, 'key listener starting' )
clients = setup()
worker = Thread(target=analyzer)
worker.setDaemon(True)
worker.start()

l = Thread(target=gpio_listener)
l.setDaemon(True)
l.start()

while True:
    time.sleep(100)


#clients[0].loop_forever()
