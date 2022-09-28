# WIRELESS TELEGRAPH


this project will operate a telegraph sounder with the original telegraph code.
It listens for either a telegraph key, or a message passed to the sounder vi MQTT.

one can publish a message using the mosquitto publishing utility: eg 

*mosquitto_pub -t telegraph -m "what hath god wrought"* 

The MQTT code will queue messages so that if many are recieved before the first one has completed sounding they will be sounded out in order.


