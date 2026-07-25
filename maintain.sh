#!/bin/bash -x
# periodic auto-update of software and reboot 
# scheduled nightly at 2am or so

echo "start maintainance  "
date
cd /usr/local/rpi_telegraph
echo "update "
pwd
git pull
crontab crontab
cp key_listener.service /lib/systemd/system/
cp telegraph_listener.service /lib/systemd/system/


cd /var/www/html
pwd
git pull

cd /root
sync
sync
sync

echo -n "reboot "
date
/usr/sbin/reboot 
