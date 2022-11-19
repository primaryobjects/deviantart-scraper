#!/bin/bash

#
# Add a cron job to run this script every 15 minutes.
# crontab -e
# */15 * * * * /home/YOUR_USER_NAME/Documents/wallpaper.sh
#
USER=$(whoami)
ORIGINAL_DIR=$(pwd)
LOG_DIR=/var/tmp/wallpaper.log

START_DATE_TIME=$(date '+%m/%d/%Y %H:%M:%S')
echo "$START_DATE_TIME Starting wallpaper change." > $LOG_DIR

# Fix to allow cronjob to accurately set the desktop background. https://askubuntu.com/a/198508
count=0
fl=$(find /proc -maxdepth 2 -user $USER -name environ -print -quit)
while [ -z $(grep -z DBUS_SESSION_BUS_ADDRESS "$fl" | cut -d= -f2- | tr -d '\000' ) ]
do
  count=$((count+1))
  if [ "$count" -gt 100 ];then
    DATE_TIME=$(date '+%m/%d/%Y %H:%M:%S')
    echo "$DATE_TIME Failed to find DBUS_SESSION after $((count-1)) attempts." >> $LOG_DIR
    break
  fi

  DATE_TIME=$(date '+%m/%d/%Y %H:%M:%S')
  echo "$DATE_TIME Searching for DBUS_SESSION ($count)." >> $LOG_DIR

  fl=$(find /proc -maxdepth 2 -user $USER -name environ -newer "$fl" -print -quit)
done

export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS "$fl" | cut -d= -f2-)
DATE_TIME=$(date '+%m/%d/%Y %H:%M:%S')
echo "$DATE_TIME Found DBUS_SESSION at $DBUS_SESSION_BUS_ADDRESS" >> $LOG_DIR

# Delete cached wallpaper.
rm -f /var/tmp/wallpaper.jpg /var/tmp/wallpaper.jpeg /var/tmp/wallpaper.gif /var/tmp/wallpaper.png

# Download image.
cd /home/$USER/Documents/deviantart-scraper/

month=$(date +%m)
if [ $month -eq "10" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/horror" >> $LOG_DIR
elif [ $month -eq "11" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/artisan-crafts" >> $LOG_DIR
elif [ $month -eq "12" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/poetry" >> $LOG_DIR
elif [ $month -eq "1" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/photography" >> $LOG_DIR
elif [ $month -eq "2" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/game-art" >> $LOG_DIR
elif [ $month -eq "3" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/stock-images" >> $LOG_DIR
elif [ $month -eq "4" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/science-fiction" >> $LOG_DIR
elif [ $month -eq "5" ]; then
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r -u "https://www.deviantart.com/topic/photo-manipulation" >> $LOG_DIR
else
    python3 devianart.py -d /var/tmp -f wallpaper -c 1 -r >> $LOG_DIR
fi

FILE_PATH=$(tail -n 1 $LOG_DIR)
cd $ORIGINAL_DIR

# Delete cached wallpaper.
rm -f /home/$USER/.cache/wallpaper/*

# Set new wallpaper.
gsettings set org.gnome.desktop.background picture-options "zoom"
gsettings set org.gnome.desktop.background picture-uri file://$FILE_PATH_invalid
gsettings set org.gnome.desktop.background picture-uri file://$FILE_PATH

END_DATE_TIME=$(date '+%m/%d/%Y %H:%M:%S')
echo "Downloaded $FILE_PATH" >> $LOG_DIR
echo "Started at $START_DATE_TIME. Finished at $END_DATE_TIME." >> $LOG_DIR
