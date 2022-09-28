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

+*sudo cp key_listener.service /lib/systemd/system/*
+*sudo cp telegraph_listener.service /lib/systemd/system/*
+*sudo systemctl enable telegraph_listener*
+*sudo systemctl enable key_listener*


and start them

+*sudo systemctl start  telegraph_listener*
+*sudo systemctl start key_listener*

    
