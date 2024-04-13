#!/bin/bash

# This is a bash script that programs a next wake-up alarm on the PiSugar2 battery for the Raspberry Pi Zero W

set -e

# Configuration variables
URL="http://clients3.google.com/generate_204" # URL to ping to check network
MAX_RETRIES=4 # Retries for the online connectivity check
RETRY_COUNT=0

# Function to test network connectivity
is_online() {
    wget -q --spider "$URL"
    return $?
}

# Function to set the RTC alarm 
set_alarm() {
    local time="$1"  # First argument provided to the function is the time to set the alarm
    local repeat="$2" # Second argument is the repeat interval
    
    # Send a command to the PiSugar module to set the alarm 
    r=$(echo "rtc_alarm_set ${time} ${repeat}" | nc -q 0 127.0.0.1 8423)
    
    # Success message
    if [[ x"$r" =~ "done" ]]; then
        echo "$rtc_time - Alarm set for [$time]"
        exit 0
    else
        echo "$rtc_time - Error while setting alarm"
        exit 1
    fi
}


# Check whether system is online, if not wait 15 seconds
while ! is_online; do
    current_time=$(date +"%Y-%m-%d %H:%M:%S") # Store initial time at start of loop
    echo "[$current_time] - Failed test to $URL, waiting for connectivity..."
    sleep 15
    RETRY_COUNT=$((RETRY_COUNT+1)) # Increment counter
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "[$current_time] - Failed to connect to $URL after $MAX_RETRIES attempts. Exiting."
        exit 1 # exit with an error
    fi
done

# Store time before RTC sync
initial_time=$(echo "get rtc_time" | nc -q 0 127.0.0.1 8423)

# when network is up, sync the RTC clock to the Pi, as the RTC clock can drift
echo 'rtc_pi2rtc' | nc -q 0 127.0.0.1 8423

# store the rtc time
rtc_time=$(echo "get rtc_time" | nc -q 0 127.0.0.1 8423)

# Note time drift
echo "$rtc_time - RTC clock synced to Pi, previous time was $initial_time"

# Check if response from module starts with the right string, if yes, store variables
if [[ x"$rtc_time" =~ "rtc_time:" ]]; then
    rtc_time=${rtc_time#*" "}  # time value
    rtc_date=$(date -d "$rtc_time" +%Y-%m-%d) # date 
    rtc_hour=$(date -d "$rtc_time" +%H:%M) # hour
else
    echo "Get RTC time error"
    exit 1
fi

timezone_offset=$(date +"%:z") # Get the current timezone offset from UTC time
current_date=$(date +"%Y-%m-%d") # Get the current date in YYYY-MM-DD
current_hour=$(date +"%-H") # Get the current hour in 24-hour format

# Check if the timezone at 2 AM on current date is EDT and if the current hour is 1
if [[ $(date -d "$current_date 02:00:00" +"%Z") == "EDT" ]] && (( current_hour == 1 )); then
    # If yes, set the current hour to 3, as the clock will move forward by 1 hour
    current_hour=$((current_hour + 1))
fi

# Set the next alarm based on the current hour
if (( current_hour < 6 )); then
    next_alarm="${rtc_date}T06:01:00${timezone_offset}"
# elif (( current_hour < 12 )); then
#     next_alarm="${rtc_date}T12:02:00${timezone_offset}"
elif (( current_hour < 18 )); then
    next_alarm="${rtc_date}T18:01:00${timezone_offset}"
else
    # Calculate next date for setting the alarm
    next_date=$(date --date='next day' +"%Y-%m-%d")
    next_alarm="${next_date}T06:01:00${timezone_offset}"
fi

set_alarm "$next_alarm" 127 # 127 means repeat every day
