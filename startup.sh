#!/bin/sh
# Startup Bash script for our timelapse project.
# To schedule this to run on reboot on your Raspberry Pi:
# sudo crontab -e
# add the line below to your file:
# @reboot sh /home/rob/timelapse/startup.sh >/home/rob/timelapse/logs/cronlog 2>&1
# This executes the startup.sh script upon reboot

# Get to the correct directory
cd /home/rob/timelapse/
# Create the logs directory if it does not exist.
mkdir -p logs
# Start a TMUX session named "take_photos"
tmux new -s take_photos
# Activate the correct environment
source timelapse/bin/activate
# Start our Python code
python timelapse.py