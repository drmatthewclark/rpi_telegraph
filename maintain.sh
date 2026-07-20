#!/bin/bash
# periodic auto-update of software and reboot 
# scheduled nightly at 2am or so

cd /usr/local/rpi_telegraph
git pull
crontab crontab

cd /var/www/html
git pull

reboot
