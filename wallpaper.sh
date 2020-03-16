#!/bin/bash

#
# Add a cron job to run this script every 15 minutes.
# crontab -e
# */15 * * * * /home/YOUR_USER_NAME/Documents/wallpaper.sh
#
USER=$(whoami)
ORIGINAL_DIR=$(pwd)

# Fix to allow cronjob to accurately set the desktop background. https://askubuntu.com/a/198508
fl=$(find /proc -maxdepth 2 -user $USER -name environ -print -quit)
while [ -z $(grep -z DBUS_SESSION_BUS_ADDRESS "$fl" | cut -d= -f2- | tr -d '\000' ) ]
do
  fl=$(find /proc -maxdepth 2 -user $USER -name environ -newer "$fl" -print -quit)
done
export DBUS_SESSION_BUS_ADDRESS=$(grep -z DBUS_SESSION_BUS_ADDRESS "$fl" | cut -d= -f2-)
echo $DBUS_SESSION_BUS_ADDRESS > /tmp/wallpaper.log

# Delete cached wallpaper.
rm -f /tmp/wallpaper.jpg /tmp/wallpaper.jpeg /tmp/wallpaper.gif /tmp/wallpaper.png

# Download image.
cd /home/$USER/Documents/deviantart-scraper/
python3 devianart.py -d /tmp -f wallpaper -c 1 -r >> /tmp/wallpaper.log
FILE_PATH=$(tail -n 1 /tmp/wallpaper.log)
cd $ORIGINAL_DIR

# Delete cached wallpaper.
rm -f /home/$USER/.cache/wallpaper/*

echo "Downloaded $FILE_PATH" >> /tmp/wallpaper.log

# Set new wallpaper.
gsettings set org.gnome.desktop.background picture-options "zoom"
gsettings set org.gnome.desktop.background picture-uri file://$FILE_PATH