#!/bin/bash
# periodic auto-update

cd /usr/local/rpi_telegraph
git pull
#service telegraph_listener restart
#service key_listener restart

cd /var/www/html
git pull

#pm2 restart all
reboot
