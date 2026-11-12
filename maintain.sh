#!/bin/bash -x
# periodic auto-update of software and reboot 
# scheduled nightly at 2am or so


# fix /etc/hosts for remote unit
ip=$(hostname -I | cut -d' ' -f 1)
echo ${ip}

if [[ ! ${ip} == 192.168.20.* ]]; then
   echo "remote fix"
   cp /etc/hosts  /etc/hosts_saved
   sed 's/^192.168.20.94.*drmatthewclark.com//' /etc/hosts > /tmp/tmp_etc_hosts
   if diff -q /etc/hosts /tmp/tmp_etc_hosts; then
      echo "no change to /etc/hosts"
   else
      echo "editing /etc/hosts to remove drmatthewclark.com"
      cp -v /tmp/temp_etc_hosts  /etc/hosts
   fi
fi


echo "start maintainance  "
date
cd /usr/local/rpi_telegraph
echo "update "
pwd
git pull
crontab crontab
cp key_listener.service /lib/systemd/system/
cp telegraph_listener.service /lib/systemd/system/


cd /var/www
pwd
git pull

cd /root
sync
sync
sync

echo -n "reboot "
date
/usr/sbin/reboot 
