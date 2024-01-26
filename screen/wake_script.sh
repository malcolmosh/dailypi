#!/bin/bash

set -e

# Shutdown after n seconds
SHUTDOWN_AFTER=180

# URL to ping to check network
URL="www.google.com"

# Function to test connectivity
is_online() {
    ping -q -c 1 -w 2 "$URL" >/dev/null 2>&1
    return $?
}

# Function to set the RTC alarm
set_alarm() {
    # 4 retries * 30 seconds sleep = 2 minutes
    MAX_RETRIES=4
    RETRY_COUNT=0
    
    while ! is_online "$URL" && [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        current_time=$(date +"%Y-%m-%d %H:%M:%S")
        echo "At [$current_time], failed test to $URL, waiting for connectivity..."
        sleep 30
        RETRY_COUNT=$((RETRY_COUNT+1))
    done

    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        echo "Failed to connect to $URL after $MAX_RETRIES attempts. Exiting."
        exit 1
    fi

    local time="$1"
    local repeat="$2"
    r=$(echo "rtc_alarm_set ${time} ${repeat}" | nc -q 0 127.0.0.1 8423)
    if [[ x"$r" =~ "done" ]]; then
        /home/osher/.dashboard_pi_env/bin/python /home/osher/.dashboard_pi_env/screen/display.py
        sleep $SHUTDOWN_AFTER
        sudo shutdown -h now
    else
        echo "Set RTC wakeup time error"
        exit 1
    fi
}

rtc_time=$(echo "get rtc_time" | nc -q 0 127.0.0.1 8423)

if [[ x"$rtc_time" =~ "rtc_time:" ]]; then
    rtc_time=${rtc_time#*" "}
    rtc_date=$(date -d "$rtc_time" +%Y-%m-%d)
    rtc_hour=$(date -d "$rtc_time" +%H:%M)
else
    echo "Get RTC time error"
    exit 1
fi

timezone_offset=$(date +"%:z")
current_date=$(date +"%Y-%m-%d")
current_hour=$(date +"%-H")

if [[ $(date -d "$current_date 02:00:00" +"%Z") == "EDT" ]] && (( current_hour == 1 )); then
    current_hour=$((current_hour + 1))
fi

if (( current_hour < 6 )); then
    next_alarm="${rtc_date}T06:02:00${timezone_offset}"
elif (( current_hour < 12 )); then
    next_alarm="${rtc_date}T12:02:00${timezone_offset}"
elif (( current_hour < 20 )); then
    next_alarm="${rtc_date}T20:02:00${timezone_offset}"
else
    # Calculate next date for setting the alarm
    next_date=$(date --date='next day' +"%Y-%m-%d")
    next_alarm="${next_date}T06:02:00${timezone_offset}"
fi

set_alarm "$next_alarm" 127
