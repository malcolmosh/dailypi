#!/bin/bash

# This script syncs the Pi Zero W's clock to RTC, sets a next alarm, displays an image pulled from the web, and shuts down the Pi
echo "______ $(date +"%Y-%m-%d %H:%M:%S") - Starting display.sh"

# The first argument is stored in $1 - it's the path to the folder where our bash scripts are stored
PATH_TO_FOLDER=$1

# Sleep while waiting for Wifi
sleep 30

# Sync Pi's clock to PiSugar2's RTC
echo 'rtc_rtc2pi' | nc -q 0 127.0.0.1 8423

# Set the next alarm according to the current time
"${PATH_TO_FOLDER}/screen/alarm.sh"

# Get battery percentage from the PiSugar module
BATTERY_STATUS=$(echo 'get battery' | nc -q 0 127.0.0.1 8423)
echo "$(date +"%Y-%m-%d %H:%M:%S") - $BATTERY_STATUS" 

# Display image from web
"${PATH_TO_FOLDER}/bin/python" "${PATH_TO_FOLDER}/screen/display.py" "$BATTERY_STATUS"

# Shutdown message
echo "$(date +"%Y-%m-%d %H:%M:%S") - Script complete - shutting down "

# Shutdown 1 min
sudo shutdown -h +1