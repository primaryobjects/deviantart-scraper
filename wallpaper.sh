#!/bin/bash

#
# Add a cron job to run this script every 15 minutes.
# crontab -e
# */15 * * * * /home/YOUR_USER_NAME/Documents/wallpaper.sh
#
USER=$(whoami)
ORIGINAL_DIR=$(pwd)

# Delete cached wallpaper.
rm -f /tmp/wallpaper.jpg /tmp/wallpaper.jpeg /tmp/wallpaper.gif /tmp/wallpaper.png

# Download image.
cd /home/$USER/Documents/deviantart-scraper/
python3 devianart.py -d /tmp -f wallpaper -c 1 -r > /tmp/wallpaper.log
FILE_PATH=$(tail -n 1 /tmp/wallpaper.log)
cd $ORIGINAL_DIR

# Delete cached wallpaper.
rm -f /home/$USER/.cache/wallpaper/*
sleep 1

echo "Downloaded $FILE_PATH" >> /tmp/wallpaper.log

# Set new wallpaper.
gsettings set org.gnome.desktop.background picture-options "zoom"
gsettings set org.gnome.desktop.background picture-uri file://$FILE_PATH