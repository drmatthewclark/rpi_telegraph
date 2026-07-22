#!/bin/bash
# periodic auto-update of software and reboot 
# scheduled nightly at 2am or so
echo "start maintainance"
date

cd /usr/local/rpi_telegraph
echo "update crontab"
crontab crontab
pwd
git pull

cd /var/www/html
pwd
git pull

cd /root
sync
sync

echo -n "reboot "
date

/usr/sbin/reboot -f
