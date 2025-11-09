# WIRELESS TELEGRAPH


this project will operate a telegraph sounder with the original telegraph code.
It listens for either a telegraph key, or a message passed to the sounder vi MQTT.

one can publish a message using the mosquitto publishing utility: eg 

*mosquitto_pub -t telegraph -m "what hath god wrought"* 

The MQTT code will queue messages so that if many are recieved before the first one has completed sounding they will be sounded out in order.


Wire the telegraph to ground, and an IO pin.  configure the gpio pin in telegraph_listener.
Wire the key to the +3v pin, and an IO pin    configure the gpio pin in key_listener

copy the service files to /lib/systemd/system to enable them as system services.
execute these commands to set up auto-starting the system on boot up:

+ *sudo cp key_listener.service /lib/systemd/system/*
+ *sudo cp telegraph_listener.service /lib/systemd/system/*
+ *sudo systemctl enable telegraph_listener*
+ *sudo systemctl enable key_listener*


and start them

+ *sudo systemctl start  telegraph_listener*
+ *sudo systemctl start key_listener*


one can set messages via a channel to change behavior. Send using 'control' as the topic

* mosquitto_pub -t speed -m 20 * to set speed
* mosquitto_pub -t code  -m IMC  # morse or IMC * to set morse1920 (preferred) or morseIMC code
* mosquitto_pub -t loglevel -m 0 * to set log level 0-7, 7 is debug.

   
# Configuration

configuration is in config.py


"""
configure which pins the equipment is connected to
"""

import RPi.GPIO as GPIO<br>
gpioMode = GPIO.BOARD

*set what pin to use to control your telegraph* <br>
gpioOutputPin = 12  <br>

*set the pin your key is connected to*  <br>
gpioInputPin = 18  <br>


*set addresss to broadcast to other telegraph sets running this system* <br>
*IP addresses for keys to send signals to*

IPS = ['localhost', '10.0.0.1']
 


to send a text message use mosquitto_pub

*mosquitto_pub -t telegraph -m "this is my message"*

use the -h option to send from other computers, or to send across networks
