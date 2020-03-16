#!/bin/bash

#
# Add a cron job to run this script every 15 minutes.
# crontab -e
# */15 * * * * /home/YOUR_USER_NAME/Documents/wallpaper.sh
#
USER=$(whoami)
ORIGINAL_DIR=$(pwd)

# Delete cached wallpaper.
rm -f /tmp/wallpaper.*

# Download image.
cd /home/$USER/Documents/deviantart-scraper/
FILE_PATH=$(python3 devianart.py -d /tmp -f wallpaper -c 1 -r | tail -1)
cd $ORIGINAL_DIR

# Delete cached wallpaper.
rm -f /home/$USER/.cache/wallpaper/*

echo "Downloaded $FILE_PATH"

# Set new wallpaper.
gsettings set org.gnome.desktop.background picture-options "zoom"
gsettings set org.gnome.desktop.background picture-uri file://$FILE_PATH