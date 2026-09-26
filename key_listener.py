#!/usr/bin/python3

import RPi.GPIO as GPIO
import time as time
from threading import Thread
from config import *
import morse
from threading import Event
from multiprocessing.connection import Client as send_client
import traceback

signals = []    # stores tuples of (time, event(up/down) )  to evaluate

UP = GPIO.RISING
DOWN = GPIO.FALLING

# reverse if signal is grounding pin
if gpioInputGnd:
    UP = GPIO.FALLING
    DOWN = GPIO.RISING


# diagnostic
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

    if len(signals) < 2:
        return

    logmesg('LOG_INFO', '%6.4f interpret...' % (interval) )
    dot = morse.lengths['dotLength']
    dash = morse.lengths['dashLength']
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
                logmesg('LOG_ERR', f'interpret long gap: {interval} from {ls} to {s}')

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
    logmesg('LOG_INFO', f' interpret: {result}' )

    if not char is None:
       sendinterpret( char.encode('utf8') )
       logmesg('LOG_INFO', f'send msg { char.encode('utf8') }' )

    signals.clear()



def analyzer():

    """
    analyze the data collected so far
    """
    criteria =  morse.lengths['letterPauseLength'] 
    sleeptime = morse.lengths['dotLength']/2

    # loop awaiting signals
    while True:
        try:
            now = time.perf_counter()
            num_signals = len(signals)

            if num_signals == 0 :
              continue

            interval = now - signals[-1][0]
    
            if interval > criteria and num_signals % 2 == 0:  # >1 cause need and up and down
                interpret(interval)

        except Exception as err:
            logmesg('LOG_ERR', f'analyzer error {err} \n{traceback.format_exc()}  ' )
            pass
        finally:
            time.sleep(sleeptime) # wait for data 


 
def setup_gpio():

        try:
           GPIO.cleanup(gpioInputPin) 
           GPIO.setmode(gpioMode) 
           GPIO.setwarnings(False)
           logmesg('LOG_INFO', f'setup_gpio success')

        except Exception as err:
           logmesg('LOG_ERR', f'setup_gpio setmode: {err}')

        if gpioInputGnd:
            pud = GPIO.PUD_UP
            last_status = 1
        else:
            pud = GPIO.PUD_DOWN
            last_status = 0

        try:
          GPIO.setup(gpioInputPin, GPIO.IN, pull_up_down = pud )
        except Exception as err:
           logmesg('LOG_ERR', f'setup_gpio setup: {err}')


def key_signal(arg):
    # called on key press or release 
    now =  time.perf_counter()
    level = int( GPIO.input(gpioInputPin) )

    if gpioInputGnd:   # if grounding gpio pin for signal
         level = 1 - level 

    signals.append( (now, level ) )
    sendmsg( level == 1 ) 



def gpio_listener():
    """ 
    main listening loop for key presses
    """
    setup_gpio() 
    GPIO.add_event_detect(gpioInputPin, GPIO.BOTH, key_signal, 1 )
    Event().wait()  # wait here forever


def daemonize( func, args=None ):
        if args is None:
            worker = Thread(target=func, name=str(func), daemon=True )
        else:
            worker = Thread(target=func, name=str(func), daemon=True, args=args)

        worker.start()
        return worker




# send interpretation of key stroke
def sendinterpret( msg ):

   global intr_conn

   try:    
       intr_conn.send(msg)
   except:
       intr_conn = send_client(intr_address, authkey=b'x')
       intr_conn.send(msg)


# send telegraph key stroke
def sendmsg( msg ):
   global key_conn

   try:    
       key_conn.send(msg)
   except:
       key_conn = send_client(key_address, authkey=b'x')
       key_conn.send(msg)
   

if __name__ == '__main__':

   key_address =  ('127.0.5.1', 16320)
   intr_address = ('127.0.5.1', 16321)
   key_conn = None
   intr_conn = send_client(intr_address, authkey=b'x')

   logmesg('LOG_INFO', 'key listener starting' )
   setup_gpio()
   ana = daemonize( analyzer )  # figures out the letters
   gpio_listener()  # listens to local key waits here forever
   ana.join()
   logmesg('LOG_ERR', 'gpio_listener ended unexpectedly' )

