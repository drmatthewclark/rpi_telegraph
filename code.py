"""
Matthew Clark  (c)2022
telegraph
29 SEP 2022
"""
loglevels = { 'LOG_EMERG':0, 'LOG_ALERT':1, 'LOG_CRIT' : 2, 'LOG_ERR': 3, 'LOG_WARNING':4, 'LOG_NOTICE':5, 'LOG_INFO':6, 'LOG_DEBUG' : 7 }
loglabels = { 0: 'LOG_EMERG', 1:'LOG_ALERT', 2:'LOG_CRIT', 3:'LOG_ERR', 4:'LOG_WARNING', 5:'LOG_NOTICE', 6:'LOG_INFO', 7:'LOG_DEBUG' }
#
# table to define dots and dashes 
# this table is 1920 telegraph code used in mechanical telegraph
# sounders, not modern international morse code.
# https://en.wikipedia.org/wiki/Telegraph_code#Comparison_of_codes
#
# this variation has pauses within the letters
#

americanMorse  =   {
	'Name': 'americanMorse',   # self identify the code map
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
# ITU recommendation ITU-R M.1677.1 (10/2009)
# http://www.itu.int/dms_pubrec/itu-r/rec/m/R-REC-M.1677-1-200910-I!!PDF-E.pdf
# oddly, the IMC has no ampersand
#
morseIMC =  {
	'Name': 'morseIMC',   # self identify the code map
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
        ';': '_._._',
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
        '÷'  :'---...',  # division
	'X' : '-..-',  # multiplication
	'′' : '.----.',  # minute symbol
        'Á' : '.--.-',
        'Ä' : '.-.-',
        'É' : '.._..',
        'Ñ' : '__.__',
        'Ö' : '___.',
        'Ü' : '..__',
        'WAIT' : '._...',
        'EOW'  : '..._._',
        'START' : '_._._',
        }
