#!/bin/bash

cd /usr/local
apt install git
git clone https://github.com/drmatthewclark/rpi_telegraph
apt install watchdog
apt-get install mosquitto
apt install python3-pip
apt install python3-paho-mqtt
apt install mosquitto-clients

if [  -z  "$( grep listen /etc/mosquitto/mosquitto.conf )" ]
then
 echo "listener 1883 0.0.0.0" >> /etc/mosquitto/mosquitto.conf
fi

if [ -z  "$(grep allow_anonymous /etc/mosquitto/mosquitto.conf)" ]
then
echo "allow_anonymous true" >> /etc/mosquitto/mosquitto.conf
fi



cp key_listener.service /lib/systemd/system/
cp telegraph_listener.service /lib/systemd/system/
systemctl enable telegraph_listener
systemctl enable key_listener


systemctl start  telegraph_listener
systemctl start  key_listener

