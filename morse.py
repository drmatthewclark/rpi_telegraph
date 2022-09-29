"""
Matthew Clark (c) 2022
telegraph
29 SEP 2022
"""

#!/usr/bin/python

import sys
from random import gauss
import RPi.GPIO as GPIO
from time import sleep
import syslog
from code import *

# global setup stuff

# interval lengths in seconds
# 80 - 15 wpm
# 60 - 20 wpm
# 50 - 24 wpm
# 20 - 60 wpm  too fast for sounder

gpioPin = 12
pinOn = False
lengths = {}

log_level = syslog.LOG_INFO
syslog.setlogmask(syslog.LOG_UPTO(log_level))

# defaults
activecode = morse1920
wpm = 20
MAX_WPM = 60

def setLoglevel(lvl):
	# LOG_EMERG, LOG_ALERT, LOG_CRIT, LOG_ERR, LOG_WARNING, LOG_NOTICE, LOG_INFO, LOG_DEBUG
	global log_level
	if lvl in loglabels:
		levelname = loglabels.get(lvl, 'UNKNOWN')

	syslog.setlogmask(syslog.LOG_UPTO(7)) # otherwise the next message might not be logged
	syslog.syslog(syslog.LOG_INFO, 'set log level to ' + str(lvl) + ':' + levelname)
	try:
		log_level = lvl
		syslog.setlogmask(syslog.LOG_UPTO(lvl))
	except:
		syslog.syslog(syslog.LOG_ERR, 'error setting syslog level to ' + str(lvl) )

	return log_level


def setSpeed(wpm):

	wpm = min(abs(wpm), MAX_WPM)
	wordsPerMinute = wpm 
	dotLength = 60.0/(wordsPerMinute * 50) # based on PARIS

	dashLength = 3 * dotLength
	pauseLength = dotLength           # used for pauses in letters for old telegraph codes, 1+1 = 2
	letterPauseLength = dotLength * 3 # pause between letters is 3 dots, but since
				  # each letter has a dot pause, this is added to make 3 dots pause.

	wordPauseLength = dotLength * 5   # pause between words, 5 + 1 letter pause for total of 6
	morseLLength = dashLength * 2     # special long dash for old Morse L
	morse0Length = dashLength * 3     # special long dash for old Morse 0
	randomAmount = 0.05  # 5% variation in length, gaussian randomness

	lengths['dotLength'] = dotLength
	lengths['dashLength'] = dashLength
	lengths['pauseLength'] = pauseLength
	lengths['letterPauseLength'] = letterPauseLength
	lengths['wordPauseLength'] = wordPauseLength
	lengths['morseLLength'] = morseLLength
	lengths['morse0Length'] = morse0Length
	lengths['randomAmount'] = randomAmount

	syslog.syslog(syslog.LOG_INFO, 'setSpeed: set speed to ' + str(wpm) )
	return lengths

lengths = setSpeed(wpm)

def setActivecode(codename):
	global activecode

	if 'IMC' in codename:
		activecode = morseIMC
	else:
		activecode = morse1920

	syslog.syslog(syslog.LOG_INFO, 'set code set to %s' %  (activecode.get('Name'))  )	
	return activecode.get('Name')


# figure below is worked out using standard characters and spacings
# PARIS has 50 elements

# standard messages
endOfMessage = 'www.-.-.'  
endOfTransmission = '.-.-.w'
endOfWork = '...-.-'

# make it a little less mechanically uniform with a Gaussian
# deviation of 5%
randomDeviation = lengths['dotLength'] * lengths['randomAmount']

#
# defines which morse code variation to use
#
def morse(char):
	return activecode.get(char, ' ')


# wrapper for pulses

def key(action):
	global pinOn # track outside of GPIO
	if action == '1':
		GPIO.output(gpioPin, GPIO.HIGH)
		pinOn = True
	elif action == '0':
		GPIO.output(gpioPin, GPIO.LOW)
		pinOn = False


def pulse(duration):
	GPIO.output(gpioPin, GPIO.HIGH)
	sleep(duration + gauss(0, randomDeviation))
	GPIO.output(gpioPin, GPIO.LOW)
	sleep(lengths['dotLength'] + gauss(0, randomDeviation))

def dot():
	syslog.syslog(syslog.LOG_DEBUG, "dit ")
	pulse(lengths['dotLength'])

def dash():
	syslog.syslog(syslog.LOG_DEBUG, "dah ")
	pulse(lengths['dashLength'])

def morseL():    # special for old morse L
	syslog.syslog(syslog.LOG_DEBUG, "dahh ")
	pulse(lengths['morseLLength'])

def morse0():   # special dash for old morse 0
	syslog.syslog(syslog.LOG_DEBUG, "dahhh ")
	pulse(lengths['morse0Length'])

def midLetterPause():   # special mid-character pause for old morse
	syslog.syslog(syslog.LOG_DEBUG, "spaced letter pause")
	sleep(lengths['pauseLength'])

def letterPause():  # pause between letters
	syslog.syslog(syslog.LOG_DEBUG, "letter pause" ) 
	sleep(lengths['letterPauseLength'])

def wordPause():  # pause between words
	syslog.syslog(syslog.LOG_DEBUG, "*-word space-*") 
	sleep(lengths['wordPauseLength'])


def space():
	syslog.syslog(syslog.LOG_DEBUG, "space") 
	sleep(lengths['wordPauseLength'])
	syslog.syslog(syslog.LOG_DEBUG, "space") 


def sendCode(code):
	# code is the character's code like --.- 

	for dahdit in code:
		if dahdit == '.':
			dot()
		elif dahdit == '-':
			dash()
		elif dahdit == 'd':
			midLetterPause()  # for old Vail US telegraphy
		elif dahdit == 'w':
			wordPause()  # pause between words
		elif dahdit == 'z':
			morse0()     # very long dash
		elif dahdit == 'L':
			morseL()     # long dash
		elif dahdit == 'l':
			letterPause() # pause between letters
		else:  # any other character, or an actual space
			syslog.syslog(syslog.LOG_WARNING, 'unexpected letter ' + dahdit )
			space()

	letterPause()


# setup IO ports
def setup():
   GPIO.setmode(GPIO.BOARD) ## Use board pin numbering
   GPIO.setup(gpioPin, GPIO.OUT)  ## Setup GPIO Pin to OUT
   GPIO.output(gpioPin, GPIO.LOW)


def message(dline):

   global pinOn
   # skip if sounder is down
   # GPIO.input doesn't work correctly here

   if pinOn:
     return 

   else:

     dline = dline.upper().strip()

     for char in dline:
       syslog.syslog(syslog.LOG_DEBUG, str(char) + " ")
       morseCode = morse(char) # convert char to morse code representation
       sendCode(morseCode)     # sound out the code


#
# realistic end of message codes
#
#sendCode(endOfMessage)
#sendCode(endOfTransmission)
#sendCode(endOfWork)

