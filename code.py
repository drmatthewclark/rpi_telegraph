#
# table to define dots and dashes 
# this table is 1920 telegraph code used in mechanical telegraph
# sounders, not modern international morse code.
# https://en.wikipedia.org/wiki/Telegraph_code#Comparison_of_codes
#
# this variation has pauses within the letters
#

morse1920 =   {
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
        '9': '-..-',
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
        }


#
# table to define dots and dashes 
# this is the modern international morse code from 1851
# 
# ITU recommendation ITU-R M.1677.1 (10/2009)
# http://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.1677-1-200910-I!!PDF-E.pdf
# oddly, the IMC has no ampersand
#
morseIMC =  {
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
	chr(247): '---...',  # division
	chr(2715) : '-..-',  # multiplication
	chr(2032) : '.----.',  # multiplication
	chr(2032) : '.----.',  # minute symbol
	chr(2033) : '.----.l.----.',  # second symbol
        }
