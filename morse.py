#!/usr/bin/python

import sys
from random import gauss
import RPi.GPIO as GPIO
from time import sleep
import syslog

# global setup stuff

# interval lengths in seconds
# 80 - 15 wpm
# 60 - 20 wpm
# 50 - 24 wpm
# 20 - 60 wpm  too fast for sounder

gpioPin = 12
pinOn = False
lengths = {}
wpm = 20

def setSpeed(wpm):

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
	return lengths

lengths = setSpeed(wpm)

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
# table to define dots and dashes 
# this table is 1920 telegraph code used in mechanical telegraph
# sounders, not modern international morse code.
# https://en.wikipedia.org/wiki/Telegraph_code#Comparison_of_codes
#
# this variation has pauses within the letters
#
def morse1920(x):
    return {
	' ': 'w',   # word pause
        'A': '.-',
        'B': '-...',
        'C': '..d.',
        'D': '-..',
        'E': '.',
        'F': '.-.',
        'G': '--.',
        'H': '....',
        'I': '..',
        'J': '-.-.',
        'K': '-.-',
        'L': 'L',
        'M': '--',
        'N': '-.',
        'O': '.d.',
        'P': '.....',
        'Q': '..-.',
        'R': '.d..',
        'S': '...',
        'T': '-',
        'U': '..-',
        'V': '...-',
        'W': '.--',
        'X': '.-..',
        'Y': '..d..',
        'Z': '...d.',
	'&': '.d...',
        '1': '.--.',
        '2': '..-..',
        '3': '...-',
        '4': '....-',
        '5': '---',
        '6': '......',
        '7': '--..',
        '8': '-....',
        '9': '-..-.',
        '0': 'z',
	'.': '..--..',
	':': '-.-d..',
	';': '.-.-.',
	',': '.-.-',
	'?': '-..-.',
	'!': '---.',
	'\n' : 'w----',
	'('  : '.-..-',
	')'  : '.-..-',
        }.get(x, ' ')  # default is space

#
# table to define dots and dashes 
# this is the modern international morse code from 1851
# 
# ITU recommendation ITU-R M.1677.1 (10/2009)
# http://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.1677-1-200910-I!!PDF-E.pdf
# oddly, the IMC has no ampersand
#
def morseIMC(x):
    return {
	' ': 'w',   # word pause
        'A': '.-',
        'B': '-...',
        'C': '-.-.',
        'D': '-..',
        'E': '.',
        'F': '..-.',
        'G': '--.',
        'H': '....',
        'I': '..',
        'J': '.---',
        'K': '-.-',
        'L': '.-..',
        'M': '--',
        'N': '-.',
        'O': '---',
        'P': '.--.',
        'Q': '--.-',
        'R': '.-.',
        'S': '...',
        'T': '-',
        'U': '..-',
        'V': '...-',
        'W': '.--',
        'X': '-..-',
        'Y': '-.--',
        'Z': '--..',
        '1': '.----',
        '2': '..---',
        '3': '...--',
        '4': '....-',
        '5': '.....',
        '6': '-....',
        '7': '--...',
        '8': '---..',
        '9': '----.',
        '0': '-----',
	'.': '.-.-.-',
	',': '--..--',
	':': '---...',
	'?': '..--..',
	'\'': '.----.',
	'-': '-....-',
	'/': '-..-.',
	'(': '-.--.',
	')': '-.--.-',
	'"': '.-..-.',
	'=': '-...-',
	'+': '.-.-.',
	'@': '.--.-.',
	'%': '-----l-..-.l-----',  # 0/0 
	unichr(247): '---...',  # division
	unichr(2715) : '-..-',  # multiplication
	unichr(2032) : '.----.',  # multiplication
	unichr(2032) : '.----.',  # minute symbol
	unichr(2033) : '.----.l.----.',  # second symbol
        }.get(x, ' ')  # default is space

#
# defines which morse code variation to use
#
def morse(char):
	return morse1920(char)

# wrapper for pulses

def key(action):
	global pinOn
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
	print("dit ")
	pulse(lengths['dotLength'])

def dash():
	print("dah ")
	pulse(lengths['dashLength'])

def morseL():    # special for old morse L
	print("dahh ")
	pulse(lengths['morseLLength'])

def morse0():   # special dash for old morse 0
	print("dahhh ")
	pulse(lengths['morse0Length'])

def midLetterPause():   # special mid-character pause for old morse
	print("pause ",)
	sleep(lengths['pauseLength'])

def letterPause():  # pause between letters
	print("\t\t-letter")
	sleep(lengths['letterPauseLength'])

def wordPause():  # pause between words
	print("*-word space-*")
	sleep(lengths['wordPauseLength'])


def space():
	print("space")
	sleep(lengths['wordPauseLength'])
	print("space")


def sendCode(code):
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
			print("unexpected letter: ", dahdit)
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
       print (char," ",)
       morseCode = morse(char)
       sendCode(morseCode)


#
# realistic end of message codes
#
#sendCode(endOfMessage)
#sendCode(endOfTransmission)
#sendCode(endOfWork)

