#!/bin/bash
# periodic auto-update of software and reboot 
# scheduled nightly at 2am or so
echo "start maintainance"
date

cd /usr/local/rpi_telegraph
crontab crontab
git pull

cd /var/www/html
git pull

#/usr/sbin/reboot
